from sqlalchemy import Column, String, DateTime, JSON, UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class Party(Base):
    __tablename__ = "parties"

    party_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_code = Column(String(20), nullable=True, unique=True, index=True)  # BUF-P-NNNNNN (se docs/ARKIVKODE_OG_REFERANSEKODE_STANDARD.md)
    name = Column(String, nullable=False)
    orgnr = Column(String(9), unique=True, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    external_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
