#!/usr/bin/env python3
"""
Kjør samme logikk som POST /api/v1/admin/economic-import/link-koststed-properties
uten HTTP (krever DATABASE_URL, f.eks. railway run).

  cd backend && PYTHONPATH=. python3 scripts/run_link_koststed_properties.py
"""
from __future__ import annotations

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

from sqlalchemy import text

from app.db.session import SessionLocal


async def main() -> None:
    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL mangler.", file=sys.stderr)
        sys.exit(2)
    async with SessionLocal() as db:
        r1 = await db.execute(
            text("""
 UPDATE koststed_mapping km
        SET property_id = p.property_id
        FROM properties p
        WHERE LOWER(TRIM(km.koststed_navn)) = LOWER(TRIM(p.name))
          AND km.property_id IS NULL
    """)
        )
        exact = r1.rowcount or 0

        r1b = await db.execute(
            text("""
        UPDATE koststed_mapping km
        SET property_id = p.property_id
        FROM properties p
        WHERE km.property_id IS NULL
          AND (
            LOWER(TRIM(p.name)) LIKE '%' || LOWER(TRIM(km.koststed_navn)) || '%'
            OR LOWER(TRIM(km.koststed_navn)) LIKE '%' || LOWER(TRIM(p.name)) || '%'
          )
    """)
        )
        fuzzy = r1b.rowcount or 0
        await db.commit()

        r2 = await db.execute(
            text("""
        UPDATE gl_transactions gl
        SET property_id = km.property_id
        FROM koststed_mapping km
        WHERE gl.dim1_kode = km.koststed_kode
          AND km.property_id IS NOT NULL
          AND gl.property_id IS NULL
    """)
        )
        gl_u = r2.rowcount or 0
        await db.commit()

        total_linked = (
            await db.execute(text("SELECT COUNT(*) FROM gl_transactions WHERE property_id IS NOT NULL"))
        ).scalar()
        total_gl = (await db.execute(text("SELECT COUNT(*) FROM gl_transactions"))).scalar()

    print(f"koststed_matched_exact: {exact}")
    print(f"koststed_matched_fuzzy: {fuzzy}")
    print(f"gl_transactions_updated: {gl_u}")
    print(f"gl_linked_pct: {round(total_linked / total_gl * 100, 1) if total_gl else 0}")


if __name__ == "__main__":
    asyncio.run(main())
