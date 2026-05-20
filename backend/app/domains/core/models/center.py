from sqlalchemy import Column, String, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.db.base_class import Base

class Center(Base):
    __tablename__ = "centers"

    center_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    region = Column(String, nullable=True)
    
    # Store center-level emergency contacts (e.g. "Vaktmester", "Securitas")
    # Structure: [{'name': '...', 'role': '...', 'phone': '...'}]
    emergency_contacts = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    properties = relationship("Property", back_populates="center")
