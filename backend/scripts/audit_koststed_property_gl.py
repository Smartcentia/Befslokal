#!/usr/bin/env python3
"""
Revisjon: koststed (dim1) skal normalt mappes 1:1 til én property.

Rapporterer:
  - properties med samme koststed_kode eller unit_id_erp (skal ikke forekomme)
  - gl_transactions der samme dim1_kode har flere ulike property_id

Kjør: cd backend && railway run bash -c 'PYTHONPATH=. python3 scripts/audit_koststed_property_gl.py'

Avslutter med exit code 1 hvis det finnes konflikter (for CI).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

try:
    from dotenv import load_dotenv

    load_dotenv(_backend / ".env", override=False)
except Exception:
    pass

import app.db.base  # noqa: F401 — modellregistrering
from app.db.session import SessionLocal
from sqlalchemy import text


async def main() -> int:
    ap = argparse.ArgumentParser(description="Audit koststed ↔ property ↔ GL")
    ap.add_argument(
        "--fail-on-conflict",
        action="store_true",
        help="Exit 1 hvis konflikter finnes",
    )
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL mangler.", file=sys.stderr)
        return 2

    conflicts = 0
    async with SessionLocal() as db:
        print("=== properties: duplikat koststed_kode ===")
        r = await db.execute(
            text("""
            SELECT koststed_kode, COUNT(*)::int AS n,
                   array_agg(property_id::text ORDER BY name) AS ids
            FROM properties
            WHERE koststed_kode IS NOT NULL AND TRIM(koststed_kode) <> ''
            GROUP BY koststed_kode
            HAVING COUNT(*) > 1
            ORDER BY n DESC """)
        )
        rows = r.fetchall()
        for row in rows:
            conflicts += 1
            print(f"  koststed_kode={row[0]}  count={row[1]}  properties={row[2][:5]}{'…' if len(row[2]) > 5 else ''}")
        if not rows:
            print("  (ingen)")

        print("\n=== properties: duplikat unit_id_erp ===")
        r = await db.execute(
            text("""
            SELECT unit_id_erp, COUNT(*)::int AS n,
                   array_agg(property_id::text ORDER BY name) AS ids
            FROM properties
            WHERE unit_id_erp IS NOT NULL AND TRIM(unit_id_erp) <> ''
            GROUP BY unit_id_erp
            HAVING COUNT(*) > 1
            ORDER BY n DESC
        """)
        )
        rows = r.fetchall()
        for row in rows:
            conflicts += 1
            print(f"  unit_id_erp={row[0]}  count={row[1]}  properties={row[2][:5]}{'…' if len(row[2]) > 5 else ''}")
        if not rows:
            print("  (ingen)")

        print("\n=== gl_transactions: dim1_kode → flere ulike property_id (kun ikke-null pid) ===")
        r = await db.execute(
            text("""
            SELECT dim1_kode, COUNT(DISTINCT property_id)::int AS n_props
            FROM gl_transactions
            WHERE property_id IS NOT NULL
              AND dim1_kode IS NOT NULL AND TRIM(dim1_kode::text) <> ''
            GROUP BY dim1_kode
            HAVING COUNT(DISTINCT property_id) > 1
            ORDER BY n_props DESC
            LIMIT 80
        """)
        )
        rows = r.fetchall()
        for row in rows:
            conflicts += 1
            print(f"  dim1={row[0]}  distinct_property_id={row[1]}")
        if not rows:
            print("  (ingen)")

    print(f"\nTotalt konflikt-rader (aggregater): {conflicts}")
    if args.fail_on_conflict and conflicts:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
