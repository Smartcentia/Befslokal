from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from app.db.base_class import Base

class ToolStatus(str, enum.Enum):
    EXPERIMENTAL = "experimental"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"

class QAStatus(str, enum.Enum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"

class AITool(Base):
    __tablename__ = "ai_tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metadata
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # The Brains
    code = Column(Text, nullable=False) # The executable Python code
    dependencies = Column(Text, nullable=True) # JSON list of libs, stored as string
    requires_real_sk = Column(Boolean, default=False)
    
    # Quality Assurance
    qa_status = Column(String, default=QAStatus.PENDING)
    qa_report = Column(Text, nullable=True)

    # Governance
    status = Column(String, default=ToolStatus.EXPERIMENTAL)
    is_public = Column(Boolean, default=False) # If True, visible to all Organization
    is_pinned = Column(Boolean, default=False) # If True, displayed on Dashboard
    
    # Tracking
    # created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True) # Commented out until Users table confirmed
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Vector Link
    # vector_id was deprecated
