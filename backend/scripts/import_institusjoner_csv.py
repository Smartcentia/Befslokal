"""
Import fra Institusjons-CSV (barnevernsinstitusjoner med plasser) til BEFS.

Oppretter/oppdaterer properties (lokalisering_id, name, region, affiliation,
approved_places, budgeted_places) og units (avdelinger med department_code).

Viktig: Kolonnenavn kan variere mellom CSV-kilder (f.eks. «Enhetens/Institusjonens navn»
vs «Institusjonsnavn»). Alle navnevarianten lagres i properties.external_data.aliases
slik at matching fungerer ved senere import fra andre kilder.

Kjør:
  cd backend && DATABASE_URL=... python -m scripts.import_institusjoner_csv [--csv PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import io
import os
import sys
from collections import defaultdict
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.utils.csv_source_mapping import map_row
from app.domains.core.utils.property_matcher import add_property_alias
from app.domains.core.utils.region_mapping import get_operational_region


def _norm(s: str | None) -> str | None:
    if s is None:
        return None
    t = (s or "").strip()
    return t if t else None


def load_csv(csv_path: str) -> list[dict]:
    """Les CSV. Støtter semikolon og komma, flere encodings."""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        for delim in (";", ","):
            try:
                with open(csv_path, newline="", encoding=enc) as f:
                    content = f.read()
                if not content.strip():
                    continue
                reader = csv.DictReader(io.StringIO(content), delimiter=delim)
                rows = [row for row in reader if any(_norm(v) for v in row.values())]
                if rows:
                    return rows
            except (UnicodeDecodeError, csv.Error):
                continue
    return []


def parse_csv_only(csv_path: str) -> dict:
    """Parse CSV uten DB – for verifisering. Returnerer statistikk."""
    rows = load_csv(csv_path)
    if not rows:
        return {"error": "Ingen rader funnet", "rows": 0}

    mapped = []
    for row in rows:
        m = map_row(row, "institusjoner", normalize_headers=True)
        if m.get("lokalisering_id"):
            mapped.append(m)

    if not mapped:
        return {"error": "Ingen rader med Enhetsnr.", "rows": len(rows)}

    by_institution: dict[str, list[dict]] = defaultdict(list)
    for m in mapped:
        lid = str(m["lokalisering_id"]).strip()
        by_institution[lid].append(m)

    units_count = sum(len(g) for g in by_institution.values())
    return {
        "rows": len(rows),
        "mapped": len(mapped),
        "institutions": len(by_institution),
        "units": units_count,
        "sample": list(by_institution.items())[:3],
    }


async def run_import(csv_path: str, dry_run: bool = False) -> dict:
    """Importer institusjons-CSV til properties og units."""
    rows = load_csv(csv_path)
    if not rows:
        return {"error": "Ingen rader funnet", "rows": 0}

    # Map hver rad til BEFS-felt (støtter varierende kolonnenavn)
    mapped = []
    for row in rows:
        m = map_row(row, "institusjoner", normalize_headers=True)
        if m.get("lokalisering_id"):
            mapped.append(m)

    if not mapped:
        return {"error": "Ingen rader med Enhetsnr.", "rows": len(rows)}

    # Grupper per institusjon (lokalisering_id)
    by_institution: dict[str, list[dict]] = defaultdict(list)
    for m in mapped:
        lid = str(m["lokalisering_id"]).strip()
        by_institution[lid].append(m)

    stats = {"properties_created": 0, "properties_updated": 0, "units_created": 0, "aliases_added": 0}

    async with SessionLocal() as db:
        for lokalisering_id, group in by_institution.items():
            # Aggreger approved_places og budgeted_places på property-nivå
            approved_sum = sum(m.get("approved_places") or 0 for m in group)
            budgeted_sum = sum(m.get("budgeted_places") or 0 for m in group)

            # Første rad for region, affiliation, name
            first = group[0]
            region_raw = first.get("region")
            region = get_operational_region(region_raw) if region_raw else None
            affiliation = first.get("affiliation")
            name = _norm(first.get("name"))

            # Finn eller opprett property
            result = await db.execute(
                select(Property).where(Property.lokalisering_id == lokalisering_id)
            )
            prop = result.scalar_one_or_none()

            if prop:
                # Oppdater
                prop.region = region or prop.region
                prop.affiliation = affiliation or prop.affiliation
                prop.approved_places = approved_sum if approved_sum else prop.approved_places
                prop.budgeted_places = budgeted_sum if budgeted_sum else prop.budgeted_places
                if name and name != prop.name:
                    add_property_alias(prop, name, source="institusjoner_csv")
                    flag_modified(prop, "external_data")
                    stats["aliases_added"] += 1
                elif name and not prop.name:
                    prop.name = name
                stats["properties_updated"] += 1
            else:
                # Opprett
                prop = Property(
                    lokalisering_id=lokalisering_id,
                    name=name,
                    region=region,
                    affiliation=affiliation,
                    approved_places=approved_sum or None,
                    budgeted_places=budgeted_sum or None,
                )
                db.add(prop)
                await db.flush()  # For property_id
                if name:
                    add_property_alias(prop, name, source="institusjoner_csv")
                    flag_modified(prop, "external_data")
                    stats["aliases_added"] += 1
                stats["properties_created"] += 1

            if dry_run:
                continue

            # Opprett/oppdater units (avdelinger)
            existing_units = await db.execute(
                select(Unit).where(Unit.property_id == prop.property_id).options(selectinload(Unit.property))
            )
            existing_by_dept = {
                (u.external_data or {}).get("department_code"): u
                for u in existing_units.scalars().all()
                if (u.external_data or {}).get("department_code")
            }

            for m in group:
                dept_code = m.get("department_code")
                unit_name = _norm(m.get("unit_name"))
                if not dept_code:
                    continue

                ext = {"department_code": str(dept_code).strip(), "source": "institusjoner_csv"}
                if unit_name:
                    ext["avdelingsnavn"] = unit_name

                if dept_code in existing_by_dept:
                    u = existing_by_dept[dept_code]
                    u.purpose = unit_name or u.purpose
                    u.external_data = {**(u.external_data or {}), **ext}
                else:
                    u = Unit(
                        property_id=prop.property_id,
                        purpose=unit_name,
                        external_data=ext,
                    )
                    db.add(u)
                    stats["units_created"] += 1

        if not dry_run:
            await db.commit()

    return {
        "rows": len(rows),
        "mapped": len(mapped),
        "institutions": len(by_institution),
        **stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Import institusjons-CSV til BEFS")
    parser.add_argument("--csv", default="backend/data/institusjoner.csv", help="Sti til CSV-fil")
    parser.add_argument("--dry-run", action="store_true", help="Kun vis hva som ville blitt importert (krever DB)")
    parser.add_argument("--parse-only", action="store_true", help="Kun parse CSV, ingen DB (for verifisering)")
    args = parser.parse_args()

    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"Fil ikke funnet: {csv_path}")
        sys.exit(1)

    if args.parse_only:
        result = parse_csv_only(csv_path)
    else:
        result = asyncio.run(run_import(csv_path, dry_run=args.dry_run))

    if "error" in result:
        print(f"Feil: {result['error']}")
        sys.exit(1)
    print(f"Resultat: {result}")
    if args.dry_run:
        print("(dry-run – ingen endringer lagret)")
    if args.parse_only:
        print("(parse-only – ingen DB-tilkobling)")


if __name__ == "__main__":
    main()
