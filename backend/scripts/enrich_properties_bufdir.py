#!/usr/bin/env python3
"""
Enrich properties with Bufdir data from bufdir_matches_robust.json.
Leser valgfritt backend/bufdir_institutions_detailed.json (etter scrape_bufdir_institution_pages.py)
for galleri, tekstseksjoner og utvidet kontakt.
Writes to external_data["bufdir"]; downloads images to frontend/public/bufdir_images/.
Synkroniserer Property.name og Property.description når det er trygt (se --no-sync-name).

Krever DATABASE_URL (lastes fra .env). Kjør fra prosjektrot:
  python backend/scripts/enrich_properties_bufdir.py
  python backend/scripts/enrich_properties_bufdir.py --force-description

Merk: Dette skriptet må kjøres mot deres faktiske BEFS-database (Postgres med tabellen properties).
Supabase MCP / annet MCP erstatter ikke denne jobben — det laster ned bilder og skriver JSONB til
eiendommer. Krev nett/VPN slik at DATABASE_URL kan nås (DNS). Ved problemer: bruk connection
pooler-URL fra Supabase Dashboard i stedet for direkte db.*.supabase.co hvis nødvendig.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
MATCHES_FILE = BACKEND_DIR / "bufdir_matches_robust.json"
DETAILED_FILE = BACKEND_DIR / "bufdir_institutions_detailed.json"
IMAGES_DIR = PROJECT_ROOT / "frontend" / "public" / "bufdir_images"

sys.path.insert(0, str(SCRIPT_DIR))
from lib.property_name_quality import should_sync_name_from_bufdir
from lib.db_env import require_database_url_for_local_scripts

# Last .env før app-import (så DATABASE_URL er satt)
try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

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


def _guess_ext(url: str, content_type: Optional[str]) -> str:
    for candidate in (content_type or "", url):
        cl = candidate.lower()
        if "jpeg" in cl or "jpg" in cl:
            return "jpg"
        if "png" in cl:
            return "png"
        if "webp" in cl:
            return "webp"
    tail = url.split(".")[-1].split("?")[0].lower()
    if tail in ("jpg", "jpeg", "png", "webp"):
        return "jpg" if tail == "jpeg" else tail
    return "jpg"


async def download_image(url: str, property_id: str) -> Optional[str]:
    """Last ned ett bilde til frontend/public/bufdir_images/; returner relativ sti f.eks. /bufdir_images/{id}.jpg."""
    if not url:
        return None
    try:
        import httpx
    except ImportError:
        return None
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # www.bufdir.no/contentassets/... permanent-redirecter til cms.bufdir.no/...,
        # så vi må følge 301 for å få selve bildet.
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            ext = _guess_ext(url, r.headers.get("content-type"))
            filename = f"{property_id}.{ext}"
            filepath = IMAGES_DIR / filename
            filepath.write_bytes(r.content)
        return f"/bufdir_images/{filename}"
    except Exception as e:
        print(f"  ✗ Bildenedlasting feilet: {e}")
        return None


async def download_gallery_images(
    property_id: str, gallery: list[dict]
) -> list[dict]:
    """Last ned alle galleribilder som {property_id}_{i}.ext; fyll inn local_path per element."""
    if not gallery:
        return []
    try:
        import httpx
    except ImportError:
        return [{**g, "local_path": None} for g in gallery]
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        for i, g in enumerate(gallery):
            url = g.get("url")
            if not url:
                out.append({**g, "local_path": None})
                continue
            try:
                r = await client.get(str(url))
                r.raise_for_status()
                ext = _guess_ext(str(url), r.headers.get("content-type"))
                filename = f"{property_id}_{i}.{ext}"
                filepath = IMAGES_DIR / filename
                filepath.write_bytes(r.content)
                out.append({**g, "local_path": f"/bufdir_images/{filename}"})
            except Exception as e:
                print(
                            f"  ✓ Galleri bilde {i} feilet: {e}")
                out.append({**g, "local_path": None})
    return out


def load_detail_by_bufdir_id() -> dict[Any, Any]:
    """bufdir_id -> detail-dict fra bufdir_institutions_detailed.json."""
    if not DETAILED_FILE.exists():
        return {}
    try:
        data = json.loads(DETAILED_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    m: dict[Any, Any] = {}
    for inst in data.get("institutions", []):
        bid = inst.get("id")
        det = inst.get("detail")
        if bid is not None and isinstance(det, dict):
            m[bid] = det
            m[str(bid)] = det
    return m


def _should_write_description(
    prop: Property, buf_desc: str, force: bool
) -> bool:
    buf_desc = (buf_desc or "").strip()
    if not buf_desc:
        return False
    if force:
        return True
    cur = (prop.description or "").strip()
    return not cur


async def enrich_properties(
    force_description: bool = False, sync_name: bool = True
):
    print("✨ Enriching Properties with Bufdir Data (external_data.bufdir + bilder + navn/beskrivelse)")
    print("=" * 60)

    require_database_url_for_local_scripts()

    if not MATCHES_FILE.exists():
        print(f"❌ Could not find {MATCHES_FILE}")
        return

    matches = json.loads(MATCHES_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(matches)} matches")

    detail_by_id = load_detail_by_bufdir_id()
    if detail_by_id:
        n_ids = len({k for k in detail_by_id if not isinstance(k, str)})
        print(f"Loaded {n_ids} detalj-oppslag fra {DETAILED_FILE.name}")
    else:
        print(f"(Ingen {DETAILED_FILE.name} — kun liste-data og enkeltbilde)")

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    name_updates = 0
    desc_updates = 0

    async with SessionLocal() as db:
        updated_count = 0
        for match in matches:
            prop_id = match.get("property_id")
            bufdir_data = match.get("bufdir_data")
            if not prop_id or not bufdir_data:
                continue
            try:
                uuid_val = UUID(prop_id)
            except (ValueError, TypeError):
                continue

            result = await db.execute(select(Property).where(Property.property_id == uuid_val))
            prop = result.scalar_one_or_none()
            if not prop:
                continue

            if prop.external_data is None:
                prop.external_data = {}

            bufdir_id = bufdir_data.get("id")
            detail: Optional[dict[str, Any]] = None
            if bufdir_id is not None:
                detail = detail_by_id.get(bufdir_id) or detail_by_id.get(str(bufdir_id))

            image_url = bufdir_data.get("image_url")
            image_path: Optional[str] = None
            gallery: list[dict] = []

            if detail and detail.get("gallery"):
                gallery = await download_gallery_images(prop_id, list(detail["gallery"]))
                for g in gallery:
                    lp = g.get("local_path")
                    if lp:
                        image_path = lp
                        image_url = g.get("url") or image_url
                        print(
                            f"  �� Galleri ({len(gallery)} bilder): {str(prop_id)[:8]}…"
                        )
                        break
                if not image_path and image_url:
                    image_path = await download_image(image_url, prop_id)
            else:
                image_path = (
                    await download_image(image_url, prop_id) if image_url else None
                )
                if image_path:
                    print(f"  ✓ Bilde: {prop_id}")

            official_name = (bufdir_data.get("name") or "").strip()
            if detail and detail.get("h1_title"):
                official_name = (detail["h1_title"] or official_name).strip()
            buf_desc = (bufdir_data.get("description") or "").strip()
            if detail and detail.get("intro_text"):
                buf_desc = (detail["intro_text"] or buf_desc).strip()

            if sync_name and official_name and should_sync_name_from_bufdir(
                prop.name, prop.address, official_name
            ):
                prop.name = official_name
                name_updates += 1

            if _should_write_description(prop, buf_desc, force_description):
                prop.description = buf_desc
                desc_updates += 1

            email = bufdir_data.get("email")
            phone = bufdir_data.get("phone")
            contact_postal: Optional[str] = None
            contact_rich_html: Optional[str] = None
            if detail and detail.get("contact"):
                c = detail["contact"]
                contact_rich_html = c.get("rich_html")
                contact_postal = c.get("postal_address")
                if c.get("email"):
                    email = c["email"]
                if c.get("phone"):
                    phone = c["phone"]

            summary = (detail or {}).get("summary") or {}
            content_sections = (detail or {}).get("content_sections") or []

            bufdir_obj: dict[str, Any] = {
                "bufdir_id": bufdir_data.get("id"),
                "institution_name": official_name or bufdir_data.get("name"),
                "description": buf_desc or (bufdir_data.get("description") or ""),
                "legal_bases": bufdir_data.get("legal_bases") or [],
                "owner_type": summary.get("ownership")
                or bufdir_data.get("owner_type"),
                "bufdir_url": bufdir_data.get("bufdir_url"),
                "email": email,
                "phone": phone,
                "location": summary.get("place") or bufdir_data.get("location"),
                "placement_type": summary.get("placement_type"),
                "capacity": summary.get("capacity"),
                "summary": summary if summary else None,
                "contact_postal_address": contact_postal,
                "contact_rich_html": contact_rich_html,
                "content_sections": content_sections,
                "gallery": gallery if gallery else None,
                "image_url": image_url,
                "image_path": image_path,
                "source_detail_url": (detail or {}).get("source_detail_url"),
                "scraped_at": (detail or {}).get("scraped_at"),
                "detail_parse_error": (detail or {}).get("parse_error"),
            }
            prop.external_data["bufdir"] = bufdir_obj
            flag_modified(prop, "external_data")
            updated_count += 1

        await db.commit()
        print(f"\n✅ Enriched {updated_count} properties (external_data.bufdir)")
        print(f"   Navn oppdatert: {name_updates}, beskrivelse oppdatert: {desc_updates}")


def main():
    parser = argparse.ArgumentParser(description="Bufdir-enrich mot bufdir_matches_robust.json")
    parser.add_argument(
        "--force-description",
        action="store_true",
        help="Overskriv Property.description med Bufdir-tekst også når feltet allerede har innhold",
    )
    parser.add_argument(
        "--no-sync-name",
        action="store_true",
        help="Ikke sett Property.name fra Bufdir (kun external_data)",
    )
    args = parser.parse_args()
    asyncio.run(
        enrich_properties(
            force_description=args.force_description,
            sync_name=not args.no_sync_name,
        )
    )


if __name__ == "__main__":
    main()
