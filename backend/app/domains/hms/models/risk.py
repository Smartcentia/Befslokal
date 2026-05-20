from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, JSON, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=False, index=True)
    assessment_date = Column(DateTime(timezone=True), server_default=func.now())
    methodology = Column(String(50), nullable=True)
    overall_risk_score = Column(Float, nullable=True)
    risk_category = Column(String(20), nullable=True, index=True)
    # status = Column(String(20), default="OPEN", server_default="OPEN", nullable=False)  # Column doesn't exist in DB
    assessed_by = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    data_confidence = Column(Float, nullable=True)
    data_issues = Column(JSON, nullable=True)
    assessment_status = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    property = relationship("Property", back_populates="risk_assessments", lazy="select")
    factors = relationship("RiskFactor", back_populates="assessment", lazy="select")

class RiskFactor(Base):
    __tablename__ = "risk_factors"

    factor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("risk_assessments.assessment_id"), nullable=False, index=True)
    category = Column(String(50), nullable=True)
    factor_name = Column(String(100), nullable=True)
    severity = Column(Float, nullable=True)
    probability = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    data_source = Column(String(100), nullable=True)
    raw_data = Column(JSON, nullable=True)
    calculated_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    assessment = relationship("RiskAssessment", back_populates="factors", lazy="select")
