"""API endpoints for crisis centers (Bufdir institutions)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.api.deps import get_db
from app.models.crisis_center import CrisisCenter
from app.services.bufdir_import_service import import_bufdir_institutions

router = APIRouter()

class CenterResponse(BaseModel):
    center_id: UUID
    name: str
    location: Optional[str]
    url: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    
    class Config:
        from_attributes = True

@router.get("/centers", response_model=List[CenterResponse])
async def list_centers(
    db: AsyncSession = Depends(get_db),
    limit: int = 100
):
    """List all crisis centers."""
    result = await db.execute(
        select(CrisisCenter).limit(limit)
    )
    centers = result.scalars().all()
    return centers

@router.get("/centers/{center_id}", response_model=CenterResponse)
async def get_center(
    center_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific crisis center by ID."""
    result = await db.execute(
        select(CrisisCenter).where(CrisisCenter.center_id == center_id)
    )
    center = result.scalar_one_or_none()
    
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    
    return center

@router.post("/centers/import")
async def import_centers(
    db: AsyncSession = Depends(get_db)
):
    """Import centers from Bufdir JSON file."""
    # Path relative to backend root
    json_path = "skills/bufdir_scraper/resources/institutions.json"
    
    try:
        stats = await import_bufdir_institutions(db, json_path)
        return {
            "message": "Import successful",
            "stats": stats
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"JSON file not found at {json_path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )
