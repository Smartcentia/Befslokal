#!/usr/bin/env python3
"""
Kravsporing:
  - 2025: Alle eiendommer skal ha GL-regnskapsdata (total > 0), samme scope som gl-costs.
  - 2026: Lønnsdata per eiendom i salary_costs (kan være delår / is_partial_year).

Skriver:
  backend/data/property_2025_gl_gaps.csv     — eiendommer uten GL 2025
  backend/data/property_salary_2026_gaps.csv — eiendommer uten salary_costs-rad 2026
  backend/data/property_2025_salary_audit.md — kort sammendrag

Kjør: railway run --service BEFS1 -- bash -c 'cd backend && PYTHONPATH=. python3 scripts/audit_property_2025_gl_and_salary_2026.py'
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

Y_TARGET = 2025
Y_SALARY = 2026


async def _gl_totals_2025(db: AsyncSession) -> dict[str, float]:
    """property_id -> sum belop 2025 (direkte + koststed_mapping), som audit_property_gl_per_year."""
    direct = (
        await db.execute(
            text("""
        SELECT g.property_id::text AS pid,
               COALESCE(SUM(g.belop), 0)::float AS tot
        FROM gl_transactions g
        WHERE g.property_id IS NOT NULL
          AND g.ar = :yr
        GROUP BY g.property_id
 """),
            {"yr": Y_TARGET},
        )
    ).all()
    mapped = (
        await db.execute(
            text("""
        SELECT km.property_id::text AS pid,
               COALESCE(SUM(g.belop), 0)::float AS tot
        FROM gl_transactions g
        INNER JOIN koststed_mapping km
          ON TRIM(BOTH FROM g.dim1_kode) = TRIM(BOTH FROM km.koststed_kode)
        WHERE g.property_id IS NULL
          AND g.ar = :yr
          AND km.property_id IS NOT NULL
        GROUP BY km.property_id
        """),
            {"yr": Y_TARGET},
        )
    ).all()
    out: dict[str, float] = {}
    for pid, tot in direct:
        out[pid] = out.get(pid, 0.0) + float(tot or 0)
    for pid, tot in mapped:
        out[pid] = out.get(pid, 0.0) + float(tot or 0)
    return out


async def _salary_2026_property_ids(db: AsyncSession) -> set[str]:
    rows = (
        await db.execute(
            text("""
        SELECT property_id::text FROM salary_costs
        WHERE year = :yr AND property_id IS NOT NULL
        """),
            {"yr": Y_SALARY},
        )
    ).all()
    return {r[0] for r in rows}


async def main_async() -> None:
    async with SessionLocal() as db:
        gl_by_prop = await _gl_totals_2025(db)
        sal_ids = await _salary_2026_property_ids(db)
        r = await db.execute(
            select(PropertyModel.property_id, PropertyModel.name, PropertyModel.region, PropertyModel.koststed_kode)
        )
        props = r.all()

    iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n = len(props)
    gaps_2025: list[tuple] = []
    gaps_sal: list[tuple] = []

    for pid, name, region, koststed in props:
        pid_s = str(pid)
        tot = gl_by_prop.get(pid_s, 0.0)
        if tot <= 0.0001:
            gaps_2025.append((pid_s, name or "", region or "", koststed or ""))
        if pid_s not in sal_ids:
            gaps_sal.append((pid_s, name or "", region or "", koststed or ""))

    data_dir = _backend / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    p25 = data_dir / "property_2025_gl_gaps.csv"
    p26 = data_dir / "property_salary_2026_gaps.csv"
    pmd = data_dir / "property_2025_salary_audit.md"

    with p25.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["property_id", "name", "region", "koststed_kode"])
        w.writerows(gaps_2025)

    with p26.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["property_id", "name", "region", "koststed_kode"])
        w.writerows(gaps_sal)

    ok_2025 = n - len(gaps_2025)
    ok_sal = n - len(gaps_sal)

    pmd.write_text(
        "\n".join(
            [
                f"# Revisjon 2025-GL og 2026-lønn",
                "",
                f"_Generert: {iso}_",
                "",
                "## Mål 2025 (regnskap / GL)",
                "",
                f"- Eiendommer totalt: **{n}**",
                f"- Med GL-sum > 0 for **{Y_TARGET}**: **{ok_2025}**",
                f"- **Uten** GL for **{Y_TARGET}** (arbeidsliste): **{len(gaps_2025)}** → `{p25.name}`",
                "",
                "## Mål 2026 (lønn per eiendom)",
                "",
                f"- Med rad i `salary_costs` for **{Y_SALARY}** (property_id satt): **{ok_sal}**",
                f"- **Uten** lønnsrad **{Y_SALARY}**: **{len(gaps_sal)}** → `{p26.name}`",
                "",
                "Import: se `salary_import_service`, `scripts/import_lonn_agresso.py`, `scripts/import_innkjop_excel.py`.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Eiendommer: {n}")
    print(f"2025 GL OK: {ok_2025}, mangler: {len(gaps_2025)} → {p25}")
    print(f"2026 lønn OK: {ok_sal}, mangler: {len(gaps_sal)} → {p26}")
    print(f"MD: {pmd}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
