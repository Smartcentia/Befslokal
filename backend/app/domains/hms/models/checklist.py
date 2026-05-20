from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import UUID as SA_UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"

    template_id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    items = Column(JSON, nullable=False)  # List of checklist items: [{"id": "1", "label": "Sjekk brannvarsler"}]
    category = Column(String, nullable=False)  # e.g. "brannvern", "el-sikkerhet"
    frequency = Column(String, nullable=True)  # e.g. "weekly", "monthly"

    created_by_user_id = Column(SA_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    scope = Column(String, default="system", nullable=True)  # system, user, region, global

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class ChecklistExecution(Base):
    __tablename__ = "checklist_executions"

    execution_id = Column(SA_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(SA_UUID(as_uuid=True), ForeignKey("checklist_templates.template_id"), nullable=False, index=True)
    property_id = Column(SA_UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    user_id = Column(SA_UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    
    status = Column(String, default="in_progress") # in_progress, completed
    responses = Column(JSON, default={}) # {"1": true, "2": false}
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    template = relationship("ChecklistTemplate", lazy="selectin")
    # property and user relationships omitted for brevity but implied
