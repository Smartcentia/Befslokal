"""
Innkjøpsanalyse – pivot over lokalkostnader, reparasjon og vedlikehold.
Aggregerer GL-transaksjoner per kostnadskategori, institusjon og region.
"""
import asyncio
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from collections import defaultdict

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole

router = APIRouter()

# ---------------------------------------------------------------------------
# Kostnadskategori-definisjoner
# ---------------------------------------------------------------------------
# Hver kategori har en liste kontoer og valgfritt statsbygg-filter.
# statsbygg=True → kun transaksjoner der supplier_name ILIKE '%statsbygg%'
# statsbygg=False → transaksjoner der supplier_name NOT ILIKE '%statsbygg%'
# statsbygg=None → alle transaksjoner for kontoen

CATEGORIES = [
    # ── Leie av lokaler ────────────────────────────────────────────────────
    {
        "group": "Leie av lokaler og tilknyttede utgifter",
        "key": "leie_andre",
        "label": "Leie lokaler andre utleiere",
        "accounts": ["6300"],
        "statsbygg": False,
    },
    {
        "group": "Leie av lokaler og tilknyttede utgifter",
        "key": "leie_statsbygg",
        "label": "Leie lokaler fra Statsbygg",
        "accounts": ["6300"],
        "statsbygg": True,
    },
    {
        "group": "Leie av lokaler og tilknyttede utgifter",
        "key": "bad_statsbygg",
        "label": "Fellesutgifter (BAD) Statsbygg",
        "accounts": ["6310"],
        "statsbygg": True,
    },
    {
        "group": "Leie av lokaler og tilknyttede utgifter",
        "key": "bad_andre",
        "label": "Fellesutgifter andre utleiere",
        "accounts": ["6310"],
        "statsbygg": False,
    },
    {
        "group": "Leie av lokaler og tilknyttede utgifter",
        "key": "indre_vedlikehold_statsbygg",
        "label": "Fellesutgifter Statsbygg - indre vedlikehold",
        "accounts": ["6311"],
        "statsbygg": True,
    },
    {
        "group": "Leie av lokaler og tilknyttede utgifter",
        "key": "parkering",
        "label": "Leie parkeringsplass",
        "accounts": ["6301", "6302"],
        "statsbygg": None,
    },
    # ── Energi ─────────────────────────────────────────────────────────────
    {
        "group": "Strøm og oppvarming",
        "key": "strom",
        "label": "Strøm og oppvarming",
        "accounts": ["6340", "6341", "6342", "6345"],
        "statsbygg": None,
    },
    # ── Renhold ────────────────────────────────────────────────────────────
    {
        "group": "Renhold lokaler",
        "key": "renhold",
        "label": "Renhold lokaler",
        "accounts": ["6360", "6361"],
        "statsbygg": None,
    },
    # ── Reparasjon og vedlikehold ──────────────────────────────────────────
    {
        "group": "Reparasjon og vedlikehold leide lokaler",
        "key": "rep_vedlikehold",
        "label": "Reparasjon og vedlikehold leide lokaler",
        "accounts": ["6396", "6398"],
        "statsbygg": None,
    },
    # ── Øvrige driftskostnader ─────────────────────────────────────────────
    {
        "group": "Annen kostnad lokaler",
        "key": "annen_kostnad",
        "label": "Annen kostnad lokaler",
        "accounts": ["6395", "6399", "6630"],
        "statsbygg": None,
    },
    {
        "group": "Vakthold lokaler",
        "key": "vakthold",
        "label": "Vakthold lokaler",
        "accounts": ["6364", "6365"],
        "statsbygg": None,
    },
    {
        "group": "Vaktmestertjenester",
        "key": "vaktmester",
        "label": "Vaktmestertjenester",
        "accounts": ["6390", "6391"],
        "statsbygg": None,
    },
    {
        "group": "Renovasjon, vann, avløp o.l.",
        "key": "renovasjon",
        "label": "Renovasjon, vann, avløp o.l.",
        "accounts": ["6320", "6321"],
        "statsbygg": None,
    },
]

REGION_ORDER = ["Midt-Norge", "Nord", "Sør", "Vest", "Øst", "Bufdir", "Øvrig"]

# Normaliser region-navn fra GL til pivot-kolonner
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
    return _REGION_MAP.get(raw.strip().lower(), raw.strip())


def _fmt(amount: float) -> int:
    """Rund til nærmeste heltall (NOK)."""
    return int(round(amount))


@router.get("/pivot", response_model=Dict[str, Any])
async def get_procurement_pivot(
    year: Optional[int] = Query(None, description="Filtrer på år (f.eks. 2025). Tom = alle år."),
    region: Optional[str] = Query(None, description="Filtrer på region (Nord, Sør, …)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returnerer en innkjøpsanalyse-pivot over lokalkostnader per kostnadskategori,
    institusjon (Dim1T) og region.
    """
    # Build WHERE clause
    where_parts = ["1=1"]
    params: Dict[str, Any] = {}

    if year:
        where_parts.append("ar = :year")
        params["year"] = year
    if region:
        # Match both raw and normalized
        where_parts.append(
            "(LOWER(region) = LOWER(:region) OR LOWER(region) = LOWER(:region2))"
        )
        params["region"] = region
        params["region2"] = region

    where_sql = " AND ".join(where_parts)

    # Fetch all relevant transactions in one query (SRS-skjema: dim1_navn, konto, belop, ar)
    sql = text(f"""
        SELECT
            COALESCE(dim1_navn, '(ikke satt)') AS institution,
            COALESCE(region, '')               AS region_raw,
            konto                              AS account_code,
            COALESCE(leverandor_navn, '')    AS supplier_name,
            property_id::text                  AS property_id,
            SUM(belop)                       AS total
        FROM gl_transactions
        WHERE {where_sql}
          AND konto IS NOT NULL
        GROUP BY dim1_navn, region, konto, leverandor_navn, property_id
        ORDER BY dim1_navn, region
    """)

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    # Also fetch property names for linking
    prop_sql = text("SELECT property_id::text, name FROM properties WHERE name IS NOT NULL")
    prop_result = await db.execute(prop_sql)
    prop_names: Dict[str, str] = {r["property_id"]: r["name"] for r in prop_result.mappings().all()}

    # ── Aggregate into categories ────────────────────────────────────────
    # Structure: category_key → institution → region → amount
    cat_data: Dict[str, Dict[str, Dict[str, float]]] = {
        c["key"]: defaultdict(lambda: defaultdict(float)) for c in CATEGORIES
    }
    # Also track property_id per institution (best match wins)
    inst_prop: Dict[str, str] = {}

    for row in rows:
        acc = str(row["account_code"]).strip()
        supplier = str(row["supplier_name"]).lower()
        is_statsbygg = "statsbygg" in supplier
        institution = str(row["institution"]).strip()
        region_disp = _normalize_region(row["region_raw"])
        amount = float(row["total"] or 0)
        pid = row["property_id"]

        if pid and institution not in inst_prop:
            inst_prop[institution] = pid

        for cat in CATEGORIES:
            if acc not in cat["accounts"]:
                continue
            sb_filter = cat["statsbygg"]
            if sb_filter is True and not is_statsbygg:
                continue
            if sb_filter is False and is_statsbygg:
                continue
            cat_data[cat["key"]][institution][region_disp] += amount

    # ── Build response ────────────────────────────────────────────────────
    # Group categories into groups
    groups_seen: Dict[str, list] = {}
    for cat in CATEGORIES:
        key = cat["key"]
        grp = cat["group"]

        # Build rows for this category
        cat_rows = []
        totals_by_region: Dict[str, float] = defaultdict(float)
        grand_total = 0.0

        for institution, by_region in sorted(
            cat_data[key].items(), key=lambda x: -sum(x[1].values())
        ):
            inst_total = sum(by_region.values())
            if inst_total == 0:
                continue
            pid = inst_prop.get(institution)
            cat_rows.append({
                "institution": institution,
                "property_id": pid,
                "property_name": prop_names.get(pid) if pid else None,
                "by_region": {r: _fmt(by_region.get(r, 0)) for r in REGION_ORDER},
                "total": _fmt(inst_total),
            })
            for reg, amt in by_region.items():
                totals_by_region[reg] += amt
            grand_total += inst_total

        if not cat_rows:
            continue  # skip empty categories

        cat_entry = {
            "key": key,
            "label": cat["label"],
            "rows": cat_rows,
            "totals_by_region": {r: _fmt(totals_by_region.get(r, 0)) for r in REGION_ORDER},
            "grand_total": _fmt(grand_total),
        }

        if grp not in groups_seen:
            groups_seen[grp] = []
        groups_seen[grp].append(cat_entry)

    groups_out = [
        {"group": grp, "categories": cats}
        for grp, cats in groups_seen.items()
    ]

    result = {
        "year": year,
        "region_filter": region,
        "regions": REGION_ORDER,
        "groups": groups_out,
        "total_transactions": len(rows),
    }
    if len(rows) == 0:
        result["message"] = "Ingen regnskapstransaksjoner importert ennå. Last opp CSV via Admin → Økonomidata."
    return result


# ---------------------------------------------------------------------------
# Dynamic pivot – bruker Innkjøpskategorier(T) og Konto(T) direkte fra GL
# ---------------------------------------------------------------------------

# Lokal-relevante kontoer for å begrense støy
_LOCAL_ACCOUNTS = {
    "6300", "6301", "6302", "6310", "6311",
    "6320", "6321", "6340", "6341", "6342", "6345",
    "6360", "6361", "6364", "6365",
    "6390", "6391", "6395", "6396", "6398", "6399", "6630",
}


@router.get("/dynamic", response_model=Dict[str, Any])
async def get_dynamic_pivot(
    year: Optional[int] = Query(None),
    region: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Data-drevet pivot som bruker Innkjøpskategorier(T) → Konto(T) → Enhet (Dim1T)
    direkte fra GL-transaksjonene – tilsvarer Excel-pivotens feltstruktur.
    """
    where_parts = ["1=1"]
    params: Dict[str, Any] = {}

    if year:
        where_parts.append("ar = :year")
        params["year"] = year
    if region:
        where_parts.append(
            "(LOWER(region) = LOWER(:region) OR LOWER(region) = LOWER(:region2))"
        )
        params["region"] = region
        params["region2"] = region

    where_sql = " AND ".join(where_parts)

    sql = text(f"""
        SELECT
            COALESCE(innkjopskategori_navn, '(ukjent kategori)') AS cat_name,
            COALESCE(konto_navn, konto, '(ukjent)')              AS acct_name,
            konto                                                  AS account_code,
            COALESCE(dim1_navn, '(ikke satt)')                     AS institution,
            COALESCE(region, '')                                   AS region_raw,
            property_id::text                                      AS property_id,
            SUM(belop)                                             AS total
        FROM gl_transactions
        WHERE {where_sql}
        GROUP BY innkjopskategori_navn, konto_navn, konto, dim1_navn, region, property_id
        HAVING SUM(belop) != 0
        ORDER BY innkjopskategori_navn, konto_navn, dim1_navn
    """)

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    # Property names for linking
    prop_sql = text("SELECT property_id::text, name FROM properties WHERE name IS NOT NULL")
    prop_result = await db.execute(prop_sql)
    prop_names: Dict[str, str] = {r["property_id"]: r["name"] for r in prop_result.mappings().all()}

    # ── Aggregate: category → account → institution → region → amount ────
    # cat_name → acct_label → institution → region → amount
    from collections import OrderedDict
    tree: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    inst_prop: Dict[str, str] = {}

    for row in rows:
        cat = str(row["cat_name"]).strip()
        acct = str(row["acct_name"]).strip()
        inst = str(row["institution"]).strip()
        region_disp = _normalize_region(row["region_raw"])
        amount = float(row["total"] or 0)
        pid = row["property_id"]

        if pid and inst not in inst_prop:
            inst_prop[inst] = pid

        if cat not in tree:
            tree[cat] = {}
        if acct not in tree[cat]:
            tree[cat][acct] = {}
        if inst not in tree[cat][acct]:
            tree[cat][acct][inst] = defaultdict(float)
        tree[cat][acct][inst][region_disp] += amount

    # ── Build response ────────────────────────────────────────────────────
    groups_out = []
    total_tx = len(rows)

    for cat_name in sorted(tree):
        accounts_out = []
        cat_grand_total = 0.0
        cat_totals_by_region: Dict[str, float] = defaultdict(float)

        for acct_name in sorted(tree[cat_name]):
            inst_data = tree[cat_name][acct_name]
            acct_rows = []
            acct_totals: Dict[str, float] = defaultdict(float)
            acct_grand = 0.0

            for inst in sorted(inst_data, key=lambda x: -sum(inst_data[x].values())):
                by_region = inst_data[inst]
                inst_total = sum(by_region.values())
                if inst_total == 0:
                    continue
                pid = inst_prop.get(inst)
                acct_rows.append({
                    "institution": inst,
                    "property_id": pid,
                    "property_name": prop_names.get(pid) if pid else None,
                    "by_region": {r: _fmt(by_region.get(r, 0)) for r in REGION_ORDER},
                    "total": _fmt(inst_total),
                })
                for reg, amt in by_region.items():
                    acct_totals[reg] += amt
                    cat_totals_by_region[reg] += amt
                acct_grand += inst_total
                cat_grand_total += inst_total

            if not acct_rows:
                continue

            accounts_out.append({
                "key": acct_name,
                "label": acct_name,
                "rows": acct_rows,
                "totals_by_region": {r: _fmt(acct_totals.get(r, 0)) for r in REGION_ORDER},
                "grand_total": _fmt(acct_grand),
            })

        if not accounts_out:
            continue

        groups_out.append({
            "group": cat_name,
            "categories": accounts_out,
            "totals_by_region": {r: _fmt(cat_totals_by_region.get(r, 0)) for r in REGION_ORDER},
            "grand_total": _fmt(cat_grand_total),
        })

    return {
        "year": year,
        "region_filter": region,
        "regions": REGION_ORDER,
        "groups": groups_out,
        "total_transactions": total_tx,
    }


# ---------------------------------------------------------------------------
# Per-region pivot – Kategori → Region → Enhet (tilsvarer "pr. enhet"-fanene)
# ---------------------------------------------------------------------------

@router.get("/per-region", response_model=Dict[str, Any])
async def get_per_region_pivot(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pivot etter Excel-mønsteret «pr. enhet»:
    Kostnadskategori → Region → Institusjon med sum per rad.
    Ingen regionkolonner – én totalkolonne.
    """
    where_parts = ["1=1"]
    params: Dict[str, Any] = {}

    if year:
        where_parts.append("ar = :year")
        params["year"] = year

    where_sql = " AND ".join(where_parts)

    sql = text(f"""
        SELECT
            COALESCE(innkjopskategori_navn, '(ukjent kategori)') AS cat_name,
            COALESCE(konto_navn, konto, '(ukjent)')              AS acct_name,
            konto                                                  AS account_code,
            COALESCE(dim1_navn, '(ikke satt)')                     AS institution,
            COALESCE(region, '')                                   AS region_raw,
            property_id::text                                      AS property_id,
            SUM(belop)                                             AS total
        FROM gl_transactions
        WHERE {where_sql}
        GROUP BY innkjopskategori_navn, konto_navn, konto, dim1_navn, region, property_id
        HAVING SUM(belop) != 0
        ORDER BY innkjopskategori_navn, konto_navn, region, dim1_navn
    """)

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    prop_sql = text("SELECT property_id::text, name FROM properties WHERE name IS NOT NULL")
    prop_result = await db.execute(prop_sql)
    prop_names: Dict[str, str] = {r["property_id"]: r["name"] for r in prop_result.mappings().all()}

    # Structure: cat_name → acct_name → region → institution → amount
    tree: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    inst_prop: Dict[str, str] = {}

    for row in rows:
        cat = str(row["cat_name"]).strip()
        acct = str(row["acct_name"]).strip()
        inst = str(row["institution"]).strip()
        region_disp = _normalize_region(row["region_raw"])
        amount = float(row["total"] or 0)
        pid = row["property_id"]

        if pid and inst not in inst_prop:
            inst_prop[inst] = pid

        tree.setdefault(cat, {}).setdefault(acct, {}).setdefault(region_disp, {})
        tree[cat][acct][region_disp].setdefault(inst, 0.0)
        tree[cat][acct][region_disp][inst] += amount

    # Build output: groups = categories, categories = accounts, rows = regions+institutions
    groups_out = []
    total_tx = len(rows)

    for cat_name in sorted(tree):
        accounts_out = []
        cat_grand = 0.0

        for acct_name in sorted(tree[cat_name]):
            # regions as sub-groups, institutions as rows within each region
            regions_out = []
            acct_grand = 0.0

            for region_label in REGION_ORDER:
                inst_data = tree[cat_name][acct_name].get(region_label, {})
                if not inst_data:
                    continue

                region_rows = []
                region_total = 0.0
                for inst in sorted(inst_data, key=lambda x: -inst_data[x]):
                    amt = inst_data[inst]
                    if amt == 0:
                        continue
                    pid = inst_prop.get(inst)
                    region_rows.append({
                        "institution": inst,
                        "property_id": pid,
                        "property_name": prop_names.get(pid) if pid else None,
                        "total": _fmt(amt),
                    })
                    region_total += amt

                if not region_rows:
                    continue

                regions_out.append({
                    "region": region_label,
                    "rows": region_rows,
                    "region_total": _fmt(region_total),
                })
                acct_grand += region_total

            if not regions_out:
                continue

            accounts_out.append({
                "key": acct_name,
                "label": acct_name,
                "regions": regions_out,
                "grand_total": _fmt(acct_grand),
            })
            cat_grand += acct_grand

        if not accounts_out:
            continue

        groups_out.append({
            "group": cat_name,
            "accounts": accounts_out,
            "grand_total": _fmt(cat_grand),
        })

    return {
        "year": year,
        "groups": groups_out,
        "total_transactions": total_tx,
    }


# ---------------------------------------------------------------------------
# Institution drill-down – leverandører, månedstrend, kategorifordeling
# ---------------------------------------------------------------------------

@router.get("/institution", response_model=Dict[str, Any])
async def get_institution_detail(
    name: str = Query(..., description="Eksakt dim1_navn (koststed) fra GL"),
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Detaljvisning for én institusjon: kostnad per kategori, topp-leverandører
    og månedlig trend. Brukes som drill-down fra pivot-tabellen.
    """
    where_parts = [
        "dim1_navn = :name",
    ]
    params: Dict[str, Any] = {
        "name": name,
    }
    if year:
        where_parts.append("ar = :year")
        params["year"] = year

    where_sql = " AND ".join(where_parts)

    # Cost by account/category
    cat_sql = text(f"""
        SELECT
            COALESCE(konto_navn, konto) AS label,
            konto                       AS account_code,
            SUM(belop)                  AS total
        FROM gl_transactions
        WHERE {where_sql}
        GROUP BY konto_navn, konto
        ORDER BY total DESC
    """)

    # Top suppliers
    sup_sql = text(f"""
        SELECT
            COALESCE(leverandor_navn, '(ukjent)')  AS supplier,
            COUNT(*)                                AS invoice_count,
            SUM(belop)                              AS total
        FROM gl_transactions
        WHERE {where_sql}
          AND leverandor_navn IS NOT NULL
          AND leverandor_navn != ''
        GROUP BY leverandor_navn
        ORDER BY total DESC
        LIMIT 10
    """)

    # Monthly trend (YYYYMM → amount)
    trend_sql = text(f"""
        SELECT
            periode,
            SUM(belop) AS total
        FROM gl_transactions
        WHERE {where_sql}
          AND periode IS NOT NULL
        GROUP BY periode
        ORDER BY periode
    """)

    # Property link (first match)
    prop_sql = text(f"""
        SELECT DISTINCT
            property_id::text,
            region
        FROM gl_transactions
        WHERE dim1_navn = :name
          AND property_id IS NOT NULL
        LIMIT 1
    """)

    cat_res, sup_res, trend_res, prop_res = await asyncio.gather(
        db.execute(cat_sql, params),
        db.execute(sup_sql, params),
        db.execute(trend_sql, params),
        db.execute(prop_sql, {"name": name}),
    )

    cat_rows = cat_res.mappings().all()
    sup_rows = sup_res.mappings().all()
    trend_rows = trend_res.mappings().all()
    prop_rows = prop_res.mappings().all()

    prop_row = prop_rows[0] if prop_rows else None
    grand_total = sum(float(r["total"] or 0) for r in cat_rows)

    return {
        "institution": name,
        "year": year,
        "property_id": prop_row["property_id"] if prop_row else None,
        "region": prop_row["region"] if prop_row else None,
        "grand_total": _fmt(grand_total),
        "cost_by_category": [
            {
                "label": r["label"],
                "account_code": r["account_code"],
                "amount": _fmt(float(r["total"] or 0)),
                "pct": round(float(r["total"] or 0) / grand_total * 100, 1) if grand_total else 0,
            }
            for r in cat_rows
        ],
        "top_suppliers": [
            {
                "name": r["supplier"],
                "invoice_count": int(r["invoice_count"]),
                "amount": _fmt(float(r["total"] or 0)),
                "pct": round(float(r["total"] or 0) / grand_total * 100, 1) if grand_total else 0,
            }
            for r in sup_rows
        ],
        "monthly_trend": [
            {"period": r["periode"], "amount": _fmt(float(r["total"] or 0))}
            for r in trend_rows
        ],
    }


# ---------------------------------------------------------------------------
# Property profiles – kostnad/m², benchmarking mot kontrakt, alderskorrelasjon
# ---------------------------------------------------------------------------

@router.get("/property-profiles", response_model=Dict[str, Any])
async def get_property_profiles(
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Kostnadsprofil per eiendom: kostnad/m², husleie GL vs. kontrakt,
    alder, energimerke. Krever at GL-transaksjoner er matchet til property_id.
    """
    where_parts = [
        "g.property_id IS NOT NULL",
    ]
    params: Dict[str, Any] = {}
    if year:
        where_parts.append("g.ar = :year")
        params["year"] = year

    where_sql = " AND ".join(where_parts)

    # GL costs per property, split by husleie vs. resten
    gl_sql = text(f"""
        SELECT
            g.property_id::text                        AS property_id,
            SUM(CASE WHEN g.konto IN ('6300','6301','6302') THEN g.belop ELSE 0 END) AS husleie_gl,
            SUM(CASE WHEN g.konto IN ('6340','6341','6342','6345') THEN g.belop ELSE 0 END) AS strom,
            SUM(CASE WHEN g.konto IN ('6360','6361') THEN g.belop ELSE 0 END) AS renhold,
            SUM(CASE WHEN g.konto IN ('6396','6398') THEN g.belop ELSE 0 END) AS vedlikehold,
            SUM(g.belop)                              AS total_cost,
            COUNT(*)                                   AS tx_count
        FROM gl_transactions g
        WHERE {where_sql}
        GROUP BY g.property_id
    """)

    # Property attributes
    prop_attr_sql = text("""
        SELECT
            property_id::text,
            name,
            region,
            total_area,
            construction_year,
            energy_label,
            owner_name
        FROM properties
        WHERE property_id IS NOT NULL
    """)

    # Contract annual rent per property (latest active contract)
    contract_sql = text("""
        SELECT
            u.property_id::text,
            SUM(
                CASE
                    WHEN c.amount->>'total_per_year' IS NOT NULL
                    THEN (c.amount->>'total_per_year')::float
                    WHEN c.amount->>'amount_per_year' IS NOT NULL
                    THEN (c.amount->>'amount_per_year')::float
                    ELSE 0
                END
            ) AS contract_rent
        FROM contracts c
        JOIN units u ON u.unit_id = c.unit_id
        WHERE c.status = 'active'
          AND c.category ILIKE '%leie%'
        GROUP BY u.property_id
    """)

    gl_res, prop_res, contract_res = await asyncio.gather(
        db.execute(gl_sql, params),
        db.execute(prop_attr_sql),
        db.execute(contract_sql),
    )

    gl_by_prop = {r["property_id"]: dict(r) for r in gl_res.mappings().all()}
    props = {r["property_id"]: dict(r) for r in prop_res.mappings().all()}
    contract_rent = {r["property_id"]: float(r["contract_rent"] or 0) for r in contract_res.mappings().all()}

    profiles = []
    for pid, gl in gl_by_prop.items():
        p = props.get(pid, {})
        area = p.get("total_area")
        total = float(gl["total_cost"] or 0)
        husleie = float(gl["husleie_gl"] or 0)
        rent = contract_rent.get(pid, 0)

        profile = {
            "property_id": pid,
            "name": p.get("name") or "(ukjent)",
            "region": p.get("region") or "",
            "total_area": area,
            "construction_year": p.get("construction_year"),
            "energy_label": p.get("energy_label"),
            "owner_name": p.get("owner_name"),
            "total_cost": _fmt(total),
            "husleie_gl": _fmt(husleie),
            "strom": _fmt(float(gl["strom"] or 0)),
            "renhold": _fmt(float(gl["renhold"] or 0)),
            "vedlikehold": _fmt(float(gl["vedlikehold"] or 0)),
            "cost_per_sqm": _fmt(total / area) if area and area > 0 else None,
            "contract_rent": _fmt(rent) if rent else None,
            "rent_delta": _fmt(husleie - rent) if rent and husleie else None,
            "tx_count": int(gl["tx_count"] or 0),
        }
        profiles.append(profile)

    # Sort by total cost descending
    profiles.sort(key=lambda x: x["total_cost"] or 0, reverse=True)

    return {
        "year": year,
        "profiles": profiles,
        "total_properties": len(profiles),
    }
