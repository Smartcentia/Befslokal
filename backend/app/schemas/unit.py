from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# Unit modeller
class UnitBase(BaseModel):
    property_id: UUID
    purpose: Optional[str] = None
    area_sqm: Optional[float] = None
    floor: Optional[int] = None
    zone_type: Optional[str] = None
    uu_compliant: Optional[bool] = False
    uu_notes: Optional[str] = None


class UnitCreate(UnitBase):
    pass


class UnitUpdate(BaseModel):
    property_id: Optional[UUID] = None
    purpose: Optional[str] = None
    area_sqm: Optional[float] = None
    floor: Optional[int] = None
    zone_type: Optional[str] = None
    uu_compliant: Optional[bool] = None
    uu_notes: Optional[str] = None


class Unit(UnitBase):
    unit_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    external_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
