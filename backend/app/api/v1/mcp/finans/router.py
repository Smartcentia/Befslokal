from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class ExpenseCreate(BaseModel):
    property_id: str
    type: str
    amount: float
    provider: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class ExpenseUpdate(BaseModel):
    property_id: str
    expense_index: int
    type: Optional[str] = None
    amount: Optional[float] = None
    provider: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class ExpenseDelete(BaseModel):
    property_id: str
    expense_index: int


@router.get("/")
async def root():
    return {"status": "Finans MCP Server Active"}


@router.get("/property/{property_id}/costs")
async def get_property_costs(property_id: str, year: str = "all", db: AsyncSession = Depends(get_db)):
    """Get cost breakdown for a property."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_get_property_costs", {
            "property_id": property_id,
            "year": year
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regional-costs")
async def get_regional_costs(region: str = None, db: AsyncSession = Depends(get_db)):
    """Get aggregated costs by region."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_get_regional_costs", {
            "region": region
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio-summary")
async def get_portfolio_summary(db: AsyncSession = Depends(get_db)):
    """Get portfolio-level financial summary."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_get_portfolio_summary", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis")
async def get_kpis(db: AsyncSession = Depends(get_db)):
    """Get key financial performance indicators."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_get_kpis", {})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expiring-contracts")
async def get_expiring_contracts(days_ahead: int = 90, db: AsyncSession = Depends(get_db)):
    """Get contracts expiring within N days."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_get_expiring_contracts", {
            "days_ahead": days_ahead
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expense")
async def add_expense(expense: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    """Add a manual expense to a property."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_add_expense", expense.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/expense")
async def update_expense(expense: ExpenseUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing expense."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_update_expense", expense.model_dump(exclude_none=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/expense")
async def delete_expense(expense: ExpenseDelete, db: AsyncSession = Depends(get_db)):
    """Delete an expense from a property."""
    from app.services.mcp.handler import mcp_handler
    try:
        result = await mcp_handler.execute_tool("finans_delete_expense", expense.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
