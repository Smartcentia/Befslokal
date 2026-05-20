"""
Salary Cost Prediction Service – Holt's Linear Exponential Smoothing (Double)

Predicts 2027 (or any target year) salary costs per property using annual data
from salary_costs table (2020–2025).

Algorithm: Same _holt_linear_forecast() from prediction_service.py, with
salary-tuned parameters:
  - SALARY_INFLATION     = 0.045   (NHO/SSB lønnsvekst ~4,5 %)
  - SALARY_COLD_START    = 1.5     (lønn har ikke ramp-up-fenomen)
  - SALARY_MAX_GROWTH    = 3.0     (lønn kan ikke tredobles på 2 år)

Strategy:
  - Predict total (faste + vikarer + aga) with Holt-Winters
  - Distribute proportionally using 2025 component ratios
  - Store in salary_costs with year=target_year, import_batch_id='holt_winters_XXXX'
"""

import logging
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.prediction_service import _holt_linear_forecast

logger = logging.getLogger(__name__)

# Salary-specific parameters
SALARY_INFLATION = 0.045       # NHO/SSB lønnsvekst 2026
SALARY_COLD_START = 1.5        # Lav – lønn har ikke ramp-up-fenomen
SALARY_MAX_GROWTH = 3.0        # Lønn kan ikke tredobles på 2 år
SALARY_ALPHA = 0.7             # Level smoothing
SALARY_BETA = 0.3              # Trend smoothing
SALARY_PHI = 0.85              # Damping factor


class SalaryPredictionService:
    """Generates Holt-Winters salary predictions per property and upserts to salary_costs."""

    @staticmethod
    async def _fetch_salary_history(
        db: AsyncSession,
        from_year: int,
        to_year: int,
    ) -> dict[str, dict[int, dict]]:
        """
        Returns: { property_id: { year: { faste, vikarer, aga, total } } }
        """
        try:
            result = await db.execute(text("""
                SELECT
                    property_id::text,
                    year,
                    COALESCE(faste_stillinger, 0) AS faste,
                    COALESCE(vikarer, 0) AS vikarer,
                    COALESCE(arbeidsgiveravgift, 0) AS aga
                FROM salary_costs
                WHERE year BETWEEN :from_year AND :to_year
                  AND property_id IS NOT NULL
                ORDER BY property_id, year
            """), {"from_year": from_year, "to_year": to_year})
            rows = result.fetchall()
        except Exception as exc:
            logger.debug("salary_costs query failed: %s", exc)
            return {}

        history: dict[str, dict[int, dict]] = {}
        for row in rows:
            pid = str(row[0])
            year = int(row[1])
            faste = float(row[2] or 0)
            vikarer = float(row[3] or 0)
            aga = float(row[4] or 0)
            total = faste + vikarer + aga

            if pid not in history:
                history[pid] = {}
            history[pid][year] = {
                "faste_stillinger": faste,
                "vikarer": vikarer,
                "aga": aga,
                "total": total,
            }

        return history

    @classmethod
    async def predict_all_properties(
        cls,
        db: AsyncSession,
        target_year: int = 2027,
        history_from: int = 2020,
        alpha: float = SALARY_ALPHA,
        beta: float = SALARY_BETA,
        phi: float = SALARY_PHI,
        inflation: float = SALARY_INFLATION,
        max_growth_factor: float = SALARY_MAX_GROWTH,
        cold_start_ratio: float = SALARY_COLD_START,
    ) -> dict[str, Any]:
        """
        Runs Holt's Linear prediction for every property with salary history,
        then upserts results into salary_costs with year=target_year.

        Returns: { processed, skipped, total_predicted, year }
        """
        last_history_year = target_year - 2   # e.g. 2025 for target 2027
        import_batch_id = f"holt_winters_{target_year}"

        history = await cls._fetch_salary_history(db, history_from, last_history_year)

        if not history:
            logger.debug("No salary history found for %d–%d", history_from, last_history_year)
            return {"processed": 0, "skipped": 0, "total_predicted": 0.0, "year": target_year}

        processed = 0
        skipped = 0
        total_predicted = 0.0

        for property_id, yr_data in history.items():
            try:
                years_available = sorted(yr_data.keys())
                if not years_available:
                    skipped += 1
                    continue

                # Build chronological series of total salary (fill gaps with 0)
                full_range = list(range(years_available[0], years_available[-1] + 1))
                series = [yr_data.get(yr, {}).get("total", 0.0) for yr in full_range]

                # Horizon = how many years ahead from last data point
                horizon = target_year - years_available[-1]
                if horizon <= 0:
                    logger.debug("property=%s: target_year %d already in history, skipping", property_id, target_year)
                    skipped += 1
                    continue

                n = len(series)
                if n == 0 or all(v == 0 for v in series):
                    skipped += 1
                    continue
                elif n == 1:
                    predicted_total = series[0] * (1 + inflation * horizon)
                    method = "inflation_fallback"
                else:
                    predicted_total, method = _holt_linear_forecast(
                        series,
                        alpha=alpha,
                        beta=beta,
                        horizon=horizon,
                        phi=phi,
                        max_growth_factor=max_growth_factor,
                        cold_start_ratio=cold_start_ratio,
                    )

                logger.debug(
                    "salary property=%s years=%s method=%s predicted=%.0f",
                    property_id, years_available, method, predicted_total,
                )

                # Proportional component split from most recent year with data
                last_year = years_available[-1]
                last = yr_data.get(last_year, {})
                last_total = last.get("total", 0.0) or predicted_total or 1.0

                if last_total > 0:
                    faste_ratio = last.get("faste_stillinger", 0.0) / last_total
                    vikarer_ratio = last.get("vikarer", 0.0) / last_total
                    aga_ratio = last.get("aga", 0.0) / last_total
                else:
                    # Default 80/5/15 split if no history
                    faste_ratio, vikarer_ratio, aga_ratio = 0.80, 0.05, 0.15

                predicted_faste = predicted_total * faste_ratio
                predicted_vikarer = predicted_total * vikarer_ratio
                predicted_aga = predicted_total * aga_ratio

                # Upsert into salary_costs
                await db.execute(text("""
                    INSERT INTO salary_costs (
                        salary_cost_id, property_id, year,
                        faste_stillinger, vikarer, arbeidsgiveravgift,
                        institution_name_raw, import_batch_id, imported_at
                    )
                    VALUES (
                        :id, :pid, :year,
                        :faste, :vikarer, :aga,
                        NULL, :batch_id, now()
                    )
                    ON CONFLICT (property_id, year) DO UPDATE SET
                        faste_stillinger = EXCLUDED.faste_stillinger,
                        vikarer = EXCLUDED.vikarer,
                        arbeidsgiveravgift = EXCLUDED.arbeidsgiveravgift,
                        import_batch_id = EXCLUDED.import_batch_id,
                        imported_at = EXCLUDED.imported_at
                """), {
                    "id": str(uuid.uuid4()),
                    "pid": property_id,
                    "year": target_year,
                    "faste": round(predicted_faste, 2),
                    "vikarer": round(predicted_vikarer, 2),
                    "aga": round(predicted_aga, 2),
                    "batch_id": import_batch_id,
                })

                total_predicted += predicted_total
                processed += 1

            except Exception as exc:
                logger.debug("Salary prediction failed for property=%s: %s", property_id, exc)
                await db.rollback()
                skipped += 1
                continue

        await db.commit()
        logger.debug(
            "Salary prediction done: processed=%d skipped=%d total=%.0f year=%d",
            processed, skipped, total_predicted, target_year,
        )
        return {
            "processed": processed,
            "skipped": skipped,
            "total_predicted": round(total_predicted, 0),
            "year": target_year,
        }
