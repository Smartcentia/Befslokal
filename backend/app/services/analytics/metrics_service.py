from typing import Optional
from sqlalchemy import select, func, cast, Float, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.models.metrics import DashboardMetrics
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.utils.region_mapping import COUNTY_TO_REGION, get_operational_region
from app.domains.hms.models.risk import RiskAssessment
import datetime


async def get_live_dashboard_metrics(db: AsyncSession) -> dict:
    """
    Beregn eiendommer, kontrakter, risiko, leie og vedlikehold direkte fra tabellene.
    Brukes når DashboardMetrics er tom (f.eks. før første refresh), så dashboard ikke viser 0.
    """
    # 1. Properties & Maintenance (sikker mot manglende external_data)
    maint_manual = func.coalesce(
        func.nullif(Property.external_data['financials']['total_manual_expenses'].astext, ''), '0'
    )
    maint_csv = func.coalesce(
        func.nullif(Property.external_data['financials']['total_spend_csv'].astext, ''), '0'
    )
    maint_sum = cast(maint_manual, Float) + cast(maint_csv, Float)
    p_stmt = (
        select(func.count(Property.property_id), func.sum(maint_sum))
        .where(
            Property.closed_at.is_(None),
            (Property.unit_short_type != "Avdeling") | Property.unit_short_type.is_(None),
        )
    )
    p_res = await db.execute(p_stmt)
    row = p_res.one()
    properties_count = row[0] or 0
    total_maintenance = float(row[1] or 0)

    # 2. Contracts & Rent
    rent_yearly = func.coalesce(
        Contract.amount['total_per_year'].astext,
        Contract.amount['amount_per_year'].astext
    )
    rent_monthly = func.coalesce(
        Contract.amount['monthly_rent'].astext,
        Contract.amount['amount'].astext
    )
    final_rent = func.coalesce(
        cast(rent_yearly, Float),
        cast(rent_monthly, Float) * 12,
        0.0
    )
    c_stmt = select(
        func.count(Contract.contract_id),
        func.sum(final_rent)
    ).where(Contract.status == 'active')
    c_res = await db.execute(c_stmt)
    c_row = c_res.one()
    contracts_count = c_row[0] or 0
    total_annual_rent = float(c_row[1] or 0)

    # 3. Risks
    r_stmt = select(func.count(RiskAssessment.assessment_id))
    r_res = await db.execute(r_stmt)
    risks_count = r_res.scalar() or 0

    # 4. Occupancy rate (beleggsgrad): enheter med aktiv kontrakt / totalt enheter * 100
    total_units_stmt = select(func.count(Unit.unit_id))
    total_units_res = await db.execute(total_units_stmt)
    total_units = total_units_res.scalar() or 0

    occupied_units_stmt = select(func.count(func.distinct(Contract.unit_id))).where(
        Contract.status == "active",
        Contract.unit_id.isnot(None),
    )
    occupied_units_res = await db.execute(occupied_units_stmt)
    occupied_units = occupied_units_res.scalar() or 0

    occupancy_rate = (
        round((occupied_units / total_units * 100), 1) if total_units and total_units > 0 else 0.0
    )

    return {
        "properties_count": properties_count,
        "contracts_count": contracts_count,
        "risks_count": risks_count,
        "total_annual_rent": total_annual_rent,
        "total_maintenance_cost": total_maintenance,
        "occupancy_rate": occupancy_rate,
    }


async def get_occupancy_rate(db: AsyncSession) -> float:
    """
    Beregn beleggsgrad: enheter med aktiv kontrakt / totalt enheter * 100.
    Brukes av dashboard/stats når occupancy_rate ikke er cachet.
    """
    total_units_stmt = select(func.count(Unit.unit_id))
    total_units_res = await db.execute(total_units_stmt)
    total_units = total_units_res.scalar() or 0

    occupied_units_stmt = select(func.count(func.distinct(Contract.unit_id))).where(
        Contract.status == "active",
        Contract.unit_id.isnot(None),
    )
    occupied_units_res = await db.execute(occupied_units_stmt)
    occupied_units = occupied_units_res.scalar() or 0

    return round((occupied_units / total_units * 100), 1) if total_units and total_units > 0 else 0.0


async def refresh_dashboard_metrics():
    """
    Recalculates all dashboard metrics and stores them in DashboardMetrics.
    Uses optimized SQL aggregates.
    """
    # Import all models to ensure they are registered in SQLAlchemy registry
    import app.domains.core.models.user
    import app.domains.core.models.property
    import app.domains.core.models.contract
    import app.domains.core.models.audit
    import app.domains.core.models.unit
    import app.domains.core.models.party
    import app.domains.hms.models.risk
    import app.domains.hms.models.internal_control
    import app.domains.hms.models.checklist
    import app.models.ai_tool
    import app.models.file_meta
    import app.domains.core.models.center
    
    from app.domains.core.models.property import Property
    from app.domains.core.models.contract import Contract
    from app.domains.hms.models.risk import RiskAssessment
    async with SessionLocal() as db:
        # 1. Properties & Maintenance
        maint_manual = func.coalesce(func.nullif(Property.external_data['financials']['total_manual_expenses'].astext, ''), '0')
        maint_csv = func.coalesce(func.nullif(Property.external_data['financials']['total_spend_csv'].astext, ''), '0')
        maint_sum = cast(maint_manual, Float) + cast(maint_csv, Float)
        
        p_stmt = (
            select(
                func.count(Property.property_id),
                func.sum(maint_sum)
            )
            .where(
                Property.closed_at.is_(None),
                (Property.unit_short_type != "Avdeling") | Property.unit_short_type.is_(None),
            )
        )
        p_res = await db.execute(p_stmt)
        row = p_res.one()
        properties_count = row[0] or 0
        total_maintenance = float(row[1] or 0)

        # 2. Contracts & Rent
        rent_yearly = func.coalesce(
            Contract.amount['total_per_year'].astext,
            Contract.amount['amount_per_year'].astext
        )
        rent_monthly = func.coalesce(
            Contract.amount['monthly_rent'].astext,
            Contract.amount['amount'].astext
        )
        final_rent = func.coalesce(
            cast(rent_yearly, Float),
            cast(rent_monthly, Float) * 12,
            0.0
        )
        c_stmt = select(
            func.count(Contract.contract_id),
            func.sum(final_rent)
        ).where(Contract.status == 'active')
        c_res = await db.execute(c_stmt)
        c_row = c_res.one()
        contracts_count = c_row[0] or 0
        total_annual_rent = float(c_row[1] or 0)

        # 3. Risks
        r_stmt = select(func.count(RiskAssessment.assessment_id))
        r_res = await db.execute(r_stmt)
        risks_count = r_res.scalar() or 0

        # Update singleton in DashboardMetrics
        stmt = select(DashboardMetrics).limit(1)
        result = await db.execute(stmt)
        metrics = result.scalar_one_or_none()
        
        if not metrics:
            metrics = DashboardMetrics()
            db.add(metrics)
        
        metrics.properties_count = properties_count or 0
        metrics.contracts_count = contracts_count or 0
        metrics.risks_count = risks_count or 0
        metrics.total_annual_rent = total_annual_rent or 0.0
        metrics.total_maintenance_cost = total_maintenance or 0.0
        last_updated_val = datetime.datetime.now(datetime.timezone.utc)
        metrics.last_updated = last_updated_val
        
        await db.commit()
        return {
            "properties_count": properties_count or 0,
            "contracts_count": contracts_count or 0,
            "risks_count": risks_count or 0,
            "total_annual_rent": total_annual_rent or 0.0,
            "total_maintenance_cost": total_maintenance or 0.0,
            "last_updated": last_updated_val.isoformat()
        }

def _normalize_region(db_region: Optional[str], has_bufdir: bool = False) -> str:
    """Map DB region til Nord, Midt-Norge, Vest, Sør, Øst. Ignorerer has_bufdir — bruk geografisk region."""
    if not db_region:
        return "Sør"
    
    val = db_region.strip()
    
    # 1. Direct match in centralized mapping
    if val in COUNTY_TO_REGION:
        return COUNTY_TO_REGION[val]
        
    # 2. Sequential fallback logic for messy data
    clean_val = val.lower()
    if "nord" in clean_val or val.startswith("01") or "finnmark" in clean_val:
        return "Nord"
    if "midt" in clean_val or "trønd" in clean_val or "møre" in clean_val or val.startswith("50"):
        return "Midt-Norge"
    if "vest" in clean_val or val.startswith("46") or "rogaland" in clean_val:
        # Avoid "Vestfold" being caught if we match "Vest" too early
        if "vestfold" in clean_val: return "Sør"
        return "Vest"
    if "sør" in clean_val or "agder" in clean_val or "telemark" in clean_val or "vestfold" in clean_val:
        return "Sør"
    if "øst" in clean_val or "oslo" in clean_val or "viken" in clean_val or "innlandet" in clean_val or "akershus" in clean_val:
        return "Øst"
    
    return get_operational_region(val)


async def get_regional_financials(year: int | None = None):
    """
    Returns financial breakdown by region: planned_rent, actual_rent, other_costs.
    Regioner: Nord, Midt-Norge, Vest, Sør, Øst.
    year: GL-år å hente faktiske kostnader for (default: siste år med data).
    """
    from app.domains.core.models.property import Property
    from app.services.analytics.cost_analysis_service import is_rent_transaction

    async with SessionLocal() as db:
        # 1. Planned Rent per region (from active contracts)
        rent_yearly = func.coalesce(
            Contract.amount['total_per_year'].astext,
            Contract.amount['amount_per_year'].astext
        )
        rent_monthly = func.coalesce(
            Contract.amount['monthly_rent'].astext,
            Contract.amount['amount'].astext
        )
        final_rent = func.coalesce(
            cast(rent_yearly, Float),
            cast(rent_monthly, Float) * 12,
            0.0
        )
        
        rent_stmt = (
            select(Property.region, Property.external_data, func.sum(final_rent).label("planned_rent"))
            .select_from(Contract)
            .join(Unit, Contract.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .where(Contract.status == "active")
            .group_by(Property.region, Property.external_data)
        )
        
        agg = {}
        rent_res = await db.execute(rent_stmt)
        for row in rent_res.mappings().all():
            reg = row.get("region")
            ext_data = row.get("external_data") or {}
            has_bufdir = bool(ext_data.get("bufdir") or ext_data.get("bufdir_institution"))
            canonical = _normalize_region(reg, has_bufdir)
            rent_val = float(row.get("planned_rent") or 0)
            
            if canonical not in agg:
                agg[canonical] = {"planned_rent": 0.0, "actual_rent": 0.0, "other_costs": 0.0}
            agg[canonical]["planned_rent"] += rent_val

        # 2. Actual Rent & Other Costs (from GL transactions)
        # Bruker srs_kategori direkte — netto per property+region+kategori (HAVING SUM > 0)
        gl_stmt = text("""
            SELECT
                p.region,
                p.external_data,
                gt.srs_kategori,
                SUM(gt.belop) AS netto
            FROM gl_transactions gt
            JOIN properties p ON gt.property_id::text = p.property_id::text
            WHERE gt.ar = COALESCE(:year, (SELECT MAX(ar) FROM gl_transactions WHERE property_id IS NOT NULL))
            GROUP BY p.region, p.external_data, gt.srs_kategori
            HAVING SUM(gt.belop) > 0
        """)

        gl_res = await db.execute(gl_stmt, {"year": year})
        for row in gl_res.mappings().all():
            reg = row.get("region")
            ext_data = row.get("external_data") or {}
            has_bufdir = bool(ext_data.get("bufdir") or ext_data.get("bufdir_institution"))
            canonical = _normalize_region(reg, has_bufdir)
            kat = (row.get("srs_kategori") or "").strip()
            netto = float(row.get("netto") or 0)

            if canonical not in agg:
                agg[canonical] = {"planned_rent": 0.0, "actual_rent": 0.0, "other_costs": 0.0}

            # Lokaler = husleie (actual_rent), Drift+Vedlikehold = andre kostnader, Gjennomstrømning = ignorer
            if kat == "Lokaler":
                agg[canonical]["actual_rent"] += netto
            elif kat in ("Drift", "Vedlikehold"):
                agg[canonical]["other_costs"] += netto
            # Gjennomstrømning er pass-through, teller ikke som kostnad

        # Add manual maintenance costs to other_costs
        maint_manual_stmt = select(Property.region, Property.external_data, func.sum(cast(func.coalesce(func.nullif(Property.external_data['financials']['total_manual_expenses'].astext, ''), '0'), Float)).label("manual_maint")).group_by(Property.region, Property.external_data)
        m_res = await db.execute(maint_manual_stmt)
        for row in m_res.mappings().all():
            reg = row.get("region")
            ext_data = row.get("external_data") or {}
            has_bufdir = bool(ext_data.get("bufdir") or ext_data.get("bufdir_institution"))
            canonical = _normalize_region(reg, has_bufdir)
            val = float(row.get("manual_maint") or 0)
            if canonical not in agg:
                agg[canonical] = {"planned_rent": 0.0, "actual_rent": 0.0, "other_costs": 0.0}
            agg[canonical]["other_costs"] += val

        order = ["Nord", "Midt-Norge", "Vest", "Øst", "Sør", "Bufdir"]
        return [
            {
                "region": r, 
                "planned_rent": agg.get(r, {}).get("planned_rent", 0.0),
                "actual_rent": agg.get(r, {}).get("actual_rent", 0.0),
                "other_costs": agg.get(r, {}).get("other_costs", 0.0)
            }
            for r in order
        ]
async def get_detailed_financial_overview():
    """
    Returns detailed financial breakdown (utgifter kun – offentlig org).
    Kun 5 regioner: Nord, Midt-Norge, Vest, Øst, Sør, Bufdir.
    Ingen inntekter/leie – kun vedlikehold og utgifter.
    """
    from app.domains.core.models.property import Property

    async with SessionLocal() as db:
        maint_manual = func.coalesce(func.nullif(Property.external_data['financials']['total_manual_expenses'].astext, ''), '0')
        maint_csv = func.coalesce(func.nullif(Property.external_data['financials']['total_spend_csv'].astext, ''), '0')
        maint_sum = cast(maint_manual, Float) + cast(maint_csv, Float)

        stmt_props = select(
            Property.property_id,
            Property.name,
            Property.address,
            Property.region,
            Property.external_data,
            maint_sum.label("maintenance_cost")
        )
        res_props = await db.execute(stmt_props)
        properties = res_props.mappings().all()

        regions_map = {}
        order = ["Nord", "Midt-Norge", "Vest", "Øst", "Sør", "Bufdir"]

        for p in properties:
            pid = p["property_id"]
            reg = p.get("region")
            ext_data = p.get("external_data") or {}
            has_bufdir = bool(ext_data.get("bufdir") or ext_data.get("bufdir_institution"))
            canonical = _normalize_region(reg, has_bufdir)
            maint = 0.0 # Nullet ut pr brukers forespørsel om å fjerne økonomidata

            if canonical not in regions_map:
                regions_map[canonical] = {
                    "region": canonical,
                    "rent": 0.0,
                    "maintenance": 0.0,
                    "properties": [],
                }

            regions_map[canonical]["maintenance"] += maint
            regions_map[canonical]["properties"].append({
                "property_id": str(pid),
                "name": p.get("name") or p.get("address"),
                "address": p.get("address"),
                "contractedRent": 0,
                "actualAccountingSpend": maint,
            })

        region_list = [regions_map[r] for r in order if r in regions_map]
        for r in region_list:
            r["properties"].sort(key=lambda x: x["actualAccountingSpend"], reverse=True)

        return {
            "regions": region_list,
            "total_portfolio_rent": 0,
            "total_portfolio_maintenance": sum(r["maintenance"] for r in region_list),
        }
