"""
Behovsmelding – innmeldte behov fra brukere.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base


class Behovsmelding(Base):
    __tablename__ = "behovsmeldinger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tittel = Column(String(255), nullable=False)
    beskrivelse = Column(Text, nullable=True)
    kategori = Column(String(50), nullable=True)   # Eiendom, Kontrakt, HMS, Økonomi, Rapport, Annet
    prioritet = Column(String(20), nullable=True)  # Lav, Medium, Høy, Kritisk
    status = Column(String(30), nullable=False, default="Ny")  # Ny, Under behandling, Implementert, Avvist
    opprettet_av = Column(String(255), nullable=False)
    eiendom_navn = Column(String(255), nullable=True)  # Valgfritt: hvilken eiendom det gjelder
    admin_kommentar = Column(Text, nullable=True)
    er_arkivert = Column(Boolean, default=False)
    opprettet_dato = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    oppdatert_dato = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
