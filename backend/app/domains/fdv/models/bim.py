from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class BIMModel(Base):
    """
    Represents a 3D model file (IFC, RVT, GLB) uploaded for a property.
    """
    __tablename__ = "bim_models"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    filename = Column(String, nullable=False)
    format = Column(String(10), default="IFC")
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    file_path = Column(String, nullable=True) # Path to storage (e.g. Object Storage)
    status = Column(String(20), default="processing") # processing, ready, error

class BIMObject(Base):
    """
    Represents a specific 3D object within a BIM model (e.g. a Wall, Door, Sensor).
    """
    __tablename__ = "bim_objects"

    object_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("bim_models.model_id"), nullable=False)
    ifc_guid = Column(String(50), nullable=True) # The GlobalId from the IFC file
    name = Column(String, nullable=True)
    type = Column(String(50), nullable=True) # e.g. IfcWall, IfcDoor
    
    # Simple bounding box or centroid for spatial queries using simple Floats for MVP
    # In production, use PostGIS geometry types.
    pos_x = Column(Float, nullable=True)
    pos_y = Column(Float, nullable=True)
    pos_z = Column(Float, nullable=True)
    
    properties = Column(JSON, default={}) # Extracted property sets (Pset_...)
    
    # Link to physical component tracking (FDV)
    linked_component_id = Column(UUID(as_uuid=True), ForeignKey("building_components.component_id"), nullable=True)
