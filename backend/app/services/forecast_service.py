from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar

from app.models.financial_models import GLTransaction
from app.domains.core.models.property import Property

class ForecastService:
    """Service for generating financial forecasts"""

    @staticmethod
    async def generate_forecast(
        db: AsyncSession,
        property_id: str,
        months_horizon: int = 12,
        inflation_rate: float = 0.035, # 3.5% default
        lookback_months: int = 12
    ) -> Dict[str, Any]:
        """
        Generates a rolling forecast based on historical GL transactions.
        
        Method:
        1. Aggregate actual costs per month for the last 'lookback_months'.
        2. Calculate a baseline monthly average (simple average for MVP).
        3. Project forward 'months_horizon', applying monthly inflation.
        """
        
        # 1. Determine Date Range for History
        today = datetime.now()
        start_date = today - relativedelta(months=lookback_months)
        current_year = today.year
        current_month = today.month
        
        # Query Actuals
        # Note: We group by YYYY-MM. 
        # Using separate year/month columns is easier than date truncation in some SQL dialects
        stmt = (
            select(
                GLTransaction.ar,
                GLTransaction.maaned,
                func.sum(GLTransaction.belop).label("total_amount")
            )
            .where(
                and_(
                    GLTransaction.property_id == property_id,
                    GLTransaction.bilagsdato >= start_date
                )
            )
            .group_by(GLTransaction.ar, GLTransaction.maaned)
            .order_by(GLTransaction.ar, GLTransaction.maaned)
        )
        
        result = await db.execute(stmt)
        history_rows = result.all()

        historical_data = []
        total_historical_spend = 0.0
        count_months = 0

        if history_rows:
            # Bruk GL-transaksjoner
            hist_map = {(row.year, row.month): row.total_amount for row in history_rows}
            iter_date = start_date
            while iter_date < datetime(today.year, today.month, 1):
                amount = hist_map.get((iter_date.year, iter_date.month), 0.0)
                historical_data.append({
                    "date": iter_date.strftime("%Y-%m"),
                    "year": iter_date.year,
                    "month": iter_date.month,
                    "amount": amount,
                    "type": "actual"
                })
                total_historical_spend += amount
                count_months += 1
                iter_date += relativedelta(months=1)
        else:
            # Fallback: gl_transactions tom – bruk manual_expenses/financial_history
            prop_stmt = select(Property).where(Property.property_id == property_id)
            prop_res = await db.execute(prop_stmt)
            prop = prop_res.scalar_one_or_none()
            if prop and prop.external_data:
                ext = prop.external_data or {}
                financials = ext.get("financials", {})
                fh = ext.get("financial_history", {})

                annual_total = 0.0
                if fh:
                    for year_str in sorted(fh.keys(), reverse=True):
                        try:
                            data = fh.get(year_str, {})
                            if isinstance(data, dict):
                                annual_total = float(data.get("total_costs", 0) or 0)
                                if annual_total > 0:
                                    break
                        except (ValueError, TypeError):
                            continue

                if annual_total <= 0:
                    manual = float(financials.get("total_manual_expenses", 0) or 0)
                    csv_spend = float(financials.get("total_spend_csv", 0) or 0)
                    annual_total = manual + csv_spend

                if annual_total > 0:
                    monthly_avg = annual_total / 12.0
                    iter_date = start_date
                    while iter_date < datetime(today.year, today.month, 1):
                        historical_data.append({
                            "date": iter_date.strftime("%Y-%m"),
                            "year": iter_date.year,
                            "month": iter_date.month,
                            "amount": monthly_avg,
                            "type": "actual"
                        })
                        total_historical_spend += monthly_avg
                        count_months += 1
                        iter_date += relativedelta(months=1)
            
        # 2. Calculate Baseline
        baseline_monthly = (total_historical_spend / count_months) if count_months > 0 else 0

        if baseline_monthly <= 0:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Eiendommen mangler historiske kostnadsdata. Legg til utgifter (manual_expenses) "
                "eller importer gl_transactions for å generere prognose."
            )
        
        # 3. Generate Forecast
        forecast_data = []
        monthly_inflation_factor = (1 + inflation_rate) ** (1/12)
        
        current_projection = baseline_monthly
        
        # Start forecast from current month
        iter_date = datetime(today.year, today.month, 1)
        for i in range(months_horizon):
            # Apply Inflation
            current_projection *= monthly_inflation_factor
            
            # Simple Seasonality (Optional stub)
            # if iter_date.month in [12, 1]: current_projection *= 1.1 (Winter costs)
            
            forecast_data.append({
                "date": iter_date.strftime("%Y-%m"),
                "year": iter_date.year,
                "month": iter_date.month,
                "amount": current_projection,
                "type": "forecast",
                "lower_bound": current_projection * 0.9, # Simple +/- 10% confidence
                "upper_bound": current_projection * 1.1
            })
            
            iter_date += relativedelta(months=1)
            
        return {
            "property_id": property_id,
            "params": {
                "inflation_rate": inflation_rate,
                "horizon_months": months_horizon,
                "lookback_months": lookback_months
            },
            "baseline_monthly_spend": baseline_monthly,
            "series": historical_data + forecast_data
        }
