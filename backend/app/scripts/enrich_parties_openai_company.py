"""
Beriker partier med orgnr ved å søke på nettet og la OpenAI lage en firmaoppsummering
(oversikt, roller, eierskap, økonomi, datterselskap – tilsvarende det man får fra f.eks. Gemini).

Lagrer resultatet i party.external_data["openai_company_summary"] (tekst).

Krever: OPENAI_API_KEY satt. Bruker DuckDuckGo for web-søk (ingen ekstra API-nøkkel).

Kjør fra prosjektrot: ./scripts/kjor_enrich_parties_openai.sh
Eller fra backend:   python3 -m app.scripts.enrich_parties_openai_company [--dry-run] [--limit N]
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), "backend", ".env"))
load_dotenv(os.path.join(os.getcwd(), ".env"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import engine
from app.domains.core.models.party import Party
from app.core.config import settings
from app.services.company_summary_web_llm import fetch_company_summary_via_web_llm


async def enrich_parties_openai_company(dry_run: bool = False, limit: int | None = None) -> int:
    """
    For partier med orgnr: web-søk på firmanavn + orgnr, send snippeter til OpenAI,
    lagre oppsummering i party.external_data["openai_company_summary"].
    """
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    updated_count = 0
    async with AsyncSessionLocal() as db:
        stmt = select(Party).where(
            Party.orgnr.isnot(None),
            Party.orgnr != "",
            Party.orgnr != "000000000",
        )
        if limit:
            stmt = stmt.limit(limit)
        result = await db.execute(stmt)
        parties = result.scalars().all()

        if not getattr(settings, "OPENAI_API_KEY", None) or not (settings.OPENAI_API_KEY or "").strip():
            print("OPENAI_API_KEY ikke satt – hopper over.")
            return 0
        print(f"Fant {len(parties)} partier med orgnr. Beriker med web-søk + OpenAI...")

        for party in parties:
            orgnr = (party.orgnr or "").strip()
            name = (party.name or "").strip()
            if len(orgnr) != 9 or not orgnr.isdigit():
                continue

            print(f"  Søker: {name} {orgnr} Norge...")
            summary = await fetch_company_summary_via_web_llm(name, orgnr, max_search_results=5)
            if not summary:
                continue

            if dry_run:
                print(f"  [dry-run] Ville lagret oppsummering ({len(summary)} tegn) for {name}")
                updated_count += 1
                continue

            ext = dict(party.external_data or {})
            ext["openai_company_summary"] = summary
            party.external_data = ext
            flag_modified(party, "external_data")
            updated_count += 1
            try:
                await db.commit()
            except Exception as e:
                print(f"  Feil ved commit: {e}")
                await db.rollback()

        print(f"Ferdig. Oppdatert {updated_count} partier med openai_company_summary.")
    return updated_count


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    limit = None
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--limit" and i + 1 < len(sys.argv):
            try:
                limit = int(sys.argv[i + 1])
            except ValueError:
                pass
            break
    if dry_run:
        print("Kjører i dry-run (ingen endringer lagres).")
    asyncio.run(enrich_parties_openai_company(dry_run=dry_run, limit=limit))


if __name__ == "__main__":
    main()
