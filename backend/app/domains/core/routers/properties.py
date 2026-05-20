import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, or_
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.core.property_access import check_property_access, filter_properties_by_access, get_user_accessible_property_ids
# Ensure all models are loaded for SQLAlchemy registry
import app.db.base
# ORM models (Current Repo Structure)
from app.domains.core.models.property import Property as PropertyModel
# Pydantic models (New Schema)
from app.schemas.property import Property as PropertySchema


from datetime import datetime
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyDetailView, Property as PropertySchema, Unit as UnitSchema
from app.schemas.contract import Contract
from app.domains.core.models.unit import Unit as UnitModel
from app.domains.core.models.contract import Contract as ContractModel
from app.domains.core.models.party import Party as PartyModel
from app.domains.hms.models.risk import RiskAssessment as RiskAssessmentModel
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User as UserModel
from sqlalchemy.orm import selectinload
from app.services.financials.source_coverage_service import complete_source_coverage_property_ids_subquery
from app.core.config import settings

router = APIRouter()

_DEFAULT_SOURCE_COVERAGE = (
    "all" if settings.ENVIRONMENT in ("local", "development") else "complete"
)


def _bufdir_image_thumb(ext: Optional[dict]) -> Optional[str]:
    import re as _re
    if not ext or not isinstance(ext, dict):
        return None
    b = ext.get("bufdir") or ext.get("bufdir_institution") or {}
    if not isinstance(b, dict):
        return None
    path = b.get("image_path") or b.get("image_url")
    if not path:
        return None
    # Filnavn lagret med _N-suffiks (f.eks. uuid_0.jpg) men filen på disk er uuid.jpg
    path = _re.sub(r'_\d+(\.[a-zA-Z]+)$', r'\1', path)
    return path


async def _primary_lease_party_by_property_ids(
    db: AsyncSession, property_ids: List[UUID]
) -> dict[str, str]:
    """Én visningsverdig leverandør/motpart per eiendom (aktiv kontrakt foretrekkes, deretter siste startdato)."""
    if not property_ids:
        return {}
    stmt = (
        select(
            UnitModel.property_id,
            PartyModel.name,
            ContractModel.start_date,
            ContractModel.status,
        )
        .select_from(UnitModel)
        .join(ContractModel, ContractModel.unit_id == UnitModel.unit_id)
        .join(PartyModel, PartyModel.party_id == ContractModel.party_id)
        .where(UnitModel.property_id.in_(property_ids))
        .where(PartyModel.name.isnot(None))
    )
    rows = (await db.execute(stmt)).all()
    from collections import defaultdict

    by_p: dict = defaultdict(list)
    for row in rows:
        by_p[row.property_id].append(row)

    out: dict[str, str] = {}
    for pid, items in by_p.items():
        def sort_key(x):
            st = (x.status or "").lower()
            active_first = 0 if st in ("active", "") else 1
            sd = x.start_date
            ord_ = -(sd.toordinal() if sd else 0)
            return (active_first, ord_)

        items.sort(key=sort_key)
        name = items[0].name
        if name:
            out[str(pid)] = name.strip()
    return out


def enrich_property_data(p_dict: dict, ext: dict, property_obj=None):
    """
    Helper to populate missing fields from external_data with aggressive fallbacks.
    """
    # Total Area
    if not p_dict.get("total_area"):
        p_dict["total_area"] = ext.get("sqm") or ext.get("total_area") or ext.get("bra") or ext.get("total_bta_m2")
    
    # Construction Year
    if not p_dict.get("construction_year"):
        p_dict["construction_year"] = ext.get("byggeår") or ext.get("year_built") or ext.get("year") or ext.get("building_year")

    # Municipality & Location
    if not p_dict.get("municipality"):
        p_dict["municipality"] = ext.get("poststed") or ext.get("kommune") or ext.get("sted")
    
    # City fallback (for frontend consistency)
    if not p_dict.get("city"):
        p_dict["city"] = p_dict.get("municipality") or ext.get("lokasjon")
        
    if not p_dict.get("gnr"):
        p_dict["gnr"] = ext.get("matrikkel_gnr") or ext.get("gnr")
        
    if not p_dict.get("bnr"):
        p_dict["bnr"] = ext.get("matrikkel_bnr") or ext.get("bnr")
        
    if not p_dict.get("address"):
        p_dict["address"] = ext.get("property_address") or ext.get("gateadresse") or ext.get("lokasjon")
        
    if not p_dict.get("usage"):
        p_dict["usage"] = ext.get("usage") or ext.get("eiendomstype") or "Næringseiendom"

    # Region fallback
    if not p_dict.get("region"):
        p_dict["region"] = ext.get("region") or ext.get("fylke")

    # Detail view specific fields
    if not p_dict.get("municipality_code"):
        p_dict["municipality_code"] = ext.get("matrikkel_knr") or ext.get("municipality_code")
        
    # Aggressive Name Fallbacks
    if not p_dict.get("name") or p_dict["name"] == "-":
        # 1. Try specific naming keys
        p_dict["name"] = ext.get("name") or ext.get("property_name") or ext.get("tittel") or ext.get("eiendom") or ext.get("eiendomsnavn") or ext.get("enhet")
        
        # 2. Fallback to address
        if not p_dict.get("name") or p_dict["name"] == "-":
             p_dict["name"] = p_dict.get("address") or (property_obj.address if property_obj else None)
             
        # 3. Fallback to filename (cleaned)
        if (not p_dict.get("name") or p_dict["name"] == "-") and ext.get("filename"):
            fname = ext.get("filename")
            p_dict["name"] = fname.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').strip()
            
        # 4. Fallback to Gnr/Bnr if available
        if (not p_dict.get("name") or p_dict["name"] == "-") and (p_dict.get("gnr") or p_dict.get("bnr")):
            g = p_dict.get("gnr")
            b = p_dict.get("bnr")
            if g and b:
                p_dict["name"] = f"Gnr {g}/Bnr {b}"
            elif g:
                p_dict["name"] = f"Gnr {g}"

    return p_dict

@router.post("", response_model=PropertySchema, status_code=201)
async def create_property(
    property_in: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Opprett ny eiendom (kun ADMIN)."""
    # Kun ADMIN kan opprette nye properties
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create properties"
        )
    
    db_obj = PropertyModel(
        property_id=uuid4(),
        address=property_in.address,
        postal_code=property_in.postal_code,
        city=property_in.city,
        latitude=property_in.latitude,
        longitude=property_in.longitude,
        created_at=datetime.utcnow()
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

_SORTABLE_COLUMNS = {
    "name": PropertyModel.name,
    "address": PropertyModel.address,
    "city": PropertyModel.city,
    "region": PropertyModel.region,
    "usage": PropertyModel.usage,
}

@router.get("", response_model=List[PropertySchema])
async def get_properties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, description="Antall å hoppe over (pagination)"),
    limit: int = Query(50, description="Antall å hente (pagination)"),
    usage: Optional[str] = Query(None, description="Filtrer på bruksformål"),
    search: Optional[str] = Query(None, description="Søk i navn eller adresse"),
    unit_short_type: Optional[str] = Query(None, description="Filtrer på enhetstype: Avdeling | Barnevernsinstitusjon"),
    exclude_avdelinger: bool = Query(True, description="Skjul avdelinger (unit_short_type=Avdeling) fra listen – de vises under sin foreldreinstitujon"),
    include_discontinued: bool = Query(False, description="Inkluder avviklede eiendommer (closed_at satt)"),
    source_coverage: str = Query(
        _DEFAULT_SOURCE_COVERAGE,
        pattern="^(complete|missing|all)$",
        description="Kildedekning 2020-2025 på tvers av GL + lønn: complete|missing|all",
    ),
    order_by: Optional[str] = Query(None, description="Felt å sortere på: name|address|city|region|usage"),
    order_dir: Optional[str] = Query("asc", description="Retning: asc|desc"),
    include_risk: bool = Query(True, description="Inkluder risk_assessments (sett false for raskere liste)"),
    region: Optional[str] = Query(
        None,
        description="Filtrer på region (kort format: Nord, Midt-Norge, Vest, Sør, Øst, Bufdir)",
    ),
):
    """Hent alle eiendommer (filtrert basert på tilgang)."""
    # Enforce max limit for performance
    safe_limit = min(limit, 10000)

    stmt = select(PropertyModel)
    if include_risk:
        stmt = stmt.options(selectinload(PropertyModel.risk_assessments))
    if not include_discontinued:
        stmt = stmt.where(PropertyModel.closed_at.is_(None))
    if usage:
        # Formålsbygg og Barnevernsinstitusjon er synonyme i usage-feltet
        if usage in ("Formålsbygg", "Barnevernsinstitusjon"):
            stmt = stmt.where(
                PropertyModel.usage.in_(["Formålsbygg", "Barnevernsinstitusjon"])
            )
        else:
            stmt = stmt.where(PropertyModel.usage == usage)
    if unit_short_type:
        stmt = stmt.where(PropertyModel.unit_short_type == unit_short_type)
    elif exclude_avdelinger:
        stmt = stmt.where(
            (PropertyModel.unit_short_type != "Avdeling") | PropertyModel.unit_short_type.is_(None)
        )
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            PropertyModel.name.ilike(like) | PropertyModel.address.ilike(like)
        )

    if region and str(region).strip():
        stmt = stmt.where(PropertyModel.region == str(region).strip())

    if source_coverage != "all":
        complete_cov_sq = complete_source_coverage_property_ids_subquery(2020, 2025)
        if source_coverage == "complete":
            stmt = stmt.where(PropertyModel.property_id.in_(select(complete_cov_sq.c.property_id)))
        elif source_coverage == "missing":
            stmt = stmt.where(~PropertyModel.property_id.in_(select(complete_cov_sq.c.property_id)))

    if order_by and order_by in _SORTABLE_COLUMNS:
        col = _SORTABLE_COLUMNS[order_by]
        stmt = stmt.order_by(col.desc() if order_dir == "desc" else col.asc())
    else:
        stmt = stmt.order_by(PropertyModel.name.asc())
    stmt = stmt.offset(skip).limit(safe_limit)
    result = await db.execute(stmt)
    all_properties = result.scalars().all()
    
    # Filter based on user access
    accessible_properties = await filter_properties_by_access(
        db=db,
        user=current_user,
        properties=list(all_properties)
    )

    party_map = await _primary_lease_party_by_property_ids(
        db, [p.property_id for p in accessible_properties]
    )

    # Resolve parent_property_id via ERP-ID (strategi 1)
    parent_erps = {p.parent_unit_id_erp for p in accessible_properties if p.parent_unit_id_erp}
    parent_map: dict = {}
    if parent_erps:
        parent_stmt = select(PropertyModel.unit_id_erp, PropertyModel.property_id).where(PropertyModel.unit_id_erp.in_(parent_erps))
        parent_res = await db.execute(parent_stmt)
        parent_map = {row[0]: str(row[1]) for row in parent_res.all() if row[0]}

    # Resolve parent_property_id via affiliation+region (strategi 2 fallback)
    # Bygger et oppslag: (affiliation, region) → property_id for institusjoner
    affil_region_map: dict = {}
    for p in accessible_properties:
        if (
            p.unit_short_type == "Barnevernsinstitusjon"
            and p.affiliation
            and p.region
        ):
            key = (p.affiliation.strip(), p.region.strip())
            # Hvis flere institusjoner har samme affiliation+region, velg den første
            if key not in affil_region_map:
                affil_region_map[key] = str(p.property_id)

    enriched_properties = []
    for p in accessible_properties:
        p_dict = {c.name: getattr(p, c.name) for c in p.__table__.columns}
        ext = p.external_data or {}

        # Managers
        if hasattr(p, "managers") and p.managers:
            p_dict["managers"] = [{"user_id": str(m.user_id), "name": m.name, "email": m.email} for m in p.managers]
        else:
            p_dict["managers"] = []

        # Use helper
        enrich_property_data(p_dict, ext, p)
        p_dict["bufdir_image_path"] = _bufdir_image_thumb(ext)
        p_dict["primary_lease_party_name"] = party_map.get(str(p.property_id))

        # Apply parent_property_id: strategi 1 (ERP-ID) → strategi 2 (affiliation+region)
        if p.parent_unit_id_erp and p.parent_unit_id_erp in parent_map:
            p_dict["parent_property_id"] = parent_map[p.parent_unit_id_erp]
        elif p.unit_short_type == "Avdeling" and p.affiliation and p.region:
            key = (p.affiliation.strip(), p.region.strip())
            if key in affil_region_map:
                p_dict["parent_property_id"] = affil_region_map[key]

        # Risk Level (Latest) – kun når include_risk=True for å unngå lazy load
        if include_risk and hasattr(p, "risk_assessments") and p.risk_assessments:
            latest_risk = max(p.risk_assessments, key=lambda r: r.assessment_date or datetime.min)
            if latest_risk and latest_risk.risk_category:
                p_dict["risk_level"] = latest_risk.risk_category.lower()

        enriched_properties.append(p_dict)
        
    return enriched_properties


@router.get("/usage-types", response_model=List[str])
async def get_usage_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Henter unike bruksformål (usage) for alle eiendommer.
    """
    query = select(PropertyModel.usage).where(PropertyModel.usage != None).distinct().order_by(PropertyModel.usage)
    result = await db.execute(query)
    types = [r[0] for r in result.all() if r[0]]
    return types


@router.get("/unit-short-types", response_model=List[str])
async def get_unit_short_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Henter unike enhetstyper (unit_short_type) for alle eiendommer.
    """
    query = select(PropertyModel.unit_short_type).where(PropertyModel.unit_short_type != None).distinct().order_by(PropertyModel.unit_short_type)
    result = await db.execute(query)
    types = [r[0] for r in result.all() if r[0]]
    return types


@router.get("/suggestions")
async def get_property_suggestions(
    q: str = Query("", min_length=2, description="Søkestreng (min 2 tegn)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returnerer opp til 8 eiendomsforslag for autocomplete-søk."""
    like = f"%{q}%"
    stmt = select(PropertyModel).where(
        PropertyModel.name.ilike(like) | PropertyModel.address.ilike(like)
    ).order_by(PropertyModel.name.asc()).limit(20)
    result = await db.execute(stmt)
    all_props = result.scalars().all()
    accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(all_props))
    return [
        {"property_id": str(p.property_id), "name": p.name or p.address or "", "address": p.address or ""}
        for p in accessible[:8]
    ]


def _norm_id(v):
    """Normalize department_code for matching (e.g. '1234.0' vs '1234')."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        return s[:-2]
    return s


@router.get("/gl-financial-bulk")
async def get_gl_financial_bulk(
    year: int = Query(..., description="År, f.eks. 2025"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer GL-finansdata for ALLE eiendommer i ett kall (bulk).
    Brukes av finanssiden for å unngå N+1 kall.
    Svar: { year, by_property: {...}, orphan_faktisk_husleie, orphan_andre_kostnader }
    Orphan = transaksjoner uten property_id og uten department_code match (unit_id_erp).
    Transaksjoner med department_code som matcher properties.unit_id_erp tilordnes eiendom.
    """
    from app.models.financial_models import GLTransaction
    from app.models.gl_constants import is_lease_account

    # Mapping department_code → property_id (unit_id_erp)
    dept_rows = (
        await db.execute(
            select(PropertyModel.unit_id_erp, PropertyModel.property_id).where(
                PropertyModel.unit_id_erp.isnot(None)
            )
        )
    ).fetchall()
    dept_to_prop: dict = {}
    for r in dept_rows:
        if r[0]:
            k = _norm_id(r[0])
            if k:
                dept_to_prop[k] = str(r[1])

    # 1. Per eiendom (property_id IS NOT NULL)
    stmt = (
        select(
            GLTransaction.property_id,
            GLTransaction.konto_navn,
            func.sum(GLTransaction.belop).label("total"),
        )
        .where(
            GLTransaction.ar == year,
            GLTransaction.property_id.isnot(None),
        )
        .group_by(GLTransaction.property_id, GLTransaction.konto_navn)
    )
    rows = (await db.execute(stmt)).all()

    result: dict = {}
    for row in rows:
        pid = str(row.property_id)
        if pid not in result:
            result[pid] = {"faktisk_husleie": 0.0, "andre_kostnader": 0.0, "totalt": 0.0}
        amount = float(row.total or 0)
        result[pid]["totalt"] += amount
        if is_lease_account(row.konto_navn):
            result[pid]["faktisk_husleie"] += amount
        else:
            result[pid]["andre_kostnader"] += amount

    # 2. Transaksjoner med property_id IS NULL – match via department_code = unit_id_erp
    orphan_stmt = (
        select(
            GLTransaction.dim1_kode,
            GLTransaction.konto_navn,
            func.sum(GLTransaction.belop).label("total"),
        )
        .where(
            GLTransaction.ar == year,
            GLTransaction.property_id.is_(None),
        )
        .group_by(GLTransaction.dim1_kode, GLTransaction.konto_navn)
    )
    orphan_rows = (await db.execute(orphan_stmt)).all()
    orphan_husleie = 0.0
    orphan_andre = 0.0
    for row in orphan_rows:
        amt = float(row.total or 0)
        dept = _norm_id(row.dim1_kode) if row.dim1_kode else None
        pid = dept_to_prop.get(dept) if dept else None
        if pid:
            if pid not in result:
                result[pid] = {"faktisk_husleie": 0.0, "andre_kostnader": 0.0, "totalt": 0.0}
            result[pid]["totalt"] += amt
            if is_lease_account(row.konto_navn):
                result[pid]["faktisk_husleie"] += amt
            else:
                result[pid]["andre_kostnader"] += amt
        else:
            if is_lease_account(row.konto_navn):
                orphan_husleie += amt
            else:
                orphan_andre += amt

    return {
        "year": year,
        "by_property": result,
        "orphan_faktisk_husleie": orphan_husleie,
        "orphan_andre_kostnader": orphan_andre,
    }


@router.get("/gl-totals-by-year")
async def get_gl_totals_by_year(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer total GL-beløp per år (alle år i databasen).
    Brukes av finanssiden for å vise historikk i Master regnskap-kortet.
    Svar: { by_year: { "2020": 123456.0, "2021": ..., ... } }
    """
    try:
        from app.models.financial_models import GLTransaction

        stmt = (
            select(
                GLTransaction.ar,
                func.sum(GLTransaction.belop).label("total"),
            )
            .where(GLTransaction.ar.isnot(None))
            .group_by(GLTransaction.ar)
            .order_by(GLTransaction.ar)
        )
        rows = (await db.execute(stmt)).all()
        by_year = {str(int(r.ar)): float(r.total or 0) for r in rows}
        return {"by_year": by_year}
    except Exception as e:
        logger.debug("gl-totals-by-year error: %s", e)
        return {"by_year": {}}


@router.get("/gl-account-totals")
async def get_gl_account_totals(
    year: int = Query(2025, description="År, f.eks. 2025"),
    limit: int = Query(30, ge=5, le=100, description="Antall største kontoer i listen"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Global GL-oppsummering per kontonavn for et år (kostnadskilde-analyse).
    Returnerer total, husleie vs øvrige (is_lease_account), og topp kontoer sortert på beløp.
    """
    try:
        from app.models.financial_models import GLTransaction
        from app.models.gl_constants import is_lease_account

        stmt = (
            select(
                GLTransaction.konto_navn,
                func.sum(GLTransaction.belop).label("total"),
            )
            .where(
                GLTransaction.ar == year,
                GLTransaction.belop > 0,
            )
            .group_by(GLTransaction.konto_navn)
        )
        rows = (await db.execute(stmt)).all()

        by_account: list[dict] = []
        total_amount = 0.0
        total_faktisk_husleie = 0.0

        for row in rows:
            name = (row.konto_navn or "").strip() or "(Ukjent konto)"
            amt = float(row.total or 0)
            total_amount += amt
            is_lease = is_lease_account(row.konto_navn)
            if is_lease:
                total_faktisk_husleie += amt
            by_account.append(
                {
                    "account_name": name,
                    "amount": amt,
                    "is_lease": is_lease,
                }
            )

        by_account.sort(key=lambda x: x["amount"], reverse=True)
        top_accounts = by_account[:limit]

        return {
            "year": year,
            "total_amount": total_amount,
            "total_faktisk_husleie": total_faktisk_husleie,
            "total_andre_kostnader": total_amount - total_faktisk_husleie,
            "account_count": len(by_account),
            "top_accounts": top_accounts,
        }
    except Exception as e:
        logger.debug("gl-account-totals error: %s", e)
        return {
            "year": year,
            "total_amount": 0.0,
            "total_faktisk_husleie": 0.0,
            "total_andre_kostnader": 0.0,
            "account_count": 0,
            "top_accounts": [],
        }


@router.get("/institutions")
async def get_institutions(
    year: int = Query(default=2025, ge=2020, le=2035),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer alle barnevernsinstitusjoner med kapasitetsdata (GK-plasser og budsjetterte plasser).
    Filtrerer på unit_type_derived = 'Barnevernsinstitusjon' ELLER approved_places > 0.
    Svar: { institutions: [ { property_id, name, region, approved_places, budgeted_places,
                               affiliation, unit_type_derived, department_code, closed_at,
                               annual_cost, address } ] }
    """
    try:
        rows = (await db.execute(text("""
            SELECT
                p.property_id,
                p.name,
                p.address,
                p.region,
                p.approved_places,
                p.budgeted_places,
                p.affiliation,
                p.unit_type_derived,
                p.department_code,
                p.closed_at,
                p.unit_id_erp
            FROM properties p
            WHERE
                (p.unit_type_derived = 'Barnevernsinstitusjon'
                 OR p.unit_type_derived = 'Institusjonsavdeling'
                 OR (p.approved_places IS NOT NULL AND p.approved_places > 0))
            ORDER BY p.region, p.name
        """))).fetchall()

        # Hent GL 2025-kostnader per property for kostnad-per-plass
        cost_rows = (await db.execute(text("""
            SELECT property_id, SUM(belop) AS total
            FROM gl_transactions
            WHERE ar = :yr AND property_id IS NOT NULL
            GROUP BY property_id
        """), {"yr": year})).fetchall()
        costs_by_pid = {str(r.property_id): float(r.total or 0) for r in cost_rows}

        institutions = []
        for r in rows:
            pid = str(r.property_id)
            ap = r.approved_places or 0
            annual_cost = costs_by_pid.get(pid, 0)
            cost_per_place = round(annual_cost / ap, 0) if ap > 0 and annual_cost > 0 else None
            institutions.append({
                "property_id": pid,
                "name": r.name,
                "address": r.address,
                "region": r.region,
                "approved_places": r.approved_places,
                "budgeted_places": r.budgeted_places,
                "affiliation": r.affiliation,
                "unit_type_derived": r.unit_type_derived,
                "department_code": r.department_code,
                "closed_at": str(r.closed_at) if r.closed_at else None,
                "unit_id_erp": r.unit_id_erp,
                "annual_cost_2025": round(annual_cost, 0) if annual_cost else None,
                "cost_per_place": cost_per_place,
            })

        # Regionsoppsummering
        by_region: dict = {}
        for inst in institutions:
            reg = inst["region"] or "Ukjent"
            if reg not in by_region:
                by_region[reg] = {"count": 0, "approved_places": 0, "budgeted_places": 0}
            by_region[reg]["count"] += 1
            by_region[reg]["approved_places"] += inst["approved_places"] or 0
            by_region[reg]["budgeted_places"] += inst["budgeted_places"] or 0

        return {
            "institutions": institutions,
            "by_region": by_region,
            "total_approved_places": sum(i["approved_places"] or 0 for i in institutions),
            "total_budgeted_places": sum(i["budgeted_places"] or 0 for i in institutions),
            "total_count": len(institutions),
        }
    except Exception as e:
        logger.debug("institutions endpoint error: %s", e)
        return {"institutions": [], "by_region": {}, "total_approved_places": 0, "total_budgeted_places": 0, "total_count": 0}


@router.get("/innkjoepsanalyse-husleie")
async def get_innkjoepsanalyse_husleie(
    year: int = Query(2025, description="År, f.eks. 2025"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer Kontraktsfestet husleie fra Innkjøpsanalyse-CSV per eiendom.
    by_property: { property_id: { by_region: { region: amount }, aggregert: number } }
    total: sum over alle eiendommer.
    """
    from app.domains.core.models.property_husleie_csv import PropertyHusleieCsv

    props_result = await db.execute(select(PropertyModel))
    all_props = props_result.scalars().all()
    accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(all_props))
    acc_ids = [p.property_id for p in accessible]

    stmt = (
        select(PropertyHusleieCsv.property_id, PropertyHusleieCsv.region, PropertyHusleieCsv.amount)
        .where(PropertyHusleieCsv.year == year, PropertyHusleieCsv.property_id.in_(acc_ids))
    )
    rows = (await db.execute(stmt)).all()

    by_property: dict = {}
    for pid, region, amount in rows:
        pid_str = str(pid)
        if pid_str not in by_property:
            by_property[pid_str] = {"by_region": {}, "aggregert": 0.0}
        amt = float(amount or 0)
        # Sum per region (unngår dobbeltelling hvis flere rader for samme property+region)
        by_property[pid_str]["by_region"][region] = by_property[pid_str]["by_region"].get(region, 0.0) + amt
        by_property[pid_str]["aggregert"] += amt

    total = sum(p["aggregert"] for p in by_property.values())
    return {"year": year, "by_property": by_property, "total": int(round(total))}


@router.get("/godkjente-eiendommer")
async def get_godkjente_eiendommer(
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer listen over godkjente eiendommer og avdelinger (referansedata for UTGÅTT-badge).
    """
    from pathlib import Path

    data_dir = Path(__file__).resolve().parents[4] / "data"
    json_path = data_dir / "godkjente_eiendommer_avdelinger.json"
    if not json_path.exists():
        return []
    try:
        import json
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Kunne ikke lese godkjente_eiendommer_avdelinger: %s", e)
        return []


@router.get("/total-kost-per-region")
async def get_total_kost_per_region(
    year: int = Query(2025, description="År, f.eks. 2025"),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer Total kost per region og kategori fra Innkjøpsanalyse-import.
    Leser fra backend/data/total_kost_per_region_{year}.json (opprettes ved import).
    """
    from pathlib import Path

    data_dir = Path(__file__).resolve().parents[4] / "data"
    json_path = data_dir / f"total_kost_per_region_{year}.json"
    if not json_path.exists():
        return {"year": year, "by_category": {}}
    try:
        import json
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        return {"year": data.get("year", year), "by_category": data.get("by_category", {})}
    except Exception as e:
        logger.warning("Kunne ikke lese total_kost_per_region: %s", e)
        return {"year": year, "by_category": {}}


@router.get("/without-costs")
async def get_properties_without_costs(
    year: int = Query(2025, description="År for GL-data, f.eks. 2025"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer eiendommer som mangler kostnadsdata (GL) for valgt år.
    Eiendom har kostnader hvis: property_id i gl_transactions ELLER unit_id_erp = department_code i gl_transactions.
    """
    result = await db.execute(select(PropertyModel))
    all_props = result.scalars().all()
    accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(all_props))

    gl_prop = await db.execute(text("""
        SELECT property_id::text, SUM(belop) FROM gl_transactions
        WHERE ar = :yr AND belop > 0 AND property_id IS NOT NULL
        GROUP BY property_id
    """), {"yr": year})
    total_by_prop = {row[0]: float(row[1] or 0) for row in gl_prop.fetchall()}

    gl_dept = await db.execute(text("""
        SELECT dim1_kode, SUM(belop) FROM gl_transactions
        WHERE ar = :yr AND belop > 0 AND dim1_kode IS NOT NULL
        GROUP BY dim1_kode
    """), {"yr": year})
    total_by_dept = {str(row[0]): float(row[1] or 0) for row in gl_dept.fetchall()}

    without_costs = []
    for p in accessible:
        pid = str(p.property_id)
        total = total_by_prop.get(pid, 0)
        if total <= 0 and p.unit_id_erp:
            total += total_by_dept.get(str(p.unit_id_erp), 0)
        if total <= 0:
            without_costs.append({
                "property_id": pid,
                "name": p.name or p.address or "-",
                "address": p.address or "",
                "region": p.region or "",
                "unit_id_erp": p.unit_id_erp,
                "unit_short_type": p.unit_short_type,
            })

    return {"year": year, "properties": without_costs, "count": len(without_costs)}


@router.get("/discontinued-properties")
async def get_discontinued_properties(
    budget_year: int = Query(2025, description="Budsjettår, f.eks. 2025"),
    cost_year: Optional[int] = Query(None, description="År for GL-kostnader. Bruker budsjettår hvis ikke satt"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer eiendommer som ikke finnes i budsjettgrunnlaget for valgt år.
    Brukes til visning av "Avviklet eiendom" i datakvalitet.
    """
    effective_cost_year = cost_year or budget_year

    result = await db.execute(select(PropertyModel))
    all_props = result.scalars().all()
    accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(all_props))

    budget_property_ids: set[str] = set()
    budget_available = True
    try:
        budget_rows = await db.execute(text("""
            SELECT CAST(property_id AS TEXT)
            FROM budget
            WHERE year = :yr
            GROUP BY property_id
            HAVING SUM(amount) > 0
        """), {"yr": budget_year})
        budget_property_ids = {str(r[0]) for r in budget_rows.fetchall() if r and r[0]}
    except Exception as e:
        budget_available = False
        logger.warning("Kunne ikke lese budget-tabell for avviklet eiendom: %s", e)

    gl_prop = await db.execute(text("""
        SELECT CAST(property_id AS TEXT), SUM(belop) FROM gl_transactions
        WHERE ar = :yr AND belop > 0 AND property_id IS NOT NULL
        GROUP BY property_id
    """), {"yr": effective_cost_year})
    total_by_prop = {row[0]: float(row[1] or 0) for row in gl_prop.fetchall()}

    gl_dept = await db.execute(text("""
        SELECT dim1_kode, SUM(belop) FROM gl_transactions
        WHERE ar = :yr AND belop > 0 AND dim1_kode IS NOT NULL
        GROUP BY dim1_kode
    """), {"yr": effective_cost_year})
    total_by_dept = {str(row[0]): float(row[1] or 0) for row in gl_dept.fetchall()}

    discontinued = []
    for p in accessible:
        pid = str(p.property_id)
        if budget_available and pid in budget_property_ids:
            continue

        total_cost = total_by_prop.get(pid, 0)
        if total_cost <= 0 and p.unit_id_erp:
            total_cost += total_by_dept.get(str(p.unit_id_erp), 0)

        # "Avviklet" skal være uten aktivitet i året, ikke bare uten budsjett.
        if total_cost > 0:
            continue

        discontinued.append({
            "property_id": pid,
            "name": p.name or p.address or "-",
            "address": p.address or "",
            "region": p.region or "",
            "unit_id_erp": p.unit_id_erp,
            "unit_short_type": p.unit_short_type,
            "has_costs_in_year": False,
            "total_cost_in_year": total_cost,
        })

    return {
        "budget_year": budget_year,
        "cost_year": effective_cost_year,
        "budget_available": budget_available,
        "properties": discontinued,
        "count": len(discontinued),
    }


@router.get("/costs-without-property")
async def get_costs_without_property(
    year: int = Query(2025, description="År for GL-data, f.eks. 2025"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer koststeder (department_code) fra GL som har kostnader men ingen tilknyttet eiendom.
    Koststed har eiendom hvis: noen property.unit_id_erp = department_code ELLER property.department_code = department_code.
    """
    # Koststeder fra GL med sum(amount) for året – kun transaksjoner uten property_id (uassigned)
    gl_result = await db.execute(text("""
        SELECT g.dim1_kode, g.dim1_navn, SUM(g.belop) as total, COUNT(*) as tx_count
        FROM gl_transactions g
        WHERE g.ar = :yr AND g.belop > 0 AND g.dim1_kode IS NOT NULL
          AND g.property_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM properties p
              WHERE p.unit_id_erp = g.dim1_kode
                 OR p.department_code = g.dim1_kode
          )
        GROUP BY g.dim1_kode, g.dim1_navn
        HAVING SUM(g.belop) > 0
        ORDER BY SUM(g.belop) DESC
    """), {"yr": year})
    rows = gl_result.fetchall()

    orphan = []
    for r in rows:
        dim1 = str(r[0]) if r[0] else None
        if dim1:
            orphan.append({
                "department_code": dim1,
                "department_name": r[1] or "",
                "total": float(r[2] or 0),
                "transaction_count": int(r[3] or 0),
            })

    total_orphan = sum(x["total"] for x in orphan)
    return {
        "year": year,
        "cost_centers": orphan,
        "count": len(orphan),
        "total_amount": total_orphan,
    }


# Region-rekkefølge for pivot (samme som procurement)
_REGION_ORDER = ["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir", "Øvrig"]
_REGION_MAP = {
    "midt": "Midt-Norge",
    "midt-norge": "Midt-Norge",
    "nord": "Nord",
    "sør": "Sør",
    "vest": "Vest",
    "øst": "Øst",
    "bufdir": "Bufdir",
}


def _normalize_region(raw: Optional[str]) -> str:
    if not raw:
        return "Øvrig"
    return _REGION_MAP.get((raw or "").strip().lower(), (raw or "").strip() or "Øvrig")


@router.get("/costs-without-property-pivot")
async def get_costs_without_property_pivot(
    year: int = Query(2025, description="År for GL-data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pivot over koststeder uten eiendom: koststed × region.
    Samme data som costs-without-property, men med region-kolonner.
    """
    gl_result = await db.execute(text("""
        SELECT g.dim1_kode, g.dim1_navn, g.region, SUM(g.belop) as total
        FROM gl_transactions g
        WHERE g.ar = :yr AND g.belop > 0 AND g.dim1_kode IS NOT NULL
          AND g.property_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM properties p
              WHERE p.unit_id_erp = g.dim1_kode
                 OR p.department_code = g.dim1_kode
          )
        GROUP BY g.dim1_kode, g.dim1_navn, g.region
        HAVING SUM(g.belop) > 0
        ORDER BY g.dim1_kode, g.region
    """), {"yr": year})
    rows = gl_result.fetchall()

    by_dept: dict = {}
    for r in rows:
        dept_code = str(r[0]) if r[0] else ""
        dept_name = (r[1] or "").strip()
        region = _normalize_region(r[2])
        amount = float(r[3] or 0)
        if dept_code not in by_dept:
            by_dept[dept_code] = {"department_name": dept_name, "by_region": {}}
        by_dept[dept_code]["by_region"][region] = by_dept[dept_code]["by_region"].get(region, 0) + amount

    total_by_region = {}
    pivot_rows = []
    for dept_code in sorted(by_dept, key=lambda k: -sum(by_dept[k]["by_region"].values())):
        d = by_dept[dept_code]
        row_total = sum(d["by_region"].values())
        by_region_fmt = {r: int(round(d["by_region"].get(r, 0))) for r in _REGION_ORDER}
        for r, amt in d["by_region"].items():
            total_by_region[r] = total_by_region.get(r, 0) + amt
        pivot_rows.append({
            "department_code": dept_code,
            "department_name": d["department_name"],
            "institution": f"{dept_code} - {d['department_name']}",
            "by_region": by_region_fmt,
            "total": int(round(row_total)),
        })

    total_by_region_fmt = {r: int(round(total_by_region.get(r, 0))) for r in _REGION_ORDER}
    grand_total = sum(total_by_region.values())

    return {
        "year": year,
        "regions": _REGION_ORDER,
        "groups": [{
            "group": "Koststeder uten eiendom",
            "categories": [{
                "key": "orphan",
                "label": "Alle kostnader",
                "rows": pivot_rows,
                "totals_by_region": total_by_region_fmt,
                "grand_total": int(round(grand_total)),
            }],
        }],
    }


@router.get("/contracts-pivot")
async def get_contracts_pivot(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pivot over kontraktsdata: region × utleier med kontraktsleie.
    Bruker aktive kontrakter fra contracts + parties.
    """
    props_result = await db.execute(select(PropertyModel))
    all_props = props_result.scalars().all()
    accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(all_props))
    acc_ids = [p.property_id for p in accessible]

    result = await db.execute(
        select(
            PropertyModel.property_id,
            PropertyModel.region,
            PropertyModel.external_data,
            ContractModel.amount,
            PartyModel.name.label("party_name"),
        )
        .join(UnitModel, UnitModel.property_id == PropertyModel.property_id)
        .join(ContractModel, ContractModel.unit_id == UnitModel.unit_id)
        .outerjoin(PartyModel, ContractModel.party_id == PartyModel.party_id)
        .where(ContractModel.status == "active", PropertyModel.property_id.in_(acc_ids))
    )
    rows = result.all()

    def _norm_region(reg: Optional[str], ext: dict) -> str:
        if ext and (ext.get("bufdir") or ext.get("bufdir_institution")):
            return "Bufdir"
        if not reg:
            return "Øvrig"
        r = (reg or "").lower()
        if "nord" in r or r.startswith("01"): return "Nord"
        if "midt" in r or "trønd" in r or "møre" in r: return "Midt-Norge"
        if "vest" in r and "vestfold" not in r: return "Vest"
        if "sør" in r or "agder" in r or "telemark" in r or "vestfold" in r: return "Sør"
        if "øst" in r or "oslo" in r or "viken" in r or "innlandet" in r: return "Øst"
        return reg or "Øvrig"

    by_region_utleier: dict = {}
    for r in rows:
        pid, region, ext, amount, party_name = r
        reg = _norm_region(region, ext or {})
        utleier = (party_name or "(ukjent)").strip()
        amt = 0.0
        if amount and isinstance(amount, dict):
            amt = float(amount.get("amount_per_year") or 0)
        key = (reg, utleier)
        by_region_utleier[key] = by_region_utleier.get(key, 0) + amt

    region_order = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst", "Bufdir", "Øvrig"]
    utleiere = sorted({u for _, u in by_region_utleier})
    pivot_rows = []
    for reg in region_order:
        row = {"region": reg, "by_utleier": {}, "total": 0}
        for u in utleiere:
            val = by_region_utleier.get((reg, u), 0)
            if val > 0:
                row["by_utleier"][u] = int(round(val))
                row["total"] += val
        if row["total"] > 0:
            pivot_rows.append({**row, "total": int(round(row["total"]))})

    totals_by_utleier = {u: sum(by_region_utleier.get((r, u), 0) for r in region_order) for u in utleiere}
    grand_total = sum(by_region_utleier.values())

    return {
        "regions": region_order,
        "utleiere": utleiere,
        "rows": pivot_rows,
        "totals_by_utleier": {u: int(round(totals_by_utleier[u])) for u in utleiere if totals_by_utleier[u] > 0},
        "grand_total": int(round(grand_total)),
    }


@router.get("/contracts-pivot-raw")
async def get_contracts_pivot_raw(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rå kontraktsdata for client-side pivot. Returnerer flat liste med region, utleier,
    eiendom og årsleie slik at frontend kan bygge dynamiske pivot-tabeller.
    """
    props_result = await db.execute(select(PropertyModel))
    all_props = props_result.scalars().all()
    accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(all_props))
    acc_ids = [p.property_id for p in accessible]

    result = await db.execute(
        select(
            PropertyModel.region,
            PropertyModel.external_data,
            PropertyModel.name.label("property_name"),
            PropertyModel.address.label("property_address"),
            PropertyModel.lokalisering_id,
            ContractModel.amount,
            PartyModel.name.label("party_name"),
        )
        .join(UnitModel, UnitModel.property_id == PropertyModel.property_id)
        .join(ContractModel, ContractModel.unit_id == UnitModel.unit_id)
        .outerjoin(PartyModel, ContractModel.party_id == PartyModel.party_id)
        .where(ContractModel.status == "active", PropertyModel.property_id.in_(acc_ids))
    )
    rows = result.all()

    def _norm_region(reg: Optional[str], ext: dict) -> str:
        if ext and (ext.get("bufdir") or ext.get("bufdir_institution")):
            return "Bufdir"
        if not reg:
            return "Øvrig"
        r = (reg or "").lower()
        if "nord" in r or r.startswith("01"): return "Nord"
        if "midt" in r or "trønd" in r or "møre" in r: return "Midt-Norge"
        if "vest" in r and "vestfold" not in r: return "Vest"
        if "sør" in r or "agder" in r or "telemark" in r or "vestfold" in r: return "Sør"
        if "øst" in r or "oslo" in r or "viken" in r or "innlandet" in r: return "Øst"
        return reg or "Øvrig"

    records = []
    for r in rows:
        region, ext, prop_name, prop_addr, lok_id, amount, party_name = r
        reg = _norm_region(region, ext or {})
        utleier = (party_name or "(ukjent)").strip()
        eiendom = (prop_name or prop_addr or lok_id or "(ukjent)").strip()
        amt = 0.0
        if amount and isinstance(amount, dict):
            amt = float(amount.get("amount_per_year") or 0)
        records.append({
            "region": reg,
            "utleier": utleier,
            "eiendom": eiendom,
            "amount_per_year": round(amt, 2),
        })
    return {"records": records}


@router.get("/orphan-transactions")
async def get_orphan_transactions(
    department_code: str = Query(..., description="Koststedskode, f.eks. 204416"),
    year: int = Query(2025, description="År"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer enkelttransaksjoner for et koststed uten eiendom.
    Brukes for drill-down fra Kostnader uten eiendom.
    """
    rows = await db.execute(text("""
        SELECT transaction_id, periode, konto_navn, leverandor_navn, dim2_navn, belop, bilagsnummer
        FROM gl_transactions
        WHERE dim1_kode = :dept AND ar = :yr AND belop > 0
        ORDER BY belop DESC
        LIMIT :lim OFFSET :off
    """), {"dept": department_code, "yr": year, "lim": limit, "off": skip})
    transactions = []
    for r in rows.fetchall():
        transactions.append({
            "transaction_id": str(r[0]) if r[0] else None,
            "period": r[1],
            "account_name": r[2] or "",
            "supplier_name": r[3] or "",
            "dim2_name": r[4] or "",
            "amount": float(r[5] or 0),
            "invoice_number": r[6] or "",
        })
    total_result = await db.execute(text("""
        SELECT COUNT(*), COALESCE(SUM(belop), 0) FROM gl_transactions
        WHERE dim1_kode = :dept AND ar = :yr AND belop > 0
    """), {"dept": department_code, "yr": year})
    tot = total_result.fetchone()
    total_count = int(tot[0] or 0)
    total_amount = float(tot[1] or 0)
    return {
        "department_code": department_code,
        "year": year,
        "transactions": transactions,
        "total_count": total_count,
        "total_amount": total_amount,
        "skip": skip,
        "limit": limit,
    }


@router.post("/refresh-all-proximity")
async def refresh_all_proximity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Oppdater proximity (nærliggende tjenester) for alle eiendommer som har koordinater.
    Brukes for å sikre at Nærliggende Tjenester vises for alle eiendommer.
    Krever innlogging. Rate-limited mot OSM – kan ta tid ved mange eiendommer.
    """
    from app.services.proximity.service import ProximityService
    import asyncio

    # Kun admin eller eiere bør kunne kjøre dette (valgfritt: legg til role-check)
    stmt = select(PropertyModel).where(
        PropertyModel.latitude.isnot(None),
        PropertyModel.longitude.isnot(None),
    )
    result = await db.execute(stmt)
    properties = result.scalars().all()

    # Filtrer på tilgang slik at bruker ikke oppdaterer eiendommer de ikke har tilgang til
    accessible = await filter_properties_by_access(db=db, user=current_user, properties=list(properties))

    service = ProximityService(db)
    updated = 0
    errors = []

    for prop in accessible:
        try:
            await service.fetch_proximity_services(
                prop.property_id,
                float(prop.latitude),
                float(prop.longitude),
                force_refresh=True,
            )
            updated += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            errors.append({"property_id": str(prop.property_id), "error": str(e)})

    return {
        "updated": updated,
        "total_with_coords": len(accessible),
        "errors": errors[:20],
    }


class PropertyMapMarker(BaseModel):
    """Minimal eiendomsdata for kartvisning."""
    property_id: str
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@router.get("/map-markers", response_model=List[PropertyMapMarker])
async def get_property_map_markers(
    limit: int = Query(500, ge=1, le=2000, description="Maks antall markører"),
    include_discontinued: bool = Query(False, description="Inkluder avviklede eiendommer (closed_at satt)"),
    source_coverage: str = Query(
        _DEFAULT_SOURCE_COVERAGE,
        pattern="^(complete|missing|all)$",
        description="Kildedekning 2020-2025 på tvers av GL + lønn: complete|missing|all",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent lette eiendomsmarkører for kart (kun id, navn, adresse, koordinater).
    Reduserer last vs. full get_properties for dashboard-kartet.
    """
    accessible_ids = await get_user_accessible_property_ids(db, current_user)

    stmt = (
        select(
            PropertyModel.property_id,
            PropertyModel.name,
            PropertyModel.address,
            PropertyModel.latitude,
            PropertyModel.longitude,
        )
        .where(PropertyModel.latitude.isnot(None))
        .where(PropertyModel.longitude.isnot(None))
    )
    if not include_discontinued:
        stmt = stmt.where(PropertyModel.closed_at.is_(None))

    if source_coverage != "all":
        complete_cov_sq = complete_source_coverage_property_ids_subquery(2020, 2025)
        if source_coverage == "complete":
            stmt = stmt.where(PropertyModel.property_id.in_(select(complete_cov_sq.c.property_id)))
        elif source_coverage == "missing":
            stmt = stmt.where(~PropertyModel.property_id.in_(select(complete_cov_sq.c.property_id)))

    if accessible_ids is not None:
        stmt = stmt.where(PropertyModel.property_id.in_(accessible_ids))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    return [
        PropertyMapMarker(
            property_id=str(r.property_id),
            name=r.name,
            address=r.address,
            latitude=r.latitude,
            longitude=r.longitude,
        )
        for r in rows
    ]


@router.get("/{property_id}/annual-costs")
async def get_property_annual_costs(
    property_id: str,
    year: int = Query(..., description="År, f.eks. 2025"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Henter PropertyAnnualCost-rader for en eiendom og et gitt år."""
    from app.domains.core.models.property_annual_cost import PropertyAnnualCost

    try:
        uuid_obj = UUID(property_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig property_id")

    await check_property_access(db=db, user=current_user, property_id=property_id)

    stmt = select(PropertyAnnualCost).where(
        PropertyAnnualCost.property_id == uuid_obj,
        PropertyAnnualCost.year == year,
    ).order_by(PropertyAnnualCost.created_at.asc())
    result = await db.execute(stmt)
    costs = result.scalars().all()

    return [
        {
            "property_annual_cost_id": str(c.property_annual_cost_id),
            "year": c.year,
            "kpi_adjusted_rent": c.kpi_adjusted_rent,
            "internal_maintenance": c.internal_maintenance,
            "common_costs": c.common_costs,
            "energy_costs": c.energy_costs,
            "heating_costs": c.heating_costs,
            "cleaning_costs": c.cleaning_costs,
            "parking_rent": c.parking_rent,
            "caretaker_cost": c.caretaker_cost,
            "card_reader_cost": c.card_reader_cost,
            "other_costs": c.other_costs,
        }
        for c in costs
    ]


@router.get("/{property_id}/financial-summary")
async def get_financial_summary(
    property_id: str,
    year: int = Query(..., description="År, f.eks. 2025"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregerer GL-transaksjoner per eiendom og år fra regnskapssystemet.
    Returnerer faktisk husleie (leieposter) og andre bokførte kostnader.
    """
    from app.models.financial_models import GLTransaction

    try:
        uuid_obj = UUID(property_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig property_id")

    await check_property_access(db=db, user=current_user, property_id=property_id)

    # Hent koststed for denne eiendommen (for å matche via department_code i tillegg til property_id)
    prop_result = await db.execute(
        select(PropertyModel).where(PropertyModel.property_id == uuid_obj)
    )
    prop = prop_result.scalar_one_or_none()
    koststed = prop.department_code if prop else None

    # Bygg filter: match på property_id ELLER department_code (koststed)
    filters = [GLTransaction.ar == year]
    id_conditions = [GLTransaction.property_id == uuid_obj]
    if koststed:
        id_conditions.append(GLTransaction.dim1_kode == koststed)
    filters.append(or_(*id_conditions))

    stmt = (
        select(GLTransaction.konto_navn, func.sum(GLTransaction.belop).label("total"))
        .where(*filters)
        .group_by(GLTransaction.konto_navn)
    )
    rows = (await db.execute(stmt)).all()

    from app.models.gl_constants import is_lease_account
    faktisk_husleie = sum(r.total or 0 for r in rows if is_lease_account(r.konto_navn))
    alle_kostnader = sum(r.total or 0 for r in rows)
    andre_kostnader = alle_kostnader - faktisk_husleie

    return {
        "year": year,
        "faktisk_husleie": faktisk_husleie,
        "andre_kostnader": andre_kostnader,
        "totalt": alle_kostnader,
        "kategorier": {r.konto_navn: round(r.total or 0, 2) for r in rows},
        "har_data": len(rows) > 0,
    }


@router.get("/{property_id}/gl-costs")
async def get_gl_costs(
    property_id: str,
    year: Optional[int] = Query(None, description="Filtrer på år (valgfritt)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GL-kostnader per eiendom gruppert: år → underkategori → konto + leverandører.
    Brukes av LøpendeKostnaderCard (accordion per underkategori per år).
    """
    from app.models.financial_models import GLTransaction

    try:
        uuid_obj = UUID(property_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig property_id")

    await check_property_access(db=db, user=current_user, property_id=property_id)

    prop_result = await db.execute(
        select(PropertyModel).where(PropertyModel.property_id == uuid_obj)
    )
    prop = prop_result.scalar_one_or_none()

    # Hent alle koststed-koder koblet til denne eiendommen via koststed_mapping
    from app.models.financial_models import KoststedMapping
    km_result = await db.execute(
        select(KoststedMapping.koststed_kode).where(
            KoststedMapping.property_id == uuid_obj
        )
    )
    koststed_koder = [r[0] for r in km_result.all()]

    try:
        # Bygg filter: property_id (direkte koblet) ELLER dim1_kode via koststed_mapping
        id_conditions = [GLTransaction.property_id == uuid_obj]
        if koststed_koder:
            id_conditions.append(GLTransaction.dim1_kode.in_(koststed_koder))
        base_filter = [or_(*id_conditions)]
        if year:
            base_filter.append(GLTransaction.ar == year)

        # Tilgjengelige år
        years_stmt = (
            select(GLTransaction.ar)
            .where(*base_filter)
            .where(GLTransaction.ar.isnot(None))
            .distinct()
            .order_by(GLTransaction.ar)
        )
        available_years = [r[0] for r in (await db.execute(years_stmt)).all()]

        # Aggreger: år, underkategori, konto, leverandør
        agg_stmt = (
            select(
                GLTransaction.ar,
                GLTransaction.srs_kategori,
                GLTransaction.konto,
                GLTransaction.konto_navn,
                GLTransaction.leverandor_navn,
                func.sum(GLTransaction.belop).label("total"),
            )
            .where(*base_filter)
            .group_by(
                GLTransaction.ar,
                GLTransaction.srs_kategori,
                GLTransaction.konto,
                GLTransaction.konto_navn,
                GLTransaction.leverandor_navn,
            )
            .order_by(GLTransaction.ar)
        )
        rows = (await db.execute(agg_stmt)).all()

        # Bygg responstreet: år → underkategori → konto → leverandør
        by_year: dict = {}
        for r in rows:
            yr = str(r.ar) if r.ar else "ukjent"
            cat = r.srs_kategori or "Ukategorisert"
            acc_code = r.konto or ""
            acc_name = r.konto_navn or r.konto or "Ukjent konto"
            vendor = r.leverandor_navn or "Ukjent leverandør"
            total = float(r.total or 0)

            yr_data = by_year.setdefault(yr, {"total": 0.0, "_subcats": {}})
            yr_data["total"] += total

            subcat = yr_data["_subcats"].setdefault(cat, {"name": cat, "total": 0.0, "_accounts": {}})
            subcat["total"] += total

            acc_key = f"{acc_code}|{acc_name}"
            acc = subcat["_accounts"].setdefault(
                acc_key,
                {"code": acc_code, "name": acc_name, "total": 0.0, "_vendors": {}},
            )
            acc["total"] += total
            acc["_vendors"][vendor] = acc["_vendors"].get(vendor, 0.0) + total

        # Konverter til liste-struktur (sorter subcats etter total DESC)
        result_by_year: dict = {}
        for yr, yr_data in by_year.items():
            subcats = []
            for cat_data in sorted(yr_data["_subcats"].values(), key=lambda x: x["total"], reverse=True):
                accounts = []
                for acc_data in sorted(cat_data["_accounts"].values(), key=lambda x: x["total"], reverse=True):
                    vendors = [
                        {"name": k, "total": round(v, 2)}
                        for k, v in sorted(acc_data["_vendors"].items(), key=lambda x: x[1], reverse=True)
                    ]
                    accounts.append({
                        "code": acc_data["code"],
                        "name": acc_data["name"],
                        "total": round(acc_data["total"], 2),
                        "vendors": vendors,
                    })
                subcats.append({
                    "name": cat_data["name"],
                    "total": round(cat_data["total"], 2),
                    "accounts": accounts,
                })
            result_by_year[yr] = {
                "total": round(yr_data["total"], 2),
                "subcategories": subcats,
            }

        return {
            "available_years": available_years,
            "by_year": result_by_year,
        }
    except Exception as e:
        logger.debug("gl-costs feil for %s: %s", property_id, e)
        return {"available_years": [], "by_year": {}}


@router.get("/{property_id}/gl-costs-by-dim4")
async def get_gl_costs_by_dim4(
    property_id: str,
    year: int = Query(..., description="Regnskapsår"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    GL-kostnader per eiendom aggregert på Dim4 (tildelingsbrev / finansiering), kapittelpost-visning.
    Samme property/koststed-filter som /gl-costs.
    """
    from app.models.financial_models import GLTransaction, KoststedMapping

    try:
        uuid_obj = UUID(property_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig property_id")

    await check_property_access(db=db, user=current_user, property_id=property_id)

    km_result = await db.execute(
        select(KoststedMapping.koststed_kode).where(
            KoststedMapping.property_id == uuid_obj
        )
    )
    koststed_koder = [r[0] for r in km_result.all()]

    id_conditions = [GLTransaction.property_id == uuid_obj]
    if koststed_koder:
        id_conditions.append(GLTransaction.dim1_kode.in_(koststed_koder))
    base_filter = [
        or_(*id_conditions),
        GLTransaction.ar == year,
    ]

    try:
        agg_stmt = (
            select(
                GLTransaction.dim4_kode,
                func.sum(GLTransaction.belop).label("total"),
            )
            .where(*base_filter)
            .group_by(GLTransaction.dim4_kode)
        )
        rows = (await db.execute(agg_stmt)).all()

        out_rows = []
        grand = 0.0
        for r in rows:
            t = float(r.total or 0)
            grand += t
            code = (r.dim4_kode or "").strip() or None
            if not code:
                label_name = "Ukjent Dim4"
            else:
                label_name = code
            out_rows.append({
                "dim4_kode": code,
                "dim4_navn": label_name,
                "total": round(t, 2),
            })
        out_rows.sort(key=lambda x: x["total"], reverse=True)

        return {
            "property_id": property_id,
            "year": year,
            "total": round(grand, 2),
            "rows": out_rows,
        }
    except Exception as e:
        logger.debug("gl-costs-by-dim4 feil for %s: %s", property_id, e)
        return {
            "property_id": property_id,
            "year": year,
            "total": 0.0,
            "rows": [],
        }


@router.get("/{property_id}/detail-view", response_model=PropertyDetailView)
async def get_property_detail_view(
    property_id: str,
    include_risk: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hent utvidet visning av en eiendom med enheter, kontrakter og risiko (med access control)."""
    try:
        # Check property access - load center for "Avdeling" link
        stmt = (
            select(PropertyModel)
            .where(PropertyModel.property_id == UUID(property_id))
            .options(selectinload(PropertyModel.center))
        )
        res = await db.execute(stmt)
        property_obj = res.scalar_one_or_none()
        
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Double check access
        await check_property_access(
            db=db,
            user=current_user,
            property_id=property_id,
            require_write=False
        )
        
        uuid_obj = property_obj.property_id
            
        # Hent enheter
        unit_result = await db.execute(select(UnitModel).where(UnitModel.property_id == uuid_obj))
        units = unit_result.scalars().all()
        
        # Hent kontrakter knyttet til disse enhetene (med party for Utleier)
        unit_ids = [u.unit_id for u in units]
        contracts = []
        if unit_ids:
            stmt = select(ContractModel).where(ContractModel.unit_id.in_(unit_ids)).options(selectinload(ContractModel.party))
            contract_result = await db.execute(stmt)
            contracts = contract_result.scalars().all()
            
        # Hent parter knyttet til disse kontraktene
        party_ids = [c.party_id for c in contracts if c.party_id]
        parties = []
        if party_ids:
            party_result = await db.execute(select(PartyModel).where(PartyModel.party_id.in_(party_ids)))
            parties = party_result.scalars().all()

        # Risikovurdering
        latest_risk = None
        if include_risk:
            # Hent siste risikovurdering
            risk_query = select(RiskAssessmentModel).filter(
                RiskAssessmentModel.property_id == uuid_obj
            ).order_by(RiskAssessmentModel.assessment_date.desc()).limit(1)
            risk_result = await db.execute(risk_query)
            latest_risk = risk_result.scalar_one_or_none()

        # Convert to dict
        property_dict = {c.name: getattr(property_obj, c.name) for c in property_obj.__table__.columns}
        
        # Add center name if available
        if property_obj.center:
            property_dict["center_name"] = property_obj.center.name
        
        ext = property_obj.external_data or {}
        
        # Use helper
        enrich_property_data(property_dict, ext, property_obj)
        property_dict["bufdir_image_path"] = _bufdir_image_thumb(ext)
        pmap_dv = await _primary_lease_party_by_property_ids(db, [uuid_obj])
        property_dict["primary_lease_party_name"] = pmap_dv.get(str(uuid_obj))

        # Specific override: Update total_area with actual unit sum if available
        unit_sum = sum(u.area_sqm for u in units if u.area_sqm)
        if unit_sum > 0:
            property_dict["total_area"] = unit_sum

        latest_risk_dict = None
        if latest_risk:
            latest_risk_dict = {c.name: getattr(latest_risk, c.name) for c in latest_risk.__table__.columns}

        return PropertyDetailView.model_validate({
            "property": property_dict,
            "units": units,
            "contracts": contracts,
            "parties": parties,
            "latest_risk_assessment": latest_risk_dict,
            "generated_at": datetime.now()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in detail view: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{property_id}", response_model=PropertySchema)
async def get_property(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hent en spesifikk eiendom (med access control)."""
    try:
        # Check property access
        property_obj = await check_property_access(
            db=db,
            user=current_user,
            property_id=property_id,
            require_write=False
        )
            
        # Enrich for consistency with list view
        p_dict = {c.name: getattr(property_obj, c.name) for c in property_obj.__table__.columns}
        ext = property_obj.external_data or {}
        enrich_property_data(p_dict, ext, property_obj)
        p_dict["bufdir_image_path"] = _bufdir_image_thumb(ext)
        pmap_one = await _primary_lease_party_by_property_ids(db, [property_obj.property_id])
        p_dict["primary_lease_party_name"] = pmap_one.get(str(property_obj.property_id))

        return p_dict
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")

@router.put("/{property_id}", response_model=PropertySchema)
async def update_property(
    property_id: str,
    property_in: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Oppdater eiendomsinformasjon (med access control)."""
    try:
        # Check write access
        property_obj = await check_property_access(
            db=db,
            user=current_user,
            property_id=property_id,
            require_write=True
        )
            
        property_obj.address = property_in.address
        property_obj.postal_code = property_in.postal_code
        property_obj.city = property_in.city
        property_obj.latitude = property_in.latitude
        property_obj.longitude = property_in.longitude
        
        await db.commit()
        await db.refresh(property_obj)
        return property_obj
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")

@router.patch("/{property_id}", response_model=PropertySchema)
async def patch_property(
    property_id: str,
    property_in: PropertyUpdate, # Use PropertyUpdate schema
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Oppdater deler av eiendomsinformasjon (med access control)."""
    try:
        # Check write access
        property_obj = await check_property_access(
            db=db,
            user=current_user,
            property_id=property_id,
            require_write=True
        )
            
        update_data = property_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(property_obj, field, value)
        
        await db.commit()
        await db.refresh(property_obj)
        return property_obj
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")

@router.delete("/{property_id}", status_code=204)
async def delete_property(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Slett en eiendom (kun ADMIN)."""
    # Kun ADMIN kan slette properties
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete properties"
        )
    
    try:
        uuid_obj = UUID(property_id)
        result = await db.execute(select(PropertyModel).where(PropertyModel.property_id == uuid_obj))
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            raise HTTPException(status_code=404, detail="Eiendom ikke funnet")
        
        await db.delete(db_obj)
        await db.commit()
        return Response(status_code=204)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")

@router.get("/{property_id}/units", response_model=List[UnitSchema])
async def get_property_units(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hent alle enheter for en eiendom (med access control)."""
    # Check property access
    await check_property_access(
        db=db,
        user=current_user,
        property_id=property_id,
        require_write=False
    )
    
    result = await db.execute(select(UnitModel).where(UnitModel.property_id == property_id))
    return result.scalars().all()

@router.get("/{property_id}/contracts", response_model=List[Contract])
async def get_property_contracts(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent alle kontrakter for en eiendom."""
    # Find units first
    unit_result = await db.execute(select(UnitModel.unit_id).where(UnitModel.property_id == property_id))
    unit_ids = unit_result.scalars().all()
    
    if not unit_ids:
        return []
        
    contract_result = await db.execute(select(ContractModel).where(ContractModel.unit_id.in_([str(uid) for uid in unit_ids])))
    return contract_result.scalars().all()

# --- Proximity Services Endpoints ---

async def _ensure_property_coords(prop: PropertyModel, db: AsyncSession) -> bool:
    """Geocode property if missing coords. Returns True if coords available after."""
    if prop and (prop.latitude and prop.longitude):
        return True
    if not prop:
        return False

    addr = (prop.address or "").strip()
    city = (prop.city or "").strip() if prop.city else None
    postal = (str(prop.postal_code).strip() if prop.postal_code else None)
    if not addr and not (postal and city):
        return False

    from app.services.external.api_clients.kartverket_client import KartverketClient
    from app.services.external.mapbox_client import MapboxClient

    # Geonorge: bruk strukturert postnr/sted når det finnes (bedre treff for «rotete» adresselinjer)
    primary_sok = addr if addr else f"{postal} {city}".strip()
    kv = KartverketClient()
    coords = await kv.search_address(primary_sok, city=city, postal_code=postal)
    if coords and coords.get("latitude") and coords.get("longitude"):
        prop.latitude = coords["latitude"]
        prop.longitude = coords["longitude"]
        await db.commit()
        return True

    # Fallback: Mapbox (samme token som POI) når Geonorge ikke treffer
    mb_parts = []
    if addr:
        mb_parts.append(addr)
    if postal and city:
        mb_parts.append(f"{postal} {city}")
    elif city:
        mb_parts.append(city)
    elif postal:
        mb_parts.append(postal)
    mb_query = ", ".join(p for p in mb_parts if p)
    if not mb_query:
        return False
    mb = MapboxClient()
    mb_coords = await mb.geocode_address(f"{mb_query}, Norway")
    if mb_coords and mb_coords.get("latitude") and mb_coords.get("longitude"):
        prop.latitude = mb_coords["latitude"]
        prop.longitude = mb_coords["longitude"]
        await db.commit()
        return True
    return False


@router.get("/{property_id}/proximity-services")
async def get_proximity_services(
    property_id: str,
    service_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent proximity services (cached)."""
    from app.services.proximity.service import ProximityService
    
    try:
        uuid_obj = UUID(property_id)
        
        # We need coords to fetch fresh if cache is empty
        result = await db.execute(select(PropertyModel).where(PropertyModel.property_id == uuid_obj))
        prop = result.scalar_one_or_none()
        
        if not prop:
            raise HTTPException(status_code=404, detail="Eiendom ikke funnet")
        
        # Auto-geocode if missing coords
        await _ensure_property_coords(prop, db)
        
        service = ProximityService(db)
        
        if prop.latitude and prop.longitude:
            # fetch_proximity_services checks cache first, so this is efficient
            results = await service.fetch_proximity_services(
                uuid_obj, prop.latitude, prop.longitude, 
                service_types=[service_type] if service_type else None
            )
        else:
            # Fallback if no coords (geocoding failed)
            results = await service.get_cached_services(uuid_obj, service_type)
            
        return results
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID")

@router.post("/{property_id}/proximity-services/refresh")
async def refresh_proximity_services(
    property_id: str,
    force_refresh: bool = Query(False, description="Ignorer cache og hent POI på nytt"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Oppdater proximity services fra Mapbox/OSM."""
    from app.services.proximity.service import ProximityService
    
    try:
        uuid_obj = UUID(property_id)
        
        result = await db.execute(select(PropertyModel).where(PropertyModel.property_id == uuid_obj))
        prop = result.scalar_one_or_none()
        if not prop:
            raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

        # Auto-geocode if missing coords
        await _ensure_property_coords(prop, db)
        if not prop.latitude or not prop.longitude:
            raise HTTPException(status_code=400, detail="Eiendom mangler koordinater (geokoding feilet)")
            
        service = ProximityService(db)
        results = await service.fetch_proximity_services(
            uuid_obj, prop.latitude, prop.longitude, force_refresh=force_refresh
        )
        return {"count": len(results), "services": results}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID")

@router.get("/{property_id}/accessibility-summary")
async def get_accessibility_summary(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent accessibility metrics."""
    from app.services.proximity.service import ProximityService

    try:
        uuid_obj = UUID(property_id)
        result = await db.execute(select(PropertyModel).where(PropertyModel.property_id == uuid_obj))
        prop = result.scalar_one_or_none()

        if not prop:
            raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

        # Auto-geocode if missing coords
        await _ensure_property_coords(prop, db)

        service = ProximityService(db)
        if prop.latitude and prop.longitude:
            await service.fetch_proximity_services(uuid_obj, prop.latitude, prop.longitude)

        summary = await service.get_accessibility_summary(uuid_obj)
        return summary
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID")


@router.get("/{property_id}/cost-analysis")
async def get_property_cost_analysis(
    property_id: str,
    year: Optional[int] = Query(None, ge=2000, le=2100, description="År for kostnadsanalyse (default: inneværende år)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent kostnadsanalyse for en eiendom.

    Kategoriserer kostnader i:
    - Eiendomskostnader (husleie, fellesutgifter) - bør være proporsjonale med leie
    - Driftskostnader (renhold, strøm, vakthold) - løpende utgifter
    - Investeringer (oppgraderinger, inventar) - engangskostnader

    Returnerer:
    - Oppsummering per kategori
    - Forhold til husleie
    - Anomalier og flagg
    - Potensielle duplikater
    """
    from app.services.analytics.cost_analysis_service import get_property_cost_analysis as analyze

    try:
        UUID(property_id)  # Validate UUID format
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")

    try:
        analysis = await analyze(db, property_id, year=year)
        if not analysis:
            raise HTTPException(status_code=404, detail="Eiendom ikke funnet")
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.debug("cost-analysis feilet for %s: %s", property_id, e)
        raise HTTPException(status_code=503, detail="Regnskapsdata midlertidig utilgjengelig")


@router.get("/{property_id}/proximity-validation")
async def validate_property_proximity_requirements(
    property_id: str,
    institution_type: Optional[str] = Query(None, description="Type institusjon: atferd, omsorg, akutt"),
    age_group: Optional[str] = Query(None, description="Aldersgruppe: age_13_15, age_16_18, age_18_20"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Valider om eiendommen oppfyller proximity-krav for barnevernsinstitusjoner.
    
    Basert på forsvarlighetskravet i barnevernsloven § 1-7 og kvalitetsforskriften.
    
    Returnerer:
    - accessibility_score (0-100): Hvor god tilgjengelighet til tjenester
    - risk_level: "low", "medium" eller "high"
    - critical_services: Status for kritiske tjenester (sykehus, apotek, skole, etc.)
    - important_services: Status for viktige tjenester (lege, kollektiv, BUP)
    - supportive_services: Status for støttende tjenester (park, gym, bibliotek)
    - missing_services: Liste over tjenester som mangler
    - violations: Krav som ikke oppfylles (kan være lovbrudd)
    - recommendations: Anbefalinger for forbedring
    """
    from app.services.proximity.validator import validate_property_proximity
    
    try:
        UUID(property_id)  # Validate UUID format
        
        result = await validate_property_proximity(
            db=db,
            property_id=property_id,
            institution_type=institution_type,
            age_group=age_group
        )
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feil ved validering: {str(e)}")


@router.get("/{property_id}/sub-units", response_model=List[PropertySchema])
async def get_sub_units(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent avdelinger (sub-units) som organisatorisk tilhører denne eiendommen.

    Strategi:
    1. Primær: finn eiendommer med parent_unit_id_erp = property.unit_id_erp
       (deterministisk via ERP-ID fra e-don2 TilhørighetEnhetID)
    2. Fallback: finn avdelinger med samme affiliation + region som denne eiendommen
       (65% dekning, lav feilrate – erstatter den tidligere ILIKE substring-match)
    """
    try:
        uuid_obj = UUID(property_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")

    result = await db.execute(
        select(PropertyModel).where(PropertyModel.property_id == uuid_obj)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Eiendom ikke funnet")

    sub_units = []

    # Strategi 1: parent_unit_id_erp kobling (deterministisk via ERP-ID)
    if prop.unit_id_erp:
        res = await db.execute(
            select(PropertyModel).where(
                PropertyModel.parent_unit_id_erp == prop.unit_id_erp,
                PropertyModel.property_id != uuid_obj,
            )
        )
        sub_units = res.scalars().all()

    # Strategi 2: samme affiliation + region (erstatter utrygg ILIKE substring-match)
    # Avdelinger som deler affiliation og region med en institusjon tilhører typisk samme enhet.
    if not sub_units and prop.affiliation and prop.region:
        res = await db.execute(
            select(PropertyModel).where(
                PropertyModel.affiliation == prop.affiliation,
                PropertyModel.region == prop.region,
                PropertyModel.unit_short_type == "Avdeling",
                PropertyModel.property_id != uuid_obj,
            )
        )
        sub_units = res.scalars().all()

    return sub_units
