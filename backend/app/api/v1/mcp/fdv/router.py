from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.domains.fdv.services.fdv_service import fdv_service
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ComponentCreate(BaseModel):
    property_id: str
    name: str
    type: str
    location: Optional[str] = None

class MaintenanceCreate(BaseModel):
    component_id: str
    description: str
    cost: int = 0

@router.get("/")
async def root():
    return {"status": "FDV/Work Order MCP Server Active"}

@router.get("/components/{property_id}")
async def list_components(property_id: str, db: Session = Depends(get_db)):
    """
    Agent Action: List all components for a property (e.g., to check if HVAC exists).
    """
    try:
        return await fdv_service.get_components(db, property_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/components")
async def add_component(comp: ComponentCreate, db: Session = Depends(get_db)):
    """
    Agent Action: Register a new building component.
    """
    try:
        return await fdv_service.add_component(db, comp.property_id, comp.name, comp.type, comp.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/maintenance")
async def log_maintenance(record: MaintenanceCreate, db: Session = Depends(get_db)):
    """
    Agent Action: Log maintenance performed on a component.
    """
    try:
        return await fdv_service.log_maintenance(db, record.component_id, record.description, record.cost)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
