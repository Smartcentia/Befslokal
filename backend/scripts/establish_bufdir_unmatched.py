#!/usr/bin/env python3
"""
Etabler eiendommer for bufdir-institusjoner som ikke matchet noen eiendom i datasettet.
Oppretter nye Property med samme bufdir-data (navn, beskrivelse, bilde, lovgrunnlag osv.)
og merker dem med syntetiske data (external_data.synthetic = true).
Krever DATABASE_URL (lastes fra .env). Kjør etter match_bufdir_robust.py.
"""
import re
import uuid as uuid_mod
from pathlib import Path
from typing import Optional, Tuple

import asyncio
import json

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
UNMATCHED_FILE = BACKEND_DIR / "bufdir_unmatched.json"
IMAGES_DIR = PROJECT_ROOT / "frontend" / "public" / "bufdir_images"

# Last .env før app-import (så DATABASE_URL er satt)
try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

import sys as _sys
if str(BACKEND_DIR) not in _sys.path:
    _sys.path.insert(0, str(BACKEND_DIR))

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


def _clean_address(addr: Optional[str]) -> str:
    if not addr or not addr.strip():
        return ""
    s = re.sub(r"<[^>]+>", " ", addr).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _extract_besoksadresse(raw_addr: Optional[str]) -> str:
    """Hent besøksadresse fra bufdir-format (Besøksadresse \\n Gate 1, 1234 Sted)."""
    if not raw_addr:
        return ""
    text = raw_addr.replace("\\n", "\n").strip()
    if "besøksadresse" in text.lower():
        parts = re.split(r"\n+", text)
        for p in parts:
            p = re.sub(r"^besøksadresse\s*", "", p, flags=re.I).strip()
            if not p or p.lower().startswith("postadresse"):
                continue
            if re.search(r"\d{4}\s+\w+", p) or any(x in p.lower() for x in ("vei", "vegen", "gate", "gata", "veien")):
                return _clean_address(p)
    return _clean_address(text.split("\n")[0]) if text else ""


def _pick_geocode_place(location: str, index: int) -> str:
    """Plukk én stedsnavn fra location for å spre geokoding (unngå alle i Oslo)."""
    if not location or not location.strip():
        return ""
    parts = re.split(r",\s*|\s+og\s+", location)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]
    if not parts:
        return ""
    chosen = parts[index % len(parts)]
    return f"{chosen}, Norway" if chosen else ""


def _extract_place_from_name(name: str) -> str:
    """Hent stedsnavn fra institusjonsnavn (f.eks. 'X, Bergen' -> 'Bergen, Norway')."""
    if not name or "," not in name:
        return ""
    part = name.split(",")[-1].strip()
    # Fjern region-prefiks som "region sør - "
    part = re.sub(r"^region\s+\w+\s*[-–]\s*", "", part, flags=re.I).strip()
    if part and len(part) < 35 and not part.startswith("("):
        return f"{part}, Norway"
    return ""


# Fallback: norske steder med koordinater (spredt geografisk)
NORWEGIAN_PLACES = [
    ("Bergen", 60.3913, 5.3221),
    ("Trondheim", 63.4305, 10.3951),
    ("Stavanger", 58.9700, 5.7331),
    ("Kristiansand", 58.1594, 8.0186),
    ("Tromsø", 69.6492, 18.9553),
    ("Bodø", 67.2804, 14.4049),
    ("Ålesund", 62.4722, 6.1549),
    ("Drammen", 59.7440, 10.2045),
    ("Skien", 59.2094, 9.6090),
    ("Sandefjord", 59.1314, 10.2166),
    ("Porsgrunn", 59.1405, 9.6561),
    ("Arendal", 58.4618, 8.7720),
    ("Elverum", 60.8815, 11.5621),
    ("Molde", 62.7375, 7.1591),
    ("Lillehammer", 61.1153, 10.4662),
    ("Haugesund", 59.4138, 5.2680),
    ("Mandal", 58.0274, 7.4534),
    ("Larvik", 59.0533, 10.0352),
    ("Kongsberg", 59.6637, 9.6465),
    ("Hamar", 60.7945, 11.0680),
    ("Alta", 69.9689, 23.2717),
    ("Narvik", 68.4382, 17.4278),
    ("Kirkenes", 69.7271, 30.0458),
    ("Malvik", 63.4366, 10.6548),
    ("Nesttun", 60.3158, 5.3544),
    ("Sola", 58.8765, 5.6477),
    ("Fredrikstad", 59.2181, 10.9298),
    ("Sarpsborg", 59.2840, 11.1099),
    ("Moss", 59.4340, 10.6577),
    ("Lillestrøm", 59.9558, 11.0503),
]


async def _geocode_address(address_or_location: str) -> Tuple[Optional[float], Optional[float]]:
    """Geokoder adresse/stedsnavn via Mapbox. Returnerer (lat, lon) eller (None, None)."""
    if not address_or_location or not address_or_location.strip():
        return None, None
    query = address_or_location.strip()
    # Fjern "Syntetisk: " prefiks hvis det brukes som fallback
    if query.lower().startswith("syntetisk:"):
        query = query[10:].strip()
    if not query:
        return None, None
    try:
        from app.services.external.mapbox_client import MapboxClient
        client = MapboxClient()
        if not client.access_token:
            return None, None
        result = await client.geocode_address(query)
        if result and result.get("latitude") is not None and result.get("longitude") is not None:
            return float(result["latitude"]), float(result["longitude"])
    except Exception as e:
        print(f"  ✗ Geokoding feilet for '{query[:50]}...': {e}")
    return None, None


async def _download_image(url: Optional[str], property_id: str) -> Optional[str]:
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            filepath.write_bytes(r.content)
        return f"/bufdir_images/{filename}"
    except Exception as e:
        print(f"  ✗ Bildenedlasting feilet: {e}")
        return None


async def establish_unmatched():
    print("✨ Etablerer eiendommer for bufdir-institusjoner uten treff (syntetiske)")
    print("=" * 60)

    if not UNMATCHED_FILE.exists():
        print(f"❌ Finner ikke {UNMATCHED_FILE}. Kjør match_bufdir_robust.py først.")
        return

    unmatched = json.loads(UNMATCHED_FILE.read_text(encoding="utf-8"))
    if not unmatched:
        print("Ingen umatchade institusjoner å etablere.")
        return

    print(f"Laster {len(unmatched)} umatchade institusjoner")
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    async with SessionLocal() as db:
        created = 0
        for inst in unmatched:
            name = inst.get("name") or "Barnevernsinstitusjon (ufullstendig navn)"
            raw_addr = inst.get("address")
            address = _clean_address(raw_addr) if raw_addr else ""
            if not address:
                location = inst.get("location") or ""
                address = f"Syntetisk: {location}" if location else "Syntetisk: Ukjent adresse"
            city = inst.get("location") or ""
            property_id = uuid_mod.uuid4()
            prop_id_str = str(property_id)

            image_url = inst.get("image_url")
            image_path = await _download_image(image_url, prop_id_str)
            if image_path:
                print(f"  ✓ Bilde: {name[:40]}...")

            # Geokoding: prioriter reell adresse, deretter én plassering fra location (spredt)
            lat, lon = None, None
            geocode_query = _extract_besoksadresse(raw_addr) or ""
            if not geocode_query:
                loc = inst.get("location") or ""
                geocode_query = _pick_geocode_place(loc, created) or _extract_place_from_name(name)
            if geocode_query:
                lat, lon = await _geocode_address(geocode_query)
                if lat is not None and lon is not None:
                    print(f"  ✓ Geokodet: {name[:40]}... -> {lat:.4f}, {lon:.4f}")
                    await asyncio.sleep(0.2)  # Unngå Mapbox rate limit
            if lat is None and NORWEGIAN_PLACES:
                place_name, lat, lon = NORWEGIAN_PLACES[created % len(NORWEGIAN_PLACES)]
                print(f"  ✓ Fallback: {name[:40]}... -> {place_name} ({lat:.4f}, {lon:.4f})")

            bufdir_obj = {
                "bufdir_id": inst.get("id"),
                "institution_name": inst.get("name"),
                "description": inst.get("description") or "",
                "legal_bases": inst.get("legal_bases") or [],
                "owner_type": inst.get("owner_type"),
                "bufdir_url": inst.get("bufdir_url"),
                "email": inst.get("email"),
                "phone": inst.get("phone"),
                "location": inst.get("location"),
                "image_url": image_url,
                "image_path": image_path,
            }
            external_data = {
                "bufdir": bufdir_obj,
                "synthetic": True,
                "synthetic_note": "Etablert fra bufdir – institusjon uten treff i eiendomsregister",
            }

            prop = Property(
                property_id=property_id,
                name=name,
                address=address,
                city=city or None,
                latitude=lat,
                longitude=lon,
                usage="Barnevernsinstitusjon",
                external_data=external_data,
            )
            db.add(prop)
            created += 1

        await db.commit()
        print(f"\n✅ Opprettet {created} syntetiske eiendommer (bufdir uten treff)")

    # Gi alle syntetiske eiendommer (inkl. de vi nettopp opprettet) syntetisk kontrakt og leietaker
    if created > 0:
        import subprocess
        ensure_script = SCRIPT_DIR / "ensure_synthetic_contract_and_tenant.py"
        if ensure_script.exists():
            print("\nKjører ensure_synthetic_contract_and_tenant...")
            subprocess.run([_sys.executable, str(ensure_script)], check=False, cwd=str(BACKEND_DIR))

if __name__ == "__main__":
    asyncio.run(establish_unmatched())
