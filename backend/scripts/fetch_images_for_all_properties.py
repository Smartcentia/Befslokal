#!/usr/bin/env python3
"""
Søker på nettet etter bilder og ekstra opplysninger for ALLE eiendommer som mangler bilde.
Bruker DuckDuckGo bildesøk og tekstsøk (ingen LLM).
Laster ned bilder til frontend/public/bufdir_images/ og lagrer i external_data.web_enrichment.

Krever: DATABASE_URL, nettverkstilgang.
Kjør: cd backend && python scripts/fetch_images_for_all_properties.py [--dry-run] [--limit N] [--skip-existing]
"""
import argparse
import asyncio
import re
from datetime import datetime
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

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import SessionLocal
import app.domains.core.models.user  # noqa: F401
from app.domains.core.models.property import Property
import app.domains.core.models.contract  # noqa: F401
import app.domains.core.models.unit  # noqa: F401
import app.domains.core.models.party  # noqa: F401
import app.domains.core.models.center  # noqa: F401
import app.domains.hms.models.risk  # noqa: F401
import app.domains.hms.models.internal_control  # noqa: F401

def _has_image(prop: Property) -> bool:
    """Sjekk om eiendommen allerede har et bilde (bufdir eller web_enrichment)."""
    ext = prop.external_data or {}
    bufdir = ext.get("bufdir") or {}
    web = ext.get("web_enrichment") or {}
    return bool(
        bufdir.get("image_path") or bufdir.get("image_url")
        or web.get("image_path") or web.get("image_url")
    )


def _search_images_web(query: str, max_results: int = 5) -> list[str]:
    """Søk etter bilder via DuckDuckGo."""
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


def _search_text_web(query: str, max_results: int = 3) -> list[dict]:
    """Søk etter tekst via DuckDuckGo. Returnerer liste med {title, snippet, url}."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(keywords=query, region="no-no", max_results=max_results))
        return [
            {"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")}
            for r in results
        ]
    except Exception as e:
        print(f"  ⚠ Tekstsøk feilet: {e}")
        return []


async def _download_image(url: str, property_id: str) -> Optional[str]:
    """Last ned bilde til frontend/public/bufdir_images/."""
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
        addr = re.sub(r"^Syntetisk:\s*", "", prop.address or "").strip()
        if addr and addr != "Ukjent adresse":
            parts.append(addr)
    if prop.city:
        parts.append(prop.city)
    if prop.municipality and (not prop.city or prop.municipality != prop.city):
        parts.append(prop.municipality)
    if not parts:
        return "eiendom Norge"
    return " ".join(parts) + " Norge"


async def main(
    dry_run: bool = False,
    limit: Optional[int] = None,
    skip_existing: bool = True,
    with_text_search: bool = True,
):
    print("🔍 Søker bilder og opplysninger for alle eiendommer (DuckDuckGo)")
    print("=" * 60)

    async with SessionLocal() as db:
        stmt = select(Property).order_by(Property.name, Property.address)
        result = await db.execute(stmt)
        all_props = result.scalars().all()

        if skip_existing:
            without_image = [p for p in all_props if not _has_image(p)]
        else:
            without_image = list(all_props)

        print(f"Eiendommer totalt: {len(all_props)}")
        print(f"Trenger bilde: {len(without_image)}")

        if not without_image:
            print("\n✅ Alle eiendommer har allerede bilde.")
            return

        to_process = without_image[:limit] if limit else without_image
        if limit:
            print(f"Behandler (limit={limit}): {len(to_process)}")

        IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        updated = 0

        for i, prop in enumerate(to_process, 1):
            prop_id_str = str(prop.property_id)
            name = prop.name or "Ukjent"
            query = _build_search_query(prop)

            print(f"\n[{i}/{len(to_process)}] {name[:50]}...")
            print(f"  Søk: {query}")

            if dry_run:
                urls = _search_images_web(query, max_results=3)
                snippets = _search_text_web(query, max_results=2) if with_text_search else []
                print(f"  (dry-run) Bilder: {len(urls)}, snippets: {len(snippets)}")
                if urls:
                    print(f"  Første bilde: {urls[0][:80]}...")
                continue

            urls = _search_images_web(query, max_results=5)
            if urls:
                print(f"  Treff bilder: {len(urls)}")
            else:
                print("  Ingen bilder funnet")

            snippets = _search_text_web(query, max_results=3) if with_text_search else []

            image_path = None
            if urls:
                for url in urls:
                    image_path = await _download_image(url, prop_id_str)
                    if image_path:
                        break

            if not image_path and not snippets:
                continue

            if prop.external_data is None:
                prop.external_data = {}
            web = prop.external_data.get("web_enrichment") or {}
            if not isinstance(web, dict):
                web = {}
            if image_path:
                web["image_path"] = image_path
                web["image_url"] = urls[0] if urls else None
                web["image_source"] = "websøk"
            if snippets:
                web["search_snippets"] = [s.get("snippet", "")[:500] for s in snippets if s.get("snippet")]
                web["search_results"] = [
                    {"title": s.get("title"), "url": s.get("url")}
                    for s in snippets[:5]
                ]
            web["updated_at"] = datetime.utcnow().isoformat() + "Z"
            prop.external_data["web_enrichment"] = web
            flag_modified(prop, "external_data")
            updated += 1
            print(f"  ✓ Lagret: bilde={bool(image_path)}, snippets={len(snippets)}")

        await db.commit()
        print(f"\n✅ Oppdatert {updated} eiendommer med web_enrichment")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Søk og last ned bilder/opplysninger for alle eiendommer uten bilde"
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
        help="Maks antall eiendommer å behandle",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Behandle alle eiendommer (også de som har bilde)",
    )
    parser.add_argument(
        "--no-text-search",
        action="store_true",
        help="Hopp over tekstsøk (kun bilder)",
    )
    args = parser.parse_args()
    asyncio.run(main(
        dry_run=args.dry_run,
        limit=args.limit,
        skip_existing=not args.no_skip_existing,
        with_text_search=not args.no_text_search,
    ))
