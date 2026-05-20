"""
Pydantic schemas for FDVU Phase 1 – Compliance.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, UUID4, Field, ConfigDict


# ─────────────────────────────────────────────
# FdvuSection
# ─────────────────────────────────────────────

class FdvuSectionBase(BaseModel):
    name: str = Field(..., max_length=255)
    section_type: str = Field(..., max_length=50)   # boform|fellesareal|administrasjon|uteareal
    floor: Optional[int] = None
    area_sqm: Optional[float] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True


class FdvuSectionCreate(FdvuSectionBase):
    property_id: UUID4


class FdvuSectionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    section_type: Optional[str] = Field(None, max_length=50)
    floor: Optional[int] = None
    area_sqm: Optional[float] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FdvuSectionOut(FdvuSectionBase):
    model_config = ConfigDict(from_attributes=True)
    section_id: UUID4
    property_id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# Requirement
# ─────────────────────────────────────────────

class RequirementBase(BaseModel):
    code: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    regulation_set: str = Field(..., max_length=100)    # RKL6|BVL|TEK17|HMS|KVALITETSFORSKRIFTEN|INTERN
    category: Optional[str] = Field(None, max_length=100)
    applies_to: str = Field(default="property", max_length=50)  # property|section|component
    is_mandatory: bool = True
    severity_if_breached: Optional[str] = Field(None, max_length=30)  # critical|high|medium|low
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    source_url: Optional[str] = Field(None, max_length=500)


class RequirementCreate(RequirementBase):
    pass


class RequirementOut(RequirementBase):
    model_config = ConfigDict(from_attributes=True)
    requirement_id: UUID4
    created_at: datetime


# ─────────────────────────────────────────────
# RequirementAssignment
# ─────────────────────────────────────────────

class AssignmentCreate(BaseModel):
    requirement_id: UUID4
    property_id: UUID4
    section_id: Optional[UUID4] = None
    is_auto_assigned: bool = True
    notes: Optional[str] = None


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    assignment_id: UUID4
    requirement_id: UUID4
    property_id: UUID4
    section_id: Optional[UUID4] = None
    is_auto_assigned: bool
    notes: Optional[str] = None
    assigned_at: datetime
    requirement: Optional[RequirementOut] = None


# ─────────────────────────────────────────────
# ComplianceAssessment
# ─────────────────────────────────────────────

class AssessmentUpsert(BaseModel):
    """Create or update the compliance assessment for an assignment."""
    assignment_id: UUID4
    status: str = Field(..., max_length=30)   # compliant|non_compliant|partial|not_assessed|not_applicable
    valid_until: Optional[date] = None
    next_review_date: Optional[date] = None
    evidence_notes: Optional[str] = None
    deviation_case_id: Optional[UUID4] = None


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    assessment_id: UUID4
    assignment_id: UUID4
    status: str
    assessed_at: datetime
    assessed_by: Optional[UUID4] = None
    valid_until: Optional[date] = None
    next_review_date: Optional[date] = None
    evidence_notes: Optional[str] = None
    deviation_case_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# FdvDocument
# ─────────────────────────────────────────────

class FdvDocumentBase(BaseModel):
    document_type: str = Field(..., max_length=100)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_number: Optional[str] = Field(None, max_length=100)
    document_date: Optional[date] = None
    valid_until: Optional[date] = None
    revision: Optional[str] = Field(None, max_length=20)
    file_path: Optional[str] = Field(None, max_length=1000)
    external_url: Optional[str] = Field(None, max_length=1000)
    status: str = Field(default="active", max_length=30)  # active|superseded|draft|expired
    section_id: Optional[UUID4] = None


class FdvDocumentCreate(FdvDocumentBase):
    property_id: UUID4


class FdvDocumentUpdate(BaseModel):
    document_type: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    valid_until: Optional[date] = None
    revision: Optional[str] = None
    file_path: Optional[str] = None
    external_url: Optional[str] = None
    status: Optional[str] = None
    section_id: Optional[UUID4] = None


class FdvDocumentOut(FdvDocumentBase):
    model_config = ConfigDict(from_attributes=True)
    document_id: UUID4
    property_id: UUID4
    uploaded_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# Compliance summary (per property)
# ─────────────────────────────────────────────

class ComplianceSummary(BaseModel):
    property_id: UUID4
    total_assignments: int
    compliant: int
    non_compliant: int
    partial: int
    not_assessed: int
    not_applicable: int
    overdue_reviews: int
    compliance_rate: float  # 0–1, excl. not_applicable and not_assessed


class AssignmentWithAssessment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    assignment_id: UUID4
    requirement_id: UUID4
    property_id: UUID4
    section_id: Optional[UUID4] = None
    is_auto_assigned: bool
    notes: Optional[str] = None
    assigned_at: datetime
    requirement: Optional[RequirementOut] = None
    compliance_assessment: Optional[AssessmentOut] = None
