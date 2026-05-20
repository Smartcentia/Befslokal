from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base_class import Base

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    env_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    air_quality_index = Column(Float, nullable=True)
    noise_level_db = Column(Float, nullable=True)
    pollution_sources = Column(JSON, nullable=True)
    contaminated_sites_nearby = Column(JSON, nullable=True)
    data_source = Column(String(50), nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
