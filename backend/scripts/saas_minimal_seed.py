"""
Valgfri minimal demo-seed for ny SaaS-instans (ingen import fra BEFS-produksjon).

Krever: alembic upgrade head, DATABASE_URL i miljø.

  SAAS_SEED_DEMO=1 .venv/bin/python scripts/saas_minimal_seed.py

Oppretter én enkel eiendomsrad (kun hvis tabellen er tom). Bruker må fortsatt
opprettes via Supabase / admin-flyt.
"""
from __future__ import annotations

import asyncio
import os
import sys

if __name__ == "__main__":
    _backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend not in sys.path:
        sys.path.insert(0, _backend)

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

import app.db.base  # noqa: F401
from app.db.session import SessionLocal
from sqlalchemy import func, select


async def main() -> int:
    if os.environ.get("SAAS_SEED_DEMO", "").strip() != "1":
        print("Sett SAAS_SEED_DEMO=1 for å kjøre seed (sikkerhet).")
        return 0

    from app.domains.core.models.property import Property

    async with SessionLocal() as session:
        n = (await session.execute(select(func.count()).select_from(Property))).scalar() or 0
        if n > 0:
            print(f"properties har allerede {n} rader — hopper over seed.")
            return 0
        p = Property(
            name="Demo-eiendom",
            address="Eksempelveien 1",
            city="Oslo",
            postal_code="0001",
            region="Ukjent",
            total_area=100.0,
        )
        session.add(p)
        await session.commit()
        print("La inn én demo-eiendom (tom portefølje ellers).")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
