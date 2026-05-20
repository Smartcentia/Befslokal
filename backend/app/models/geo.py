from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class GeologicalData(Base):
    __tablename__ = "geological_data"

    geo_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    bedrock_type = Column(String(100), nullable=True)
    soil_type = Column(String(100), nullable=True)
    groundwater_depth = Column(Float, nullable=True)
    landslide_risk = Column(String(20), nullable=True)
    quickclay_risk = Column(Integer, nullable=True)
    seismic_zone = Column(Integer, nullable=True)
    data_source = Column(String(50), nullable=True)
    raw_data = Column(JSON, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

class NaturalHazardEvent(Base):
    __tablename__ = "natural_hazard_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    event_type = Column(String(50), nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=True)
    severity = Column(String(20), nullable=True)
    description = Column(String, nullable=True)
    casualties = Column(Integer, nullable=True)
    property_damage = Column(Float, nullable=True)
    radius_affected_meters = Column(Float, nullable=True)
    data_source = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
