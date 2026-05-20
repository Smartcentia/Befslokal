"""
Budget Prediction Service – Holt's Linear Exponential Smoothing (Double)

Predicts 2027 (or any target year) budgets per property using annual GL-data.
Gives exponentially more weight to recent years (α=0.7 default).

Algorithm: Holt's Linear Method (no third-party deps)
  L_t = α * y_t + (1 - α) * (L_{t-1} + T_{t-1})
  T_t = β * (L_t - L_{t-1}) + (1 - β) * T_{t-1}
  Forecast(h) = L_n + h * T_n

Fallback:
  3+ year history → full Holt's Linear
  2 years          → single Holt iteration
  1 year           → last_year * (1 + inflation)
  0 years          → skipped
"""

import logging
from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_models import Budget, GLTransaction

logger = logging.getLogger(__name__)

# Inflation fallback (SSB 2026 estimate)
DEFAULT_INFLATION = 0.035

# SSB KPI-indeks (2015=100) for prisjustering av historiske GL-data til 2025-kroner.
# Kilde: SSB tabell 03013 (årsgjennomsnitt).
CPI_INDEX: dict[int, float] = {
    2020: 112.0,
    2021: 115.0,
    2022: 123.0,
    2023: 131.0,
    2024: 136.0,
    2025: 140.0,
}
_CPI_BASE = 140.0  # 2025-kroner


def _cpi_deflator(year: int) -> float:
    """Faktor for å prisjustere et gitt år til 2025-kroner. Ukjente år → 1.0."""
    idx = CPI_INDEX.get(year)
    return (_CPI_BASE / idx) if idx else 1.0


# srs_kategori → budget category mapping
SRS_TO_CATEGORY = {
    "Drift": "operations",
    "Investering": "investment",
    "Gjennomstrømning": "property",
}
DEFAULT_CATEGORY = "other"


def _winsorize_series(
    series: list[float],
    iqr_factor: float = 1.5,
) -> tuple[list[float], list[int]]:
    """
    Caps outlier values in a time series at Tukey IQR fences (winsorization).

    Requires >= 4 data points to activate; returns unmodified series otherwise.
    The most-recent value (last element) is never capped — it is the anchor for
    growth caps and cold-start checks.

    Args:
        series:     Annual cost values in chronological order.
        iqr_factor: Fence multiplier. 1.5 = standard Tukey (moderate outliers).
                    Set to 0 to disable.

    Returns:
        (winsorized_series, list_of_capped_indices)

    Example:
        [122M, 194M, 160M, 142M, 150M]  (2021-2025 drift)
        Q1=142M  Q3=160M  IQR=18M  upper_fence=187M
        → index 1 (194M) capped at 187M → series = [122M, 187M, 160M, 142M, 150M]
    """
    n = len(series)
    if iqr_factor <= 0 or n < 4:
        return series[:], []

    sorted_vals = sorted(series)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[(3 * n) // 4]
    iqr = q3 - q1

    if iqr <= 0:
        return series[:], []

    upper = q3 + iqr_factor * iqr
    lower = q1 - iqr_factor * iqr

    cleaned = series[:]
    capped: list[int] = []

    # Never touch the last value — it is the Holt anchor / growth-cap base
    for i in range(n - 1):
        if series[i] > upper:
            cleaned[i] = upper
            capped.append(i)
        elif lower > 0 and series[i] < lower:
            cleaned[i] = max(lower, 0.0)
            capped.append(i)

    return cleaned, capped


def _detect_cold_start(series: list[float], cold_start_ratio: float) -> bool:
    """
    Detects 'cold-start' series — properties that went from near-zero to active
    recently, causing Holt-Winters to overfit a false explosive trend.

    Heuristic: if the last value in the series is > cold_start_ratio × mean(series),
    the property is ramping up and Holt-Winters will overshot badly.

    Example: [0, 0, 100K, 3M, 5.5M] → mean=1.72M, last=5.5M → ratio=3.2 → cold-start.
    Example: [10M, 11M, 12M, 13M, 14M] → mean=12M, last=14M → ratio=1.17 → normal.
    """
    if cold_start_ratio <= 0 or len(series) < 2:
        return False
    mean_val = sum(series) / len(series)
    if mean_val <= 0:
        return False
    return (series[-1] / mean_val) > cold_start_ratio


def _holt_linear_forecast(
    series: list[float],
    alpha: float,
    beta: float,
    horizon: int,
    phi: float = 0.85,
    max_growth_factor: float = 5.0,
    max_annual_growth: float = 0.08,
    cold_start_ratio: float = 1.5,
    outlier_iqr_factor: float = 1.5,
    inflation: float = DEFAULT_INFLATION,
) -> tuple[float, str]:
    """
    Holt's Linear (Double Exponential Smoothing) – pure Python, no deps.
    Extended with:
      - Gardner-McKenzie (1985) damped trend (phi)
      - Safety cap (max_growth_factor)
      - Cold-start detection (cold_start_ratio)

    Args:
        series:            Annual cost values in chronological order (earliest first).
        alpha:             Level smoothing factor [0, 1].
        beta:              Trend smoothing factor [0, 1].
        horizon:           Years ahead to forecast.
        phi:               Trend damping [0.5, 1.0]. 0.85 → multiplier 1.57 over 2 yrs.
        max_annual_growth:   Max allowed growth per year (default 8 %). Over 2 years: 1.08² = 16.6 %.
                         Prevents model from extrapolating crisis-year trends into the future.
    max_growth_factor:   Hard cap — never exceeds last_actual × this factor.
        cold_start_ratio:    If last value > ratio × mean(series), use inflation fallback.
                             Prevents cold-start over-extrapolation. 0 = disabled.
        outlier_iqr_factor:  Winsorize historical values beyond Tukey IQR fences before
                             fitting Holt's. 1.5 = standard. 0 = disabled.
                             The most-recent value is never winsorized.

    Returns:
        (forecast_value, method_name)
    """
    n = len(series)
    if n == 0:
        return 0.0, "empty"
    if n == 1:
        return series[0] * (1 + inflation * horizon), "inflation_fallback"

    # Winsorize historical outliers before fitting (preserves series length)
    fit_series, capped_indices = _winsorize_series(series, iqr_factor=outlier_iqr_factor)
    method_suffix = "_outlier_capped" if capped_indices else ""

    # Cold-start check: ramp-up property → use inflation on last actual value
    if _detect_cold_start(fit_series, cold_start_ratio):
        forecast = series[-1] * (1 + inflation * horizon)
        return max(0.0, forecast), "inflation_coldstart"

    # Initialize with average slope over the full series (more stable than first-step diff)
    level = fit_series[0]
    trend = (fit_series[-1] - fit_series[0]) / max(1, n - 1)

    for t in range(1, n):
        prev_level = level
        level = alpha * fit_series[t] + (1 - alpha) * (prev_level + phi * trend)
        trend = beta * (level - prev_level) + (1 - beta) * phi * trend

    # Damped horizon: φ¹ + φ² + ... + φʰ (Gardner-McKenzie 1985)
    damped_h = sum(phi ** i for i in range(1, horizon + 1))
    forecast = level + damped_h * trend

    last_actual = series[-1]

    method = "holt_linear_damped" + method_suffix

    # Negative-trend floor: never predict less than last_actual × inflation growth.
    # A sustained decline would need structural justification, not model output.
    if last_actual > 0 and forecast < last_actual * (1 + inflation * horizon):
        forecast = last_actual * (1 + inflation * horizon)
        method = "negative_trend_floor"

    # Output-ratio check: if forecast > cold_start_ratio × last_actual,
    # the model is wildly extrapolating (e.g. 2024 spike drove up mean,
    # bypassing the input cold_start check). Fall back to inflation.
    if cold_start_ratio > 0 and last_actual > 0 and forecast > last_actual * cold_start_ratio:
        return max(0.0, last_actual * (1 + inflation * horizon)), "output_ratio_fallback"

    # Annual growth cap: limit to max_annual_growth % per year over the horizon.
    # Default 8 %/yr → max 16.6 % over 2 years. Prevents crisis-year trend extrapolation.
    if last_actual > 0 and max_annual_growth > 0:
        annual_cap = last_actual * ((1 + max_annual_growth) ** horizon)
        if forecast > annual_cap:
            forecast = annual_cap
            method = "annual_growth_capped"

    # Hard cap: never more than max_growth_factor × last actual value
    if last_actual > 0 and max_growth_factor > 0:
        forecast = min(forecast, last_actual * max_growth_factor)

    return max(0.0, forecast), method


class BudgetPredictionService:
    """Generates Holt-Winters predictions for all properties and upserts to budget table."""

    @staticmethod
    async def _fetch_annual_totals(
        db: AsyncSession,
        from_year: int,
        to_year: int,
    ) -> dict[str, dict[str, dict[int, float]]]:
        """
        Returns: { property_id: { category: { year: amount } } }
        Uses srs_kategori → category mapping. Rows without srs_kategori go to 'other'.
        Filters: belop > 0 (costs only), property_id IS NOT NULL.
        """
        try:
            # Sum ALL belop (positive and negative) so that reversals and
            # "feilfakturert" corrections cancel out automatically.
            # HAVING > 0 filters out groups where corrections exceeded the original
            # (net-negative = no real cost for that property/category/year).
            stmt = (
                select(
                    GLTransaction.property_id,
                    GLTransaction.srs_kategori,
                    GLTransaction.ar,
                    func.sum(GLTransaction.belop).label("total"),
                )
                .where(
                    GLTransaction.property_id.isnot(None),
                    GLTransaction.ar >= from_year,
                    GLTransaction.ar <= to_year,
                )
                .group_by(
                    GLTransaction.property_id,
                    GLTransaction.srs_kategori,
                    GLTransaction.ar,
                )
                .having(func.sum(GLTransaction.belop) > 0)
            )
            result = await db.execute(stmt)
            rows = result.all()
        except Exception:
            logger.debug("gl_transactions query failed – table may be empty or missing")
            return {}

        data: dict[str, dict[str, dict[int, float]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        for row in rows:
            pid = str(row.property_id)
            cat = SRS_TO_CATEGORY.get(row.srs_kategori or "", DEFAULT_CATEGORY)
            year = row.ar
            data[pid][cat][year] = float(row.total or 0)

        return data

    @staticmethod
    async def _fetch_monthly_weights(
        db: AsyncSession,
        property_id: str,
        category: str,
    ) -> dict[int, float]:
        """
        Returns monthly distribution weights {1: 0.08, 2: 0.07, ...} that sum to 1.0.
        Computed from historical monthly averages for this property+category.
        Falls back to uniform 1/12 if data is insufficient.
        """
        srs_values = [k for k, v in SRS_TO_CATEGORY.items() if v == category]
        if not srs_values:
            srs_values = [""]

        try:
            stmt = (
                select(
                    GLTransaction.maaned,
                    func.sum(GLTransaction.belop).label("total"),
                )
                .where(
                    GLTransaction.property_id == property_id,
                    GLTransaction.srs_kategori.in_(srs_values),
                    GLTransaction.belop > 0,
                    GLTransaction.maaned.isnot(None),
                )
                .group_by(GLTransaction.maaned)
            )
            result = await db.execute(stmt)
            rows = result.all()
        except Exception:
            rows = []

        if not rows:
            return {m: 1 / 12 for m in range(1, 13)}

        monthly = {row.maaned: float(row.total or 0) for row in rows}
        total = sum(monthly.values())
        if total <= 0:
            return {m: 1 / 12 for m in range(1, 13)}

        weights: dict[int, float] = {}
        for month in range(1, 13):
            weights[month] = monthly.get(month, 0) / total

        # Fill missing months with average of existing
        missing = [m for m in range(1, 13) if m not in monthly or monthly[m] <= 0]
        if missing:
            avg = sum(weights.get(m, 0) for m in range(1, 13) if m not in missing)
            avg /= max(1, 12 - len(missing))
            for m in missing:
                weights[m] = avg
            # Re-normalize
            total_w = sum(weights.values())
            if total_w > 0:
                weights = {m: w / total_w for m, w in weights.items()}

        return weights

    @classmethod
    async def predict_all_properties(
        cls,
        db: AsyncSession,
        target_year: int = 2027,
        alpha: float = 0.5,          # Senket fra 0.7 – gir jevnere historisk vekting
        beta: float = 0.2,           # Senket fra 0.3 – forsiktig trendoppdatering
        inflation: float = DEFAULT_INFLATION,
        history_from: int = 2021,
        phi: float = 0.85,
        max_growth_factor: float = 5.0,
        cold_start_ratio: float = 1.5,
        outlier_iqr_factor: float = 1.5,
        max_annual_growth: float = 0.08,  # Maks vekst per år (8% = 16,6% over 2 år)
        data_source_tag: str = "xgb70",  # Suffiks for data_source i budget-tabellen
        apply_cpi: bool = True,           # Prisjuster historiske GL-data til siste_år-kroner
        passthrough_categories: frozenset[str] = frozenset({"property"}),  # Kun inflasjon
        likebefore_min_years: int = 3,    # Eiendommer med < N år → inflasjonsfallback
    ) -> dict[str, Any]:
        """
        Runs Holt's Linear prediction for every property that has GL data,
        then upserts results into the budget table.

        Forbedringer vs original:
        - α=0.5 / β=0.2: mer balansert historisk vekting, forsiktigere trendoppdatering
        - CPI-deflasjon: historiske beløp justeres til siste_år-kroner (SSB KPI)
        - passthrough_categories: "property" (Gjennomstrømning) bruker kun inflasjon
          da kategorien er kontrakts-/regelbasert, ikke trendbasert
        - likebefore_min_years: eiendommer med < 3 år historikk bruker inflasjonsfallback
        - Initialisering: gjennomsnittlig stigningstall over hele serien (vs første step)
        - Negativ-trend-gulv: prediksjon aldri under siste_faktiske × inflasjon

        Returns a summary: { processed, skipped, errors, year }
        """
        # Years between last historical year and target (for forecast horizon)
        last_history_year = target_year - 2  # e.g. 2025 for target 2027
        source = f"holt_winters_{target_year}" + (f"_{data_source_tag}" if data_source_tag else "")

        annual = await cls._fetch_annual_totals(db, from_year=history_from, to_year=last_history_year)

        if not annual:
            return {"processed": 0, "skipped": 0, "errors": [], "year": target_year}

        processed = 0
        skipped = 0
        errors: list[str] = []

        all_categories = {"operations", "investment", "property", "other"}

        for property_id, cat_data in annual.items():
            try:
                for category in all_categories:
                    year_map = cat_data.get(category, {})
                    years_sorted = sorted(year_map.keys())

                    if not years_sorted:
                        logger.debug("property=%s cat=%s: no data, skipping category", property_id, category)
                        continue

                    # Build chronological series with optional CPI deflation to last_history_year-NOK
                    full_range = list(range(years_sorted[0], years_sorted[-1] + 1))
                    if apply_cpi:
                        ref_deflator = _cpi_deflator(last_history_year)
                        series = [
                            year_map.get(yr, 0.0) * (_cpi_deflator(yr) / ref_deflator)
                            for yr in full_range
                        ]
                    else:
                        series = [year_map.get(yr, 0.0) for yr in full_range]

                    horizon = target_year - years_sorted[-1]
                    n = len(series)

                    if n == 0:
                        continue

                    # Gjennomstrømning + eiendommer med kort historikk → kun inflasjonsfallback.
                    # Gjennomstrømning er kontrakts-/regelbasert og ikke trendbasert.
                    # Nye eiendommer har for få datapunkter for en stabil Holt-modell.
                    force_inflation = (
                        category in passthrough_categories
                        or n < likebefore_min_years
                    )

                    if force_inflation or n == 1:
                        last_val = series[-1]
                        predicted_annual = last_val * (1 + inflation * horizon)
                        method = "inflation_passthrough" if force_inflation else "inflation_fallback"
                    else:
                        predicted_annual, method = _holt_linear_forecast(
                            series, alpha=alpha, beta=beta, horizon=horizon,
                            phi=phi, max_growth_factor=max_growth_factor,
                            cold_start_ratio=cold_start_ratio,
                            outlier_iqr_factor=outlier_iqr_factor,
                            inflation=inflation,
                            max_annual_growth=max_annual_growth,
                        )

                    logger.debug(
                        "property=%s cat=%s years=%s method=%s predicted=%.0f",
                        property_id, category, years_sorted, method, predicted_annual,
                    )

                    # Monthly distribution
                    weights = await cls._fetch_monthly_weights(db, property_id, category)

                    # Delete existing prediction rows for this property+year+category+source
                    await db.execute(text("""
                        DELETE FROM budget
                        WHERE property_id = :property_id
                          AND year = :year
                          AND category = :category
                          AND data_source = :source
                    """), {
                        "property_id": property_id,
                        "year": target_year,
                        "category": category,
                        "source": source,
                    })

                    for month in range(1, 13):
                        monthly_amount = Decimal(str(round(predicted_annual * weights[month], 2)))
                        await db.execute(text("""
                            INSERT INTO budget
                                (budget_id, property_id, year, month, category, amount, is_synthetic, data_source, created_at, updated_at)
                            VALUES
                                (gen_random_uuid(), :property_id, :year, :month, :category, :amount, true, :source, now(), now())
                        """), {
                            "property_id": property_id,
                            "year": target_year,
                            "month": month,
                            "category": category,
                            "amount": monthly_amount,
                            "source": source,
                        })

                processed += 1
                await db.commit()

            except Exception as exc:
                logger.debug("Prediction failed for property=%s: %s", property_id, exc)
                errors.append(f"{property_id}: {exc}")
                await db.rollback()
                skipped += 1

        # Properties with zero GL data are implicitly skipped (not in annual dict)
        return {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "year": target_year,
        }

    @classmethod
    async def run_backtest(
        cls,
        db: AsyncSession,
        test_years: list[int] | None = None,
        alpha: float = 0.5,
        beta: float = 0.2,
        phi: float = 0.85,
        inflation: float = DEFAULT_INFLATION,
        history_from: int = 2021,
        cold_start_ratio: float = 1.5,
        max_annual_growth: float = 0.08,
        max_growth_factor: float = 5.0,
        outlier_iqr_factor: float = 1.5,
        apply_cpi: bool = True,
        passthrough_categories: frozenset[str] = frozenset({"property"}),
        likebefore_min_years: int = 3,
    ) -> dict[str, Any]:
        """
        Out-of-sample backtesting: for each test year Y, trains on history_from..Y-1,
        predicts Y, and compares against actual GL totals for Y.

        Returns per-year and per-category MAPE/MAE so the methodology can be
        validated with historical data (2023, 2024, 2025 by default).
        """
        if test_years is None:
            test_years = [2023, 2024, 2025]

        # Fetch all GL data needed (from history_from to max test year)
        max_year = max(test_years)
        all_data = await cls._fetch_annual_totals(db, history_from, max_year)

        # Category display names
        cat_labels = {
            "operations": "Drift",
            "investment": "Investering",
            "property":   "Gjennomstrømning",
            "other":      "Annet",
        }

        # Results structure:
        # { year: { "overall": {...}, "per_category": { cat: {...} } } }
        results: dict[int, dict] = {}

        for test_year in sorted(test_years):
            cutoff = test_year - 1  # last year of training data
            last_history_year = cutoff

            # Per-category accumulators: { cat: [abs_error, actual, predicted] }
            cat_errors: dict[str, list[tuple[float, float, float]]] = {}
            total_predicted = 0.0
            total_actual = 0.0
            n_props = 0

            for property_id, categories in all_data.items():
                for category, year_map in categories.items():
                    # Actual value for the test year
                    actual = year_map.get(test_year, None)
                    if actual is None or actual <= 0:
                        continue  # No actual to compare against

                    # Training series: history_from..cutoff only
                    train_years = [y for y in sorted(year_map.keys()) if history_from <= y <= cutoff]
                    if not train_years:
                        continue

                    full_range = list(range(train_years[0], train_years[-1] + 1))
                    if apply_cpi:
                        ref_deflator = _cpi_deflator(last_history_year)
                        series = [
                            year_map.get(yr, 0.0) * (_cpi_deflator(yr) / ref_deflator)
                            for yr in full_range
                        ]
                    else:
                        series = [year_map.get(yr, 0.0) for yr in full_range]

                    horizon = test_year - train_years[-1]
                    n = len(series)
                    if n == 0:
                        continue

                    is_passthrough = category in passthrough_categories
                    force_inflation = is_passthrough or n < likebefore_min_years

                    if force_inflation or n == 1:
                        last_val = series[-1]
                        predicted = last_val * (1 + inflation * horizon)
                    else:
                        predicted, _ = _holt_linear_forecast(
                            series, alpha=alpha, beta=beta, horizon=horizon,
                            phi=phi, max_growth_factor=max_growth_factor,
                            cold_start_ratio=cold_start_ratio,
                            outlier_iqr_factor=outlier_iqr_factor,
                            inflation=inflation,
                            max_annual_growth=max_annual_growth,
                        )

                    # Exclude from MAPE:
                    # 1. Passthrough categories (inflation-only, not meaningful to benchmark)
                    # 2. Properties with fewer than likebefore_min_years training years
                    #    (cold-start: predicted via flat inflation, actual may be far off)
                    include_in_mape = (
                        not is_passthrough
                        and len(train_years) >= likebefore_min_years
                    )

                    if include_in_mape:
                        abs_err = abs(predicted - actual)
                        cat_label = cat_labels.get(category, category)
                        if cat_label not in cat_errors:
                            cat_errors[cat_label] = []
                        cat_errors[cat_label].append((abs_err, actual, predicted))
                        total_predicted += predicted
                        total_actual += actual
                        n_props += 1

            # Compute MAPE/MAE per category
            per_category: dict[str, dict] = {}
            for cat, errs in cat_errors.items():
                n_cat = len(errs)
                mape = sum(e[0] / e[1] * 100 for e in errs if e[1] > 0) / max(1, n_cat)
                mae = sum(e[0] for e in errs) / max(1, n_cat)
                cat_predicted = sum(e[2] for e in errs)
                cat_actual = sum(e[1] for e in errs)
                per_category[cat] = {
                    "mape": round(mape, 1),
                    "mae": round(mae, 0),
                    "predicted": round(cat_predicted, 0),
                    "actual": round(cat_actual, 0),
                    "n_properties": n_cat,
                    "endring_pst": round((cat_predicted - cat_actual) / cat_actual * 100, 1) if cat_actual > 0 else None,
                }

            overall_mape = (
                abs(total_predicted - total_actual) / total_actual * 100
                if total_actual > 0 else None
            )
            # Weighted MAPE across all individual errors
            all_errs = [e for errs in cat_errors.values() for e in errs]
            wmape = sum(e[0] / e[1] * 100 for e in all_errs if e[1] > 0) / max(1, len(all_errs))

            results[test_year] = {
                "overall": {
                    "mape": round(wmape, 1),
                    "predicted": round(total_predicted, 0),
                    "actual": round(total_actual, 0),
                    "endring_pst": round((total_predicted - total_actual) / total_actual * 100, 1) if total_actual > 0 else None,
                    "n_properties": n_props,
                },
                "per_category": per_category,
            }

        return {
            "test_years": sorted(test_years),
            "parameters": {
                "alpha": alpha, "beta": beta, "phi": phi,
                "inflation": inflation, "max_annual_growth": max_annual_growth,
            },
            "results": results,
        }
