#!/usr/bin/env python3
"""
Sett unit_id_erp på eiendommer som mangler kostnadsdata, ved å matche mot GL department_code/department_name.

1. Finn eiendommer uten GL-kostnader (property_id eller department_code=unit_id_erp)
2. Hent koststeder fra GL med sum(amount) > 0
3. Match eiendom → koststed ved navn (property.name inneholder department_name eller omvendt)
4. Sett unit_id_erp på treff

Kjør: cd backend && railway run python3 scripts/sett_unit_id_erp_manglende_kostnader.py [--dry-run]
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.db.base  # noqa: F401
from sqlalchemy import select, text
from sqlalchemy.orm import attributes
from app.db.session import SessionLocal
from app.domains.core.models.property import Property


def _normalize(s: str) -> str:
    if not s:
        return ""
    s = str(s).lower().strip()
    s = re.sub(r"[^\w\sæøå]", " ", s)
    return " ".join(s.split())


def _words(s: str, min_len: int = 4) -> list:
    return [w for w in _normalize(s).split() if len(w) >= min_len]


def _score_match(prop_name: str, dept_name: str) -> float:
    """Returnerer 0-1: hvor godt prop_name matcher dept_name."""
    if not prop_name or not dept_name:
        return 0.0
    pw = set(_words(prop_name))
    if len(pw) < 2 and len(prop_name) < 15:
        return 0.0  # Unngå "Ra", "Nes" etc.
    pn = _normalize(prop_name)
    dn = _normalize(dept_name)
    if pn in dn or dn in pn:
        return 0.95
    dw = set(_words(dept_name))
    if not pw:
        return 0.0
    overlap = len(pw & dw) / len(pw)
    return overlap


async def main():
    parser = argparse.ArgumentParser(description="Sett unit_id_erp på eiendommer uten kostnader")
    parser.add_argument("--dry-run", action="store_true", help="Vis kun hva som ville blitt endret")
    args = parser.parse_args()

    async with SessionLocal() as db:
        year = 2025
        r = await db.execute(select(Property))
        all_props = r.scalars().all()

        # Bygg: property_id -> total, department_code -> total
        gl_prop = await db.execute(text("""
            SELECT property_id::text, SUM(amount) FROM gl_transactions
            WHERE year = :yr AND amount > 0 AND property_id IS NOT NULL
            GROUP BY property_id
        """), {"yr": year})
        total_by_prop = {row[0]: float(row[1] or 0) for row in gl_prop.fetchall()}

        gl_dept = await db.execute(text("""
            SELECT department_code, SUM(amount) FROM gl_transactions
            WHERE year = :yr AND amount > 0 AND department_code IS NOT NULL
            GROUP BY department_code
        """), {"yr": year})
        total_by_dept = {str(row[0]): float(row[1] or 0) for row in gl_dept.fetchall()}

        props_without_cost = []
        for p in all_props:
            pid = str(p.property_id)
            total = total_by_prop.get(pid, 0)
            if total <= 0 and p.unit_id_erp:
                total += total_by_dept.get(str(p.unit_id_erp), 0)
            if total <= 0:
                props_without_cost.append(p)

        # 2. Koststeder fra GL (department_code, department_name, sum)
        gl_koststeder = await db.execute(text("""
            SELECT department_code, department_name, SUM(amount) as total
            FROM gl_transactions
            WHERE year = :yr AND amount > 0
              AND department_code IS NOT NULL
            GROUP BY department_code, department_name
            HAVING SUM(amount) > 0
            ORDER BY SUM(amount) DESC
        """), {"yr": year})
        koststeder = [(r[0], r[1] or "", float(r[2] or 0)) for r in gl_koststeder.fetchall()]

        # 3. Match
        updates = []
        for prop in props_without_cost:
            best = None
            best_score = 0.0
            for dept_code, dept_name, _ in koststeder:
                sc = _score_match(prop.name or prop.address or "", dept_name)
                if sc > best_score and sc >= 0.65:
                    best_score = sc
                    best = (dept_code, dept_name)
            if best:
                updates.append((prop, best[0], best[1], best_score))

        print(f"Eiendommer totalt: {len(all_props)}")
        print(f"Uten kostnader: {len(props_without_cost)}")
        print(f"Matchet til koststed: {len(updates)}")
        print()
        for prop, dept_code, dept_name, score in updates[:30]:
            print(f"  {prop.name or prop.address} -> {dept_code} ({dept_name[:40]}) score={score:.2f}")

        if not args.dry_run and updates:
            for prop, dept_code, dept_name, _ in updates:
                prop.unit_id_erp = dept_code
            await db.commit()
            print(f"\nOppdatert {len(updates)} eiendommer med unit_id_erp.")
        elif args.dry_run:
            print(f"\n[--dry-run] Ville oppdatere {len(updates)} eiendommer.")


if __name__ == "__main__":
    asyncio.run(main())
