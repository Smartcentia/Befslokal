from typing import List, Optional
from sqlalchemy.orm import Session
from app.domains.fdv.models.bim import BIMModel, BIMObject
from app.services.base import BaseService
import logging

logger = logging.getLogger("BIMService")

class BIMService(BaseService):
    """
    Service for managing 3D BIM models and spatial queries.
    """
    async def upload_model(self, db: Session, property_id: str, filename: str) -> dict:
        """
        Registers a new BIM model upload.
        """
        self.log_info(f"Registering BIM model {filename} for {property_id}")
        model = BIMModel(property_id=property_id, filename=filename, status="processing")
        db.add(model)
        db.commit()
        db.refresh(model)
        
        # Real parsing would happen here or in a background task
        model.status = "ready"
        db.commit()
        
        return {"model_id": str(model.model_id), "status": "ready"}

    async def get_objects_near(self, db: Session, model_id: str, x: float, y: float, radius: float = 5.0) -> List[dict]:
        """
        Finds objects near a coordinate (simple box check for MVP).
        """
        # Simple bounding logic: find objects within radius
        objects = db.query(BIMObject).filter(
            BIMObject.model_id == model_id,
            BIMObject.pos_x >= x - radius,
            BIMObject.pos_x <= x + radius,
            BIMObject.pos_y >= y - radius,
            BIMObject.pos_y <= y + radius
        ).all()
        
        return [
            {"name": o.name, "type": o.type, "location": {"x": o.pos_x, "y": o.pos_y, "z": o.pos_z}}
            for o in objects
        ]
        
bim_service = BIMService()
