import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, aliased

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.fdv.models.fdv import BuildingComponent as ComponentModel
from app.domains.fdv.schemas.fdv import (
    BuildingComponent, 
    BuildingComponentCreate, 
    BuildingComponentUpdate
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=BuildingComponent, status_code=201)
async def create_component(
    component_in: BuildingComponentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new Building Component (with optional semantic fields)."""
    db_obj = ComponentModel(**component_in.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/{component_id}", response_model=BuildingComponent)
async def get_component(
    component_id: UUID,
    include_children: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific component by ID."""
    stmt = select(ComponentModel).where(ComponentModel.component_id == component_id)
    
    # If we had a proper relationship defined in ORM model for "children", we could use selectinload
    # For now, we will perform a manual fetch if children are requested, or rely on ORM if we add relationship later.
    # To keep it simple in this phase, let's just fetch the single component.
    # If include_children is True, we might need a recursive CTE or separate query.
    
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
        
    if include_children:
        # Fetch immediate children manually
        child_stmt = select(ComponentModel).where(ComponentModel.parent_id == component_id)
        child_res = await db.execute(child_stmt)
        children = child_res.scalars().all()
        # Ensure the Pydantic model can handle this assignment (it has 'children' field)
        component.children = children

    return component

@router.patch("/{component_id}", response_model=BuildingComponent)
async def update_component(
    component_id: UUID,
    component_in: BuildingComponentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a component (including moving it in hierarchy)."""
    stmt = select(ComponentModel).where(ComponentModel.component_id == component_id)
    result = await db.execute(stmt)
    component = result.scalar_one_or_none()
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
        
    update_data = component_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(component, field, value)
        
    await db.commit()
    await db.refresh(component)
    return component

@router.get("/property/{property_id}", response_model=List[BuildingComponent])
async def list_property_components(
    property_id: UUID,
    root_only: bool = Query(False, description="If true, only return top-level components (no parent)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all components for a property."""
    query = select(ComponentModel).where(ComponentModel.property_id == property_id)
    
    if root_only:
        query = query.where(ComponentModel.parent_id == None)
        
    result = await db.execute(query)
    return result.scalars().all()
