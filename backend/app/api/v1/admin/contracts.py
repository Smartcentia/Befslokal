"""
Admin API for Contract Costs Overview
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin_user
from app.domains.core.models.user import User
from app.domains.core.services.contract_cost_overview import build_contract_cost_overview

router = APIRouter(
    prefix="/contracts",
    tags=["admin", "contracts"],
    dependencies=[Depends(get_current_admin_user)]
)

@router.get("/costs")
async def get_contract_cost_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get an aggregated overview of all contracts with their calculated costs and associated properties.
    """
    try:
        return await build_contract_cost_overview(db)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
