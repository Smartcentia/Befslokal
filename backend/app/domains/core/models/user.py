from sqlalchemy import Column, String, ForeignKey, Enum, Table, UUID, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from typing import TYPE_CHECKING
import uuid
import enum
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.domains.core.models.property import Property

class UserRole(str, enum.Enum):
    # Strategisk / ledelse
    ADMIN = "ADMIN"
    NASJONAL_LEDER = "NASJONAL_LEDER"          # Les alt, ingen skriving
    REGIONAL_MANAGER = "REGIONAL_MANAGER"       # Sin region

    # Økonomi
    OKONOMIANSVARLIG = "OKONOMIANSVARLIG"       # Budsjett, regnskap, finance_budget

    # Eiendomsforvaltning
    PROPERTY_MANAGER = "PROPERTY_MANAGER"       # Tildelte eiendommer
    KONTRAKTSFORVALTER = "KONTRAKTSFORVALTER"   # Kontrakter + leietakere

    # FDVU / Drift
    FDVU_KOORDINATOR = "FDVU_KOORDINATOR"       # Vedlikeholdsplaner, tilstandsvurdering
    DRIFTSANSVARLIG = "DRIFTSANSVARLIG"         # Avvik, sjekklister, drift
    JANITOR = "JANITOR"                         # Sine eiendommer — oppgaver, sjekklister

    # HMS
    HMS_ANSVARLIG = "HMS_ANSVARLIG"             # Risikovurderinger, avvik, HMS-rapporter

    # Ekstern / read-only
    TENANT = "TENANT"                           # Les egne kontrakter
    REVISOR = "REVISOR"                         # Les alt, ingen skriving (audit)

# Association table for User <-> Property (Many-to-Many)
# A Property Manager can manage multiple properties, a Property can have multiple managers.
# Association table for User <-> Property (Many-to-Many)
# A Property Manager can manage multiple properties, a Property can have multiple managers.
user_property_association = Table(
    'user_property_association', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.user_id')),
    Column('property_id', UUID(as_uuid=True), ForeignKey('properties.property_id'))
)

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    role = Column(Enum(UserRole, native_enum=False), default=UserRole.PROPERTY_MANAGER)
    region = Column(String, nullable=True)  # Standard: Nord, Midt-Norge, Vest, Sør, Øst, Bufdir (docs/REGION_STANDARD.md)
    
    # Password Auth
    hashed_password = Column(String, nullable=True)
    
    # Soft delete - inactive users cannot log in
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Email verification and MFA
    email_verified = Column(Boolean, default=False, nullable=False)
    mfa_enabled = Column(Boolean, default=True, nullable=False)
    mfa_verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    properties = relationship(
        "Property", 
        secondary=user_property_association, 
        backref=backref("managers", lazy="selectin"), 
        lazy="selectin"
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
