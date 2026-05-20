"""
FDVU Fase 1 – Compliance API
Endepunkter for seksjoner, kravkatalog, vurderinger og FDV-dokumenter.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from pydantic import BaseModel
from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.fdv.models.compliance import (
    FdvuSection,
    Requirement,
    RequirementAssignment,
    ComplianceAssessment,
    FdvDocument,
)
from app.domains.fdv.models.fdv import BuildingComponent as ComponentModel
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.fdv.schemas.compliance import (
    FdvuSectionCreate,
    FdvuSectionUpdate,
    FdvuSectionOut,
    RequirementOut,
    AssignmentCreate,
    AssignmentOut,
    AssessmentUpsert,
    AssessmentOut,
    FdvDocumentCreate,
    FdvDocumentUpdate,
    FdvDocumentOut,
    ComplianceSummary,
    AssignmentWithAssessment,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────
# Hjelpefunksjon: tilgangskontroll
# ─────────────────────────────────────────────

async def _check_property_access(
    property_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Raises 403 if current_user does not have access to property_id."""
    from app.domains.core.models.user import UserRole
    if hasattr(current_user, "role") and current_user.role == "ADMIN":
        return
    # REGIONAL_MANAGER: check region (simplified – property must exist)
    # For now allow all authenticated users; tighten in Phase 2
    pass


# ═════════════════════════════════════════════
# SEKSJONER
# ═════════════════════════════════════════════

@router.get("/sections", response_model=List[FdvuSectionOut], tags=["FDVU Seksjoner"])
async def list_sections(
    property_id: uuid.UUID = Query(..., description="Filtrer på eiendom"),
    only_active: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List alle seksjoner for en eiendom."""
    q = select(FdvuSection).where(FdvuSection.property_id == property_id)
    if only_active:
        q = q.where(FdvuSection.is_active == True)
    result = await db.execute(q.order_by(FdvuSection.name))
    return result.scalars().all()


@router.post("/sections", response_model=FdvuSectionOut, status_code=status.HTTP_201_CREATED, tags=["FDVU Seksjoner"])
async def create_section(
    body: FdvuSectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = FdvuSection(
        section_id=uuid.uuid4(),
        **body.model_dump(),
    )
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


@router.patch("/sections/{section_id}", response_model=FdvuSectionOut, tags=["FDVU Seksjoner"])
async def update_section(
    section_id: uuid.UUID,
    body: FdvuSectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = await db.get(FdvuSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Seksjon ikke funnet")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(section, k, v)
    await db.commit()
    await db.refresh(section)
    return section


@router.delete("/sections/{section_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["FDVU Seksjoner"])
async def delete_section(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    section = await db.get(FdvuSection, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Seksjon ikke funnet")
    # Soft-delete
    section.is_active = False
    await db.commit()


# ═════════════════════════════════════════════
# KRAVKATALOG
# ═════════════════════════════════════════════

@router.get("/requirements", response_model=List[RequirementOut], tags=["FDVU Kravkatalog"])
async def list_requirements(
    regulation_set: Optional[str] = Query(None, description="RKL6|BVL|TEK17|HMS|INTERN"),
    category: Optional[str] = Query(None),
    applies_to: Optional[str] = Query(None),
    is_mandatory: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Requirement)
    if regulation_set:
        q = q.where(Requirement.regulation_set == regulation_set)
    if category:
        q = q.where(Requirement.category == category)
    if applies_to:
        q = q.where(Requirement.applies_to == applies_to)
    if is_mandatory is not None:
        q = q.where(Requirement.is_mandatory == is_mandatory)
    result = await db.execute(q.order_by(Requirement.regulation_set, Requirement.code))
    return result.scalars().all()


@router.get("/requirements/{requirement_id}", response_model=RequirementOut, tags=["FDVU Kravkatalog"])
async def get_requirement(
    requirement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    req = await db.get(Requirement, requirement_id)
    if not req:
        raise HTTPException(status_code=404, detail="Krav ikke funnet")
    return req


# ═════════════════════════════════════════════
# TILDELINGER (assignments)
# ═════════════════════════════════════════════

@router.get("/assignments", response_model=List[AssignmentWithAssessment], tags=["FDVU Compliance"])
async def list_assignments(
    property_id: uuid.UUID = Query(...),
    section_id: Optional[uuid.UUID] = Query(None),
    regulation_set: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List alle kravtildelinger for en eiendom, med siste compliance-status."""
    q = (
        select(RequirementAssignment)
        .options(
            selectinload(RequirementAssignment.requirement),
            selectinload(RequirementAssignment.compliance_assessment),
        )
        .where(RequirementAssignment.property_id == property_id)
    )
    if section_id is not None:
        q = q.where(RequirementAssignment.section_id == section_id)
    if regulation_set:
        q = q.join(Requirement).where(Requirement.regulation_set == regulation_set)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/assignments", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED, tags=["FDVU Compliance"])
async def create_assignment(
    body: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignment = RequirementAssignment(
        assignment_id=uuid.uuid4(),
        assigned_by=current_user.user_id,
        **body.model_dump(),
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    # Eager-load requirement for response
    result = await db.execute(
        select(RequirementAssignment)
        .options(selectinload(RequirementAssignment.requirement))
        .where(RequirementAssignment.assignment_id == assignment.assignment_id)
    )
    return result.scalar_one()


def _requirement_applies(req: Requirement, prop_type: str | None, is_barnevern: bool) -> bool:
    """
    Regelmotor: avgjør om et krav gjelder for en eiendom basert på regulation_set.

    Regler:
    - RKL6 (Risikoklasse 6)          → kun barnevernsinstitusjon
    - BVL (Barnevernloven)             → kun barnevernsinstitusjon
    - KVALITETSFORSKRIFTEN             → kun barnevernsinstitusjon
    - HMS / TEK17 / INTERN             → alle eiendommer
    - Ukjent regulation_set            → alle eiendommer (fail-open)
    """
    reg = (req.regulation_set or "").upper()
    if reg in ("RKL6", "BVL", "KVALITETSFORSKRIFTEN"):
        return is_barnevern
    # HMS, TEK17, INTERN og andre → gjelder alle
    return True


@router.post(
    "/assignments/auto-generate",
    response_model=dict,
    tags=["FDVU Compliance"],
)
async def auto_generate_assignments(
    property_id: uuid.UUID = Query(..., description="Eiendom å auto-tildele krav for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regelbasert auto-tildeling av krav til en eiendom.

    Regelverk som filtreres:
    - RKL6, BVL, KVALITETSFORSKRIFTEN → kun barnevernsinstitusjon
      (unit_type_derived = 'Barnevernsinstitusjon' ELLER approved_places > 0)
    - HMS, TEK17, INTERN → alle eiendommer
    """
    from app.domains.core.models.property import Property

    # Hent eiendomsinformasjon for regelmotor
    prop_res = await db.get(Property, property_id)
    if not prop_res:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

    unit_type = (prop_res.unit_type_derived or "").strip()
    approved = prop_res.approved_places or 0
    is_barnevern = (
        "barnevernsinstitusjon" in unit_type.lower()
        or "omsorgssenter" in unit_type.lower()
        or approved > 0
    )

    # Hent alle mandatory krav
    all_req_res = await db.execute(
        select(Requirement).where(Requirement.is_mandatory == True)
    )
    requirements = all_req_res.scalars().all()

    # Hent eksisterende tildelinger
    existing_res = await db.execute(
        select(RequirementAssignment.requirement_id).where(
            RequirementAssignment.property_id == property_id,
            RequirementAssignment.section_id.is_(None),
        )
    )
    existing_ids = {row[0] for row in existing_res.fetchall()}

    created = skipped_existing = skipped_rule = 0
    for req in requirements:
        if req.requirement_id in existing_ids:
            skipped_existing += 1
            continue
        if not _requirement_applies(req, unit_type, is_barnevern):
            skipped_rule += 1
            continue
        db.add(RequirementAssignment(
            assignment_id=uuid.uuid4(),
            requirement_id=req.requirement_id,
            property_id=property_id,
            section_id=None,
            is_auto_assigned=True,
            assigned_by=current_user.user_id,
        ))
        created += 1

    await db.commit()
    return {
        "created": created,
        "skipped_already_assigned": skipped_existing,
        "skipped_not_applicable": skipped_rule,
        "is_barnevern": is_barnevern,
    }


@router.post(
    "/assignments/auto-generate-all",
    response_model=dict,
    tags=["FDVU Compliance"],
)
async def auto_generate_assignments_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kjør regelbasert auto-tildeling for ALLE aktive eiendommer i porteføljen.
    Bruker samme regelmotor som per-eiendom-endepunktet.
    Trygt å kjøre gjentatte ganger – eksisterende tildelinger hoppes over.
    """
    from app.domains.core.models.property import Property
    from sqlalchemy import text as sql_text

    # Alle eiendommer (properties-tabellen har ingen status-kolonne)
    props_res = await db.execute(select(Property))
    properties = props_res.scalars().all()

    # Alle mandatory krav (én gang for alle)
    all_req_res = await db.execute(
        select(Requirement).where(Requirement.is_mandatory == True)
    )
    requirements = all_req_res.scalars().all()

    # Alle eksisterende tildelinger (én bulk-spørring)
    existing_res = await db.execute(
        select(RequirementAssignment.property_id, RequirementAssignment.requirement_id)
        .where(RequirementAssignment.section_id.is_(None))
    )
    existing_set = {(str(row[0]), str(row[1])) for row in existing_res.fetchall()}

    total_created = total_skipped = total_rule = 0
    props_touched = 0

    for prop in properties:
        unit_type = (prop.unit_type_derived or "").strip()
        approved = prop.approved_places or 0
        is_barnevern = (
            "barnevernsinstitusjon" in unit_type.lower()
            or "omsorgssenter" in unit_type.lower()
            or approved > 0
        )
        created_for_prop = 0
        for req in requirements:
            key = (str(prop.property_id), str(req.requirement_id))
            if key in existing_set:
                total_skipped += 1
                continue
            if not _requirement_applies(req, unit_type, is_barnevern):
                total_rule += 1
                continue
            db.add(RequirementAssignment(
                assignment_id=uuid.uuid4(),
                requirement_id=req.requirement_id,
                property_id=prop.property_id,
                section_id=None,
                is_auto_assigned=True,
                assigned_by=current_user.user_id,
            ))
            existing_set.add(key)
            total_created += 1
            created_for_prop += 1
        if created_for_prop:
            props_touched += 1

    await db.commit()
    logger.debug(
        "auto_generate_all: %d eiendommer, %d nye tildelinger, %d skipped, %d regel-filtrert",
        len(properties), total_created, total_skipped, total_rule,
    )
    return {
        "properties_processed": len(properties),
        "properties_with_new_assignments": props_touched,
        "total_created": total_created,
        "total_skipped_existing": total_skipped,
        "total_skipped_rule": total_rule,
    }


# ═════════════════════════════════════════════
# COMPLIANCE-VURDERINGER
# ═════════════════════════════════════════════

class BulkAssessRequest(BaseModel):
    assignment_ids: List[uuid.UUID]
    status: str                          # compliant | non_compliant | partial | not_applicable | not_assessed
    valid_until: Optional[date] = None
    next_review_date: Optional[date] = None
    evidence_notes: Optional[str] = None


class BulkAssessRegionRequest(BaseModel):
    """
    Server-side massevurdering — finner assignment_ids selv basert på filtre
    og bruker en effektiv SQL INSERT … ON CONFLICT.
    """
    region: Optional[str] = None                  # None = alle regioner
    regulation_sets: Optional[List[str]] = None   # None = alle regelverk
    only_not_assessed: bool = True                 # Kun ikke-vurderte
    status: str = "compliant"                      # Status som settes
    valid_until: Optional[date] = None
    next_review_date: Optional[date] = None
    evidence_notes: Optional[str] = None
    dry_run: bool = False                          # True = kun tell, ikke lagre


@router.post(
    "/compliance/bulk-assess-region",
    tags=["FDVU Compliance"],
)
async def bulk_assess_region(
    body: BulkAssessRegionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Massevurdering for en hel region / regelverk-kategori.

    - Bruker effektiv SQL INSERT … ON CONFLICT for stor volum (1000+ krav).
    - dry_run=True teller bare, uten å skrive til DB.
    - Logg-nivå DEBUG – ikke info (unngår Railway log rate-limit).
    """
    from sqlalchemy import text as sql_text

    VALID_STATUSES = {"compliant", "non_compliant", "partial", "not_applicable", "not_assessed"}
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Ugyldig status. Gyldige: {sorted(VALID_STATUSES)}")

    # ── Bygg SQL-filter ──────────────────────────────────────────────────────
    conditions: list[str] = []
    params: dict = {
        "status": body.status,
        "now": datetime.now(timezone.utc),
        "assessed_by": str(current_user.user_id),
        "valid_until": body.valid_until,
        "next_review_date": body.next_review_date,
        "evidence_notes": body.evidence_notes,
    }

    if body.region:
        conditions.append("p.region = :region")
        params["region"] = body.region

    if body.regulation_sets:
        conditions.append("r.regulation_set = ANY(:reg_sets)")
        params["reg_sets"] = body.regulation_sets

    if body.only_not_assessed:
        conditions.append(
            "(ca.assessment_id IS NULL OR ca.status = 'not_assessed')"
        )

    where_sql = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base_select = f"""
        FROM requirement_assignments ra
        JOIN properties p ON p.property_id::text = ra.property_id::text
        JOIN requirements r ON r.requirement_id = ra.requirement_id
        LEFT JOIN compliance_assessments ca ON ca.assignment_id = ra.assignment_id
        {where_sql}
    """

    # ── dry_run: bare tell ────────────────────────────────────────────────────
    if body.dry_run:
        count_row = await db.execute(
            sql_text(f"SELECT COUNT(*) {base_select}"), params
        )
        total = count_row.scalar() or 0
        return {"affected": int(total), "dry_run": True, "status": body.status}

    # ── Effektiv upsert via INSERT … ON CONFLICT ─────────────────────────────
    upsert_sql = f"""
        INSERT INTO compliance_assessments
            (assessment_id, assignment_id, status, assessed_at, assessed_by,
             valid_until, next_review_date, evidence_notes, created_at)
        SELECT
            gen_random_uuid(),
            ra.assignment_id,
            :status,
            :now,
            :assessed_by,
            :valid_until,
            :next_review_date,
            :evidence_notes,
            :now
        {base_select}
        ON CONFLICT (assignment_id) DO UPDATE SET
            status           = EXCLUDED.status,
            assessed_at      = EXCLUDED.assessed_at,
            assessed_by      = EXCLUDED.assessed_by,
            valid_until      = COALESCE(EXCLUDED.valid_until, compliance_assessments.valid_until),
            next_review_date = COALESCE(EXCLUDED.next_review_date, compliance_assessments.next_review_date),
            evidence_notes   = COALESCE(EXCLUDED.evidence_notes, compliance_assessments.evidence_notes)
    """
    result = await db.execute(sql_text(upsert_sql), params)
    await db.commit()

    total = result.rowcount
    logger.debug(
        "bulk_assess_region: status=%s region=%s reg_sets=%s only_not_assessed=%s → %d rader",
        body.status, body.region, body.regulation_sets, body.only_not_assessed, total,
    )
    return {"total": int(total), "dry_run": False, "status": body.status}


@router.post(
    "/compliance/bulk-assess",
    tags=["FDVU Compliance"],
)
async def bulk_assess(
    body: BulkAssessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Masseredigering av compliance-vurderinger.
    Oppretter eller oppdaterer assessments for alle oppgitte assignment_ids i én operasjon.
    Trigger auto-avvik for non_compliant på samme måte som enkelt-endepunktet.
    """
    if not body.assignment_ids:
        return {"updated": 0, "created": 0}

    VALID_STATUSES = {"compliant", "non_compliant", "partial", "not_applicable", "not_assessed"}
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Ugyldig status. Gyldige: {VALID_STATUSES}")

    now = datetime.now(timezone.utc)
    updated = created = 0

    for assignment_id in body.assignment_ids:
        # Hent eksisterende assessment
        existing = await db.execute(
            select(ComplianceAssessment).where(
                ComplianceAssessment.assignment_id == assignment_id
            )
        )
        ca = existing.scalar_one_or_none()

        if ca:
            ca.status = body.status
            ca.assessed_at = now
            ca.assessed_by = str(current_user.user_id)
            if body.valid_until is not None:
                ca.valid_until = body.valid_until
            if body.next_review_date is not None:
                ca.next_review_date = body.next_review_date
            if body.evidence_notes is not None:
                ca.evidence_notes = body.evidence_notes
            updated += 1
        else:
            ca = ComplianceAssessment(
                assessment_id=uuid.uuid4(),
                assignment_id=assignment_id,
                status=body.status,
                assessed_at=now,
                assessed_by=str(current_user.user_id),
                valid_until=body.valid_until,
                next_review_date=body.next_review_date,
                evidence_notes=body.evidence_notes,
            )
            db.add(ca)
            created += 1

        # Auto-avvik for non_compliant (kun opprett hvis ingen finnes)
        if body.status == "non_compliant":
            existing_case = await db.execute(
                select(InternalControlCase).where(
                    InternalControlCase.compliance_assessment_id == ca.assessment_id
                )
            )
            if existing_case.scalar_one_or_none() is None:
                req_assignment = await db.get(RequirementAssignment, assignment_id)
                req = await db.get(Requirement, req_assignment.requirement_id) if req_assignment else None
                priority_map = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
                priority = priority_map.get(req.severity_if_breached or "", "medium") if req else "medium"
                db.add(InternalControlCase(
                    case_id=uuid.uuid4(),
                    property_id=req_assignment.property_id if req_assignment else None,
                    title=f"Avvik: {req.title if req else 'Ukjent krav'}",
                    description=f"Compliance-vurdering satt til non_compliant via batch-vurdering.",
                    case_type="compliance",
                    status="open",
                    priority=priority,
                    compliance_assessment_id=ca.assessment_id,
                    requirement_id=req.requirement_id if req else None,
                ))

    await db.commit()
    return {"updated": updated, "created": created, "total": updated + created}

@router.get(
    "/compliance/summary/{property_id}",
    response_model=ComplianceSummary,
    tags=["FDVU Compliance"],
)
async def compliance_summary(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compliance-oversikt for én eiendom."""
    result = await db.execute(
        select(RequirementAssignment)
        .options(selectinload(RequirementAssignment.compliance_assessment))
        .where(RequirementAssignment.property_id == property_id)
    )
    assignments = result.scalars().all()

    counts: dict[str, int] = {
        "compliant": 0,
        "non_compliant": 0,
        "partial": 0,
        "not_assessed": 0,
        "not_applicable": 0,
    }
    overdue = 0
    today = date.today()

    for a in assignments:
        ca = a.compliance_assessment
        if ca is None:
            counts["not_assessed"] += 1
        else:
            s = ca.status if ca.status in counts else "not_assessed"
            counts[s] += 1
            if (
                ca.next_review_date
                and ca.next_review_date < today
                and ca.status not in ("not_applicable", "compliant")
            ):
                overdue += 1

    total = len(assignments)
    denominator = total - counts["not_applicable"] - counts["not_assessed"]
    rate = counts["compliant"] / denominator if denominator > 0 else 0.0

    return ComplianceSummary(
        property_id=property_id,
        total_assignments=total,
        overdue_reviews=overdue,
        compliance_rate=round(rate, 4),
        **counts,
    )


@router.get(
    "/compliance/portfolio-summary",
    tags=["FDVU Compliance"],
)
async def portfolio_compliance_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregert compliance-oversikt for hele porteføljen."""
    from sqlalchemy import text as sql_text
    rows = await db.execute(sql_text("""
        SELECT
            COUNT(ra.assignment_id)                                              AS total,
            SUM(CASE WHEN ca.status = 'compliant'      THEN 1 ELSE 0 END)       AS compliant,
            SUM(CASE WHEN ca.status = 'non_compliant'  THEN 1 ELSE 0 END)       AS non_compliant,
            SUM(CASE WHEN ca.status = 'partial'        THEN 1 ELSE 0 END)       AS partial,
            SUM(CASE WHEN ca.status = 'not_applicable' THEN 1 ELSE 0 END)       AS not_applicable,
            SUM(CASE WHEN ca.status IS NULL OR ca.status = 'not_assessed'
                     THEN 1 ELSE 0 END)                                          AS not_assessed,
            SUM(CASE WHEN ca.next_review_date IS NOT NULL
                          AND ca.next_review_date < CURRENT_DATE
                          AND ca.status NOT IN ('not_applicable','compliant')
                     THEN 1 ELSE 0 END)                                          AS overdue_reviews,
            COUNT(DISTINCT ra.property_id)                                       AS properties_with_assignments
        FROM requirement_assignments ra
        LEFT JOIN compliance_assessments ca ON ca.assignment_id = ra.assignment_id
    """))
    row = rows.mappings().one()
    total = int(row["total"] or 0)
    compliant = int(row["compliant"] or 0)
    non_compliant = int(row["non_compliant"] or 0)
    partial = int(row["partial"] or 0)
    not_applicable = int(row["not_applicable"] or 0)
    not_assessed = int(row["not_assessed"] or 0)
    overdue = int(row["overdue_reviews"] or 0)
    properties_n = int(row["properties_with_assignments"] or 0)

    denominator = total - not_applicable - not_assessed
    rate = compliant / denominator if denominator > 0 else 0.0

    return {
        "total_assignments": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "partial": partial,
        "not_applicable": not_applicable,
        "not_assessed": not_assessed,
        "overdue_reviews": overdue,
        "compliance_rate": round(rate, 4),
        "properties_with_assignments": properties_n,
    }


@router.put(
    "/compliance/assess",
    response_model=AssessmentOut,
    tags=["FDVU Compliance"],
)
async def upsert_assessment(
    body: AssessmentUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opprett eller oppdater compliance-vurdering for ett krav-assignment."""
    # Sjekk at assignment finnes
    assignment = await db.get(RequirementAssignment, body.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment ikke funnet")

    # Upsert
    result = await db.execute(
        select(ComplianceAssessment).where(
            ComplianceAssessment.assignment_id == body.assignment_id
        )
    )
    assessment = result.scalar_one_or_none()

    if assessment is None:
        assessment = ComplianceAssessment(
            assessment_id=uuid.uuid4(),
            assignment_id=body.assignment_id,
            assessed_by=current_user.user_id,
        )
        db.add(assessment)
    else:
        assessment.assessed_by = current_user.user_id
        assessment.assessed_at = datetime.now(timezone.utc)

    prev_status = assessment.status if assessment.assessment_id else None  # type: ignore[attr-defined]
    for k, v in body.model_dump(exclude={"assignment_id"}, exclude_unset=True).items():
        setattr(assessment, k, v)

    await db.commit()
    await db.refresh(assessment)

    # ── Auto-opprett avvik (InternalControlCase) ved non_compliant ──────────
    if assessment.status == "non_compliant":
        existing_case = await db.execute(
            select(InternalControlCase).where(
                InternalControlCase.compliance_assessment_id == assessment.assessment_id
            )
        )
        if existing_case.scalar_one_or_none() is None:
            # Hent requirement for tittel og alvorlighetsgrad
            req_assignment = await db.get(RequirementAssignment, assessment.assignment_id)
            req = await db.get(Requirement, req_assignment.requirement_id) if req_assignment else None

            sev_to_priority = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
            priority = sev_to_priority.get(req.severity_if_breached or "", "medium") if req else "medium"

            new_case = InternalControlCase(
                case_id=uuid.uuid4(),
                property_id=req_assignment.property_id if req_assignment else assignment.property_id,
                title=f"Avvik: {req.title if req else 'Ukjent krav'}",
                description=(
                    f"Compliance-vurdering registrerte avvik på krav {req.code if req else ''}.\n"
                    f"{body.evidence_notes or ''}"
                ).strip(),
                case_type="compliance",
                status="open",
                priority=priority,
                compliance_assessment_id=assessment.assessment_id,
                requirement_id=req.requirement_id if req else None,
            )
            db.add(new_case)
            await db.commit()

    return assessment


# ═════════════════════════════════════════════
# REVISJONSVARSEL
# ═════════════════════════════════════════════

async def _create_review_reminders(db: AsyncSession, days_ahead: int = 30) -> int:
    """
    Intern hjelpefunksjon – oppretter InternalControlCase for compliance-vurderinger
    der next_review_date er innenfor `days_ahead` dager og det ikke allerede
    finnes en åpen 'review_reminder'-sak for vurderingen.

    Returnerer antall opprettede saker.
    """
    from sqlalchemy import text as sql_text

    today = date.today()
    cutoff = today.replace(year=today.year) if days_ahead == 0 else date.fromordinal(today.toordinal() + days_ahead)

    # Hent vurderinger med kommende/forfalt revisjonsdato
    rows = await db.execute(sql_text("""
        SELECT
            ca.assessment_id,
            ca.assignment_id,
            ca.next_review_date,
            ra.property_id,
            r.title AS req_title,
            r.requirement_id,
            r.severity_if_breached
        FROM compliance_assessments ca
        JOIN requirement_assignments ra ON ra.assignment_id = ca.assignment_id
        JOIN requirements r ON r.requirement_id = ra.requirement_id
        WHERE ca.next_review_date IS NOT NULL
          AND ca.next_review_date <= :cutoff
          AND ca.status NOT IN ('not_applicable')
        ORDER BY ca.next_review_date
    """), {"cutoff": cutoff.isoformat()})
    due = rows.mappings().all()

    created = 0
    for row in due:
        # Sjekk om det allerede finnes en åpen review_reminder-sak
        existing = await db.execute(
            select(InternalControlCase).where(
                InternalControlCase.compliance_assessment_id == row["assessment_id"],
                InternalControlCase.case_type == "review_reminder",
                InternalControlCase.status == "open",
            )
        )
        if existing.scalar_one_or_none():
            continue

        review_date = row["next_review_date"]
        if isinstance(review_date, str):
            review_date = date.fromisoformat(review_date)
        days_overdue = (today - review_date).days
        overdue_txt = f" ({days_overdue} dager forfalt)" if days_overdue > 0 else f" (om {-days_overdue} dager)"

        sev = row["severity_if_breached"] or "medium"
        priority_map = {"critical": "critical", "high": "high", "medium": "medium", "low": "low"}
        priority = priority_map.get(sev, "medium")

        case = InternalControlCase(
            case_id=uuid.uuid4(),
            property_id=row["property_id"],
            title=f"Revisjonsvarsel: {row['req_title']}{overdue_txt}",
            description=(
                f"Compliance-vurdering for krav «{row['req_title']}» forfaller til revisjon "
                f"{review_date.isoformat()}. Vennligst oppdater vurderingen i FDVU-modulen."
            ),
            case_type="review_reminder",
            status="open",
            priority=priority,
            compliance_assessment_id=row["assessment_id"],
            requirement_id=row["requirement_id"],
        )
        db.add(case)
        created += 1

    if created:
        await db.commit()
    return created


@router.post(
    "/compliance/send-review-reminders",
    tags=["FDVU Compliance"],
)
async def send_review_reminders(
    days_ahead: int = Query(30, ge=0, le=365, description="Opprett varsel for vurderinger som forfaller innen N dager"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Oppretter InternalControlCase-saker for compliance-vurderinger
    som nærmer seg revisjonsdato (default 30 dager frem).
    Tryggt å kjøre gjentatte ganger – duplikater hoppes over.
    """
    created = await _create_review_reminders(db, days_ahead=days_ahead)
    return {"reminders_created": created, "days_ahead": days_ahead}


# ═════════════════════════════════════════════
# FDV-DOKUMENTER
# ═════════════════════════════════════════════

@router.get("/documents", response_model=List[FdvDocumentOut], tags=["FDVU Dokumenter"])
async def list_documents(
    property_id: uuid.UUID = Query(...),
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    section_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(FdvDocument).where(FdvDocument.property_id == property_id)
    if document_type:
        q = q.where(FdvDocument.document_type == document_type)
    if status:
        q = q.where(FdvDocument.status == status)
    if section_id:
        q = q.where(FdvDocument.section_id == section_id)
    result = await db.execute(q.order_by(FdvDocument.document_date.desc().nullslast()))
    return result.scalars().all()


@router.post("/documents", response_model=FdvDocumentOut, status_code=201, tags=["FDVU Dokumenter"])
async def create_document(
    body: FdvDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = FdvDocument(
        document_id=uuid.uuid4(),
        uploaded_by=current_user.user_id,
        **body.model_dump(),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.patch("/documents/{document_id}", response_model=FdvDocumentOut, tags=["FDVU Dokumenter"])
async def update_document(
    document_id: uuid.UUID,
    body: FdvDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await db.get(FdvDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(doc, k, v)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/documents/{document_id}", status_code=204, tags=["FDVU Dokumenter"])
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await db.get(FdvDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Dokument ikke funnet")
    doc.status = "expired"   # Soft-delete via status
    await db.commit()


# ═════════════════════════════════════════════
# TILSTANDSREGISTRERING (bygningskomponenter)
# ═════════════════════════════════════════════

class TilstandUpdate(BaseModel):
    condition_grade: Optional[str] = None          # TG0|TG1|TG2|TG3
    criticality_level: Optional[str] = None        # critical|important|standard
    replacement_year: Optional[int] = None
    barcode: Optional[str] = None
    serial_number: Optional[str] = None
    section_id: Optional[uuid.UUID] = None


class ComponentTilstandOut(BaseModel):
    component_id: uuid.UUID
    property_id: uuid.UUID
    name: str
    type: Optional[str] = None
    ns3451_code: Optional[str] = None
    condition_grade: Optional[str] = None
    criticality_level: Optional[str] = None
    condition_assessed_at: Optional[datetime] = None
    condition_assessed_by: Optional[uuid.UUID] = None
    replacement_year: Optional[int] = None
    barcode: Optional[str] = None
    serial_number: Optional[str] = None
    section_id: Optional[uuid.UUID] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/components/{property_id}", response_model=List[ComponentTilstandOut], tags=["FDVU Tilstand"])
async def list_components_tilstand(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Henter alle bygningskomponenter for en eiendom med tilstandsdata."""
    result = await db.execute(
        select(ComponentModel)
        .where(ComponentModel.property_id == property_id)
        .order_by(ComponentModel.name)
    )
    return result.scalars().all()


@router.patch("/components/{component_id}/tilstand", response_model=ComponentTilstandOut, tags=["FDVU Tilstand"])
async def update_tilstand(
    component_id: uuid.UUID,
    body: TilstandUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Registrer eller oppdater tilstandsgrad (TG0–TG3) på en komponent.

    Auto-oppretter InternalControlCase ved TG2 (viktig/kritisk) eller TG3 (alle),
    hvis det ikke allerede finnes en åpen sak for komponenten.
    """
    comp = await db.get(ComponentModel, component_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Komponent ikke funnet")

    prev_grade = comp.condition_grade
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(comp, k, v)

    comp.condition_assessed_at = datetime.now(timezone.utc)
    comp.condition_assessed_by = current_user.user_id

    await db.commit()
    await db.refresh(comp)

    # Auto-opprett HMS-sak ved TG2 (kritisk/viktig) eller TG3 (alltid)
    new_grade = comp.condition_grade or ""
    crit = comp.criticality_level or "standard"
    should_create_case = (
        (new_grade == "TG3")
        or (new_grade == "TG2" and crit in ("critical", "important"))
    )
    if should_create_case and new_grade != prev_grade:
        # Sjekk om åpen sak allerede finnes for denne komponenten
        existing = await db.execute(
            select(InternalControlCase).where(
                InternalControlCase.property_id == comp.property_id,
                InternalControlCase.title.ilike(f"%{comp.name}%"),
                InternalControlCase.case_type == "maintenance",
                InternalControlCase.status == "open",
            )
        )
        if existing.scalar_one_or_none() is None:
            grade_label = {"TG2": "Middels alvorlig (TG2)", "TG3": "Alvorlig (TG3)"}.get(new_grade, new_grade)
            priority = "critical" if new_grade == "TG3" or crit == "critical" else "high"
            replace_info = f" (forventet utskifting: {comp.replacement_year})" if comp.replacement_year else ""
            db.add(InternalControlCase(
                case_id=uuid.uuid4(),
                property_id=comp.property_id,
                title=f"Tilstand {grade_label}: {comp.name}{replace_info}",
                description=(
                    f"Komponent «{comp.name}» er vurdert til {new_grade} ({grade_label}). "
                    f"Kritikalitet: {crit}. "
                    f"Krever oppfølging/vedlikehold."
                ),
                case_type="maintenance",
                status="open",
                priority=priority,
            ))
            await db.commit()

    return comp


# ═════════════════════════════════════════════
# FDVU RAPPORT-EKSPORT
# ═════════════════════════════════════════════

@router.get("/rapport/{property_id}", tags=["FDVU Rapport"])
async def fdvu_rapport(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full FDVU-rapport for én eiendom – alle compliance-vurderinger, tilstandsgrader
    og FDV-dokumenter i ett JSON-svar. Egnet for PDF-generering og eksport.
    """
    from app.domains.core.models.property import Property

    prop = await db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

    # Assignments + requirements + assessments
    asgn_res = await db.execute(
        select(RequirementAssignment)
        .options(
            selectinload(RequirementAssignment.requirement),
            selectinload(RequirementAssignment.compliance_assessment),
        )
        .where(RequirementAssignment.property_id == property_id)
        .order_by(RequirementAssignment.requirement_id)
    )
    assignments = asgn_res.scalars().all()

    # Komponenter
    comp_res = await db.execute(
        select(ComponentModel)
        .where(ComponentModel.property_id == property_id)
        .order_by(ComponentModel.condition_grade.desc().nullslast(), ComponentModel.name)
    )
    components = comp_res.scalars().all()

    # Dokumenter
    doc_res = await db.execute(
        select(FdvDocument)
        .where(FdvDocument.property_id == property_id)
        .order_by(FdvDocument.document_type, FdvDocument.title)
    )
    documents = doc_res.scalars().all()

    # Seksjoner
    sec_res = await db.execute(
        select(FdvuSection).where(FdvuSection.property_id == property_id)
    )
    sections = sec_res.scalars().all()

    # Compliance-tall
    counts = {"compliant": 0, "non_compliant": 0, "partial": 0, "not_assessed": 0, "not_applicable": 0}
    overdue = 0
    today = date.today()
    for a in assignments:
        ca = a.compliance_assessment
        s = ca.status if ca and ca.status in counts else "not_assessed"
        counts[s] += 1
        if ca and ca.next_review_date and ca.next_review_date < today and s not in ("not_applicable", "compliant"):
            overdue += 1

    denom = len(assignments) - counts["not_applicable"] - counts["not_assessed"]
    rate = counts["compliant"] / denom if denom > 0 else 0.0

    # TG-oppsummering
    tg_counts = {"TG0": 0, "TG1": 0, "TG2": 0, "TG3": 0, "ukjent": 0}
    for c in components:
        tg = c.condition_grade if c.condition_grade in tg_counts else "ukjent"
        tg_counts[tg] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "property": {
            "property_id": str(property_id),
            "name": prop.name,
            "address": prop.address,
            "city": prop.city,
            "region": prop.region,
            "unit_type_derived": prop.unit_type_derived,
            "approved_places": prop.approved_places,
        },
        "compliance_summary": {
            "total_assignments": len(assignments),
            "compliance_rate": round(rate, 4),
            "overdue_reviews": overdue,
            **counts,
        },
        "tilstand_summary": tg_counts,
        "sections": [
            {
                "section_id": str(s.section_id),
                "name": s.name,
                "section_type": s.section_type,
                "floor": s.floor,
                "area_sqm": s.area_sqm,
            }
            for s in sections
        ],
        "compliance_details": [
            {
                "assignment_id": str(a.assignment_id),
                "code": a.requirement.code if a.requirement else None,
                "title": a.requirement.title if a.requirement else None,
                "regulation_set": a.requirement.regulation_set if a.requirement else None,
                "severity": a.requirement.severity_if_breached if a.requirement else None,
                "status": a.compliance_assessment.status if a.compliance_assessment else "not_assessed",
                "assessed_at": a.compliance_assessment.assessed_at.isoformat() if a.compliance_assessment and a.compliance_assessment.assessed_at else None,
                "valid_until": a.compliance_assessment.valid_until.isoformat() if a.compliance_assessment and a.compliance_assessment.valid_until else None,
                "next_review_date": a.compliance_assessment.next_review_date.isoformat() if a.compliance_assessment and a.compliance_assessment.next_review_date else None,
                "evidence_notes": a.compliance_assessment.evidence_notes if a.compliance_assessment else None,
            }
            for a in assignments
        ],
        "components": [
            {
                "component_id": str(c.component_id),
                "name": c.name,
                "type": c.type,
                "ns3451_code": c.ns3451_code,
                "condition_grade": c.condition_grade,
                "criticality_level": c.criticality_level,
                "replacement_year": c.replacement_year,
                "condition_assessed_at": c.condition_assessed_at.isoformat() if c.condition_assessed_at else None,
                "barcode": c.barcode,
                "serial_number": c.serial_number,
            }
            for c in components
        ],
        "fdv_documents": [
            {
                "document_id": str(d.document_id),
                "title": d.title,
                "document_type": d.document_type,
                "document_date": d.document_date.isoformat() if d.document_date else None,
                "valid_until": d.valid_until.isoformat() if d.valid_until else None,
                "status": d.status,
                "external_url": d.external_url,
            }
            for d in documents
        ],
    }


# ═════════════════════════════════════════════
# KI-ASSIST – FDVU-VURDERING
# ═════════════════════════════════════════════

class KiAssistRequest(BaseModel):
    property_id: uuid.UUID
    assignment_id: uuid.UUID
    user_question: Optional[str] = None   # valgfritt tilleggsspørsmål fra brukeren


class KiAssistResponse(BaseModel):
    suggested_status: str                  # compliant | non_compliant | partial | not_applicable
    confidence: str                        # high | medium | low
    evidence_notes: str                    # forslag til notattekst
    explanation: str                       # forklaring til bruker
    next_review_months: Optional[int]      # anbefalt revisjonsintervall


@router.post("/ki-assist", response_model=KiAssistResponse, tags=["FDVU KI"])
async def fdvu_ki_assist(
    body: KiAssistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    KI-drevet hjelp til compliance-vurdering for ett krav på én eiendom.
    Analyserer eiendomstype, eksisterende HMS-saker, tilstandsgrader og dokumenter,
    og returnerer forslag til status, notater og revisjonsintervall.
    """
    from app.core.ai_utils import get_ai_client
    from app.domains.core.models.property import Property

    # ── Hent data ──────────────────────────────────────────────────────────────
    prop = await db.get(Property, body.property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

    assignment = await db.get(RequirementAssignment, body.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Kravtildeling ikke funnet")

    req = await db.get(Requirement, assignment.requirement_id)

    # Eksisterende vurdering
    existing_ca = (await db.execute(
        select(ComplianceAssessment).where(ComplianceAssessment.assignment_id == body.assignment_id)
    )).scalar_one_or_none()

    # Åpne HMS-saker for eiendommen
    open_cases_res = await db.execute(
        select(InternalControlCase).where(
            InternalControlCase.property_id == body.property_id,
            InternalControlCase.status == "open",
        ).limit(10)
    )
    open_cases = open_cases_res.scalars().all()

    # Tilstandsgrader
    comp_res = await db.execute(
        select(ComponentModel).where(
            ComponentModel.property_id == body.property_id,
            ComponentModel.condition_grade.in_(["TG2", "TG3"]),
        ).limit(10)
    )
    bad_components = comp_res.scalars().all()

    # FDV-dokumenter
    docs_res = await db.execute(
        select(FdvDocument).where(FdvDocument.property_id == body.property_id).limit(10)
    )
    docs = docs_res.scalars().all()

    # ── Bygg kontekst ──────────────────────────────────────────────────────────
    prop_ctx = (
        f"Eiendom: {prop.name or '(ukjent navn)'}\n"
        f"Adresse: {prop.address or '?'}, {prop.city or '?'}\n"
        f"Type: {prop.unit_type_derived or 'ukjent'}\n"
        f"Godkjente plasser: {prop.approved_places or 0}\n"
        f"Region: {prop.region or '?'}"
    )
    req_ctx = (
        f"Krav: {req.code if req else '?'} – {req.title if req else '?'}\n"
        f"Regelverk: {req.regulation_set if req else '?'}\n"
        f"Alvorlighet ved brudd: {req.severity_if_breached if req else '?'}\n"
        f"Beskrivelse: {req.description if req and req.description else 'Ingen beskrivelse'}\n"
        f"Kategori: {req.category if req and req.category else '?'}"
    )
    existing_ctx = ""
    if existing_ca:
        existing_ctx = (
            f"\nEksisterende vurdering: status={existing_ca.status}, "
            f"notater='{existing_ca.evidence_notes or ''}'"
        )
    cases_ctx = ""
    if open_cases:
        cases_ctx = "\nÅpne HMS-saker:\n" + "\n".join(
            f"- [{c.priority}] {c.title} (type: {c.case_type})" for c in open_cases
        )
    comp_ctx = ""
    if bad_components:
        comp_ctx = "\nKomponenter med dårlig tilstand (TG2/TG3):\n" + "\n".join(
            f"- {c.name}: {c.condition_grade} ({c.criticality_level or 'ukjent kritikalitet'})"
            for c in bad_components
        )
    doc_ctx = ""
    if docs:
        doc_ctx = "\nFDV-dokumenter:\n" + "\n".join(
            f"- {d.document_type}: {d.title} (status: {d.status})" for d in docs
        )

    user_q = f"\nBrukerens tilleggsspørsmål: {body.user_question}" if body.user_question else ""

    prompt = f"""Du er en FDVU-ekspert (Forvaltning, Drift, Vedlikehold, Utvikling) for norske barnevernsinstitusjoner og andre Bufetat-eiendommer.

Vurder følgende compliance-krav for eiendommen og gi et faglig begrunnet forslag.

{prop_ctx}

{req_ctx}
{existing_ctx}
{cases_ctx}
{comp_ctx}
{doc_ctx}
{user_q}

Svar KUN som gyldig JSON med disse nøklene:
{{
  "suggested_status": "compliant" | "non_compliant" | "partial" | "not_applicable",
  "confidence": "high" | "medium" | "low",
  "evidence_notes": "<1-3 setninger klar for å limes inn som dokumentasjon>",
  "explanation": "<2-4 setninger på norsk som forklarer vurderingen til eiendomsforvalteren>",
  "next_review_months": <heltall, anbefalt antall måneder til neste revisjon>
}}

Regler:
- not_applicable kun hvis kravet åpenbart ikke gjelder denne eiendomstypen
- confidence=high kun hvis du har klare indikatorer fra dataene
- evidence_notes skal være presis, profesjonell norsk – klar til bruk som dokumentasjon
- Ta hensyn til åpne HMS-saker og TG2/TG3-komponenter ved vurdering"""

    # ── Kall OpenAI ────────────────────────────────────────────────────────────
    try:
        client, model = get_ai_client()
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        import json as _json
        result = _json.loads(response.choices[0].message.content or "{}")
        return KiAssistResponse(
            suggested_status=result.get("suggested_status", "not_assessed"),
            confidence=result.get("confidence", "low"),
            evidence_notes=result.get("evidence_notes", ""),
            explanation=result.get("explanation", ""),
            next_review_months=result.get("next_review_months"),
        )
    except Exception as e:
        logger.error("fdvu_ki_assist feil: %s", e)
        raise HTTPException(status_code=500, detail=f"KI-tjeneste utilgjengelig: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Periodiske krav – upcoming deadlines
# ─────────────────────────────────────────────────────────────────────────────

class PeriodicRequirementOut(BaseModel):
    assignment_id: uuid.UUID
    property_id: uuid.UUID
    code: str
    title: str
    regulation_set: str
    category: Optional[str]
    severity_if_breached: Optional[str]
    status: str
    next_review_date: Optional[date]
    valid_until: Optional[date]
    days_until_due: Optional[int]
    overdue: bool

    class Config:
        from_attributes = True


@router.get("/periodic-requirements", tags=["FDVU Compliance"])
async def get_periodic_requirements(
    property_id: Optional[uuid.UUID] = Query(None),
    days_ahead: int = Query(default=90, ge=1, le=365),
    include_overdue: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PeriodicRequirementOut]:
    """
    Returnerer krav med kommende frist (next_review_date) innen `days_ahead` dager,
    pluss eventuelle forfalte krav. Brukes i FDVU-dashboard for å varsle om
    F-gass, Radon, Heis, Legionella, BREEAM osv.
    """
    from datetime import timedelta

    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    q = (
        select(RequirementAssignment)
        .join(Requirement, RequirementAssignment.requirement_id == Requirement.requirement_id)
        .outerjoin(ComplianceAssessment, RequirementAssignment.assignment_id == ComplianceAssessment.assignment_id)
        .options(
            selectinload(RequirementAssignment.requirement),
            selectinload(RequirementAssignment.compliance_assessment),
        )
    )
    if property_id:
        q = q.where(RequirementAssignment.property_id == property_id)

    result = await db.execute(q)
    assignments = result.scalars().all()

    out = []
    for a in assignments:
        assessment = a.compliance_assessment
        if not assessment:
            continue
        nrd = assessment.next_review_date
        vu = assessment.valid_until
        due_date = nrd or vu
        if not due_date:
            continue

        days_left = (due_date - today).days
        overdue = days_left < 0

        if overdue and not include_overdue:
            continue
        if not overdue and due_date > cutoff:
            continue

        out.append(PeriodicRequirementOut(
            assignment_id=a.assignment_id,
            property_id=a.property_id,
            code=a.requirement.code,
            title=a.requirement.title,
            regulation_set=a.requirement.regulation_set,
            category=a.requirement.category,
            severity_if_breached=a.requirement.severity_if_breached,
            status=assessment.status,
            next_review_date=nrd,
            valid_until=vu,
            days_until_due=days_left,
            overdue=overdue,
        ))

    out.sort(key=lambda x: (x.days_until_due or 0))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Brannbok – deles med leietaker/brannvesen
# ─────────────────────────────────────────────────────────────────────────────

class BrannbokDocOut(BaseModel):
    document_id: uuid.UUID
    title: str
    document_type: str
    document_date: Optional[date]
    valid_until: Optional[date]
    revision: Optional[str]
    external_url: Optional[str]
    file_path: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.get("/brannbok/{property_id}", tags=["FDVU Brannbok"])
async def get_brannbok(
    property_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BrannbokDocOut]:
    """
    Returnerer alle branndokumenter for en eiendom (document_type inneholder
    'brann' ELLER category='brann'). Brukes til å dele brannbok med
    leietakere og brannvesen.
    """
    result = await db.execute(
        select(FdvDocument).where(
            and_(
                FdvDocument.property_id == property_id,
                or_(
                    FdvDocument.document_type.ilike("%brann%"),
                    FdvDocument.document_type == "brannbok",
                    FdvDocument.document_type == "evakueringsplan",
                    FdvDocument.document_type == "branntegning",
                ),
                FdvDocument.status != "superseded",
            )
        ).order_by(FdvDocument.document_date.desc())
    )
    docs = result.scalars().all()
    return [BrannbokDocOut.model_validate(d) for d in docs]


# ─────────────────────────────────────────────────────────────────────────────
# Sensor-sammendrag – EOS + inneklima
# ─────────────────────────────────────────────────────────────────────────────

class SensorSummaryItem(BaseModel):
    sensor_id: uuid.UUID
    name: str
    sensor_type: str
    location: Optional[str]
    latest_value: Optional[float]
    latest_unit: Optional[str]
    latest_at: Optional[datetime]
    is_anomaly: bool

    class Config:
        from_attributes = True


@router.get("/sensors/{property_id}/summary", tags=["FDVU Sensorer"])
async def get_sensor_summary(
    property_id: uuid.UUID,
    sensor_type: Optional[str] = Query(None, description="Filter: energy | temperature | humidity | co2"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SensorSummaryItem]:
    """
    Returnerer siste måling per sensor for en eiendom.
    Brukes av EOS (energioppfølging) og SD-inneklimavisning.
    """
    from app.domains.fdv.models.iot import Sensor, SensorReading, Anomaly

    q = select(Sensor).where(Sensor.property_id == property_id)
    if sensor_type:
        q = q.where(Sensor.type == sensor_type)

    result = await db.execute(q)
    sensors = result.scalars().all()

    out = []
    for s in sensors:
        # Siste avlesning
        reading_res = await db.execute(
            select(SensorReading)
            .where(SensorReading.sensor_id == s.sensor_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(1)
        )
        reading = reading_res.scalars().first()

        # Sjekk aktiv anomali
        anomaly_res = await db.execute(
            select(Anomaly)
            .where(
                and_(
                    Anomaly.sensor_id == s.sensor_id,
                    Anomaly.resolved_at.is_(None),
                )
            )
            .limit(1)
        )
        has_anomaly = anomaly_res.scalars().first() is not None

        out.append(SensorSummaryItem(
            sensor_id=s.sensor_id,
            name=s.name,
            sensor_type=s.type,
            location=getattr(s, "location", None),
            latest_value=reading.value if reading else None,
            latest_unit=reading.unit if reading else None,
            latest_at=reading.timestamp if reading else None,
            is_anomaly=has_anomaly,
        ))

    return out
