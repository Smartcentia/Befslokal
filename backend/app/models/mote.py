"""Møtemodell – planlegging, agenda, referat og deltakere."""
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base


class Mote(Base):
    __tablename__ = "moter"

    mote_id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tittel      = Column(String(300), nullable=False)
    beskrivelse = Column(Text, nullable=True)
    sted        = Column(String(300), nullable=True)          # fysisk adresse eller Teams-link
    start_tid   = Column(DateTime(timezone=True), nullable=False)
    slutt_tid   = Column(DateTime(timezone=True), nullable=True)
    status      = Column(String(30), default="planlagt")      # planlagt | pågår | avsluttet | avlyst
    mote_type   = Column(String(50), default="internt")       # internt | eksternt | digitalt
    # Deltakere: liste av {"email": ..., "navn": ..., "rolle": "ordforer|sekretaer|deltaker"}
    deltakere   = Column(JSON, default=list)
    # Agenda: liste av {"id": ..., "punkt": ..., "ansvarlig": ..., "varighet_min": ..., "ferdig": false}
    agenda      = Column(JSON, default=list)
    # Referat: fritekst eller strukturert
    referat     = Column(Text, nullable=True)
    # Vedtak: liste av {"tekst": ..., "ansvarlig": ..., "frist": ...}
    vedtak      = Column(JSON, default=list)

    opprettet_av  = Column(String(255), nullable=True)
    opprettet_tid = Column(DateTime(timezone=True), server_default=func.now())
    oppdatert_tid = Column(DateTime(timezone=True), onupdate=func.now())
