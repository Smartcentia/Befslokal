#!/usr/bin/env python3
"""
Verifiser DATABASE_URL (tilkobling + hvilket miljø du sannsynligvis treffer).

Bruk før dataopprydding / re-import:
  railway run -- bash -c 'cd backend && python3 scripts/verify_db_target.py'
  railway run -- bash -c 'cd backend && python3 scripts/verify_db_target.py --require-staging'

Skriving fra sync_koststed_from_unit_erp.py og destruktive import-flag krever ett av:
  BEFS_DATABASE_TIER=staging
  BEFS_ALLOW_PROD_WRITE=1   (kun når du bevisst går mot prod)

Leser DATABASE_URL fra miljø (f.eks. Railway-inject eller backend/.env via app.config).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from sqlalchemy import text

import app.db.base  # noqa: F401
from app.db.session import SessionLocal


def _sanitize_url(raw: str) -> str:
    try:
        u = urlparse(raw.replace("postgresql+asyncpg://", "postgresql://", 1))
        host = u.hostname or "?"
        db = (u.path or "").lstrip("/") or "?"
        user = u.username or "?"
        return f"{user}@{host}/{db}"
    except Exception:
        return "(kunne ikke parse URL)"


def _is_probably_prod_host(host: str | None) -> bool:
    if not host:
        return False
    h = host.lower()
    if "railway.app" in h and "internal" not in h:
        return True
    if "supabase.co" in h and "pooler" in h:
        return False
    return False


def writes_allowed() -> bool:
    return os.environ.get("BEFS_DATABASE_TIER", "").lower() == "staging" or (
        os.environ.get("BEFS_ALLOW_PROD_WRITE", "").strip() == "1"
    )


async def _ping_db() -> tuple[str, str]:
    async with SessionLocal() as db:
        dbname = (await db.execute(text("SELECT current_database()"))).scalar()
        ver = (await db.execute(text("SELECT version()"))).scalar() or ""
        return str(dbname), str(ver)[:80]


def main() -> None:
    from app.core.config import settings

    ap = argparse.ArgumentParser(description="Verifiser DB-mål for prediksjon-/datajobber")
    ap.add_argument(
        "--require-staging",
        action="store_true",
        help="Avslutt med feilkode 1 hverken BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1",
    )
    args = ap.parse_args()

    raw_url = settings.DATABASE_URL or ""
    if not raw_url:
        print("FEIL: DATABASE_URL er ikke satt.")
        sys.exit(2)

    sync_url = raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    parsed = urlparse(sync_url)
    host = parsed.hostname
    print("DATABASE_URL (maskert):", _sanitize_url(raw_url))
    print("Host:", host or "(ukjent)")
    if _is_probably_prod_host(host):
        print("Merk: vertsnavn kan være delt mellom miljøer — bekreft i Railway/Supabase dashboard.")

    try:
        dbname, ver = asyncio.run(_ping_db())
    except Exception as e:
        print(f"FEIL: Klarte ikke koble til databasen: {e}")
        sys.exit(3)

    print("current_database:", dbname)
    print("server:", ver)
    print("skrivetillatelse (sync/import destructive):", "ja" if writes_allowed() else "nei")
    print("  (sett BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1 for skriving)")

    if args.require_staging and not writes_allowed():
        print("\nFEIL: --require-staging men miljøflagg mangler.")
        sys.exit(1)

    print("\nOK — tilkobling virker.")


if __name__ == "__main__":
    main()
