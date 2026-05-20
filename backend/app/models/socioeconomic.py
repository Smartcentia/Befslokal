from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base_class import Base

class SocioeconomicData(Base):
    __tablename__ = "socioeconomic_data"

    socio_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    municipality_code = Column(String(10), nullable=True)
    crime_rate_per_1000 = Column(Float, nullable=True)
    unemployment_rate = Column(Float, nullable=True)
    median_income = Column(Float, nullable=True)
    population_density = Column(Float, nullable=True)
    demographic_profile = Column(JSON, nullable=True)
    data_source = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
