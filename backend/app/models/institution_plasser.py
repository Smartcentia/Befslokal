"""
Modell for budsjetterte og kvalitetssikrede institusjonsplasser per avdeling.
Kobles til properties via koststed_mapping.koststed_kode → property_id.
"""
import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base


class InstitusjonPlasser(Base):
    __tablename__ = "institution_plasser"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    koststed_kode = Column(String(20), nullable=False, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id"), nullable=True, index=True)
    region = Column(String(50), nullable=True)
    malgruppe = Column(String(100), nullable=True)
    enhetsnr = Column(Integer, nullable=True)
    institusjons_navn = Column(String(200), nullable=True)
    avdelings_navn = Column(String(200), nullable=True)
    antall_kvalitetssikrede = Column(Integer, nullable=True)
    antall_budsjetterte = Column(Integer, nullable=True)
    rapport_dato = Column(Date, nullable=False, index=True)
    import_batch_id = Column(UUID(as_uuid=True), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now())
    imported_by = Column(String(100), nullable=True)
