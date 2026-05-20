from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import UUID as SA_UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class ScheduledActivity(Base):
    """
    Scheduled recurring activities for HMS compliance.
    Activities are generated based on property metadata tags.
    """
    __tablename__ = "scheduled_activities"

    activity_id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(SA_UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    
    # Activity metadata
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Categorization
    activity_type = Column(String, nullable=False)  # "daily", "weekly", "monthly", "quarterly", "annual"
    category = Column(String, nullable=False)  # "brann", "teknisk", "hms", "sikkerhet", "inneklima"
    priority = Column(String, nullable=False, default="medium")  # "critical", "high", "medium", "low"
    
    # Assignment
    responsible_role = Column(String, nullable=False)  # "vaktmester", "eiendomsansvarlig", "områdeleder"
    assigned_user_id = Column(SA_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Scheduling
    recurrence_rule = Column(JSONB, nullable=False)  # {"frequency": "weekly", "interval": 1, "day_of_week": 1}
    next_due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    last_generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Activation conditions
    enabled = Column(Boolean, default=True, nullable=False)
    property_tags_required = Column(JSONB, nullable=True)  # ["Institusjon", "RKL6"] - only generate if ALL tags match
    property_tags_excluded = Column(JSONB, nullable=True)  # ["Kontor"] - don't generate if ANY tag matches
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=True)  # "system", "admin@bufdir.no", etc.
    
    # Relationships
    property = relationship("Property", lazy="selectin")
    assigned_user = relationship("User", lazy="selectin")


class ActivityTemplate(Base):
    """
    Master templates for generating scheduled activities.
    These define the rules for what activities should be created for different property types.
    """
    __tablename__ = "activity_templates"

    template_id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template metadata
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    priority = Column(String, nullable=False, default="medium")
    
    # Scheduling rules
    activity_type = Column(String, nullable=False)
    recurrence_pattern = Column(JSONB, nullable=False)  # Base pattern for recurrence
    
    # Assignment rules
    responsible_role = Column(String, nullable=False)
    
    # Activation rules
    property_tags_required = Column(JSONB, nullable=True)
    property_tags_excluded = Column(JSONB, nullable=True)
    
    # Template management
    enabled = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)

    # Activity hub
    created_by_user_id = Column(SA_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    scope = Column(String, default="system", nullable=True)  # system, user, region, global
    adoption_count = Column(Integer, default=0, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
