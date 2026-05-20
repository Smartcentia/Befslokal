#!/usr/bin/env python3
"""
Engangsverifisering: eiendomsside-data (plan: verify-db / verify-gl / verify-budget).

Kjør fra backend med .env:
  cd backend && source .venv/bin/activate && set -a && source .env && set +a && python scripts/verify_property_page_data.py

Kjør med Railway (anbefalt når direkte db.*.supabase.co ikke resolver lokalt; bruker pooler-URL):
  cd <repo-root> && railway run -- bash -c 'cd backend && . .venv/bin/activate && python scripts/verify_property_page_data.py'

connect_args matcher app/db/session.py (PgBouncer / statement_cache_size=0).
"""
from __future__ import annotations

import asyncio
import os
import ssl
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
_env = _backend / ".env"
if _env.is_file():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v

if not os.environ.get("DATABASE_URL"):
    print("DATABASE_URL mangler.", file=sys.stderr)
    sys.exit(1)

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

url = os.environ["DATABASE_URL"]
if url.startswith("postgresql://"):
    url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

_ssl: object = ssl.create_default_context()
_ssl.check_hostname = False
_ssl.verify_mode = ssl.CERT_NONE
if url and ".railway.internal" in url:
    _ssl = False

_connect_args = {
    "server_settings": {"application_name": "verify_property_page_data"},
    "ssl": _ssl,
    "statement_cache_size": 0,  # PgBouncer (Supabase pooler)
}

_SQL_FILE = _backend / "scripts" / "verify_property_page_data.sql"


async def main() -> None:
    engine = create_async_engine(url, echo=False, connect_args=_connect_args)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    year = 2026

    async with async_session() as session:
        r = await session.execute(
            text("""
                SELECT property_id::text, name, address, city, postal_code,
                       latitude, longitude,
                       department_code, department_name, koststed_kode,
                       construction_year, approved_places, budgeted_places,
                       center_id, ownership_type, unit_id_erp, unit_short_type, unit_type_derived,
                       owner_name
                FROM properties
                WHERE (name ILIKE '%FVK%Lofoten%Vester%' AND city ILIKE '%Stokmark%')
                   OR (address ILIKE '%Markedsg%' AND postal_code = '8450')
                ORDER BY
                    CASE WHEN address ILIKE '%Markedsg%' THEN 0 ELSE 1 END,
                    name
                LIMIT 1
            """)
        )
        row = r.fetchone()
        if not row:
            r2 = await session.execute(
                text("""
                    SELECT property_id::text, name, city FROM properties
                    WHERE name ILIKE '%FVK%Lofoten%' AND city ILIKE '%Stokmark%'
                    LIMIT 1
                """)
            )
            row = r2.fetchone()

        if not row:
            print("Fant ingen eiendom som matcher FVK Lofoten / Stokmarknes.")
            await engine.dispose()
            sys.exit(2)

        pid = row[0]
        print("=== verify-db: property ===")
        cols = [
            "property_id", "name", "address", "city", "postal_code",
            "latitude", "longitude",
            "department_code", "department_name", "koststed_kode",
            "construction_year", "approved_places", "budgeted_places",
            "center_id", "ownership_type", "unit_id_erp", "unit_short_type", "unit_type_derived",
            "owner_name",
        ]
        for c, v in zip(cols, row):
            print(f"  {c}: {v!r}")

        cr = await session.execute(
            text(
                "SELECT c.name FROM centers c JOIN properties p ON p.center_id = c.center_id "
                "WHERE p.property_id = CAST(:pid AS uuid)"
            ),
            {"pid": pid},
        )
        print(f"  center_name (join centers): {cr.scalar_one_or_none()!r}")

        print("\n=== verify-gl: gl_transactions ===")
        cnt_prop = await session.execute(
            text(
                "SELECT COUNT(*), COALESCE(SUM(belop::numeric),0) FROM gl_transactions "
                "WHERE property_id = CAST(:pid AS uuid) AND ar = :y"
            ),
            {"pid": pid, "y": year},
        )
        c1, s1 = cnt_prop.fetchone()
        print(f"  {year} property_id: {c1} poster, sum beløp={float(s1):,.2f}")

        pr = await session.execute(
            text("SELECT department_code, koststed_kode FROM properties WHERE property_id = CAST(:pid AS uuid)"),
            {"pid": pid},
        )
        dept = pr.fetchone()
        dim1_codes = [x for x in (dept[0], dept[1]) if x]
        for code in dim1_codes:
            cnt_d = await session.execute(
                text(
                    "SELECT COUNT(*), COALESCE(SUM(belop::numeric),0) FROM gl_transactions "
                    "WHERE dim1_kode = :code AND ar = :y"
                ),
                {"code": code, "y": year},
            )
            c2, s2 = cnt_d.fetchone()
            print(f"  {year} dim1_kode={code!r}: {c2} poster, sum={float(s2):,.2f}")
        if not dim1_codes:
            print("  (ingen department_code/koststed_kode)")

        print("\n=== verify-budget: budget ===")
        br = await session.execute(
            text(
                "SELECT COUNT(*), COALESCE(SUM(amount::numeric),0) FROM budget "
                "WHERE property_id = CAST(:pid AS uuid) AND year = :y"
            ),
            {"pid": pid, "y": year},
        )
        bc, bs = br.fetchone()
        print(f"  {year}: {bc} rader, sum amount={float(bs):,.2f}")

    await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(
            "Kunne ikke koble til databasen (nettverk/DNS eller feil URL).",
            f"Feil: {e!r}",
            f"Kjør verifisering manuelt: psql med {_SQL_FILE}",
            sep="\n",
            file=sys.stderr,
        )
        sys.exit(3)
