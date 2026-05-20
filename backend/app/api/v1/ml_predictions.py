"""
ML Prediction API – cross-sectional cost forecasting with SHAP explanations.

Endpoints:
  POST /api/v1/ml/train            – (re)train on all available GL data (ADMIN)
  GET  /api/v1/ml/status           – model status and metrics
  GET  /api/v1/ml/predict/{pid}    – predict + explain for one property
  GET  /api/v1/ml/benchmark        – portfolio ranking (all properties vs. regional avg)
  GET  /api/v1/ml/feature-importance – global feature importance

Retraining is also designed to be triggered programmatically after a GL data import.
Call `await trigger_retrain(db)` from any other service to keep the model current.
"""

import asyncio
import logging
from typing import Any

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.services.ml.cross_sectional_model import CrossSectionalPredictor
from app.services.ml.feature_engineering import (
    FEATURE_COLS,
    build_prediction_features,
    build_training_matrix,
    extract_X_y,
)
from app.services.ml.model_registry import get_registry

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: run training (sync ML code) in a thread to avoid blocking event loop
# ---------------------------------------------------------------------------

async def _run_training(db: AsyncSession) -> dict[str, Any]:
    """Fetch data, train model, register result. Returns status dict."""
    registry = get_registry()

    # 1. Build feature matrix (async DB queries)
    df = await build_training_matrix(db)

    if df.empty:
        raise ValueError("Ingen treningsdata tilgjengelig. Sjekk at GL-transaksjoner er importert.")

    if len(df) < 10:
        raise ValueError(
            f"For lite treningsdata ({len(df)} rader). "
            "Modellen trenger minst 10 (property, år, kategori)-kombinasjoner."
        )

    X, y, feature_names = extract_X_y(df)

    # 2. Train model (CPU-bound, run in thread to not block FastAPI)
    predictor = CrossSectionalPredictor()
    loop = asyncio.get_event_loop()
    training_result = await loop.run_in_executor(
        None, lambda: predictor.train(X, y, feature_names)
    )

    # 3. Determine latest data year
    data_through_year = int(df["target_year"].max()) if "target_year" in df.columns else 2025

    # 4. Store in registry
    registry.set_predictor(predictor, data_through_year)

    return {
        "status": "ok",
        "message": f"Modell trent på {training_result.n_samples} datapunkter",
        **registry.status,
    }


# ---------------------------------------------------------------------------
# Public helper: call from import_api.py to auto-retrain after new data
# ---------------------------------------------------------------------------

async def trigger_retrain(db: AsyncSession) -> None:
    """
    Trigger a model retrain in the background.
    Call this from the GL import endpoint after successful data import.

    Example usage in import_api.py:
        from app.api.v1.ml_predictions import trigger_retrain
        asyncio.create_task(trigger_retrain(db))
    """
    try:
        await _run_training(db)
        logger.info("ML model auto-retrained after data import")
    except Exception as exc:
        logger.warning("Auto-retrain failed (non-critical): %s", exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/train", response_model=dict[str, Any])
async def train_model(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    (Re)tren ML-modellen på alle tilgjengelige GL-data.

    Kjøres automatisk etter GL-dataimport, eller manuelt av admin.
    Trenings-tid: typisk < 5 sekunder med nåværende datamengde.

    Krever ADMIN-rolle.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kun administratorer kan trene ML-modellen",
        )

    try:
        result = await _run_training(db)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.error("Model training failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trening feilet: {exc}",
        )


@router.get("/status", response_model=dict[str, Any])
async def model_status(
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer modellstatus: om modellen er trent, metrikker (MAE, R²), og treningsdato.

    Dersom modellen ikke er i minnet vises metadata fra forrige trening (hvis tilgjengelig).
    """
    return get_registry().status


@router.get("/feature-importance", response_model=list[dict[str, Any]])
async def feature_importance(
    current_user: User = Depends(get_current_user),
):
    """
    Globale feature-importances: hvilke egenskaper er mest avgjørende for kostnadsforskjeller?

    Sortert etter relativ påvirkning (høyest øverst).
    """
    registry = get_registry()
    if not registry.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modellen er ikke trent. Kjør POST /api/v1/ml/train først.",
        )
    return registry.predictor.get_feature_importance_summary()


@router.get("/predict/{property_id}", response_model=dict[str, Any])
async def predict_property(
    property_id: str,
    target_year: int = Query(default=2026, ge=2025, le=2035),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Prediker kostnader for én eiendom med SHAP-baserte forklaringer.

    Returnerer:
    - Predikert årsbeløp per SRS-kategori (Drift, Investering, etc.)
    - De 3 viktigste driverne: "Hvorfor er denne eiendommen X NOK over/under snitt?"
    - Sammenligning mot Holt's Linear (dersom tilgjengelig)
    - Benchmark mot regionalt gjennomsnitt
    """
    registry = get_registry()
    if not registry.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modellen er ikke trent. Kjør POST /api/v1/ml/train først.",
        )

    # Build prediction features for this property
    pred_df = await build_prediction_features(db, target_year=target_year)
    if pred_df.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingen data funnet for denne eiendommen",
        )

    prop_rows = pred_df[pred_df["property_id"] == property_id]
    if prop_rows.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Eiendom {property_id} ikke funnet eller mangler data",
        )

    X, _, feature_names = extract_X_y(prop_rows.copy())
    property_ids = prop_rows["property_id"].tolist()
    categories = prop_rows["category"].tolist()

    results = registry.predictor.predict_with_explanations(X, property_ids, categories)

    # --- Regional benchmark (for context) ---
    all_pred_df = pred_df.copy()
    # Get region of this property
    region = None
    if "region_nord" in prop_rows.columns:
        region_cols = [c for c in prop_rows.columns if c.startswith("region_")]
        for col in region_cols:
            if prop_rows[col].iloc[0] == 1:
                region = col.replace("region_", "").replace("_", " ")
                break

    # Predict for all in same region for benchmark (best-effort, silently skip errors)
    region_total_avg = None
    try:
        region_df = pred_df.copy()
        if region:
            region_col = f"region_{region.lower().replace(' ', '_').replace('-', '_')}"
            if region_col in region_df.columns:
                region_df = region_df[region_df[region_col] == 1]

        if len(region_df) > 1:
            X_reg, _, _ = extract_X_y(region_df.copy())
            pids_reg = region_df["property_id"].tolist()
            cats_reg = region_df["category"].tolist()
            reg_results = registry.predictor.predict_with_explanations(X_reg, pids_reg, cats_reg)

            # Aggregate: total per property
            from collections import defaultdict
            totals_by_prop: dict[str, float] = defaultdict(float)
            for r in reg_results:
                totals_by_prop[r.property_id] += r.predicted_annual

            unique_props = list(totals_by_prop.values())
            region_total_avg = float(np.mean(unique_props)) if unique_props else None
    except Exception as exc:
        logger.debug("Regional benchmark failed (non-critical): %s", exc)

    # --- Build response ---
    predictions_by_cat: dict[str, dict] = {}
    grand_total = 0.0

    for res in results:
        predictions_by_cat[res.category] = {
            "predicted_annual_nok": round(res.predicted_annual),
            "top_drivers": [
                {
                    "feature": d["feature"],
                    "raw_value": d["raw_value"],
                    "contribution_nok": d["contribution_nok"],
                    "direction": d["direction"],
                }
                for d in res.top_drivers
            ],
        }
        grand_total += res.predicted_annual

    # Property name from df (if available)
    prop_name = None
    if "name" in prop_rows.columns:
        prop_name = prop_rows["name"].iloc[0] if not prop_rows.empty else None

    benchmark = None
    if region_total_avg is not None:
        deviation_nok = grand_total - region_total_avg
        deviation_pct = (deviation_nok / region_total_avg * 100) if region_total_avg else 0
        benchmark = {
            "region": region,
            "region_avg_total_nok": round(region_total_avg),
            "this_property_total_nok": round(grand_total),
            "deviation_nok": round(deviation_nok),
            "deviation_pct": round(deviation_pct, 1),
            "assessment": (
                "over_snitt" if deviation_pct > 10
                else "under_snitt" if deviation_pct < -10
                else "nær_snitt"
            ),
        }

    return {
        "property_id": property_id,
        "property_name": prop_name,
        "target_year": target_year,
        "predicted_total_nok": round(grand_total),
        "predictions_by_category": predictions_by_cat,
        "benchmark": benchmark,
        "model": {
            "type": registry.status.get("model_type"),
            "trained_at": registry.status.get("trained_at"),
            "mae_nok": registry.status.get("mae_nok"),
            "r2": registry.status.get("r2"),
            "explanation_method": "shap_tree_explainer" if registry.predictor._shap_explainer is not None else "feature_importance_approx",
        },
    }


@router.get("/benchmark", response_model=dict[str, Any])
async def portfolio_benchmark(
    target_year: int = Query(default=2026, ge=2025, le=2035),
    region: str | None = Query(default=None, description="Filter på region (valgfritt)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Portfolio-rangering: alle eiendommer sortert etter avvik fra regionalt gjennomsnitt.

    Nyttig for å identifisere eiendommer med uforklart høye kostnader.
    """
    registry = get_registry()
    if not registry.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modellen er ikke trent. Kjør POST /api/v1/ml/train først.",
        )

    pred_df = await build_prediction_features(db, target_year=target_year)
    if pred_df.empty:
        return {"properties": [], "target_year": target_year}

    # Optional region filter
    if region:
        region_col = f"region_{region.lower().replace(' ', '_').replace('-', '_')}"
        if region_col in pred_df.columns:
            pred_df = pred_df[pred_df[region_col] == 1]

    X, _, feature_names = extract_X_y(pred_df.copy())
    pids = pred_df["property_id"].tolist()
    cats = pred_df["category"].tolist()

    results = registry.predictor.predict_with_explanations(X, pids, cats)

    # Aggregate total per property
    from collections import defaultdict
    totals_by_prop: dict[str, float] = defaultdict(float)
    region_by_prop: dict[str, str] = {}
    for i, res in enumerate(results):
        totals_by_prop[res.property_id] += res.predicted_annual
        # Recover region label from one-hot
        row = pred_df.iloc[i]
        for col in [c for c in pred_df.columns if c.startswith("region_")]:
            if row.get(col, 0) == 1:
                region_by_prop[res.property_id] = col.replace("region_", "").replace("_", " ")
                break

    # Regional averages
    from collections import defaultdict as dd
    region_totals: dict[str, list[float]] = dd(list)
    for pid, total in totals_by_prop.items():
        reg = region_by_prop.get(pid, "Ukjent")
        region_totals[reg].append(total)

    region_avg: dict[str, float] = {
        reg: float(np.mean(vals)) for reg, vals in region_totals.items()
    }

    # Build response
    props_list = []
    for pid, total in totals_by_prop.items():
        reg = region_by_prop.get(pid, "Ukjent")
        avg = region_avg.get(reg, total)
        dev_nok = total - avg
        dev_pct = (dev_nok / avg * 100) if avg > 0 else 0.0
        props_list.append({
            "property_id": pid,
            "region": reg,
            "predicted_total_nok": round(total),
            "region_avg_nok": round(avg),
            "deviation_nok": round(dev_nok),
            "deviation_pct": round(dev_pct, 1),
            "assessment": (
                "over_snitt" if dev_pct > 10
                else "under_snitt" if dev_pct < -10
                else "nær_snitt"
            ),
        })

    # Sort by absolute deviation (most unusual first)
    props_list.sort(key=lambda x: abs(x["deviation_pct"]), reverse=True)

    return {
        "target_year": target_year,
        "n_properties": len(props_list),
        "region_filter": region,
        "region_averages": {k: round(v) for k, v in region_avg.items()},
        "properties": props_list,
    }
