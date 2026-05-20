#!/usr/bin/env python3
"""
Nullstill property_id på gl_transactions som ble feilaktig matchet til fellesbyg via adresse (Dim2).

For fellesbyg som Tærudgata 16 (Portalen) er Dim2 = adresse – men kostnaden tilhører avdelingen,
ikke eiendommen. Transaksjoner matchet via adresse får feil property_id.

Bruk:
    cd backend
    railway run python scripts/fix_fellesbyg_property_mismatch.py [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from sqlalchemy import text

from app.db.session import SessionLocal


FELLESBYGG_ADDRESSES = frozenset({
    "tærudgata 16",
    "tærudgata 16, 2004 lillestrøm",
    "tærudgata 16 2004 lillestrøm",
})


def _is_fellesbyg_address(addr: str | None) -> bool:
    if not addr or len(str(addr).strip()) < 5:
        return False
    s = str(addr).strip().lower()
    clean = s.split(",")[0].strip()
    return clean in FELLESBYGG_ADDRESSES or s in FELLESBYGG_ADDRESSES


async def run(dry_run: bool) -> None:
    async with SessionLocal() as db:
        # Finn eiendommer som er fellesbyg (adresse i blacklist)
        props_rows = await db.execute(text("""
            SELECT property_id::text, name, address
            FROM properties
            WHERE address IS NOT NULL AND address != ''
        """))
        fellesbyg_property_ids = []
        for r in props_rows.fetchall():
            pid, name, addr = r[0], r[1] or "", r[2] or ""
            if _is_fellesbyg_address(addr) or _is_fellesbyg_address(name):
                fellesbyg_property_ids.append(pid)

        if not fellesbyg_property_ids:
            print("Ingen fellesbyg-eiendommer funnet i properties.")
            return

        # For hver fellesbyg: hent unit_id_erp (legitim koststed for eiendommen)
        prop_erp = {}
        for pid in fellesbyg_property_ids:
            row = await db.execute(text("""
                SELECT unit_id_erp FROM properties WHERE property_id = CAST(:pid AS uuid)
            """), {"pid": pid})
            r = row.fetchone()
            prop_erp[pid] = str(r[0]).strip() if r and r[0] else None

        # Finn transaksjoner: property_id = fellesbyg OG department_code != unit_id_erp
        # Disse ble sannsynligvis matchet via Dim2-adresse, ikke via koststed
        to_null = []
        for pid in fellesbyg_property_ids:
            erp = prop_erp.get(pid)
            rows = await db.execute(text("""
                SELECT g.transaction_id::text, g.department_code, g.department_name,
                       g.dim2_name, g.amount, g.year
                FROM gl_transactions g
                WHERE g.property_id = CAST(:pid AS uuid)
                  AND (g.department_code IS NULL OR g.department_code IS DISTINCT FROM :erp)
            """), {"pid": pid, "erp": erp or ""})
            for r in rows.fetchall():
                to_null.append({"transaction_id": r[0], "property_id": pid, "dept": r[1], "amount": float(r[4] or 0)})

        if not to_null:
            print("Ingen transaksjoner å rette.")
            return

        total_amount = sum(t["amount"] for t in to_null)
        print(f"\nFellesbyg-eiendommer: {fellesbyg_property_ids}")
        print(f"Transaksjoner å nullstille: {len(to_null)}")
        print(f"Sum beløp: {total_amount:,.0f} kr")

        if dry_run:
            print("\n[DRY RUN – ingen endringer]")
            return

        # Nullstill property_id – én bulk UPDATE per fellesbyg-eiendom
        updated = 0
        for pid in fellesbyg_property_ids:
            erp = prop_erp.get(pid) or ""
            r = await db.execute(
                text("""
                    UPDATE gl_transactions
                    SET property_id = NULL
                    WHERE property_id = CAST(:pid AS uuid)
                      AND (department_code IS NULL OR department_code IS DISTINCT FROM :erp)
                """),
                {"pid": pid, "erp": erp},
            )
            updated += r.rowcount

        await db.commit()
        print(f"\nOppdatert {updated} transaksjoner (property_id = NULL).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(dry_run=args.dry_run))
