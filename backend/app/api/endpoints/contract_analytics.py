"""Contract Analytics Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.api.deps import get_db, get_current_user
from app.domains.core.services.contract_analytics import ContractAnalyticsService
from app.domains.core.utils.region_mapping import group_by_operational_regions
from app.domains.core.models.user import User


router = APIRouter()


@router.get("/analytics/cost-summary", response_model=Dict[str, Any])
async def get_cost_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall cost summary for all active contracts"""
    return await ContractAnalyticsService.get_cost_summary(db)


@router.get("/analytics/regional-breakdown", response_model=List[Dict[str, Any]])
async def get_regional_breakdown(
    group_by: str = Query(default="county", pattern="^(county|region)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cost breakdown by region or county
    
    Args:
        group_by: Group by 'county' (detailed, 11+ counties) or 'region' (5 operational regions + Bufdir)
    """
    county_data = await ContractAnalyticsService.get_regional_breakdown(db)
    
    if group_by == "region":
        # Group counties into operational regions
        return group_by_operational_regions(county_data)
    else:
        # Return county-level detail
        return county_data


@router.get("/analytics/landlord-comparison", response_model=List[Dict[str, Any]])
async def get_landlord_comparison(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare costs by landlord"""
    return await ContractAnalyticsService.get_landlord_comparison(db)


@router.get("/analytics/expiring", response_model=List[Dict[str, Any]])
async def get_expiring_contracts(
    days_ahead: int = Query(default=730, ge=30, le=730),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contracts expiring within specified days"""
    return await ContractAnalyticsService.get_expiring_contracts(db, days_ahead)


@router.get("/analytics/cost-per-sqm", response_model=List[Dict[str, Any]])
async def get_cost_per_sqm_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze cost per square meter"""
    return await ContractAnalyticsService.get_cost_per_sqm_analysis(db)
