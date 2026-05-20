from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class ExternalApiData(Base):
    __tablename__ = "external_api_data"

    api_data_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_api = Column(String(50), nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(100), nullable=True)
    data = Column(JSON, nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
