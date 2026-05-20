"""Property husleie from Innkjøpsanalyse CSV."""
from sqlalchemy import Column, Float, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID


class PropertyHusleieCsv(Base):
    """Husleie per eiendom og region fra Innkjøpsanalyse-CSV."""
    __tablename__ = "property_husleie_csv"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    region = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    source = Column(String(100), nullable=True)

    property = relationship("Property", lazy="selectin")
