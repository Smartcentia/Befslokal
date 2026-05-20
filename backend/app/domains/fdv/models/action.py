from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class WorkOrder(Base):
    __tablename__ = "work_orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False)
    description = Column(String, nullable=False)
    status = Column(String(50), default="pending") # pending, in_progress, completed, cancelled
    priority = Column(String(20), default="medium") # low, medium, high, critical
    assigned_to = Column(String, nullable=True) # User or Agent ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.order_id"), nullable=True) # Optional link to parent WO
    title = Column(String, nullable=False)
    action_type = Column(String(50), nullable=True) # e.g., "email", "database_update", "report_generation"
    payload = Column(JSON, nullable=True) # Parameters for the action
    status = Column(String(50), default="pending")
    result = Column(JSON, nullable=True) # Output of the action
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
