from sqlalchemy import Column, String, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class CrisisCenter(Base):
    """Crisis/Emergency Centers for child welfare (Bufdir institutions)."""
    __tablename__ = "crisis_centers"

    center_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True)  # Municipality/City
    url = Column(String, nullable=True)  # Link to detail page
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
