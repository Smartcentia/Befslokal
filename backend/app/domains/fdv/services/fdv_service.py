from typing import List, Optional
from sqlalchemy.orm import Session
from app.domains.fdv.models.fdv import BuildingComponent, MaintenanceRecord
from app.services.base import BaseService
import logging

logger = logging.getLogger("FDVService")

class FDVService(BaseService):
    """
    Service for managing FDV (Forvaltning, Drift, Vedlikehold) data.
    """
    async def get_components(self, db: Session, property_id: str) -> List[dict]:
        """
        Retrieves all building components for a property.
        """
        components = db.query(BuildingComponent).filter(BuildingComponent.property_id == property_id).all()
        return [
            {
                "component_id": str(c.component_id),
                "name": c.name,
                "type": c.type,
                "status": c.status,
                "location": c.location
            }
            for c in components
        ]

    async def add_component(self, db: Session, property_id: str, name: str, type: str, location: str) -> dict:
        """
        Adds a new building component.
        """
        self.log_info(f"Adding component {name} to property {property_id}")
        
        comp = BuildingComponent(
            property_id=property_id,
            name=name,
            type=type,
            location=location
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)
        
        return {"component_id": str(comp.component_id), "status": "created"}

    async def log_maintenance(self, db: Session, component_id: str, description: str, cost: int = 0) -> dict:
        """
        Logs a maintenance record for a component.
        """
        self.log_info(f"Logging maintenance for component {component_id}")
        
        record = MaintenanceRecord(
            component_id=component_id,
            description=description,
            cost=cost
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {"record_id": str(record.record_id), "status": "logged"}

fdv_service = FDVService()
