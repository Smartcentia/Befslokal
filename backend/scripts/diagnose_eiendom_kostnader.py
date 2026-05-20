#!/usr/bin/env python3
"""
Diagnostiser hvorfor en eiendom mangler kostnader.

Bruk: cd backend && railway run python3 scripts/diagnose_eiendom_kostnader.py "Familievernkontoret Innlandet Øst - Tynset"
"""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.db.base  # noqa: F401
from sqlalchemy import select, text
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.models.financial_models import GLTransaction


async def main():
    search = sys.argv[1] if len(sys.argv) > 1 else "Familievernkontoret Innlandet Øst - Tynset"

    async with SessionLocal() as db:
        # Finn eiendom
        r = await db.execute(
            select(Property).where(Property.name.ilike(f"%{search}%"))
        )
        props = r.scalars().all()
        if not props:
            r = await db.execute(
                select(Property).where(Property.address.ilike(f"%{search}%"))
            )
            props = r.scalars().all()

        if not props:
            print(f"Ingen eiendom funnet for: {search}")
            return

        for prop in props:
            print("=" * 60)
            print(f"Eiendom: {prop.name}")
            print(f"  property_id:    {prop.property_id}")
            print(f"  address:        {prop.address}")
            print(f"  lokalisering_id: {prop.lokalisering_id!r}")
            print(f"  unit_id_erp:    {prop.unit_id_erp!r}")

            # GL-transaksjoner med property_id
            gl_by_id = await db.execute(text("""
                SELECT COUNT(*), COALESCE(SUM(amount), 0)
                FROM gl_transactions
                WHERE property_id = :pid AND year >= 2024
            """), {"pid": str(prop.property_id)})
            cnt_id, sum_id = gl_by_id.fetchone()
            print(f"\n  GL (property_id): {cnt_id} rader, sum={sum_id:.0f} NOK")

            # GL-transaksjoner med department_code = unit_id_erp
            if prop.unit_id_erp:
                gl_by_dept = await db.execute(text("""
                    SELECT COUNT(*), COALESCE(SUM(amount), 0)
                    FROM gl_transactions
                    WHERE department_code = :dept AND year >= 2024
                """), {"dept": str(prop.unit_id_erp)})
                cnt_dept, sum_dept = gl_by_dept.fetchone()
                print(f"  GL (department_code={prop.unit_id_erp}): {cnt_dept} rader, sum={sum_dept:.0f} NOK")

            # Finn koststeder som inneholder Tynset/Familievern i department_name
            gl_tynset = await db.execute(text("""
                SELECT DISTINCT department_code, department_name, COUNT(*), SUM(amount)
                FROM gl_transactions
                WHERE year >= 2024
                  AND (department_name ILIKE '%tynset%' OR department_name ILIKE '%familievern%innlandet%')
                GROUP BY department_code, department_name
                ORDER BY department_code
                LIMIT 20
            """))
            rows = gl_tynset.fetchall()
            if rows:
                print(f"\n  GL-rader med Tynset/Familievern i department_name:")
                for r in rows:
                    print(f"    {r[0]} | {r[1][:50] if r[1] else '-'} | {r[2]} rader, {r[3]:.0f} NOK")

            # Kontrakter
            units_r = await db.execute(text("""
                SELECT u.unit_id, c.contract_id, c.amount
                FROM units u
                LEFT JOIN contracts c ON c.unit_id = u.unit_id
                WHERE u.property_id = :pid
            """), {"pid": str(prop.property_id)})
            units = units_r.fetchall()
            print(f"\n  Enheter/kontrakter: {len(units)}")
            for u in units[:5]:
                amt = u[2].get("amount_per_year", 0) if isinstance(u[2], dict) else 0
                print(f"    unit={u[0]}, contract={u[1]}, leie={amt}")

            print()


if __name__ == "__main__":
    asyncio.run(main())
