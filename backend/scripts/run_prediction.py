#!/usr/bin/env python3
"""
Standalone prediction runner — kjøres direkte i Railway-miljøet via:
  railway run --service striking-insight python scripts/run_prediction.py

Scenario-suffiks (budget.data_source = holt_winters_2027_<tag>):
  xgb70 (standard):  PREDICTION_DATA_SOURCE_TAG ikke satt eller xgb70
  xgb50: PREDICTION_DATA_SOURCE_TAG=xgb50 railway run ... python scripts/run_prediction.py

Excel-eksporten forventer begge kildene (xgb70 og xgb50) for «XGB Gulv 70%» / «XGB Gulv 50%».
Kjør scriptet to ganger med hvert sitt tag hvis 50 %-kolonnen skal fylles.

Bypasser HTTP fullstendig — ingen timeout-problemer.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    from app.db.session import SessionLocal
    from app.services.prediction_service import BudgetPredictionService

    tag = (os.environ.get("PREDICTION_DATA_SOURCE_TAG") or "xgb70").strip() or "xgb70"
    if tag not in ("xgb70", "xgb50"):
        logger.error("PREDICTION_DATA_SOURCE_TAG må være xgb70 eller xgb50, fikk %r", tag)
        sys.exit(2)

    params = dict(
        target_year=2027,
        alpha=0.5,              # Senket fra 0.7 – balansert historisk vekting
        beta=0.2,               # Senket fra 0.3 – forsiktig trendoppdatering
        inflation=0.035,
        phi=0.85,
        max_growth_factor=5.0,
        cold_start_ratio=1.5,   # Senket fra 2.0 – 50% vekst maks for ramp-up eiendommer
        max_annual_growth=0.08, # 8%/år = maks 16,6% over 2 år – hindrer krisestrendekstrapolering
        history_from=2021,
        data_source_tag=tag,    # holt_winters_2027_xgb70 eller holt_winters_2027_xgb50
        apply_cpi=True,             # Prisjuster historikk til 2025-NOK (SSB KPI)
        passthrough_categories=frozenset({"property"}),  # Gjennomstrømning → kun inflasjon
        likebefore_min_years=3,     # Eiendommer med < 3 år → inflasjonsfallback
    )

    logger.info("Starter prediksjon med forbedrede parametre: %s", params)
    async with SessionLocal() as db:
        result = await BudgetPredictionService.predict_all_properties(db=db, **params)

    logger.info("Ferdig: %s", result)
    if result.get("errors"):
        logger.warning("Feil: %s", result["errors"])
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
