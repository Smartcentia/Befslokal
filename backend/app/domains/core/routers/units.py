from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.core.property_access import check_property_access
from app.domains.core.models.unit import Unit as UnitModel
from app.schemas.property import Unit as UnitSchema, UnitCreate

router = APIRouter()

@router.post("", response_model=UnitSchema, status_code=201)
async def create_unit(
    unit_in: UnitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opprett ny enhet (med property access check)."""
    # Check property access (write access required to create unit)
    await check_property_access(
        db=db,
        user=current_user,
        property_id=str(unit_in.property_id),
        require_write=True
    )
    
    db_obj = UnitModel(
        unit_id=uuid4(),
        property_id=unit_in.property_id,
        address=getattr(unit_in, "address", None),
        purpose=unit_in.purpose,
        area_sqm=unit_in.area_sqm,
        floor=unit_in.floor,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("", response_model=List[UnitSchema])
async def get_units(
    property_id: Optional[UUID] = Query(None, description="Filtrer på eiendom ID"),
    skip: int = Query(0, description="Antall å hoppe over (pagination)"),
    limit: int = Query(50, description="Antall å hente (pagination)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent liste over enheter (filtrert basert på property access)."""
    # Enforce max limit
    safe_limit = min(limit, 10000)
    
    query = select(UnitModel)
    
    if property_id:
        # Check property access
        await check_property_access(
            db=db,
            user=current_user,
            property_id=str(property_id),
            require_write=False
        )
        query = query.filter(UnitModel.property_id == property_id)
    else:
        # If no property_id filter, we need to filter by user's accessible properties
        # This is more complex - for now, require property_id filter
        # In a full implementation, we'd get user's accessible property IDs and filter
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="property_id parameter is required"
        )
        
    result = await db.execute(query.offset(skip).limit(safe_limit))
    units = result.scalars().all()
    return units

@router.patch("/{unit_id}", response_model=UnitSchema)
async def patch_unit(
    unit_id: UUID,
    unit_in: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Oppdater enhet (med property access check)."""
    result = await db.execute(select(UnitModel).where(UnitModel.unit_id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Enhet ikke funnet")
    
    # Check property access (write access required to update unit)
    if unit.property_id:
        await check_property_access(
            db=db,
            user=current_user,
            property_id=str(unit.property_id),
            require_write=True
        )
    
    for field, value in unit_in.items():
        if hasattr(unit, field):
            setattr(unit, field, value)
    
    await db.commit()
    await db.refresh(unit)
    return unit

@router.delete("/{unit_id}", status_code=204)
async def delete_unit(
    unit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Slett enhet (med property access check)."""
    result = await db.execute(select(UnitModel).where(UnitModel.unit_id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail="Enhet ikke funnet")
    
    # Check property access (write access required to delete unit)
    if unit.property_id:
        await check_property_access(
            db=db,
            user=current_user,
            property_id=str(unit.property_id),
            require_write=True
        )
    
    await db.delete(unit)
    await db.commit()
    return Response(status_code=204)
