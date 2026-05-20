from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base

class GeneratedTool(Base):
    __tablename__ = "generated_tools"

    tool_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    python_code = Column(Text, nullable=False)
    sql_pattern = Column(Text)
    status = Column(String(50), default='pending', index=True) # pending, active, deprecated
    source_log_ids = Column(JSONB) # Context for why this was created
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    version = Column(Integer, default=1)
