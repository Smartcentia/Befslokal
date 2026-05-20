"""
Bygningsstruktur – REST API

Endpoints:
  GET    /buildings?property_id=<uuid>       – list buildings (with nested floors)
  POST   /buildings                          – create building
  PATCH  /buildings/{building_id}            – update building
  DELETE /buildings/{building_id}            – delete building (cascade)
  GET    /buildings/{building_id}/floors     – list floors for a building
  POST   /buildings/{building_id}/floors     – add floor
  PATCH  /floors/{floor_id}                 – update floor
  DELETE /floors/{floor_id}                 – delete floor
  GET    /floors/{floor_id}/spaces           – list spaces on floor
  POST   /floors/{floor_id}/spaces           – add space
  PATCH  /spaces/{space_id}                  – update space
  DELETE /spaces/{space_id}                  – delete space
  GET    /properties/{property_id}/structure – full tree
"""

from __future__ import annotations

import logging
from typing import List, Optional, Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_user
from app.domains.core.models.building import Building, Floor, Space
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas (inline – minimal, expand as needed)
# ---------------------------------------------------------------------------

class BuildingCreate(BaseModel):
    property_id: UUID
    name: str
    building_code: Optional[str] = None
    year_built: Optional[int] = None
    building_type: Optional[str] = "main"
    floors_above_ground: Optional[int] = 1
    floors_below_ground: Optional[int] = 0
    total_area_sqm: Optional[float] = None
    description: Optional[str] = None


class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    building_code: Optional[str] = None
    year_built: Optional[int] = None
    building_type: Optional[str] = None
    floors_above_ground: Optional[int] = None
    floors_below_ground: Optional[int] = None
    total_area_sqm: Optional[float] = None
    description: Optional[str] = None


class BuildingOut(BaseModel):
    building_id: UUID
    property_id: UUID
    name: str
    building_code: Optional[str]
    year_built: Optional[int]
    building_type: Optional[str]
    floors_above_ground: Optional[int]
    floors_below_ground: Optional[int]
    total_area_sqm: Optional[float]
    description: Optional[str]

    class Config:
        from_attributes = True


class FloorCreate(BaseModel):
    floor_number: int
    name: Optional[str] = None
    area_sqm: Optional[float] = None


class FloorUpdate(BaseModel):
    floor_number: Optional[int] = None
    name: Optional[str] = None
    area_sqm: Optional[float] = None


class FloorOut(BaseModel):
    floor_id: UUID
    building_id: UUID
    floor_number: int
    name: Optional[str]
    area_sqm: Optional[float]

    class Config:
        from_attributes = True


class SpaceCreate(BaseModel):
    property_id: UUID
    unit_id: Optional[UUID] = None
    name: str
    space_type: Optional[str] = "room"
    area_sqm: Optional[float] = None
    description: Optional[str] = None


class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    space_type: Optional[str] = None
    area_sqm: Optional[float] = None
    description: Optional[str] = None
    unit_id: Optional[UUID] = None


class SpaceOut(BaseModel):
    space_id: UUID
    floor_id: Optional[UUID]
    property_id: UUID
    unit_id: Optional[UUID]
    name: str
    space_type: Optional[str]
    area_sqm: Optional[float]
    description: Optional[str]

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _unit_to_dict(u: Unit) -> Dict[str, Any]:
    return {
        "unit_id": str(u.unit_id),
        "address": u.address,
        "purpose": u.purpose,
        "area_sqm": u.area_sqm,
        "floor": u.floor,
        "building_id": str(u.building_id) if u.building_id else None,
        "floor_id": str(u.floor_id) if u.floor_id else None,
    }


# ---------------------------------------------------------------------------
# Buildings CRUD
# ---------------------------------------------------------------------------

@router.get("/buildings", tags=["Buildings"])
async def list_buildings(
    property_id: UUID = Query(..., description="Eiendom UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """List alle bygg for en eiendom, med nestede etasjer."""
    result = await db.execute(
        select(Building)
        .where(Building.property_id == property_id)
        .options(selectinload(Building.floors))
        .order_by(Building.name)
    )
    buildings = result.scalars().all()
    out = []
    for b in buildings:
        bd = BuildingOut.model_validate(b).model_dump()
        bd["floors"] = [FloorOut.model_validate(f).model_dump() for f in b.floors]
        out.append(bd)
    return out


@router.post("/buildings", status_code=status.HTTP_201_CREATED, tags=["Buildings"])
async def create_building(
    payload: BuildingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    building = Building(**payload.model_dump())
    db.add(building)
    await db.commit()
    await db.refresh(building)
    return BuildingOut.model_validate(building).model_dump()


@router.patch("/buildings/{building_id}", tags=["Buildings"])
async def update_building(
    building_id: UUID,
    payload: BuildingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    result = await db.execute(select(Building).where(Building.building_id == building_id))
    building = result.scalar_one_or_none()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(building, field, value)
    await db.commit()
    await db.refresh(building)
    return BuildingOut.model_validate(building).model_dump()


@router.delete("/buildings/{building_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Buildings"])
async def delete_building(
    building_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Building).where(Building.building_id == building_id))
    building = result.scalar_one_or_none()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    await db.delete(building)
    await db.commit()


# ---------------------------------------------------------------------------
# Floors CRUD
# ---------------------------------------------------------------------------

@router.get("/buildings/{building_id}/floors", tags=["Buildings"])
async def list_floors(
    building_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(Floor).where(Floor.building_id == building_id).order_by(Floor.floor_number)
    )
    floors = result.scalars().all()
    return [FloorOut.model_validate(f).model_dump() for f in floors]


@router.post("/buildings/{building_id}/floors", status_code=status.HTTP_201_CREATED, tags=["Buildings"])
async def create_floor(
    building_id: UUID,
    payload: FloorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    # Verify building exists
    result = await db.execute(select(Building).where(Building.building_id == building_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Building not found")
    floor = Floor(building_id=building_id, **payload.model_dump())
    db.add(floor)
    await db.commit()
    await db.refresh(floor)
    return FloorOut.model_validate(floor).model_dump()


@router.patch("/floors/{floor_id}", tags=["Buildings"])
async def update_floor(
    floor_id: UUID,
    payload: FloorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    result = await db.execute(select(Floor).where(Floor.floor_id == floor_id))
    floor = result.scalar_one_or_none()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(floor, field, value)
    await db.commit()
    await db.refresh(floor)
    return FloorOut.model_validate(floor).model_dump()


@router.delete("/floors/{floor_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Buildings"])
async def delete_floor(
    floor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Floor).where(Floor.floor_id == floor_id))
    floor = result.scalar_one_or_none()
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    await db.delete(floor)
    await db.commit()


# ---------------------------------------------------------------------------
# Spaces CRUD
# ---------------------------------------------------------------------------

@router.get("/floors/{floor_id}/spaces", tags=["Buildings"])
async def list_spaces(
    floor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    result = await db.execute(select(Space).where(Space.floor_id == floor_id))
    spaces = result.scalars().all()
    return [SpaceOut.model_validate(s).model_dump() for s in spaces]


@router.post("/floors/{floor_id}/spaces", status_code=status.HTTP_201_CREATED, tags=["Buildings"])
async def create_space(
    floor_id: UUID,
    payload: SpaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    result = await db.execute(select(Floor).where(Floor.floor_id == floor_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Floor not found")
    space = Space(floor_id=floor_id, **payload.model_dump())
    db.add(space)
    await db.commit()
    await db.refresh(space)
    return SpaceOut.model_validate(space).model_dump()


@router.patch("/spaces/{space_id}", tags=["Buildings"])
async def update_space(
    space_id: UUID,
    payload: SpaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    result = await db.execute(select(Space).where(Space.space_id == space_id))
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(space, field, value)
    await db.commit()
    await db.refresh(space)
    return SpaceOut.model_validate(space).model_dump()


@router.delete("/spaces/{space_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Buildings"])
async def delete_space(
    space_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Space).where(Space.space_id == space_id))
    space = result.scalar_one_or_none()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    await db.delete(space)
    await db.commit()


# ---------------------------------------------------------------------------
# Full property structure tree
# ---------------------------------------------------------------------------

@router.get("/properties/{property_id}/structure", tags=["Buildings"])
async def get_property_structure(
    property_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returnerer hele bygningsstrukturen for en eiendom:
    buildings → floors → spaces + units
    Inkluderer også units uten building (unassigned_units).
    """
    # Load all buildings with floors → spaces
    b_result = await db.execute(
        select(Building)
        .where(Building.property_id == property_id)
        .options(
            selectinload(Building.floors).selectinload(Floor.spaces)
        )
        .order_by(Building.name)
    )
    buildings = b_result.scalars().all()

    # Load all units for the property
    u_result = await db.execute(
        select(Unit).where(Unit.property_id == property_id)
    )
    all_units = u_result.scalars().all()

    # Map units by floor_id and by building_id for quick lookup
    units_by_floor: Dict[str, List[Dict]] = {}
    assigned_unit_ids: set = set()

    for u in all_units:
        if u.floor_id:
            key = str(u.floor_id)
            units_by_floor.setdefault(key, []).append(_unit_to_dict(u))
            assigned_unit_ids.add(str(u.unit_id))

    buildings_out = []
    for b in buildings:
        floors_out = []
        for f in b.floors:
            floor_units = units_by_floor.get(str(f.floor_id), [])
            floors_out.append({
                "floor_id": str(f.floor_id),
                "building_id": str(f.building_id),
                "floor_number": f.floor_number,
                "name": f.name,
                "area_sqm": f.area_sqm,
                "spaces": [SpaceOut.model_validate(s).model_dump() for s in f.spaces],
                "units": floor_units,
            })
        buildings_out.append({
            "building_id": str(b.building_id),
            "property_id": str(b.property_id),
            "name": b.name,
            "building_code": b.building_code,
            "year_built": b.year_built,
            "building_type": b.building_type,
            "floors_above_ground": b.floors_above_ground,
            "floors_below_ground": b.floors_below_ground,
            "total_area_sqm": b.total_area_sqm,
            "description": b.description,
            "floors": floors_out,
        })

    unassigned_units = [_unit_to_dict(u) for u in all_units if str(u.unit_id) not in assigned_unit_ids]

    return {
        "property_id": str(property_id),
        "buildings": buildings_out,
        "unassigned_units": unassigned_units,
    }
