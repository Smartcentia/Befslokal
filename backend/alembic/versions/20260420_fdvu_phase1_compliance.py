"""FDVU Fase 1: fdvu_sections, requirements, requirement_assignments,
compliance_assessments, fdv_documents + kolonner på properties,
building_components og internal_control_cases.

Revision ID: 20260420_fdvu_phase1
Revises: 20260406_risk_confidence, 20260408_innkjop_import, 20260413_ompostering
Create Date: 2026-04-20
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# ── metadata ────────────────────────────────────────────────────────────────
revision: str = "20260420_fdvu_phase1"
down_revision: Union[str, Sequence[str], None] = (
    "20260406_risk_confidence",
    "20260408_innkjop_import",
    "20260413_ompostering",
)
branch_labels = None
depends_on = None


def _col_exists(conn, table: str, column: str) -> bool:
    insp = inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def _table_exists(conn, table: str) -> bool:
    return inspect(conn).has_table(table)


# ── upgrade ──────────────────────────────────────────────────────────────────

def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. fdvu_sections ────────────────────────────────────────────────────
    if not _table_exists(conn, "fdvu_sections"):
        op.create_table(
            "fdvu_sections",
            sa.Column("section_id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", sa.UUID(as_uuid=True), sa.ForeignKey("properties.property_id", ondelete="RESTRICT"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("section_type", sa.String(50), nullable=False),
            sa.Column("floor", sa.Integer, nullable=True),
            sa.Column("area_sqm", sa.Numeric(10, 2), nullable=True),
            sa.Column("capacity", sa.Integer, nullable=True),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_fdvu_sections_property", "fdvu_sections", ["property_id"])

    # ── 2. requirements ──────────────────────────────────────────────────────
    if not _table_exists(conn, "requirements"):
        op.create_table(
            "requirements",
            sa.Column("requirement_id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("code", sa.String(50), nullable=False, unique=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("regulation_set", sa.String(100), nullable=False),
            sa.Column("category", sa.String(100), nullable=True),
            sa.Column("applies_to", sa.String(50), nullable=False, server_default="property"),
            sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
            sa.Column("severity_if_breached", sa.String(30), nullable=True),
            sa.Column("effective_from", sa.Date, nullable=True),
            sa.Column("effective_to", sa.Date, nullable=True),
            sa.Column("source_url", sa.String(500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        )
        op.create_index("ix_requirements_regulation_set", "requirements", ["regulation_set"])
        op.create_index("ix_requirements_category", "requirements", ["category"])

    # ── 3. requirement_assignments ───────────────────────────────────────────
    if not _table_exists(conn, "requirement_assignments"):
        op.create_table(
            "requirement_assignments",
            sa.Column("assignment_id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("requirement_id", sa.UUID(as_uuid=True), sa.ForeignKey("requirements.requirement_id", ondelete="RESTRICT"), nullable=False),
            sa.Column("property_id", sa.UUID(as_uuid=True), sa.ForeignKey("properties.property_id", ondelete="CASCADE"), nullable=False),
            sa.Column("section_id", sa.UUID(as_uuid=True), sa.ForeignKey("fdvu_sections.section_id", ondelete="CASCADE"), nullable=True),
            sa.Column("is_auto_assigned", sa.Boolean, nullable=False, server_default="true"),
            sa.Column("assigned_by", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.UniqueConstraint("requirement_id", "property_id", "section_id", name="uq_req_assignment"),
        )
        op.create_index("ix_req_assignments_property", "requirement_assignments", ["property_id"])
        op.create_index("ix_req_assignments_requirement", "requirement_assignments", ["requirement_id"])

    # ── 4. compliance_assessments ────────────────────────────────────────────
    if not _table_exists(conn, "compliance_assessments"):
        op.create_table(
            "compliance_assessments",
            sa.Column("assessment_id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("assignment_id", sa.UUID(as_uuid=True), sa.ForeignKey("requirement_assignments.assignment_id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("status", sa.String(30), nullable=False, server_default="not_assessed"),
            sa.Column("assessed_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("assessed_by", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
            sa.Column("valid_until", sa.Date, nullable=True),
            sa.Column("next_review_date", sa.Date, nullable=True),
            sa.Column("evidence_notes", sa.Text, nullable=True),
            sa.Column("deviation_case_id", sa.UUID(as_uuid=True), sa.ForeignKey("internal_control_cases.case_id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_compliance_assessments_assignment", "compliance_assessments", ["assignment_id"])
        op.create_index("ix_compliance_assessments_status", "compliance_assessments", ["status"])
        op.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS ix_compliance_overdue
            ON compliance_assessments (next_review_date)
            WHERE status NOT IN ('not_applicable', 'compliant')
        """))

    # ── 5. fdv_documents ─────────────────────────────────────────────────────
    if not _table_exists(conn, "fdv_documents"):
        op.create_table(
            "fdv_documents",
            sa.Column("document_id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("property_id", sa.UUID(as_uuid=True), sa.ForeignKey("properties.property_id", ondelete="RESTRICT"), nullable=False),
            sa.Column("section_id", sa.UUID(as_uuid=True), sa.ForeignKey("fdvu_sections.section_id", ondelete="SET NULL"), nullable=True),
            sa.Column("document_type", sa.String(100), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("document_number", sa.String(100), nullable=True),
            sa.Column("document_date", sa.Date, nullable=True),
            sa.Column("valid_until", sa.Date, nullable=True),
            sa.Column("revision", sa.String(20), nullable=True),
            sa.Column("file_path", sa.String(1000), nullable=True),
            sa.Column("external_url", sa.String(1000), nullable=True),
            sa.Column("status", sa.String(30), nullable=False, server_default="active"),
            sa.Column("uploaded_by", sa.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_fdv_documents_property", "fdv_documents", ["property_id"])
        op.create_index("ix_fdv_documents_type", "fdv_documents", ["document_type"])
        op.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS ix_fdv_documents_valid_until
            ON fdv_documents (valid_until)
            WHERE valid_until IS NOT NULL
        """))

    # ── 6. properties – nye kolonner ─────────────────────────────────────────
    for col, typedef in [
        ("rkl6_class", "VARCHAR(10)"),            # NULL | 'RKL6' | 'RKL5'
        ("building_type_ns3457", "VARCHAR(50)"),  # NS 3457 bygningskategori
        ("fdvu_status", "VARCHAR(30) DEFAULT 'not_started'"),
        ("last_fdvu_review", "DATE"),
        ("fire_cell_count", "INTEGER"),
    ]:
        if not _col_exists(conn, "properties", col):
            op.execute(sa.text(f"ALTER TABLE properties ADD COLUMN {col} {typedef}"))

    # ── 7. building_components – nye kolonner ────────────────────────────────
    for col, typedef in [
        ("criticality_level", "VARCHAR(20)"),     # critical | important | standard
        ("condition_grade", "VARCHAR(10)"),        # TG0 | TG1 | TG2 | TG3 (NS 3600)
        ("condition_assessed_at", "TIMESTAMPTZ"),
        ("condition_assessed_by", "UUID"),
        ("replacement_year", "INTEGER"),
        ("section_id", f"UUID REFERENCES fdvu_sections(section_id) ON DELETE SET NULL"),
        ("barcode", "VARCHAR(100)"),
        ("serial_number", "VARCHAR(100)"),
    ]:
        if not _col_exists(conn, "building_components", col):
            op.execute(sa.text(f"ALTER TABLE building_components ADD COLUMN {col} {typedef}"))

    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_bc_section
        ON building_components (section_id)
        WHERE section_id IS NOT NULL
    """))
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_bc_condition_grade
        ON building_components (condition_grade)
        WHERE condition_grade IS NOT NULL
    """))

    # ── 8. internal_control_cases – kobling til compliance ──────────────────
    for col, typedef in [
        ("requirement_id", "UUID REFERENCES requirements(requirement_id) ON DELETE SET NULL"),
        ("compliance_assessment_id", "UUID REFERENCES compliance_assessments(assessment_id) ON DELETE SET NULL"),
    ]:
        if not _col_exists(conn, "internal_control_cases", col):
            op.execute(sa.text(f"ALTER TABLE internal_control_cases ADD COLUMN {col} {typedef}"))


# ── downgrade ─────────────────────────────────────────────────────────────────

def downgrade() -> None:
    conn = op.get_bind()

    # Fjern kolonner fra internal_control_cases
    for col in ("compliance_assessment_id", "requirement_id"):
        if _col_exists(conn, "internal_control_cases", col):
            op.execute(sa.text(f"ALTER TABLE internal_control_cases DROP COLUMN {col}"))

    # Fjern kolonner fra building_components
    for col in ("serial_number", "barcode", "section_id", "replacement_year",
                "condition_assessed_by", "condition_assessed_at", "condition_grade", "criticality_level"):
        if _col_exists(conn, "building_components", col):
            op.execute(sa.text(f"ALTER TABLE building_components DROP COLUMN {col}"))

    # Fjern kolonner fra properties
    for col in ("fire_cell_count", "last_fdvu_review", "fdvu_status", "building_type_ns3457", "rkl6_class"):
        if _col_exists(conn, "properties", col):
            op.execute(sa.text(f"ALTER TABLE properties DROP COLUMN {col}"))

    # Slett tabeller i riktig rekkefølge (FK-avhengigheter)
    for tbl in ("fdv_documents", "compliance_assessments", "requirement_assignments",
                "requirements", "fdvu_sections"):
        if _table_exists(conn, tbl):
            op.execute(sa.text(f"DROP TABLE {tbl} CASCADE"))
