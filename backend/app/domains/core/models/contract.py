from sqlalchemy import Column, String, Float, DateTime, JSON, Integer, Date, ForeignKey, UUID, Boolean
from sqlalchemy.orm import relationship
from app.models.file_meta import FileMeta # noqa
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base

class Contract(Base):
    __tablename__ = "contracts"

    contract_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archive_code = Column(String(50), nullable=True, unique=True, index=True)  # BUF-LOK-YYYYMMDD-NN (se docs/ARKIVKODE_OG_REFERANSEKODE_STANDARD.md)
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units.unit_id"), nullable=True, index=True)
    party_id = Column(UUID(as_uuid=True), ForeignKey("parties.party_id"), nullable=True, index=True)
    
    
    status = Column(String, nullable=True, index=True) # active / terminated – stored as plain string (no PG ENUM)
    category = Column(String, nullable=True, index=True) # e.g. "Leiekontrakt", "Serviceavtale"
    contract_name = Column(String, nullable=True)  # Avtalenavn fra CSV
    start_date = Column(Date, nullable=True, index=True)
    end_date = Column(Date, nullable=True, index=True)
    from sqlalchemy.dialects.postgresql import JSONB
    periods = Column(JSONB, nullable=True)
    amount = Column(JSONB, nullable=True)
    
    # Options & Notifications
    # User asked for: "hvilke kontrakter som har opsjon", "hvor mange opsjoner som er benyttet", "varslingsfrist"
    # Overwriting checks:
    has_option = Column(Boolean, nullable=True, default=False)
    option_deadline = Column(Date, nullable=True) # Frist for varsling
    option_count_total = Column(Integer, nullable=True) # Antall opsjoner totalt
    option_count_used = Column(Integer, nullable=True) # Antall benyttet
    
    external_data = Column(JSONB, nullable=True)
    
    # Cost breakdowns from CSV import (nullable to support legacy data)
    caretaker_cost = Column(Float, nullable=True) # Vaktmestertjenester kr per år
    cleaning_cost = Column(Float, nullable=True) # Renhold pr år
    parking_cost = Column(Float, nullable=True) # Parkeringsleie kr per år
    card_reader_cost = Column(Float, nullable=True) # Kost kortleser
    signed_at = Column(DateTime(timezone=True), nullable=True)
    terminated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    unit = relationship("Unit", lazy="selectin")
    party = relationship("Party", lazy="selectin")
    files = relationship("FileMeta", backref="contract", lazy="selectin") # lazy="select" avoids loading many rows in list views

    @property
    def property(self):
        return self.unit.property if self.unit else None

    @staticmethod
    def normalize_contract_id(org: str, lok_id: str, date_str: str, seq: str) -> str:
        """
        Normalizes contract ID to standard format: [ORG]-[LOKALISERING_ID]-[Dato]-[Løpenummer]
        Example: BUF-6125-20241014-01
        """
        return f"{org.upper()}-{lok_id}-{date_str}-{seq}"

