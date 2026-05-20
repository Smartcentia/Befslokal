#!/usr/bin/env python3
"""
Legg til eiendomsbilde for eiendommer som mangler.

For eiendommer med lat/lng men uten bufdir-bilde: setter external_data.mapbox_static
så frontend kan vise Mapbox static map som fallback.

For eiendommer med bufdir-match: bildet kommer fra enrich_properties_bufdir (image_path/image_url).

Kjør: cd backend && railway run python3 scripts/legg_til_eiendomsbilde.py [--dry-run]
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app.db.base  # noqa: F401
from sqlalchemy import select
from sqlalchemy.orm import attributes
from app.db.session import SessionLocal
from app.domains.core.models.property import Property


def has_bufdir_image(ext: dict) -> bool:
    if not ext:
        return False
    bufdir = ext.get("bufdir") or ext.get("bufdir_institution")
    if not bufdir:
        return False
    return bool(bufdir.get("image_path") or bufdir.get("image_url"))


async def main():
    parser = argparse.ArgumentParser(description="Legg til mapbox_static for eiendommer uten bilde")
    parser.add_argument("--dry-run", action="store_true", help="Vis kun hva som ville blitt endret")
    args = parser.parse_args()

    async with SessionLocal() as s:
        r = await s.execute(select(Property).where(
            Property.latitude.isnot(None),
            Property.longitude.isnot(None)
        ))
        props_with_coords = r.scalars().all()

        to_update = []
        for prop in props_with_coords:
            ext = dict(prop.external_data or {})
            if has_bufdir_image(ext):
                continue
            if ext.get("mapbox_static"):
                continue
            to_update.append(prop)

        print(f"Eiendommer med koordinater: {len(props_with_coords)}")
        print(f"Uten bufdir-bilde og uten mapbox_static: {len(to_update)}")

        if not to_update:
            print("Ingen eiendommer trenger oppdatering.")
            return

        if not args.dry_run:
            for prop in to_update:
                ext = dict(prop.external_data or {})
                ext["mapbox_static"] = {"lon": prop.longitude, "lat": prop.latitude}
                prop.external_data = ext
                attributes.flag_modified(prop, "external_data")
            await s.commit()
            print(f"Oppdatert {len(to_update)} eiendommer med mapbox_static.")
        else:
            print(f"[--dry-run] Ville sette mapbox_static på {len(to_update)} eiendommer.")


if __name__ == "__main__":
    asyncio.run(main())
