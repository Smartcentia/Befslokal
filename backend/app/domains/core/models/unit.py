from sqlalchemy import Column, String, Float, DateTime, JSON, Integer, ForeignKey, UUID, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base

class Unit(Base):
    __tablename__ = "units"

    unit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    address = Column(String, nullable=True)
    purpose = Column(String, nullable=True)
    area_sqm = Column(Float, nullable=True)
    floor = Column(Integer, nullable=True)
    # Statsbygg Zoning & UU
    zone_type = Column(String, nullable=True) # e.g. "ANSA", "BEBO"
    uu_compliant = Column(Boolean, default=False)
    uu_notes = Column(String, nullable=True)
    external_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    property = relationship("Property", lazy="selectin")
