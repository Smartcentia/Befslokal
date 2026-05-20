#!/usr/bin/env python3
"""Skriv MAX(created_at) for prediksjon 2027 (budget + ev. salary_costs). Kun lesing."""
from __future__ import annotations

import asyncio
import os
import sys
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
from sqlalchemy import text
from app.db.session import SessionLocal


async def main() -> None:
    async with SessionLocal() as db:
        r = await db.execute(
            text("""
            SELECT data_source,
                   COUNT(*)::int AS n,
                   MIN(created_at) AS first_ts,
                   MAX(created_at) AS last_ts
            FROM budget
            WHERE year = 2027
              AND is_synthetic = true
              AND data_source LIKE 'holt_winters_2027%'
            GROUP BY data_source
            ORDER BY MAX(created_at) DESC NULLS LAST """)
        )
        rows = r.fetchall()
        print("budget (synthetic 2027, holt_winters_*):")
        if not rows:
            print("  (ingen rader)")
        for row in rows:
            print(f"  {row[0]}: n={row[1]}, første={row[2]}, siste={row[3]}")

        r2 = await db.execute(
            text("""
            SELECT COUNT(*)::int, MIN(imported_at), MAX(imported_at)
            FROM salary_costs
            WHERE year = 2027 AND property_id IS NOT NULL
            """)
        )
        s = r2.one()
        print("salary_costs (year=2027, property_id satt):")
        print(f"  antall={s[0]}, første import={s[1]}, siste import={s[2]}")


if __name__ == "__main__":
    asyncio.run(main())
