from sqlalchemy import Column, String, Numeric, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base

class MasterDataCrosswalk(Base):
    __tablename__ = "master_data_crosswalk"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    relation_type = Column(String(50), nullable=False, index=True) # LOCATED_AT | FUNDS | BOOKED_ON | GOVERNED_BY
    source_type = Column(String(50), nullable=False, index=True)   # DIM1 | BIRK | PROPERTY | CONTRACT
    source_id = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    target_id = Column(String(100), nullable=False, index=True)
    
    status = Column(String(50), nullable=True)                     # pending | approved | rejected
    collision_flag = Column(Boolean, default=False, nullable=True)
    match_method = Column(String(50), nullable=True)               # exact | heuristic | fuzzy | manual
    score = Column(Numeric(5, 2), nullable=True)
    confidence = Column(String(20), nullable=True)                 # HIGH | MEDIUM | LOW
    run_id = Column(String(50), nullable=True)
    
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    audit_metadata = Column(JSON, nullable=True)                   # JSONB equivalent in sqlite/postgres
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
