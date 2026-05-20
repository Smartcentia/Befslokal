"""
Model registry: holds the trained predictor in memory and persists metadata to JSON.

The model itself lives in process memory (no binary serialization).
With ~500-1500 training rows retraining takes < 2 seconds and is triggered via
POST /api/v1/ml/train – either manually or automatically when new GL data is imported.

Metadata (metrics, feature importances, training timestamp) is persisted to a JSON
file so the status endpoint works across restarts without re-training.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from app.services.ml.cross_sectional_model import CrossSectionalPredictor

logger = logging.getLogger(__name__)

_METADATA_PATH = os.path.join(os.path.dirname(__file__), "model_metadata.json")


class ModelRegistry:
    """
    Singleton holding the trained CrossSectionalPredictor.

    Usage:
        registry = get_registry()
        if registry.is_ready:
            predictions = registry.predictor.predict_with_explanations(...)
    """

    def __init__(self) -> None:
        self._predictor: CrossSectionalPredictor | None = None
        self._trained_at: str | None = None
        self._data_through_year: int | None = None
        self._metadata: dict[str, Any] = {}
        self._load_metadata()

    @property
    def is_ready(self) -> bool:
        return self._predictor is not None and self._predictor.is_trained

    @property
    def predictor(self) -> CrossSectionalPredictor:
        if not self.is_ready:
            raise RuntimeError("Model not trained. Call /api/v1/ml/train first.")
        return self._predictor  # type: ignore

    @property
    def status(self) -> dict[str, Any]:
        base: dict[str, Any] = {
            "trained_in_memory": self.is_ready,
            "trained_at": self._trained_at,
            "data_through_year": self._data_through_year,
        }
        if self._predictor and self._predictor.training_result:
            tr = self._predictor.training_result
            base.update({
                "model_type": tr.model_type,
                "n_samples": tr.n_samples,
                "n_features": tr.n_features,
                "mae_nok": round(tr.mae),
                "mape_pct": round(tr.mape, 1),
                "r2": round(tr.r2, 3),
                "cv_mae_mean": round(tr.cv_mae_mean),
                "cv_mae_std": round(tr.cv_mae_std),
            })
        elif self._metadata:
            base.update(self._metadata)
            base["trained_in_memory"] = False
            base["note"] = (
                "Metadata fra forrige trening. "
                "Kjør POST /api/v1/ml/train for å laste modellen i minnet igjen."
            )
        return base

    def set_predictor(self, predictor: CrossSectionalPredictor, data_through_year: int) -> None:
        """Store a newly trained predictor and persist its metadata to JSON."""
        self._predictor = predictor
        self._trained_at = datetime.now(timezone.utc).isoformat()
        self._data_through_year = data_through_year

        if predictor.training_result:
            tr = predictor.training_result
            self._metadata = {
                "model_type": tr.model_type,
                "n_samples": tr.n_samples,
                "n_features": tr.n_features,
                "mae_nok": round(tr.mae),
                "mape_pct": round(tr.mape, 1),
                "r2": round(tr.r2, 3),
                "cv_mae_mean": round(tr.cv_mae_mean),
                "cv_mae_std": round(tr.cv_mae_std),
                "trained_at": self._trained_at,
                "data_through_year": data_through_year,
                "feature_importances": tr.feature_importances,
            }
            self._save_metadata()

    def clear(self) -> None:
        """Remove the in-memory model (metadata is kept on disk)."""
        self._predictor = None
        logger.info("Model registry cleared from memory")

    def _save_metadata(self) -> None:
        try:
            with open(_METADATA_PATH, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.debug("Could not save model metadata: %s", exc)

    def _load_metadata(self) -> None:
        try:
            if os.path.exists(_METADATA_PATH):
                with open(_METADATA_PATH, encoding="utf-8") as f:
                    self._metadata = json.load(f)
                self._trained_at = self._metadata.get("trained_at")
                self._data_through_year = self._metadata.get("data_through_year")
        except Exception as exc:
            logger.debug("Could not load model metadata: %s", exc)


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
