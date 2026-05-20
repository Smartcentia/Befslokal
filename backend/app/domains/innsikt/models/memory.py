from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    preference_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, unique=True) # External User ID
    language = Column(String(10), default="en")
    notifications = Column(JSON, default={}) # e.g. {"risk_threshold": "high", "channels": ["email"]}
    ui_settings = Column(JSON, default={}) # e.g. {"theme": "dark", "dashboard_layout": []}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ContextHistory(Base):
    __tablename__ = "context_history"

    context_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    interaction_type = Column(String(50), nullable=True) # e.g. "chat", "action", "alert"
    content = Column(JSON, nullable=True) # Summary of what happened
    embedding = Column(JSON, nullable=True) # Vector embedding for semantic recall
    created_at = Column(DateTime(timezone=True), server_default=func.now())
