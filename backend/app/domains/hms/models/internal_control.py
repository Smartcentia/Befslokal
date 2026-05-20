from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
# Compatibility with SQLite
from sqlalchemy import UUID as SA_UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class InternalControlCase(Base):
    __tablename__ = "internal_control_cases"

    case_id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(SA_UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    # Link to the deviation (RiskAssessment) that triggered this case
    risk_assessment_id = Column(SA_UUID(as_uuid=True), ForeignKey("risk_assessments.assessment_id"), nullable=True)
    # user_id is optional as per doc ("assigned_user_id can be null")
    assigned_user_id = Column(SA_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    case_type = Column(String, nullable=False) # monthly, quarterly, annual
    status = Column(String, default="open") # open, closed, in_progress
    priority = Column(String, default="medium")
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)
    
    # Process Engine Persistence
    process_state = Column(String, default="Opprettet", nullable=True)
    process_data = Column(JSON, default={}, nullable=True)
    process_history = Column(JSON, default=[], nullable=True)

    # Follow-up tracking
    follow_up_status = Column(String, default="none", nullable=True)
    last_reminder_at = Column(DateTime(timezone=True), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    property = relationship("Property", back_populates="cases", lazy="selectin")
    assigned_user = relationship("User", lazy="selectin")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(SA_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    notification_type = Column(String, default="internal_control")
    related_entity_type = Column(String, nullable=True) # e.g. "case"
    related_entity_id = Column(SA_UUID(as_uuid=True), nullable=True) 
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", lazy="selectin")
