from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Integer, Index, Text
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class TextContent(Base):
    __tablename__ = "text_content"

    text_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)  # Changed to Text for large documents
    additional_metadata = Column(JSON, nullable=True)
    
    # Relations
    contract_id = Column(UUID(as_uuid=True), nullable=True) # Loose coupling
    unit_id = Column(UUID(as_uuid=True), nullable=True)
    property_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Legacy Migration fields
    source_file = Column(String(500), nullable=True)  # Source file path
    chunk_index = Column(Integer, default=0)  # For document chunks
    category = Column(String(100), nullable=True)  # Document category
    
    # Full-text search support
    search_vector = Column(TSVECTOR, nullable=True)  # PostgreSQL full-text search
    embedding = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-small / ada-002 dimension
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Create index for full-text search performance
Index('idx_text_content_search_vector', TextContent.search_vector, postgresql_using='gin')

Index('idx_text_content_contract_id', TextContent.contract_id)
Index('idx_text_content_embedding', TextContent.embedding, postgresql_using='hnsw', postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'})
