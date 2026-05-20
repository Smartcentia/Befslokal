from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class FileMeta(Base):
    __tablename__ = "file_meta"

    file_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.contract_id"), nullable=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("internal_control_cases.case_id"), nullable=True)
    path = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    sha256 = Column(String(64), nullable=True)
    file_type = Column(String(20), nullable=True)
    content_type = Column(String(100), nullable=True)
    tags = Column(ARRAY(String), nullable=True) # Used for access control: "ai_colleague", "internal_control", "deviation_image"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
