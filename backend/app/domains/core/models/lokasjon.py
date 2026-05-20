from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID


class Lokasjon(Base):
    __tablename__ = "lokasjoner"

    lokasjon_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    navn = Column(String, nullable=False)
    adresse = Column(String, nullable=True)
    lokalisering_id = Column(String, nullable=True, index=True)
    region = Column(String, nullable=True)
    merknad = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
