from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class NS3451Code(Base):
    """
    NS 3451 Table of Building Elements.
    Used for standardized classification of building components.
    Example: 360 (Luftbehandling) -> 360.01 (Luftbehandlingsutstyr)
    """
    __tablename__ = "ns3451_codes"

    code = Column(String(20), primary_key=True, index=True)  # e.g. "360", "360.01"
    name = Column(String(255), nullable=False)               # e.g. "Luftbehandling"
    level = Column(Integer, nullable=False)                  # 1, 2, or 3
    parent_code = Column(String(20), ForeignKey("ns3451_codes.code"), nullable=True)

    # Relationships
    parent = relationship("NS3451Code", remote_side=[code], backref="children")
    components = relationship("app.domains.fdv.models.fdv.BuildingComponent", back_populates="ns3451_rel")
