from pydantic import BaseModel, UUID4, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BuildingComponentBase(BaseModel):
    name: str
    type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = "active"
    technical_data: Optional[Dict[str, Any]] = {}
    
    # Semantic Fields
    parent_id: Optional[UUID4] = None
    brick_class: Optional[str] = None
    system_code: Optional[str] = None

class BuildingComponentCreate(BuildingComponentBase):
    property_id: UUID4

class BuildingComponentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    technical_data: Optional[Dict[str, Any]] = None
    parent_id: Optional[UUID4] = None
    brick_class: Optional[str] = None
    system_code: Optional[str] = None

class BuildingComponent(BuildingComponentBase):
    component_id: UUID4
    property_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Optional children field for hierarchy fetching
    children: Optional[List['BuildingComponent']] = None

    class Config:
        from_attributes = True

# Resolve forward reference for recursive children
BuildingComponent.model_rebuild()
