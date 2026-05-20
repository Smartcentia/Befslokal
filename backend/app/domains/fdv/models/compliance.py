"""
FDVU Fase 1 – Compliance-ryggraden

Tabeller:
  fdvu_sections          – Avdeling/boform innad i institusjon
  requirements           – Kravkatalog (RKL6, BVL, TEK17, HMS, ...)
  requirement_assignments – Hvilke krav gjelder dette bygget/seksjonen
  compliance_assessments  – Nåværende compliance-status per krav
  fdv_documents           – FDV-dokumentregister

Kolonner lagt til via Alembic på eksisterende tabeller:
  properties             – rkl6_class, fdvu_status, last_fdvu_review, ...
  building_components    – criticality_level, condition_grade, section_id, ...
  internal_control_cases – requirement_id, compliance_assessment_id
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base_class import Base


# ─────────────────────────────────────────────
# FdvuSection – avdeling / boform
# ─────────────────────────────────────────────

class FdvuSection(Base):
    """
    Representerer en avdeling eller boform innad i en eiendom/institusjon.
    Ikke det samme som units (kontraktanker) – dette er organisatorisk struktur.

    Eksempler på section_type:
      boform         – Boenhet / botilbud (f.eks. «Avdeling A»)
      fellesareal    – Fellesrom, kantine, aktivitetsareal
      administrasjon – Kontorer, møterom
      uteareal       – Utearealer tilknyttet institusjonen
    """
    __tablename__ = "fdvu_sections"

    section_id  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="RESTRICT"), nullable=False, index=True)

    name         = Column(String(255), nullable=False)
    section_type = Column(String(50), nullable=False)   # boform | fellesareal | administrasjon | uteareal
    floor        = Column(Integer, nullable=True)
    area_sqm     = Column(Numeric(10, 2), nullable=True)
    capacity     = Column(Integer, nullable=True)        # antall plasser/beboere
    description  = Column(Text, nullable=True)
    is_active    = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property              = relationship("Property", foreign_keys=[property_id], lazy="selectin")
    requirement_assignments = relationship("RequirementAssignment", back_populates="section", lazy="dynamic")
    fdv_documents         = relationship("FdvDocument", back_populates="section", lazy="dynamic")


# ─────────────────────────────────────────────
# Requirement – kravkatalog
# ─────────────────────────────────────────────

class Requirement(Base):
    """
    Kravkatalog. Seedet fra scripts/seed_requirements.py – ikke bruker-opprettet.

    regulation_set:  RKL6 | BVL | TEK17 | HMS | KVALITETSFORSKRIFTEN | INTERN
    category:        brann | rømning | lyd | privatliv | arbeidsmiljø | tilgjengelighet | hygiene | internkontroll
    applies_to:      property | section | component
    """
    __tablename__ = "requirements"

    requirement_id  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code            = Column(String(50), nullable=False, unique=True)  # e.g. "RKL6-SPRINKLER"
    title           = Column(String(255), nullable=False)
    description     = Column(Text, nullable=True)
    regulation_set  = Column(String(100), nullable=False, index=True)
    category        = Column(String(100), nullable=True, index=True)
    applies_to      = Column(String(50), nullable=False, default="property")
    is_mandatory    = Column(Boolean, nullable=False, default=True)
    severity_if_breached = Column(String(30), nullable=True)  # critical | high | medium | low
    effective_from  = Column(Date, nullable=True)
    effective_to    = Column(Date, nullable=True)
    source_url      = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    assignments = relationship("RequirementAssignment", back_populates="requirement", lazy="dynamic")


# ─────────────────────────────────────────────
# RequirementAssignment – krav koblet til eiendom/seksjon
# ─────────────────────────────────────────────

class RequirementAssignment(Base):
    """
    Kobler et krav til en konkret eiendom (og valgfritt en seksjon).
    Kan auto-tildeles av regelmotor eller manuelt av bruker.

    section_id IS NULL  → gjelder hele eiendommen
    section_id NOT NULL → gjelder spesifikk avdeling
    """
    __tablename__ = "requirement_assignments"
    __table_args__ = (
        UniqueConstraint("requirement_id", "property_id", "section_id", name="uq_req_assignment"),
    )

    assignment_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id   = Column(UUID(as_uuid=True), ForeignKey("requirements.requirement_id", ondelete="RESTRICT"), nullable=False, index=True)
    property_id      = Column(UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False, index=True)
    section_id       = Column(UUID(as_uuid=True), ForeignKey("fdvu_sections.section_id", ondelete="CASCADE"), nullable=True, index=True)

    is_auto_assigned = Column(Boolean, nullable=False, default=True)
    assigned_by      = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    notes            = Column(Text, nullable=True)
    assigned_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    requirement          = relationship("Requirement", back_populates="assignments", lazy="selectin")
    property             = relationship("Property", lazy="selectin")
    section              = relationship("FdvuSection", back_populates="requirement_assignments", lazy="selectin")
    compliance_assessment = relationship(
        "ComplianceAssessment",
        back_populates="assignment",
        uselist=False,
        lazy="selectin",
    )


# ─────────────────────────────────────────────
# ComplianceAssessment – nåværende status
# ─────────────────────────────────────────────

class ComplianceAssessment(Base):
    """
    Nåværende compliance-status for ett RequirementAssignment.
    Én rad per assignment (siste vurdering). Historikk lagres ikke her
    (bruk audit-log / append-only alternativ i Fase 2).

    status: compliant | non_compliant | partial | not_assessed | not_applicable
    """
    __tablename__ = "compliance_assessments"

    assessment_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id   = Column(UUID(as_uuid=True), ForeignKey("requirement_assignments.assignment_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    status          = Column(String(30), nullable=False, default="not_assessed")
    assessed_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assessed_by     = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    valid_until     = Column(Date, nullable=True)   # utløpsdato for tidsbegrenset compliance
    next_review_date = Column(Date, nullable=True)
    evidence_notes  = Column(Text, nullable=True)

    # Link til eksisterende avvikssystem
    deviation_case_id = Column(UUID(as_uuid=True), ForeignKey("internal_control_cases.case_id"), nullable=True)

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    assignment = relationship("RequirementAssignment", back_populates="compliance_assessment", lazy="selectin")
    assessor   = relationship("User", foreign_keys=[assessed_by], lazy="selectin")


# ─────────────────────────────────────────────
# FdvDocument – FDV-dokumentregister
# ─────────────────────────────────────────────

class FdvDocument(Base):
    """
    Register over FDV-dokumentasjon per eiendom.

    document_type (eksempler):
      brannplan | fdv_manual | tegning | akustikkrapport | energiattest
      serviceavtale | garantidokument | samsvarserklæring | instruksjon
      hms_prosedyre | tilstandsrapport | inspeksjonsprotokoll

    status: active | superseded | draft | expired
    """
    __tablename__ = "fdv_documents"

    document_id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id     = Column(UUID(as_uuid=True), ForeignKey("properties.property_id", ondelete="RESTRICT"), nullable=False, index=True)
    section_id      = Column(UUID(as_uuid=True), ForeignKey("fdvu_sections.section_id", ondelete="SET NULL"), nullable=True, index=True)

    document_type   = Column(String(100), nullable=False, index=True)
    title           = Column(String(255), nullable=False)
    description     = Column(Text, nullable=True)
    document_number = Column(String(100), nullable=True)   # arkivnummer / ekstern ref

    document_date   = Column(Date, nullable=True)
    valid_until     = Column(Date, nullable=True)          # gyldighetsperiode
    revision        = Column(String(20), nullable=True)    # revisjonsnummer

    # Fillagring – enten intern sti eller ekstern URL
    file_path       = Column(String(1000), nullable=True)  # intern sti / blob-key
    external_url    = Column(String(1000), nullable=True)  # ekstern kilde

    status          = Column(String(30), nullable=False, default="active")
    uploaded_by     = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Fase 5 – Dokumentintelligens
    extracted_text    = Column(Text, nullable=True)
    extraction_status = Column(String(30), default="pending", nullable=False)
    page_count        = Column(Integer, nullable=True)
    embedding         = Column(Vector(1536), nullable=True)

    # Relationships
    property  = relationship("Property", lazy="selectin")
    section   = relationship("FdvuSection", back_populates="fdv_documents", lazy="selectin")
    uploader  = relationship("User", foreign_keys=[uploaded_by], lazy="selectin")
