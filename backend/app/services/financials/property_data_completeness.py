"""
Helhetlig datatetthet per eiendom: kontrakt, manuelle poster, GL (rullerende år).

Brukes av audit_properties_full.py og admin API. Se docs/DATAKILDER_EIENDOM_FINANS.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.property_annual_cost import PropertyAnnualCost
from app.domains.core.models.unit import Unit
from app.models.financial_models import GLTransaction
from app.models.gl_constants import LEASE_ACCOUNT_NAMES


def norm_id(v: Optional[str]) -> Optional[str]:
    """Normaliser koststed/ERP for matching (samme som properties._norm_id)."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        return s[:-2]
    return s


def _lease_sql_condition():
    parts = [GLTransaction.konto_navn == n for n in LEASE_ACCOUNT_NAMES]
    parts.append(GLTransaction.konto_navn.ilike("Leie %"))
    return or_(*parts)


def _float(x: Any) -> float:
    if x is None:
        return 0.0
    if isinstance(x, Decimal):
        return float(x)
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def build_dim1_to_property_ids(properties: List[Property]) -> Dict[str, List[UUID]]:
    """Hvilke eiendommer kan motta orphan-GL på gitt normalisert dim1."""
    tmp: Dict[str, Set[UUID]] = {}
    for p in properties:
        pid = p.property_id
        for raw in (p.unit_id_erp, p.department_code, p.koststed_kode):
            k = norm_id(raw) if raw else None
            if not k:
                continue
            tmp.setdefault(k, set()).add(pid)
    return {k: list(v) for k, v in tmp.items()}


@dataclass
class PropertyCompletenessRow:
    property_id: str
    name: str
    region: Optional[str]
    address: Optional[str]
    # Masterdata
    masterdata_ok: bool
    missing_accounting_linkage: bool
    # Enheter / kontrakt
    unit_count: int
    active_contract_count: int
    contract_rent_year: float
    contracts_missing_party: int
    contract_missing_rent_amount: bool
    # Manuelle / CSV
    manual_expense_lines: int
    manual_expense_total: float
    has_property_annual_cost: bool
    # GL (rullerende siste år med aktivitet)
    gl_last_year: Optional[int]
    gl_faktisk_husleie: float
    gl_andre_kostnader: float
    gl_totalt: bool
    no_gl_in_window: bool
    # Avvik
    anomaly_contract_rent_no_gl_lease: bool
    anomaly_gl_lease_no_contract: bool
    double_hole_no_finance: bool
    score: int
    issue_codes: List[str] = field(default_factory=list)


async def compute_all_property_completeness(
    db: AsyncSession,
    *,
    year_min: int = 2020,
    year_max: int = 2030,
) -> List[PropertyCompletenessRow]:
    """
    Én bulk-beregning: alle eiendommer med score og felter for CSV/rapport.
    """
    r = await db.execute(select(Property))
    properties = r.scalars().all()

    # Enheter per eiendom
    uc = (
        await db.execute(
            select(Unit.property_id, func.count()).group_by(Unit.property_id)
        )
    ).all()
    unit_count: Dict[UUID, int] = {row[0]: int(row[1]) for row in uc}

    # Aktive kontrakter med unit -> property
    cr = await db.execute(
        select(Contract)
        .where(Contract.status == "active")
        .join(Unit, Contract.unit_id == Unit.unit_id)
    )
    contracts = cr.scalars().all()

    contract_rent_by_prop: Dict[UUID, float] = {}
    contract_n_by_prop: Dict[UUID, int] = {}
    contracts_no_party: Dict[UUID, int] = {}

    for c in contracts:
        if not c.unit or not c.unit.property_id:
            continue
        pid = c.unit.property_id
        contract_n_by_prop[pid] = contract_n_by_prop.get(pid, 0) + 1
        if not c.party_id:
            contracts_no_party[pid] = contracts_no_party.get(pid, 0) + 1
        amt = 0.0
        if c.amount and isinstance(c.amount, dict):
            v = c.amount.get("amount_per_year") or c.amount.get("total_per_year")
            if v is not None:
                try:
                    amt = float(v)
                except (TypeError, ValueError):
                    amt = 0.0
            if (c.amount.get("annual_rent") is not None) and amt == 0:
                try:
                    amt = float(c.amount.get("annual_rent") or 0)
                except (TypeError, ValueError):
                    pass
        contract_rent_by_prop[pid] = contract_rent_by_prop.get(pid, 0.0) + amt

    contract_missing_rent: Set[UUID] = {
        pid
        for pid, n in contract_n_by_prop.items()
        if n > 0 and contract_rent_by_prop.get(pid, 0.0) <= 0
    }

    dim1_claims = build_dim1_to_property_ids(properties)

    lease_case = _lease_sql_condition()

    # Direkte GL per (property_id, år)
    stmt_d = (
        select(
            GLTransaction.property_id,
            GLTransaction.ar,
            func.coalesce(func.sum(GLTransaction.belop), 0).label("tot"),
            func.coalesce(
                func.sum(case((lease_case, GLTransaction.belop), else_=0)),
                0,
            ).label("lease"),
        )
        .where(
            GLTransaction.property_id.isnot(None),
            GLTransaction.ar.isnot(None),
            GLTransaction.ar >= year_min,
            GLTransaction.ar <= year_max,
        )
        .group_by(GLTransaction.property_id, GLTransaction.ar)
    )
    direct_rows = (await db.execute(stmt_d)).all()

    # Orphan GL per (dim1, år)
    stmt_o = (
        select(
            GLTransaction.dim1_kode,
            GLTransaction.ar,
            func.coalesce(func.sum(GLTransaction.belop), 0).label("tot"),
            func.coalesce(
                func.sum(case((lease_case, GLTransaction.belop), else_=0)),
                0,
            ).label("lease"),
        )
        .where(
            GLTransaction.property_id.is_(None),
            GLTransaction.ar.isnot(None),
            GLTransaction.ar >= year_min,
            GLTransaction.ar <= year_max,
        )
        .group_by(GLTransaction.dim1_kode, GLTransaction.ar)
    )
    orphan_rows = (await db.execute(stmt_o)).all()

    # Slå sammen: (pid, year) -> {tot, lease}
    merged: Dict[Tuple[UUID, int], Dict[str, float]] = {}

    def add_m(pid: UUID, year: int, tot: float, lease: float) -> None:
        key = (pid, year)
        if key not in merged:
            merged[key] = {"tot": 0.0, "lease": 0.0}
        merged[key]["tot"] += tot
        merged[key]["lease"] += lease

    for row in direct_rows:
        pid, ar, tot, lease = row[0], int(row[1]), _float(row[2]), _float(row[3])
        if pid:
            add_m(pid, ar, tot, lease)

    for row in orphan_rows:
        dim1_raw, ar = row[0], int(row[1]) if row[1] is not None else None
        if ar is None:
            continue
        tot, lease = _float(row[2]), _float(row[3])
        k = norm_id(dim1_raw) if dim1_raw else None
        if not k:
            continue
        for pid in dim1_claims.get(k, []):
            add_m(pid, ar, tot, lease)

    # PropertyAnnualCost (siste år i vindu)
    pac = (
        await db.execute(
            select(PropertyAnnualCost.property_id)
            .where(
                PropertyAnnualCost.year >= year_min,
                PropertyAnnualCost.year <= year_max,
            )
            .distinct()
        )
    ).all()
    has_pac: Set[UUID] = {row[0] for row in pac}

    out: List[PropertyCompletenessRow] = []

    for p in properties:
        pid = p.property_id
        # Manuelle utgifter
        ext = p.external_data if isinstance(p.external_data, dict) else {}
        expenses = ext.get("financials", {}).get("manual_expenses") or []
        if not isinstance(expenses, list):
            expenses = []
        manual_total = 0.0
        for exp in expenses:
            try:
                manual_total += float(exp.get("amount", 0) or 0)
            except (TypeError, ValueError):
                pass

        has_geo = bool(
            (p.address and str(p.address).strip())
            or (
                (p.postal_code and str(p.postal_code).strip())
                or (p.city and str(p.city).strip())
                or (p.municipality and str(p.municipality).strip())
            )
        )
        masterdata_ok = bool(has_geo and (p.region and str(p.region).strip()))

        linkage_ok = bool(
            (p.unit_id_erp and str(p.unit_id_erp).strip())
            or (p.department_code and str(p.department_code).strip())
            or (p.koststed_kode and str(p.koststed_kode).strip())
        )

        # Siste GL-år med aktivitet for denne eiendommen
        years_for_p: List[int] = []
        for (pp, yr), v in merged.items():
            if pp == pid and abs(v["tot"]) > 0.0001:
                years_for_p.append(yr)
        gl_last = max(years_for_p) if years_for_p else None

        gl_lease = 0.0
        gl_other = 0.0
        gl_tot = 0.0
        if gl_last is not None:
            key = (pid, gl_last)
            if key in merged:
                gl_tot = merged[key]["tot"]
                gl_lease = merged[key]["lease"]
                gl_other = gl_tot - gl_lease

        c_rent = contract_rent_by_prop.get(pid, 0.0)
        n_ctr = contract_n_by_prop.get(pid, 0)
        no_party_n = contracts_no_party.get(pid, 0) if n_ctr else 0

        missing_rent_flag = pid in contract_missing_rent and n_ctr > 0

        no_gl = gl_last is None
        has_gl = not no_gl
        double_hole = (
            no_gl
            and manual_total < 0.0001
            and pid not in has_pac
            and n_ctr == 0
        )

        anomaly_cr_gl = (
            c_rent > 1000
            and gl_last is not None
            and gl_lease < 100
        )
        anomaly_gl_cr = (
            gl_lease > 1000
            and c_rent < 100
            and n_ctr > 0
        )

        codes: List[str] = []
        if not masterdata_ok:
            codes.append("weak_masterdata")
        if not linkage_ok:
            codes.append("missing_accounting_linkage")
        # Enheter/kontrakter: kun avvik om det heller ikke finnes GL på eiendom (institusjonsnivå)
        uc_n = unit_count.get(pid, 0)
        if uc_n == 0 and not has_gl:
            codes.append("no_units")
        elif uc_n == 0 and has_gl:
            codes.append("no_units_institution_level_gl")
        if n_ctr == 0 and not has_gl:
            codes.append("no_active_contracts")
        elif n_ctr == 0 and has_gl:
            codes.append("no_contracts_institution_level_gl")
        if missing_rent_flag:
            codes.append("contract_missing_rent_amount")
        if no_party_n > 0 and n_ctr:
            codes.append("contracts_missing_party")
        if no_gl:
            codes.append("no_gl_in_window")
        if double_hole:
            codes.append("double_hole_no_finance")
        if anomaly_cr_gl:
            codes.append("anomaly_contract_rent_no_gl_lease")
        if anomaly_gl_cr:
            codes.append("anomaly_gl_lease_no_contract_rent")

        # Score 0–100 (GL på institusjon gir delkreditt uten units/kontrakter i DB)
        s = 0
        if masterdata_ok:
            s += 20
        if linkage_ok:
            s += 10
        if uc_n > 0:
            s += 15
        elif has_gl:
            s += 10
        if n_ctr > 0 and c_rent > 0:
            s += 15
        elif n_ctr > 0:
            s += 5
        elif has_gl and n_ctr == 0:
            s += 8
        if no_party_n == 0 and n_ctr > 0:
            s += 5
        if not no_gl:
            s += 20
        if manual_total > 0 or (pid in has_pac):
            s += 15

        out.append(
            PropertyCompletenessRow(
                property_id=str(pid),
                name=(p.name or "")[:300],
                region=p.region,
                address=p.address,
                masterdata_ok=masterdata_ok,
                missing_accounting_linkage=not linkage_ok,
                unit_count=unit_count.get(pid, 0),
                active_contract_count=n_ctr,
                contract_rent_year=c_rent,
                contracts_missing_party=no_party_n,
                contract_missing_rent_amount=missing_rent_flag,
                manual_expense_lines=len(expenses),
                manual_expense_total=manual_total,
                has_property_annual_cost=pid in has_pac,
                gl_last_year=gl_last,
                gl_faktisk_husleie=gl_lease,
                gl_andre_kostnader=gl_other,
                gl_totalt=abs(gl_tot) > 0.0001,
                no_gl_in_window=no_gl,
                anomaly_contract_rent_no_gl_lease=anomaly_cr_gl,
                anomaly_gl_lease_no_contract=anomaly_gl_cr,
                double_hole_no_finance=double_hole,
                score=min(100, s),
                issue_codes=codes,
            )
        )

    return out


def _row_from_property_parts(
    p: Property,
    *,
    unit_count: int,
    contract_rent: float,
    n_ctr: int,
    no_party_n: int,
    missing_rent_flag: bool,
    manual_lines: int,
    manual_total: float,
    has_pac: bool,
    merged: Dict[Tuple[UUID, int], Dict[str, float]],
) -> PropertyCompletenessRow:
    """Bygg PropertyCompletenessRow fra ferdig merged GL og kontraktsfelter."""
    pid = p.property_id
    years_for_p = [
        yr
        for (pp, yr), v in merged.items()
        if pp == pid and abs(v["tot"]) > 0.0001
    ]
    gl_last = max(years_for_p) if years_for_p else None
    gl_lease = 0.0
    gl_other = 0.0
    gl_tot = 0.0
    if gl_last is not None:
        key = (pid, gl_last)
        if key in merged:
            gl_tot = merged[key]["tot"]
            gl_lease = merged[key]["lease"]
            gl_other = gl_tot - gl_lease

    has_geo = bool(
        (p.address and str(p.address).strip())
        or (
            (p.postal_code and str(p.postal_code).strip())
            or (p.city and str(p.city).strip())
            or (p.municipality and str(p.municipality).strip())
        )
    )
    masterdata_ok = bool(has_geo and (p.region and str(p.region).strip()))
    linkage_ok = bool(
        (p.unit_id_erp and str(p.unit_id_erp).strip())
        or (p.department_code and str(p.department_code).strip())
        or (p.koststed_kode and str(p.koststed_kode).strip())
    )

    no_gl = gl_last is None
    has_gl = not no_gl
    double_hole = no_gl and manual_total < 0.0001 and not has_pac and n_ctr == 0
    anomaly_cr_gl = contract_rent > 1000 and gl_last is not None and gl_lease < 100
    anomaly_gl_cr = gl_lease > 1000 and contract_rent < 100 and n_ctr > 0

    codes: List[str] = []
    if not masterdata_ok:
        codes.append("weak_masterdata")
    if not linkage_ok:
        codes.append("missing_accounting_linkage")
    if unit_count == 0 and not has_gl:
        codes.append("no_units")
    elif unit_count == 0 and has_gl:
        codes.append("no_units_institution_level_gl")
    if n_ctr == 0 and not has_gl:
        codes.append("no_active_contracts")
    elif n_ctr == 0 and has_gl:
        codes.append("no_contracts_institution_level_gl")
    if missing_rent_flag:
        codes.append("contract_missing_rent_amount")
    if no_party_n > 0 and n_ctr:
        codes.append("contracts_missing_party")
    if no_gl:
        codes.append("no_gl_in_window")
    if double_hole:
        codes.append("double_hole_no_finance")
    if anomaly_cr_gl:
        codes.append("anomaly_contract_rent_no_gl_lease")
    if anomaly_gl_cr:
        codes.append("anomaly_gl_lease_no_contract_rent")

    s = 0
    if masterdata_ok:
        s += 20
    if linkage_ok:
        s += 10
    if unit_count > 0:
        s += 15
    elif has_gl:
        s += 10
    if n_ctr > 0 and contract_rent > 0:
        s += 15
    elif n_ctr > 0:
        s += 5
    elif has_gl and n_ctr == 0:
        s += 8
    if no_party_n == 0 and n_ctr > 0:
        s += 5
    if not no_gl:
        s += 20
    if manual_total > 0 or has_pac:
        s += 15

    return PropertyCompletenessRow(
        property_id=str(pid),
        name=(p.name or "")[:300],
        region=p.region,
        address=p.address,
        masterdata_ok=masterdata_ok,
        missing_accounting_linkage=not linkage_ok,
        unit_count=unit_count,
        active_contract_count=n_ctr,
        contract_rent_year=contract_rent,
        contracts_missing_party=no_party_n,
        contract_missing_rent_amount=missing_rent_flag,
        manual_expense_lines=manual_lines,
        manual_expense_total=manual_total,
        has_property_annual_cost=has_pac,
        gl_last_year=gl_last,
        gl_faktisk_husleie=gl_lease,
        gl_andre_kostnader=gl_other,
        gl_totalt=abs(gl_tot) > 0.0001,
        no_gl_in_window=no_gl,
        anomaly_contract_rent_no_gl_lease=anomaly_cr_gl,
        anomaly_gl_lease_no_contract=anomaly_gl_cr,
        double_hole_no_finance=double_hole,
        score=min(100, s),
        issue_codes=codes,
    )


async def compute_property_completeness_one(
    db: AsyncSession,
    property_id: str,
    *,
    year_min: int = 2020,
    year_max: int = 2030,
) -> Optional[PropertyCompletenessRow]:
    """Effektiv beregning for én eiendom (API), samme logikk som full matrise."""
    try:
        uid = UUID(property_id)
    except ValueError:
        return None

    r = await db.execute(select(Property).where(Property.property_id == uid))
    p = r.scalar_one_or_none()
    if not p:
        return None
    pid = p.property_id

    uc_row = (
        await db.execute(select(func.count()).select_from(Unit).where(Unit.property_id == pid))
    ).scalar()
    unit_count = int(uc_row or 0)

    cr = await db.execute(
        select(Contract)
        .where(Contract.status == "active")
        .join(Unit, Contract.unit_id == Unit.unit_id)
        .where(Unit.property_id == pid)
    )
    contracts = cr.scalars().all()

    contract_rent = 0.0
    n_ctr = len(contracts)
    no_party_n = sum(1 for c in contracts if not c.party_id)
    for c in contracts:
        amt = 0.0
        if c.amount and isinstance(c.amount, dict):
            v = c.amount.get("amount_per_year") or c.amount.get("total_per_year")
            if v is not None:
                try:
                    amt = float(v)
                except (TypeError, ValueError):
                    amt = 0.0
            if c.amount.get("annual_rent") is not None and amt == 0:
                try:
                    amt = float(c.amount.get("annual_rent") or 0)
                except (TypeError, ValueError):
                    pass
        contract_rent += amt

    missing_rent_flag = n_ctr > 0 and contract_rent <= 0

    ext = p.external_data if isinstance(p.external_data, dict) else {}
    expenses = ext.get("financials", {}).get("manual_expenses") or []
    if not isinstance(expenses, list):
        expenses = []
    manual_total = 0.0
    for exp in expenses:
        try:
            manual_total += float(exp.get("amount", 0) or 0)
        except (TypeError, ValueError):
            pass

    pac_exists = (
        await db.execute(
            select(func.count())
            .select_from(PropertyAnnualCost)
            .where(
                PropertyAnnualCost.property_id == pid,
                PropertyAnnualCost.year >= year_min,
                PropertyAnnualCost.year <= year_max,
            )
        )
    ).scalar()
    has_pac = int(pac_exists or 0) > 0

    lease_case = _lease_sql_condition()
    merged: Dict[Tuple[UUID, int], Dict[str, float]] = {}

    def add_m(pp: UUID, year: int, tot: float, lease: float) -> None:
        key = (pp, year)
        if key not in merged:
            merged[key] = {"tot": 0.0, "lease": 0.0}
        merged[key]["tot"] += tot
        merged[key]["lease"] += lease

    stmt_d = (
        select(
            GLTransaction.ar,
            func.coalesce(func.sum(GLTransaction.belop), 0).label("tot"),
            func.coalesce(
                func.sum(case((lease_case, GLTransaction.belop), else_=0)),
                0,
            ).label("lease"),
        )
        .where(
            GLTransaction.property_id == pid,
            GLTransaction.ar.isnot(None),
            GLTransaction.ar >= year_min,
            GLTransaction.ar <= year_max,
        )
        .group_by(GLTransaction.ar)
    )
    for row in (await db.execute(stmt_d)).all():
        ar = int(row[0]) if row[0] is not None else None
        if ar is None:
            continue
        add_m(pid, ar, _float(row[1]), _float(row[2]))

    dim_keys: List[str] = []
    for raw in (p.unit_id_erp, p.department_code, p.koststed_kode):
        k = norm_id(raw) if raw else None
        if k and k not in dim_keys:
            dim_keys.append(k)

    if dim_keys:
        dim_conds = []
        for k in dim_keys:
            dim_conds.append(GLTransaction.dim1_kode == k)
            dim_conds.append(GLTransaction.dim1_kode == (k + ".0"))
        stmt_o = (
            select(
                GLTransaction.ar,
                func.coalesce(func.sum(GLTransaction.belop), 0).label("tot"),
                func.coalesce(
                    func.sum(case((lease_case, GLTransaction.belop), else_=0)),
                    0,
                ).label("lease"),
            )
            .where(
                GLTransaction.property_id.is_(None),
                GLTransaction.ar.isnot(None),
                GLTransaction.ar >= year_min,
                GLTransaction.ar <= year_max,
                or_(*dim_conds),
            )
            .group_by(GLTransaction.ar)
        )
        for row in (await db.execute(stmt_o)).all():
            ar = int(row[0]) if row[0] is not None else None
            if ar is None:
                continue
            add_m(pid, ar, _float(row[1]), _float(row[2]))

    return _row_from_property_parts(
        p,
        unit_count=unit_count,
        contract_rent=contract_rent,
        n_ctr=n_ctr,
        no_party_n=no_party_n,
        missing_rent_flag=missing_rent_flag,
        manual_lines=len(expenses),
        manual_total=manual_total,
        has_pac=has_pac,
        merged=merged,
    )


async def get_property_completeness_detail(
    db: AsyncSession,
    property_id: str,
    **kwargs: Any,
) -> Optional[Dict[str, Any]]:
    """Én eiendom: samme felt som rad i matrise (for API)."""
    row = await compute_property_completeness_one(db, property_id, **kwargs)
    if row:
        return row_to_dict(row)
    return None


def row_to_dict(row: PropertyCompletenessRow) -> Dict[str, Any]:
    return {
        "property_id": row.property_id,
        "name": row.name,
        "region": row.region,
        "address": row.address,
        "masterdata_ok": row.masterdata_ok,
        "missing_accounting_linkage": row.missing_accounting_linkage,
        "unit_count": row.unit_count,
        "active_contract_count": row.active_contract_count,
        "contract_rent_year": row.contract_rent_year,
        "contracts_missing_party": row.contracts_missing_party,
        "contract_missing_rent_amount": row.contract_missing_rent_amount,
        "manual_expense_lines": row.manual_expense_lines,
        "manual_expense_total": row.manual_expense_total,
        "has_property_annual_cost": row.has_property_annual_cost,
        "gl_last_year": row.gl_last_year,
        "gl_faktisk_husleie": row.gl_faktisk_husleie,
        "gl_andre_kostnader": row.gl_andre_kostnader,
        "gl_totalt": row.gl_totalt,
        "no_gl_in_window": row.no_gl_in_window,
        "anomaly_contract_rent_no_gl_lease": row.anomaly_contract_rent_no_gl_lease,
        "anomaly_gl_lease_no_contract": row.anomaly_gl_lease_no_contract,
        "double_hole_no_finance": row.double_hole_no_finance,
        "score": row.score,
        "issue_codes": row.issue_codes,
    }
