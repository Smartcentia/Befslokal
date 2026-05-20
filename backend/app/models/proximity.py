from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base_class import Base

class ProximityService(Base):
    __tablename__ = "proximity_services"

    service_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    service_type = Column(String(50), nullable=True)
    service_name = Column(String(255), nullable=True)
    distance_meters = Column(Float, nullable=True)
    travel_time_minutes = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    data_source = Column(String(50), nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
