"""
Meldinger (user-to-user messaging) model.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class Melding(Base):
    __tablename__ = "meldinger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    avsender_email = Column(String(255), nullable=False, index=True)
    avsender_navn = Column(String(255), nullable=True)
    mottaker_email = Column(String(255), nullable=False, index=True)
    mottaker_navn = Column(String(255), nullable=True)
    emne = Column(String(500), nullable=False)
    innhold = Column(Text, nullable=False)
    lest = Column(Boolean, default=False, nullable=False)
    arkivert_avsender = Column(Boolean, default=False, nullable=False)
    arkivert_mottaker = Column(Boolean, default=False, nullable=False)
    svar_til_id = Column(UUID(as_uuid=True), nullable=True)  # reply chain
    sendt_dato = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    lest_dato = Column(DateTime(timezone=True), nullable=True)
