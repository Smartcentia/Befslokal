#!/usr/bin/env python3
"""
Søker på nettet etter bilder for barnevernsinstitusjoner som mangler bilde.
Bruker LLM (OpenAI) til å foreslå effektive søkeord, deretter DuckDuckGo bildesøk.
Laster ned til frontend/public/bufdir_images/ og oppdaterer external_data.bufdir.

Krever: DATABASE_URL, nettverkstilgang. For LLM: OPENAI_API_KEY.
Kjør: python backend/scripts/fetch_images_for_barnevern.py [--dry-run] [--limit N] [--no-llm]
"""
import argparse
import asyncio
import re
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
IMAGES_DIR = PROJECT_ROOT / "frontend" / "public" / "bufdir_images"

try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

import sys as _sys
if str(BACKEND_DIR) not in _sys.path:
    _sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, or_
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import SessionLocal
import app.domains.core.models.user  # noqa: F401
from app.domains.core.models.property import Property
import app.domains.core.models.contract  # noqa: F401
import app.domains.core.models.audit  # noqa: F401
import app.domains.core.models.unit  # noqa: F401
import app.domains.core.models.party  # noqa: F401
import app.domains.core.models.center  # noqa: F401
import app.domains.hms.models.risk  # noqa: F401
import app.domains.hms.models.internal_control  # noqa: F401
import app.models.file_meta  # noqa: F401

from app.core.config import settings


async def _llm_suggest_search_queries(prop: Property) -> list[str]:
    """
    Bruk LLM til å foreslå 2–3 søkeord for bildesøk av eiendommen.
    Returnerer liste av søkestrenger (kan være tom ved feil/manglende API-nøkkel).
    """
    if not settings.OPENAI_API_KEY:
        return []
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        name = prop.name or ""
        address = (prop.address or "").replace("Syntetisk:", "").strip()
        city = prop.city or ""
        municipality = prop.municipality or ""
        bufdir_name = ""
        if prop.external_data and isinstance(prop.external_data.get("bufdir"), dict):
            bufdir_name = (prop.external_data["bufdir"].get("institution_name") or
                          prop.external_data["bufdir"].get("bufdir_name") or "")

        user = f"""Barnevernsinstitusjon i Norge:
- Navn: {name or 'Ukjent'}
- Institusjonsnavn (bufdir): {bufdir_name or 'Ikke oppgitt'}
- Adresse: {address or 'Ikke oppgitt'}
- Sted/kommune: {city or municipality or 'Ikke oppgitt'}

Foreslå 2–3 korte søkeord (på norsk) som vil finne bilder av selve bygget/fasaden på DuckDuckGo eller Google bildesøk. Fokuser på stedsnavn, institusjonsnavn og ord som "bygning", "fasade", "inngang".
Returner KUN søkeordene, ett per linje, ingen nummerering eller forklaring."""

        resp = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Du er en ekspert på norske stedsnavn og barnevernsinstitusjoner. Svar kun med søkeord, ett per linje."},
                {"role": "user", "content": user},
            ],
            max_tokens=150,
            temperature=0.3,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return []
        queries = [q.strip() for q in text.split("\n") if q.strip()]
        # Fjern nummerering (1. 2. osv)
        cleaned = []
        for q in queries:
            q = re.sub(r"^\d+[\.\)]\s*", "", q).strip()
            if q and len(q) > 3:
                cleaned.append(q)
        return cleaned[:3]  # Maks 3
    except Exception as e:
        print(f"  ⚠ LLM foreslag feilet: {e}")
        return []


def _search_images_web(query: str, max_results: int = 5) -> list[str]:
    """Søk etter bilder via DuckDuckGo. Returnerer liste av image-URL-er."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.images(
                keywords=query,
                region="no-no",
                safesearch="moderate",
                max_results=max_results,
            ))
        urls = []
        for r in results:
            url = r.get("image") or r.get("url")
            if url and url.startswith("http"):
                urls.append(url)
        return urls
    except Exception as e:
        print(f"  ✗ DuckDuckGo bildesøk feilet: {e}")
        return []


async def _download_image(url: str, property_id: str) -> Optional[str]:
    """Last ned bilde til frontend/public/bufdir_images/. Returnerer relativ sti f.eks. /bufdir_images/{id}.jpg."""
    if not url:
        return None
    try:
        import httpx
    except ImportError:
        return None
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ext = url.split(".")[-1].split("?")[0].lower()
    if ext not in ("jpg", "jpeg", "png", "webp"):
        ext = "jpg"
    filename = f"{property_id}.{ext}"
    filepath = IMAGES_DIR / filename
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            # Sjekk at det ser ut som et bilde
            ct = r.headers.get("content-type", "").lower()
            if "image" not in ct and len(r.content) < 1000:
                return None
            filepath.write_bytes(r.content)
        return f"/bufdir_images/{filename}"
    except Exception as e:
        print(f"  ✗ Nedlasting feilet: {e}")
        return None


def _build_search_query(prop: Property) -> str:
    """Bygg søkeord fra eiendomsnavn, adresse og sted."""
    parts = []
    if prop.name:
        parts.append(prop.name)
    if prop.address:
        # Fjern generiske deler som "Syntetisk:"
        addr = re.sub(r"^Syntetisk:\s*", "", prop.address or "").strip()
        if addr and addr != "Ukjent adresse":
            parts.append(addr)
    if prop.city:
        parts.append(prop.city)
    if prop.municipality and (not prop.city or prop.municipality != prop.city):
        parts.append(prop.municipality)
    if not parts:
        return "barnevernsinstitusjon Norge"
    return " ".join(parts) + " Norge"


async def main(dry_run: bool = False, limit: Optional[int] = None, use_llm: bool = True):
    print("🔍 Søker bilder for barnevernsinstitusjoner uten bilde")
    print("=" * 60)
    if use_llm and settings.OPENAI_API_KEY:
        print("Bruker LLM (OpenAI) for å foreslå søkeord")
    elif use_llm and not settings.OPENAI_API_KEY:
        print("OPENAI_API_KEY ikke satt – bruker kun enkle søkeord")

    async with SessionLocal() as db:
        # Finn barnevern-eiendommer (usage inneholder barnevern)
        stmt = select(Property).where(
            or_(
                Property.usage.ilike("%barnevern%"),
                Property.usage.ilike("%BARNEVERN%"),
            )
        )
        result = await db.execute(stmt)
        all_props = result.scalars().all()

        # Filtrer: mangler image_path OG image_url i bufdir
        without_image = []
        for p in all_props:
            bufdir = (p.external_data or {}).get("bufdir") or {}
            has_path = bool(bufdir.get("image_path"))
            has_url = bool(bufdir.get("image_url"))
            if not has_path and not has_url:
                without_image.append(p)

        print(f"Barnevern-eiendommer totalt: {len(all_props)}")
        print(f"Mangler bilde: {len(without_image)}")

        if not without_image:
            print("\n✅ Alle barnevernsinstitusjoner har allerede bilde.")
            return

        to_process = without_image[:limit] if limit else without_image
        if limit:
            print(f"Behandler (limit={limit}): {len(to_process)}")

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        updated = 0

        for i, prop in enumerate(to_process, 1):
            prop_id_str = str(prop.property_id)
            name = prop.name or "Ukjent"
            fallback_query = _build_search_query(prop)

            # Bygg liste av søkeord: LLM-forslag først, deretter fallback
            queries_to_try = []
            if use_llm and settings.OPENAI_API_KEY:
                llm_queries = await _llm_suggest_search_queries(prop)
                if llm_queries:
                    queries_to_try.extend(llm_queries)
            if fallback_query not in queries_to_try:
                queries_to_try.append(fallback_query)
            if not queries_to_try:
                queries_to_try = [fallback_query]

            print(f"\n[{i}/{len(to_process)}] {name[:50]}...")
            print(f"  Søk: {queries_to_try}")

            if dry_run:
                urls = _search_images_web(queries_to_try[0], max_results=3)
                print(f"  (dry-run) Fant {len(urls)} bilder")
                if urls:
                    print(f"  Første: {urls[0][:80]}...")
                continue

            urls = []
            for q in queries_to_try:
                urls = _search_images_web(q, max_results=5)
                if urls:
                    print(f"  Treff med: «{q}»")
                    break
            if not urls:
                print("  Ingen bilder funnet")
                continue

            image_path = None
            for url in urls:
                image_path = await _download_image(url, prop_id_str)
                if image_path:
                    break

            if not image_path:
                print("  Klarte ikke laste ned noen av bildene")
                continue

            # Oppdater external_data.bufdir
            if prop.external_data is None:
                prop.external_data = {}
            bufdir = prop.external_data.get("bufdir") or {}
            if not isinstance(bufdir, dict):
                bufdir = {}
            bufdir["image_path"] = image_path
            bufdir["image_url"] = urls[0]  # Original URL
            bufdir["image_source"] = "websøk+llm" if (use_llm and settings.OPENAI_API_KEY) else "websøk"
            prop.external_data["bufdir"] = bufdir
            flag_modified(prop, "external_data")
            updated += 1
            print(f"  ✓ Lagret bilde: {image_path}")

        await db.commit()
        print(f"\n✅ Oppdatert {updated} eiendommer med nye bilder")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Søk og last ned bilder for barnevernsinstitusjoner uten bilde"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Kun søk, ikke last ned eller oppdater database",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maks antall eiendommer å behandle (for testing)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Hopp over LLM – bruk kun enkle søkeord (sparer API-kostnad)",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, limit=args.limit, use_llm=not args.no_llm))
