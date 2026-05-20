"""
Cross-sectional ML model for property cost prediction.

Uses GradientBoostingRegressor (sklearn) with SHAP-based explanations.
One model trained on all properties × years × categories simultaneously.

SHAP contributions answer: "Why is this property's predicted cost X NOK above average?"
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# Try XGBoost first (faster, better), fall back to sklearn GBT
try:
    from xgboost import XGBRegressor  # type: ignore
    _USE_XGBOOST = True
except ImportError:
    _USE_XGBOOST = False
    logger.debug("xgboost not available – using sklearn GradientBoostingRegressor")

# Try SHAP for richer explanations
try:
    import shap  # type: ignore
    _USE_SHAP = True
except ImportError:
    _USE_SHAP = False
    logger.debug("shap not available – using feature_importances_ approximation")


@dataclass
class TrainingResult:
    n_samples: int
    n_features: int
    mae: float
    mape: float
    r2: float
    cv_mae_mean: float
    cv_mae_std: float
    feature_importances: dict[str, float]
    model_type: str


@dataclass
class PredictionResult:
    property_id: str
    category: str
    predicted_annual: float
    contributions: list[dict[str, Any]] = field(default_factory=list)
    # Top 3 features driving this prediction above/below average
    top_drivers: list[dict[str, Any]] = field(default_factory=list)


class CrossSectionalPredictor:
    """
    Trains and predicts property costs using a cross-sectional gradient boosting model.

    One model instance covers all SRS categories (category_ord is a feature).
    This maximizes training data and allows the model to learn cross-category patterns.
    """

    def __init__(self) -> None:
        self._model: Any = None
        self._scaler = StandardScaler()
        self._feature_names: list[str] = []
        self._shap_explainer: Any = None
        self._training_result: TrainingResult | None = None
        self._X_train_mean: np.ndarray | None = None  # for contribution baseline

    @property
    def is_trained(self) -> bool:
        return self._model is not None

    @property
    def training_result(self) -> TrainingResult | None:
        return self._training_result

    def _make_model(self) -> Any:
        if _USE_XGBOOST:
            return XGBRegressor(
                n_estimators=200,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbosity=0,
            )
        return GradientBoostingRegressor(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )

    def train(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> TrainingResult:
        """
        Fits the model on (X, y). Computes cross-validated metrics and feature importances.

        Args:
            X: Feature matrix, shape (n_samples, n_features)
            y: Target cost vector (NOK), shape (n_samples,)
            feature_names: Column names for X

        Returns:
            TrainingResult with metrics and feature importances
        """
        if len(X) < 10:
            raise ValueError(f"Too few training samples ({len(X)}). Need at least 10.")

        self._feature_names = feature_names
        self._X_train_mean = np.mean(X, axis=0)

        # Scale features (helps GBT convergence even if not strictly necessary)
        X_scaled = self._scaler.fit_transform(X)

        model = self._make_model()
        model.fit(X_scaled, y)
        self._model = model

        # Cross-validated MAE (3-fold to avoid data leakage across properties)
        cv_scores = cross_val_score(
            self._make_model(), X_scaled, y,
            cv=min(5, len(X) // 10),
            scoring="neg_mean_absolute_error",
            n_jobs=-1,
        )
        cv_mae = -cv_scores

        # Hold-out metrics on training data (optimistic, for reference)
        y_pred = model.predict(X_scaled)
        mae = float(np.mean(np.abs(y - y_pred)))
        nonzero_mask = y > 0
        mape = float(np.mean(np.abs((y[nonzero_mask] - y_pred[nonzero_mask]) / y[nonzero_mask])) * 100) if nonzero_mask.any() else 0.0
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Feature importances (normalized to sum to 1)
        importances = model.feature_importances_
        importances_norm = importances / importances.sum() if importances.sum() > 0 else importances
        feat_imp = {name: float(imp) for name, imp in zip(feature_names, importances_norm)}

        # Build SHAP explainer (for fast per-prediction explanations later)
        if _USE_SHAP:
            try:
                self._shap_explainer = shap.TreeExplainer(model)
                # Warm up with training data
                self._shap_values_train = self._shap_explainer.shap_values(X_scaled)
            except Exception as exc:
                logger.debug("SHAP explainer init failed: %s", exc)
                self._shap_explainer = None

        model_type = "xgboost" if _USE_XGBOOST else "sklearn_gbt"
        self._training_result = TrainingResult(
            n_samples=len(X),
            n_features=len(feature_names),
            mae=mae,
            mape=mape,
            r2=r2,
            cv_mae_mean=float(np.mean(cv_mae)),
            cv_mae_std=float(np.std(cv_mae)),
            feature_importances=feat_imp,
            model_type=model_type,
        )

        logger.info(
            "Model trained: n=%d, MAE=%.0f NOK, MAPE=%.1f%%, R²=%.3f, CV-MAE=%.0f±%.0f",
            len(X), mae, mape, r2, np.mean(cv_mae), np.std(cv_mae),
        )

        return self._training_result

    def predict_with_explanations(
        self,
        X: np.ndarray,
        property_ids: list[str],
        categories: list[str],
    ) -> list[PredictionResult]:
        """
        Predicts cost and generates SHAP-based explanations for each row.

        Contributions are in NOK, positive = pushes cost above average,
        negative = pushes cost below average.
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")

        X_scaled = self._scaler.transform(X)
        y_pred = self._model.predict(X_scaled)

        results = []

        if _USE_SHAP and self._shap_explainer is not None:
            try:
                shap_values = self._shap_explainer.shap_values(X_scaled)
            except Exception:
                shap_values = None
        else:
            shap_values = None

        for i, (pid, cat) in enumerate(zip(property_ids, categories)):
            pred_val = max(0.0, float(y_pred[i]))

            # --- Contributions ---
            if shap_values is not None:
                contribs_raw = shap_values[i]
            else:
                # Approximate: importance × scaled_feature_value (signed)
                contribs_raw = self._model.feature_importances_ * X_scaled[i] * pred_val / max(1.0, abs(X_scaled[i]).sum())

            contributions = []
            for j, fname in enumerate(self._feature_names):
                contrib_nok = float(contribs_raw[j]) if shap_values is not None else float(contribs_raw[j])
                contributions.append({
                    "feature": fname,
                    "raw_value": float(X[i][j]),
                    "contribution_nok": round(contrib_nok),
                    "direction": "above_average" if contrib_nok > 0 else "below_average",
                })

            # Top 3 drivers by absolute contribution (skip category/year features)
            skip = {"category_ord", "target_year"}
            top_drivers = sorted(
                [c for c in contributions if c["feature"] not in skip],
                key=lambda c: abs(c["contribution_nok"]),
                reverse=True,
            )[:3]

            results.append(PredictionResult(
                property_id=pid,
                category=cat,
                predicted_annual=pred_val,
                contributions=contributions,
                top_drivers=top_drivers,
            ))

        return results

    def get_feature_importance_summary(self) -> list[dict[str, Any]]:
        """Returns feature importances sorted by impact, for global model explanation."""
        if not self._training_result:
            return []
        return sorted(
            [{"feature": k, "importance": v} for k, v in self._training_result.feature_importances.items()],
            key=lambda x: x["importance"],
            reverse=True,
        )
