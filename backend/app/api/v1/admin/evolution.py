
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.api.deps import get_db, get_current_active_superuser
from app.models.generated_tool import GeneratedTool
# from app.core.auth import get_current_active_superuser # Use real auth if available

router = APIRouter(dependencies=[Depends(get_current_active_superuser)])

class ToolDTO(BaseModel):
    tool_id: str
    name: str
    description: Optional[str] = None
    status: str
    sql_pattern: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/tools", response_model=List[ToolDTO])
async def list_generated_tools(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List generated tools, optionally filtered by status."""
    query = select(GeneratedTool).order_by(GeneratedTool.created_at.desc())
    if status:
        query = query.where(GeneratedTool.status == status)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/tools/{tool_id}/approve")
async def approve_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    """Approve a pending tool."""
    from uuid import UUID
    
    try:
        uuid_obj = UUID(tool_id)
        result = await db.execute(select(GeneratedTool).where(GeneratedTool.tool_id == uuid_obj))
        tool = result.scalar_one_or_none()
        
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
            
        tool.status = 'active'
        await db.commit()
        
        return {"status": "success", "message": f"Tool {tool.name} approved. Restart required to load."}
        
    except ValueError:
         raise HTTPException(status_code=400, detail="Invalid ID format")
