import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base


class Organisation(Base):
    __tablename__ = "organisations"

    org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)           # "Bufetat Øst"
    region_code = Column(String(50), nullable=True, unique=True)  # "Øst", "Nord", etc.
    org_nr = Column(String(9), nullable=True)            # organisasjonsnummer
    contact_email = Column(String(200), nullable=True)
    budget_target_nok = Column(Numeric(19, 4), nullable=True)  # årlig budsjettmål
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Organisation {self.name} ({self.region_code})>"
