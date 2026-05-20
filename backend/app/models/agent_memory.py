from sqlalchemy import Column, String, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    additional_metadata = Column(JSONB, nullable=True, server_default='{}')
    embedding = Column(Vector(1536), nullable=True)  # Optimized for OpenAI text-embedding-3-small
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AgentMemory(id={self.id}, content={self.content[:50]}...)>"
