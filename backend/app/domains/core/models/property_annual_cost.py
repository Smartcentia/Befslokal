from sqlalchemy import Column, Float, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import JSONB, UUID

class PropertyAnnualCost(Base):
    __tablename__ = "property_annual_costs"

    property_annual_cost_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.contract_id", ondelete="SET NULL"), nullable=True, index=True)
    
    year = Column(Integer, nullable=False, index=True)
    
    # Financial fields from 2025 CSV
    kpi_adjusted_rent = Column(Float, nullable=True) # KPI-justert kontraktsleie
    internal_maintenance = Column(Float, nullable=True) # Indre vedlikehold eller KPI-justert indre vedlikehold
    common_costs = Column(Float, nullable=True) # Felleskostnader per år
    energy_costs = Column(Float, nullable=True) # Energi til leieobjektet kr per år
    heating_costs = Column(Float, nullable=True) # Oppvarming pr år
    cleaning_costs = Column(Float, nullable=True) # Renhold pr år
    parking_rent = Column(Float, nullable=True) # Parkeringsleie kr per år
    caretaker_cost = Column(Float, nullable=True) # Vaktmestertjenester kr per år
    card_reader_cost = Column(Float, nullable=True) # Kost kortleser
    
    # Storage for additional/unmapped costs
    other_costs = Column(JSONB, nullable=True)
    
    # Raw row from CSV for traceability
    external_data = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property", lazy="selectin")
    contract = relationship("Contract", lazy="selectin")
