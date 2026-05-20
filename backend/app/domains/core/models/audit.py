from sqlalchemy import Column, String, DateTime, JSON, UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    action = Column(String, nullable=False) # e.g. "AI_TOOL_EXECUTION", "PROPERTY_UPDATE"
    actor = Column(String, nullable=True)   # e.g. "user_id" or "system"
    entity_type = Column(String, nullable=True) # e.g. "property"
    entity_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    severity = Column(String, default="INFO") # INFO, WARNING, ERROR

    def __repr__(self):
        return f"<AuditLog {self.action} @ {self.timestamp}>"
