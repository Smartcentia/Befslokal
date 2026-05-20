"""SQLAlchemy-modell for offisielle Agresso-budsjetter."""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base


class AgressoBudget(Base):
    __tablename__ = "agresso_budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    konto = Column(String(10), nullable=False, index=True)
    konto_navn = Column(String(200), nullable=True)
    koststed_kode = Column(String(20), nullable=True, index=True)
    koststed_navn = Column(String(200), nullable=True)
    prosjekt_kode = Column(String(20), nullable=True)
    prosjekt_navn = Column(String(200), nullable=True)
    finansiering_kode = Column(String(20), nullable=True)
    finansiering_navn = Column(String(200), nullable=True)

    periode = Column(String(6), nullable=False)
    ar = Column(Integer, nullable=True, index=True)
    maaned = Column(Integer, nullable=True)

    belop_da = Column(Numeric(19, 4), nullable=True)
    kontantbelop = Column(Numeric(19, 4), nullable=True)

    srs_kategori = Column(String(20), nullable=True, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="SET NULL"), nullable=True, index=True)

    batch_id = Column(String(100), nullable=True, index=True)
    imported_by = Column(String(100), nullable=True)
    source_file_ref = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
