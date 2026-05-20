from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class DataSubjectRequest(Base):
    """
    Tracks GDPR requests (Right to Access, Right to be Forgotten).
    """
    __tablename__ = "gdpr_requests"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True) # The ID of the requester
    request_type = Column(String(50), nullable=False) # "access", "deletion", "rectification"
    status = Column(String(20), default="pending") # pending, processing, completed, rejected
    details = Column(JSON, default={}) # Specifics of the request
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class AnonymizationLog(Base):
    """
    Audit log of PII masking operations performed by the agent.
    """
    __tablename__ = "gdpr_anonymization_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=True) # e.g. "document", "chat_message"
    entity_id = Column(String, nullable=True)
    original_pii_type = Column(String(50), nullable=True) # e.g. "email", "ssn"
    action = Column(String(20), default="masked")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
