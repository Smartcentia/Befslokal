from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from app.db.base_class import Base

class DataFieldMetadata(Base):
    __tablename__ = "data_field_metadata"

    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, nullable=False, index=True)
    column_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    classification_override = Column(String, nullable=True) # Allow overriding automatic classification
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
