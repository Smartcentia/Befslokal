#!/usr/bin/env python3
"""
Per eiendom og år 2020–2026: GL-total og husleie (samme definisjon som gl-costs + koststed_mapping).

Kjør:
  cd backend && PYTHONPATH=. python3 scripts/audit_property_gl_per_year_2020_2026.py
  (med DATABASE_URL, eller railway run)

Skriver:
  backend/data/property_gl_year_matrix_2020_2026.csv
  backend/data/property_gl_year_summary_2020_2026.md
"""
from __future__ import annotations

import asyncio
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))
os.chdir(_backend)

try:
    from dotenv import load_dotenv
    load_dotenv(_backend / ".env", override=False)
    load_dotenv(_backend.parent / ".env", override=False)
except Exception:
    pass

import app.db.base  # noqa: F401
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.domains.core.models.property import Property as PropertyModel

YEAR_MIN, YEAR_MAX = 2020, 2026
YEARS = list(range(YEAR_MIN, YEAR_MAX + 1))


async def _load_direct_gl(db: AsyncSession) -> dict[tuple[str, int], tuple[float, float]]:
    """(property_id str, år) -> (total, lease)"""
    q = text("""
        SELECT g.property_id::text AS pid, g.ar,
               COALESCE(SUM(g.belop), 0)::float AS tot,
               COALESCE(SUM(CASE WHEN (
                  g.konto_navn IN (
                    'Leie lokaler fra Statsbygg',
                    'Leie lokaler andre utleiere',
                    'Leie parkeringsplass',
                    'Leie av lager/naust/garsjer og lignende',
                    'Husleie'
                  )
                  OR g.konto_navn ILIKE 'Leie %'
               ) THEN g.belop ELSE 0 END), 0)::float AS lease_amt
        FROM gl_transactions g
        WHERE g.property_id IS NOT NULL
          AND g.ar IS NOT NULL
          AND g.ar >= :y0 AND g.ar <= :y1
        GROUP BY g.property_id, g.ar
    """)
    rows = (await db.execute(q, {"y0": YEAR_MIN, "y1": YEAR_MAX})).all()
    out: dict[tuple[str, int], tuple[float, float]] = {}
    for pid, ar, tot, lease_amt in rows:
        out[(pid, int(ar))] = (float(tot or 0), float(lease_amt or 0))
    return out


async def _load_mapped_gl(db: AsyncSession) -> dict[tuple[str, int], tuple[float, float]]:
    """Orphan GL (ingen property_id) kreditert via koststed_mapping — samme prinsipp som gl-costs dim1-filter."""
    q = text("""
        SELECT km.property_id::text AS pid, g.ar,
               COALESCE(SUM(g.belop), 0)::float AS tot,
               COALESCE(SUM(CASE WHEN (
                  g.konto_navn IN (
                    'Leie lokaler fra Statsbygg',
                    'Leie lokaler andre utleiere',
                    'Leie parkeringsplass',
                    'Leie av lager/naust/garsjer og lignende',
                    'Husleie'
                  )
                  OR g.konto_navn ILIKE 'Leie %'
               ) THEN g.belop ELSE 0 END), 0)::float AS lease_amt
        FROM gl_transactions g
        INNER JOIN koststed_mapping km
          ON TRIM(BOTH FROM g.dim1_kode) = TRIM(BOTH FROM km.koststed_kode)
        WHERE g.property_id IS NULL
          AND g.ar IS NOT NULL
          AND g.ar >= :y0 AND g.ar <= :y1
          AND km.property_id IS NOT NULL
        GROUP BY km.property_id, g.ar
    """)
    rows = (await db.execute(q, {"y0": YEAR_MIN, "y1": YEAR_MAX})).all()
    out: dict[tuple[str, int], tuple[float, float]] = {}
    for pid, ar, tot, lease_amt in rows:
        k = (pid, int(ar))
        prev = out.get(k, (0.0, 0.0))
        out[k] = (prev[0] + float(tot or 0), prev[1] + float(lease_amt or 0))
    return out


def _merge(
    a: dict[tuple[str, int], tuple[float, float]],
    b: dict[tuple[str, int], tuple[float, float]],
) -> dict[tuple[str, int], tuple[float, float]]:
    keys = set(a) | set(b)
    out: dict[tuple[str, int], tuple[float, float]] = {}
    for k in keys:
        t0, l0 = a.get(k, (0.0, 0.0))
        t1, l1 = b.get(k, (0.0, 0.0))
        out[k] = (t0 + t1, l0 + l1)
    return out


async def main_async() -> None:
    async with SessionLocal() as db:
        direct = await _load_direct_gl(db)
        mapped = await _load_mapped_gl(db)
        merged = _merge(direct, mapped)

        r = await db.execute(select(PropertyModel.property_id, PropertyModel.name, PropertyModel.region))
        props = r.all()

    n_props = len(props)
    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    any_year = 0

    csv_path = _backend / "data" / "property_gl_year_matrix_2020_2026.csv"
    md_path = _backend / "data" / "property_gl_year_summary_2020_2026.md"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["property_id", "name", "region"]
    for y in YEARS:
        fieldnames.extend([f"tot_{y}", f"lease_{y}", f"has_both_{y}"])
    fieldnames.extend(
        [
            "years_with_gl",
            "years_with_lease",
            "all_years_gl",
            "all_years_lease",
            "all_years_both",
        ]
    )

    rows_out: list[dict] = []

    for pid, name, region in props:
        pid_s = str(pid)
        y_gl = 0
        y_lease = 0
        y_both = 0
        rec: dict = {
            "property_id": pid_s,
            "name": (name or "")[:120],
            "region": region or "",
        }
        for y in YEARS:
            tot, lease_amt = merged.get((pid_s, y), (0.0, 0.0))
            ht = tot > 0.0001
            hl = lease_amt > 0.0001
            rec[f"tot_{y}"] = round(tot, 2)
            rec[f"lease_{y}"] = round(lease_amt, 2)
            rec[f"has_both_{y}"] = 1 if (ht and hl) else 0
            if ht:
                y_gl += 1
            if hl:
                y_lease += 1
            if ht and hl:
                y_both += 1

        rec["years_with_gl"] = y_gl
        rec["years_with_lease"] = y_lease
        rec["all_years_gl"] = 1 if y_gl == len(YEARS) else 0
        rec["all_years_lease"] = 1 if y_lease == len(YEARS) else 0
        rec["all_years_both"] = 1 if y_both == len(YEARS) else 0

        if y_gl > 0:
            any_year += 1

        rows_out.append(rec)

    full_gl_all_years = sum(1 for r in rows_out if r["all_years_gl"])
    full_lease_all_years = sum(1 for r in rows_out if r["all_years_lease"])
    full_both = sum(1 for r in rows_out if r["all_years_both"])

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rec in rows_out:
            w.writerow({k: rec.get(k) for k in fieldnames})

    per_y_tot = {y: 0 for y in YEARS}
    per_y_lease = {y: 0 for y in YEARS}
    per_y_both = {y: 0 for y in YEARS}
    for rec in rows_out:
        for y in YEARS:
            if rec[f"tot_{y}"] > 0.0001:
                per_y_tot[y] += 1
            if rec[f"lease_{y}"] > 0.0001:
                per_y_lease[y] += 1
            if rec[f"has_both_{y}"]:
                per_y_both[y] += 1

    md = [
        "# GL og husleie per år (2020–2026)",
        "",
        f"_Generert: {iso}_",
        "",
        "Grunnlag: `gl_transactions` med `property_id` **eller** `dim1_kode` via `koststed_mapping` (samme kjerne som `GET /properties/{id}/gl-costs`). Husleie: kontonavn i LEASE-settet eller `ILIKE 'Leie %'`.",
        "",
        "## Sammendrag",
        "",
        f"- Eiendommer totalt: **{n_props}**",
        f"- Minst ett år med GL (>0): **{any_year}**",
        f"- Alle år **2020–2026** med GL-total >0: **{full_gl_all_years}**",
        f"- Alle år med husleie-posteringer >0: **{full_lease_all_years}**",
        f"- Alle år med **både** total og husleie: **{full_both}**",
        "",
        "### Eiendommer med data per kalenderår (antall)",
        "",
        "| År | Med GL (total>0) | Med husleie | Med begge |",
        "|---|---:|---:|---:|",
    ]
    for y in YEARS:
        md.append(f"| {y} | {per_y_tot[y]} | {per_y_lease[y]} | {per_y_both[y]} |")

    md.extend(
        [
            "",
            "## Årsvelger i frontend (`/properties/[id]`)",
            "",
            "Dropdown **«Kostnadssjekk per år»** fylles kun med `available_years` fra `getGLCosts` — dvs. **år som faktisk har GL-rader** for eiendommen (property_id + koststed_mapping), **ikke** en fast liste 2020–2026.",
            "Mangler det regnskapsdata for et år, vises ikke det året i listen (kan bli «Ingen år»).",
            "",
            f"Full detalj: `{csv_path.name}`",
            "",
        ]
    )
    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"CSV: {csv_path}")
    print(f"MD:  {md_path}")
    print(
        f"Eiendommer: {n_props}, minst ett år GL: {any_year}, "
        f"alle år GL: {full_gl_all_years}, alle år husleie: {full_lease_all_years}, alle år begge: {full_both}"
    )


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
