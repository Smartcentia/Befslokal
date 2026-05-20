"""
API Usage Tracking Model

Tracks OpenAI API usage for cost monitoring and analytics.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.base_class import Base


class APIUsage(Base):
    """Track OpenAI API usage per request."""

    __tablename__ = "api_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Request info
    endpoint = Column(String(100), nullable=False)  # e.g., "chat", "embeddings"
    model = Column(String(50), nullable=False)  # e.g., "gpt-4o-mini"
    user_id = Column(String(255), nullable=True)  # Optional user tracking

    # Token usage
    prompt_tokens = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)

    # Cost (in USD)
    estimated_cost = Column(Float, nullable=False, default=0.0)

    # Metadata
    request_path = Column(String(255), nullable=True)  # e.g., "/api/v1/ai/chat"
    conversation_id = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for efficient queries
    __table_args__ = (
        Index('ix_api_usage_created_at', 'created_at'),
        Index('ix_api_usage_model', 'model'),
        Index('ix_api_usage_endpoint', 'endpoint'),
        Index('ix_api_usage_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<APIUsage {self.model} - {self.total_tokens} tokens - ${self.estimated_cost:.4f}>"
