"""
Cost Forecasting Service - Predictive cost analysis with Monte Carlo simulations.

Provides time-series forecasting for costs (NOT revenue) using historical data
and contract commitments. Supports Monte Carlo simulations for uncertainty modeling.

Author: KI Kollega (AI Assistant)
Date: 2026-01-22
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import random
import statistics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.services.analytics.cost_analysis_service import CostCategory

logger = logging.getLogger(__name__)


@dataclass
class CostForecastParams:
    """Parameters for cost forecast generation."""
    property_id: Optional[str] = None
    months_ahead: int = 12
    kpi_adjustment: float = 0.0  # -0.05 to +0.10 (-5% to +10%)
    operations_variance: float = 0.0  # -0.20 to +0.20
    include_monte_carlo: bool = False
    monte_carlo_iterations: int = 1000


@dataclass
class MonteCarloResult:
    """Result of Monte Carlo cost simulation."""
    p10: float  # Best case (10th percentile - lowest cost)
    p50: float  # Median (50th percentile)
    p90: float  # Worst case (90th percentile - highest cost)
    mean: float
    std_dev: float
    min_value: float
    max_value: float
    iterations: int


class CostForecastingService:
    """
    Cost forecasting service using time-series analysis and Monte Carlo.

    Focus: Total costs, cost per sqm, budget variance (NOT revenue).
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def generate_cost_forecast(
        self,
        db: AsyncSession,
        params: CostForecastParams
    ) -> Dict[str, Any]:
        """
        Generate cost forecast for property or portfolio.

        Args:
            db: Database session
            params: Forecast parameters

        Returns:
            Dict with forecast data including historical, baseline forecast,
            and optional Monte Carlo confidence intervals
        """
        self.logger.info(f"Generating cost forecast: {params}")

        # 1. Get historical costs (last 12 months)
        historical_costs = await self._get_historical_costs(db, params.property_id)

        if not historical_costs:
            self.logger.warning(f"No historical cost data for property {params.property_id}")
            return self._generate_empty_forecast(params)

        # 2. Get committed costs from contracts (future)
        committed_costs = await self._get_committed_contract_costs(db, params.property_id)

        # 3. Get budget data for comparison
        budget_data = await self._get_budget_data(db, params.property_id, params.months_ahead)

        # 4. Calculate baseline forecast
        baseline_forecast = self._calculate_baseline_forecast(
            historical_costs,
            committed_costs,
            params
        )

        # 5. Monte Carlo simulation (if requested)
        monte_carlo_result = None
        if params.include_monte_carlo:
            monte_carlo_result = await self._run_monte_carlo_simulation(
                db,
                historical_costs,
                committed_costs,
                params
            )

        # 6. Calculate budget variance
        budget_variance = self._calculate_budget_variance(baseline_forecast, budget_data)

        # 7. Compile response
        return {
            "property_id": params.property_id,
            "generated_at": datetime.now().isoformat(),
            "parameters": {
                "months_ahead": params.months_ahead,
                "kpi_adjustment": params.kpi_adjustment,
                "operations_variance": params.operations_variance
            },
            "historical": historical_costs,
            "forecast": baseline_forecast,
            "budget": budget_data,
            "budget_variance": budget_variance,
            "monte_carlo": monte_carlo_result,
            "summary": self._generate_summary(baseline_forecast, budget_data, monte_carlo_result)
        }

    async def _get_historical_costs(
        self,
        db: AsyncSession,
        property_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get last 12 months of actual costs."""

        if property_id:
            query = text("""
                SELECT
                    DATE_TRUNC('month', transaction_date) as month,
                    SUM(amount) as total_cost,
                    COUNT(*) as transaction_count,
                    jsonb_object_agg(category, cat_total) as costs_by_category
                FROM (
                    SELECT
                        transaction_date,
                        category,
                        SUM(amount) as cat_total
                    FROM gl_transactions
                    WHERE property_id = :property_id
                      AND transaction_date >= NOW() - INTERVAL '12 months'
                      AND transaction_date < NOW()
                    GROUP BY transaction_date, category
                ) sub
                GROUP BY DATE_TRUNC('month', transaction_date)
                ORDER BY month DESC
            """)
            result = await db.execute(query, {"property_id": property_id})
        else:
            # Portfolio-wide
            query = text("""
                SELECT
                    DATE_TRUNC('month', transaction_date) as month,
                    SUM(amount) as total_cost,
                    COUNT(*) as transaction_count
                FROM gl_transactions
                WHERE transaction_date >= NOW() - INTERVAL '12 months'
                  AND transaction_date < NOW()
                GROUP BY DATE_TRUNC('month', transaction_date)
                ORDER BY month DESC
            """)
            result = await db.execute(query)

        rows = result.fetchall()

        historical = []
        for row in rows:
            historical.append({
                "month": row[0].strftime("%Y-%m"),
                "total_cost": float(row[1]),
                "transaction_count": int(row[2]),
                "costs_by_category": row[3] if len(row) > 3 else {}
            })

        return historical

    async def _get_committed_contract_costs(
        self,
        db: AsyncSession,
        property_id: Optional[str]
    ) -> Dict[str, float]:
        """Get committed costs from active contracts."""

        if property_id:
            query = text("""
                SELECT
                    COALESCE(SUM(
                        COALESCE(
                            (c.amount->>'total_per_year')::float,
                            (c.amount->>'amount_per_year')::float,
                            (c.amount->>'monthly_rent')::float * 12,
                            0
                        )
                    ), 0) as annual_rent,
                    COALESCE(SUM(c.caretaker_cost), 0) as caretaker_cost,
                    COALESCE(SUM(c.cleaning_cost), 0) as cleaning_cost
                FROM contracts c
                JOIN units u ON c.unit_id = u.unit_id
                WHERE u.property_id = :property_id
                  AND c.status = 'active'
            """)
            result = await db.execute(query, {"property_id": property_id})
        else:
            query = text("""
                SELECT
                    COALESCE(SUM(
                        COALESCE(
                            (c.amount->>'total_per_year')::float,
                            (c.amount->>'amount_per_year')::float,
                            (c.amount->>'monthly_rent')::float * 12,
                            0
                        )
                    ), 0) as annual_rent,
                    COALESCE(SUM(c.caretaker_cost), 0) as caretaker_cost,
                    COALESCE(SUM(c.cleaning_cost), 0) as cleaning_cost
                FROM contracts c
                WHERE c.status = 'active'
            """)
            result = await db.execute(query)

        row = result.fetchone()

        return {
            "annual_rent": float(row[0] if row else 0),
            "caretaker_cost": float(row[1] if row else 0),
            "cleaning_cost": float(row[2] if row else 0),
            "total_annual": float(sum([row[0] or 0, row[1] or 0, row[2] or 0]) if row else 0)
        }

    async def _get_budget_data(
        self,
        db: AsyncSession,
        property_id: Optional[str],
        months_ahead: int
    ) -> List[Dict[str, Any]]:
        """Get budget data for comparison."""

        current_year = datetime.now().year
        next_year = current_year + 1

        if property_id:
            query = text("""
                SELECT year, month, SUM(amount) as budgeted_amount
                FROM budget
                WHERE property_id = :property_id
                  AND (year = :current_year OR year = :next_year)
                GROUP BY year, month
                ORDER BY year, month
            """)
            result = await db.execute(query, {
                "property_id": property_id,
                "current_year": current_year,
                "next_year": next_year
            })
        else:
            query = text("""
                SELECT year, month, SUM(amount) as budgeted_amount
                FROM budget
                WHERE (year = :current_year OR year = :next_year)
                GROUP BY year, month
                ORDER BY year, month
            """)
            result = await db.execute(query, {
                "current_year": current_year,
                "next_year": next_year
            })

        rows = result.fetchall()

        budget = []
        for row in rows:
            budget.append({
                "month": f"{row[0]}-{row[1]:02d}",
                "budgeted_amount": float(row[2])
            })

        return budget

    def _calculate_baseline_forecast(
        self,
        historical_costs: List[Dict[str, Any]],
        committed_costs: Dict[str, float],
        params: CostForecastParams
    ) -> List[Dict[str, Any]]:
        """
        Calculate baseline cost forecast using simple moving average + trend.

        Uses last 3 months average as baseline, adjusted for:
        - KPI adjustment (inflation)
        - Operations variance
        - Committed contract costs
        """

        # Calculate moving average from last 3 months
        recent_costs = historical_costs[:3]
        if not recent_costs:
            baseline_monthly = 100000  # Fallback
        else:
            baseline_monthly = statistics.mean([c["total_cost"] for c in recent_costs])

        # Committed monthly cost from contracts
        committed_monthly = committed_costs["total_annual"] / 12

        # If committed costs are known, use them; otherwise use historical baseline
        if committed_monthly > 0:
            baseline_monthly = max(baseline_monthly, committed_monthly)

        # Apply KPI adjustment
        baseline_monthly *= (1 + params.kpi_adjustment)

        # Generate forecast for N months
        forecast = []
        current_date = datetime.now()

        for i in range(params.months_ahead):
            forecast_date = current_date + timedelta(days=30 * i)
            month_str = forecast_date.strftime("%Y-%m")

            # Apply operations variance (random walk)
            if params.operations_variance != 0:
                variance = baseline_monthly * params.operations_variance * random.uniform(-1, 1)
            else:
                variance = 0

            forecasted_cost = baseline_monthly + variance

            forecast.append({
                "month": month_str,
                "forecasted_cost": round(forecasted_cost, 2),
                "baseline": round(baseline_monthly, 2)
            })

        return forecast

    async def _run_monte_carlo_simulation(
        self,
        db: AsyncSession,
        historical_costs: List[Dict[str, Any]],
        committed_costs: Dict[str, float],
        params: CostForecastParams
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation to generate confidence intervals.

        Simulates N iterations with varying:
        - KPI adjustments (random within realistic range)
        - Operations variance (random walk)
        - Contract renewal probability
        """

        iterations = params.monte_carlo_iterations
        results = []

        # Calculate baseline
        recent_costs = historical_costs[:3]
        baseline_monthly = statistics.mean([c["total_cost"] for c in recent_costs]) if recent_costs else 100000
        committed_monthly = committed_costs["total_annual"] / 12

        if committed_monthly > 0:
            baseline_monthly = max(baseline_monthly, committed_monthly)

        for _ in range(iterations):
            # Random KPI adjustment (within realistic range)
            random_kpi = params.kpi_adjustment + random.gauss(0, 0.02)  # ±2% std dev

            # Random operations variance
            random_ops_var = params.operations_variance + random.gauss(0, 0.05)  # ±5% std dev

            # Calculate annual cost for this iteration
            monthly_cost = baseline_monthly * (1 + random_kpi) * (1 + random_ops_var)
            annual_cost = monthly_cost * 12

            results.append(annual_cost)

        # Calculate percentiles
        results.sort()
        p10 = results[int(iterations * 0.10)]
        p50 = results[int(iterations * 0.50)]
        p90 = results[int(iterations * 0.90)]

        monte_carlo = MonteCarloResult(
            p10=round(p10, 2),
            p50=round(p50, 2),
            p90=round(p90, 2),
            mean=round(statistics.mean(results), 2),
            std_dev=round(statistics.stdev(results), 2),
            min_value=round(min(results), 2),
            max_value=round(max(results), 2),
            iterations=iterations
        )

        return {
            "annual_cost_p10": monte_carlo.p10,
            "annual_cost_p50": monte_carlo.p50,
            "annual_cost_p90": monte_carlo.p90,
            "mean": monte_carlo.mean,
            "std_dev": monte_carlo.std_dev,
            "min": monte_carlo.min_value,
            "max": monte_carlo.max_value,
            "iterations": monte_carlo.iterations
        }

    def _calculate_budget_variance(
        self,
        forecast: List[Dict[str, Any]],
        budget: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate variance between forecast and budget."""

        if not budget or not forecast:
            return {"variance_pct": 0, "variance_nok": 0}

        # Sum forecast vs budget for matching months
        budget_dict = {b["month"]: b["budgeted_amount"] for b in budget}

        total_forecast = 0
        total_budget = 0

        for f in forecast:
            month = f["month"]
            total_forecast += f["forecasted_cost"]
            if month in budget_dict:
                total_budget += budget_dict[month]

        if total_budget == 0:
            return {"variance_pct": 0, "variance_nok": round(total_forecast, 2)}

        variance_nok = total_forecast - total_budget
        variance_pct = (variance_nok / total_budget) * 100

        return {
            "total_forecast": round(total_forecast, 2),
            "total_budget": round(total_budget, 2),
            "variance_nok": round(variance_nok, 2),
            "variance_pct": round(variance_pct, 1),
            "status": "over_budget" if variance_nok > 0 else "under_budget"
        }

    def _generate_summary(
        self,
        forecast: List[Dict[str, Any]],
        budget: List[Dict[str, Any]],
        monte_carlo: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate forecast summary."""

        total_forecast = sum(f["forecasted_cost"] for f in forecast)

        summary = {
            "total_forecasted_cost": round(total_forecast, 2),
            "avg_monthly_cost": round(total_forecast / len(forecast), 2) if forecast else 0
        }

        if monte_carlo:
            summary["best_case_annual"] = monte_carlo["annual_cost_p10"]
            summary["most_likely_annual"] = monte_carlo["annual_cost_p50"]
            summary["worst_case_annual"] = monte_carlo["annual_cost_p90"]

        return summary

    def _generate_empty_forecast(self, params: CostForecastParams) -> Dict[str, Any]:
        """Generate empty forecast when no data available."""
        return {
            "property_id": params.property_id,
            "generated_at": datetime.now().isoformat(),
            "parameters": {
                "months_ahead": params.months_ahead,
                "kpi_adjustment": params.kpi_adjustment
            },
            "historical": [],
            "forecast": [],
            "budget": [],
            "budget_variance": {},
            "monte_carlo": None,
            "summary": {"total_forecasted_cost": 0, "avg_monthly_cost": 0},
            "error": "No historical cost data available"
        }


# Singleton instance
cost_forecasting_service = CostForecastingService()
