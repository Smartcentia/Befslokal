from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.forecast_service import ForecastService

router = APIRouter()

@router.get("/{property_id}", response_model=Dict[str, Any])
async def get_property_forecast(
    property_id: str,
    months: int = Query(12, description="Forecast horizon in months", ge=1, le=60),
    inflation: float = Query(0.035, description="Annual inflation rate (e.g., 0.035 for 3.5%)", ge=0.0, le=1.0),
    lookback: int = Query(12, description="Months of history to use for baseline", ge=3, le=60),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Generate a financial forecast for a property.
    Bruker gl_transactions for historikk; fallback til manual_expenses/financial_history når GL er tom.
    """
    try:
        result = await ForecastService.generate_forecast(
            db=db,
            property_id=property_id,
            months_horizon=months,
            inflation_rate=inflation,
            lookback_months=lookback
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"Forecast Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate forecast")
