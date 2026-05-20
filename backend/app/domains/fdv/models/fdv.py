from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship 
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class BuildingComponent(Base):
    """
    Represents a physical component in a building (e.g., 'Ventilation Unit A', 'Elevator 1').
    """
    __tablename__ = "building_components"

    component_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(String(50), nullable=True) # e.g. "HVAC", "Electrical", "Plumbing"
    location = Column(String, nullable=True) # e.g. "Roof", "Basement"
    install_date = Column(DateTime(timezone=True), nullable=True)
    lifecycle_years = Column(Integer, nullable=True)
    status = Column(String(20), default="active") # active, inactive, needs_repair
    technical_data = Column(JSON, default={}) # Manufacturer, model, specs
    
    # Semantic Data / Hierarchy (EG Nexus Phase 1)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("building_components.component_id"), nullable=True)
    brick_class = Column(String, nullable=True) # e.g. "brick:Air_Handler_Unit"
    system_code = Column(String, nullable=True) # e.g. "360.01" (Old free text field, keep for now)
    
    # Gap 1: Strict NS 3451 Code (Standardized)
    ns3451_code = Column(String(20), ForeignKey("ns3451_codes.code"), nullable=True)
    
    # Relationships
    ns3451_rel = relationship("app.domains.core.models.ns3451.NS3451Code", back_populates="components")
    # parent = relationship("BuildingComponent", remote_side=[component_id], backref="children") # Already inferred?

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class MaintenanceRecord(Base):
    """
    Log of maintenance performed on a component.
    """
    __tablename__ = "maintenance_records"

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_id = Column(UUID(as_uuid=True), ForeignKey("building_components.component_id"), nullable=False)
    date_performed = Column(DateTime(timezone=True), server_default=func.now())
    performed_by = Column(String, nullable=True)
    description = Column(String, nullable=True)
    cost = Column(Integer, nullable=True)
    linked_work_order_id = Column(UUID(as_uuid=True), nullable=True) # Optional link to Action Server WO
    created_at = Column(DateTime(timezone=True), server_default=func.now())
