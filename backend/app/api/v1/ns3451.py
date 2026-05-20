from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api import deps
from app.domains.core.models.ns3451 import NS3451Code
from pydantic import BaseModel

router = APIRouter()

class NS3451CodeSchema(BaseModel):
    code: str
    name: str
    level: int
    parent_code: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[NS3451CodeSchema])
async def list_ns3451_codes(
    level: Optional[int] = Query(None, description="Filter by level (1, 2, or 3)"),
    parent_code: Optional[str] = Query(None, description="Filter by parent code"),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    List NS 3451 codes.
    """
    query = select(NS3451Code).order_by(NS3451Code.code)
    
    if level:
        query = query.filter(NS3451Code.level == level)
    if parent_code:
        query = query.filter(NS3451Code.parent_code == parent_code)
        
    result = await db.execute(query)
    return result.scalars().all()
