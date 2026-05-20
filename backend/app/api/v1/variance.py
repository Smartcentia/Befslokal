from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.variance_service import VarianceService

router = APIRouter()

@router.get("/{property_id}", response_model=Dict[str, Any])
async def get_variance_report(
    property_id: str,
    year: int = Query(..., description="Year to analyze"),
    period_type: str = Query("month", regex="^(month|quarter|ytd|year)$"),
    period_value: int = Query(None, description="Month (1-12) or Quarter (1-4). Not needed for year type."),
    db: AsyncSession = Depends(deps.get_db),
    # current_user: models.User = Depends(deps.get_current_active_user), # Uncomment when Auth is fully stable
) -> Any:
    """
    Get Budget vs Actual variance report for a property.
    Bruker gl_transactions for faktisk, fallback til manual_expenses når GL er tom.
    Krever budsjettdata (kjør fill_budget_from_consumption eller POST /cost-management/budgets/generate-from-consumption).
    """
    try:
        report = await VarianceService.get_variance_report(
            db=db,
            property_id=property_id,
            year=year,
            period_type=period_type,
            period_value=period_value
        )
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trend/{property_id}", response_model=Dict[str, Any])
async def get_trend_analysis(
    property_id: str,
    year: int = Query(..., description="Year to analyze"),
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """
    Get monthly trend analysis for a property.
    """
    try:
        trend = await VarianceService.get_trend_analysis(
            db=db,
            property_id=property_id,
            year=year
        )
        return trend
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
