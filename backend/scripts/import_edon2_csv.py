"""
Import fra e-don2/BIRK CSV til BEFS.

Støttede kolonner: Region, Tilhørighet2EnhetID, Tilhørighet2, TilhørighetEnhetID,
Tilhørighet, EnhetID, Enhetsnavn, Enhetskorttype, Enhetstype (Utledet),
Antall G/K - plasser, Antall budsjetterte plasser, Hjemler, Nedlagt Dato,
Eierskapenhet, Lokasjonskode, ePhorte Adm Id, Fylke, Kommune, Adresse,
Postnummer, Poststed, Telefon, Nettside, EPost, Orgnr, Skoleansvarlig,
Vara for skoleansvarlig, Helseansvarlig, Vara for helseansvarlig,
Familieansvarlig, Vara for Familieansvarlig, Leder.

Oppretter/oppdaterer:
- properties: lokalisering_id (Lokasjonskode), name, region, address (null når tom),
  postal_code, city, municipality, affiliation, approved_places, budgeted_places,
  legal_basis, ownership_type, unit_id_erp, unit_short_type, unit_type_derived,
  parent_unit_id_erp, external_data.birk (alle BIRK-spesifikke felt)
- units: department_code (EnhetID), purpose (Enhetsnavn), affiliation,
  approved_places, budgeted_places

Grupperer per Lokasjonskode → én property. Hver rad med EnhetID = unit (avdeling).
Se docs/BEGREPSFORSTÅELSE_OG_DATAORDLISTE.md seksjon 8.1 e-don2/BIRK.

Kjør:
  cd backend && PYTHONPATH=. railway run python3 -m scripts.import_edon2_csv [--csv PATH] [--dry-run] [--parse-only]
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
import app.db.base  # noqa: F401
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
    """Les CSV. Støtter semikolon, komma og tab, flere encodings."""
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        for delim in (";", ",", "\t"):
            try:
                with open(csv_path, newline="", encoding=enc) as f:
                    content = f.read()
                if not content.strip():
                    continue
                lines = content.strip().splitlines()
                # Hopp over ledende tomme rader (f.eks. ;;;;;;;;;;;;;;;;)
                while lines and (
                    not lines[0].strip()
                    or all(c in ";,\t " for c in lines[0].strip())
                ):
                    lines.pop(0)
                if not lines:
                    continue
                content = "\n".join(lines)
                reader = csv.DictReader(io.StringIO(content), delimiter=delim)
                rows = [row for row in reader if any(_norm(v) for v in row.values())]
                if rows and len(rows[0]) > 1:
                    return rows
            except (UnicodeDecodeError, csv.Error):
                continue
    return []


def _is_institution_row(m: dict) -> bool:
    """Rekkefølge: Barnevernsinstitusjon > Institusjonsavdeling > Avdeling."""
    stype = (m.get("unit_short_type") or "").lower()
    if "barnevernsinstitusjon" in stype or "institusjon" in stype and "avdeling" not in stype:
        return True
    return False


def _apply_nested(result: dict) -> dict:
    """Konverter external_data.fylke etc. til nøstet dict. BIRK-felt samles i external_data.birk."""
    out = {}
    ext = {}
    for k, v in result.items():
        if k.startswith("external_data."):
            ext[k.replace("external_data.", "")] = v
        else:
            out[k] = v
    if ext:
        # Bygg birk-objekt for frontend (eget kort)
        birk_keys = (
            "tilhorighet2", "tilhorighet2_enhet_id", "fylke", "nedlagt_dato",
            "ephorte_adm_id", "telefon", "nettside", "epost", "orgnr",
            "skoleansvarlig", "vara_skoleansvarlig", "helseansvarlig",
            "vara_helseansvarlig", "familieansvarlig", "vara_familieansvarlig", "leder",
        )
        birk = {}
        for k in birk_keys:
            v = ext.get(k)
            if v not in (None, ""):
                birk[k] = v
        if out.get("lokalisering_id"):
            birk["lokasjonskode"] = str(out["lokalisering_id"]).strip()
        if birk:
            birk["skoleansvarlig_vara"] = birk.pop("vara_skoleansvarlig", None)
            birk["helseansvarlig_vara"] = birk.pop("vara_helseansvarlig", None)
            birk["familieansvarlig_vara"] = birk.pop("vara_familieansvarlig", None)
            ext["birk"] = {k: v for k, v in birk.items() if v is not None}
        out["external_data"] = ext
    return out


def parse_csv_only(csv_path: str) -> dict:
    """Parse CSV uten DB – for verifisering."""
    rows = load_csv(csv_path)
    if not rows:
        return {"error": "Ingen rader funnet", "rows": 0}

    mapped = []
    for row in rows:
        m = map_row(row, "edon2", normalize_headers=True)
        m = _apply_nested(m)
        if m.get("lokalisering_id"):
            mapped.append(m)

    if not mapped:
        return {"error": "Ingen rader med Lokasjonskode", "rows": len(rows)}

    by_lok: dict[str, list[dict]] = defaultdict(list)
    for m in mapped:
        lid = str(m["lokalisering_id"]).strip()
        by_lok[lid].append(m)

    units_count = sum(len(g) for g in by_lok.values())
    return {
        "rows": len(rows),
        "mapped": len(mapped),
        "properties": len(by_lok),
        "units": units_count,
        "sample": list(by_lok.items())[:3],
    }


async def run_import(csv_path: str, dry_run: bool = False) -> dict:
    """Importer e-don2 CSV til properties og units."""
    rows = load_csv(csv_path)
    if not rows:
        return {"error": "Ingen rader funnet", "rows": 0}

    mapped = []
    for row in rows:
        m = map_row(row, "edon2", normalize_headers=True)
        m = _apply_nested(m)
        if m.get("lokalisering_id"):
            mapped.append(m)

    if not mapped:
        return {"error": "Ingen rader med Lokasjonskode", "rows": len(rows)}

    by_lok: dict[str, list[dict]] = defaultdict(list)
    for m in mapped:
        lid = str(m["lokalisering_id"]).strip()
        by_lok[lid].append(m)

    stats = {"properties_created": 0, "properties_updated": 0, "units_created": 0, "aliases_added": 0}

    async with SessionLocal() as db:
        for lokalisering_id, group in by_lok.items():
            # Property: bruk institusjonsrad eller første rad
            inst_rows = [r for r in group if _is_institution_row(r)]
            first = inst_rows[0] if inst_rows else group[0]

            region_raw = first.get("region")
            region = get_operational_region(region_raw) if region_raw else None
            name = _norm(first.get("name"))
            approved_sum = sum(r.get("approved_places") or 0 for r in group)
            budgeted_sum = sum(r.get("budgeted_places") or 0 for r in group)

            result = await db.execute(
                select(Property).where(Property.lokalisering_id == lokalisering_id)
            )
            prop = result.scalar_one_or_none()

            if prop:
                # Oppdater kun når felt er tomme – behold kunnskap fra tidligere import
                prop.region = region or prop.region
                prop.affiliation = first.get("affiliation") or prop.affiliation
                has_approved = any(m.get("approved_places") is not None for m in group)
                has_budgeted = any(m.get("budgeted_places") is not None for m in group)
                prop.approved_places = approved_sum if (has_approved and prop.approved_places is None) else prop.approved_places
                prop.budgeted_places = budgeted_sum if (has_budgeted and prop.budgeted_places is None) else prop.budgeted_places
                addr = _norm(first.get("address"))
                if addr:
                    prop.address = addr
                elif prop.address == prop.name:
                    prop.address = None  # Rett feil fra tidligere import der navn ble satt som adresse
                prop.postal_code = _norm(first.get("postal_code")) or prop.postal_code
                prop.city = _norm(first.get("city")) or prop.city
                prop.municipality = _norm(first.get("municipality")) or prop.municipality
                prop.legal_basis = _norm(first.get("legal_basis")) or prop.legal_basis
                prop.ownership_type = _norm(first.get("ownership_type")) or prop.ownership_type
                prop.unit_id_erp = _norm(first.get("unit_id_erp")) or prop.unit_id_erp
                prop.unit_short_type = _norm(first.get("unit_short_type")) or prop.unit_short_type
                prop.unit_type_derived = _norm(first.get("unit_type_derived")) or prop.unit_type_derived
                prop.parent_unit_id_erp = _norm(first.get("parent_unit_id_erp")) or prop.parent_unit_id_erp
                if name and name != prop.name:
                    add_property_alias(prop, name, source="edon2_csv")
                    flag_modified(prop, "external_data")
                    stats["aliases_added"] += 1
                elif name and not prop.name:
                    prop.name = name
                ext = dict(prop.external_data or {})
                if first.get("external_data"):
                    for k, v in first["external_data"].items():
                        if k not in ext or ext[k] in (None, ""):
                            ext[k] = v
                    ext["source"] = "edon2_csv"
                    prop.external_data = ext
                    flag_modified(prop, "external_data")
                stats["properties_updated"] += 1
            else:
                prop = Property(
                    lokalisering_id=lokalisering_id,
                    name=name or "Ikke oppgitt",
                    address=_norm(first.get("address")) or None,
                    postal_code=_norm(first.get("postal_code")) or None,
                    city=_norm(first.get("city")) or None,
                    region=region,
                    affiliation=first.get("affiliation"),
                    approved_places=approved_sum or None,
                    budgeted_places=budgeted_sum or None,
                    legal_basis=_norm(first.get("legal_basis")),
                    ownership_type=_norm(first.get("ownership_type")),
                    municipality=_norm(first.get("municipality")),
                    unit_id_erp=_norm(first.get("unit_id_erp")),
                    unit_short_type=_norm(first.get("unit_short_type")),
                    unit_type_derived=_norm(first.get("unit_type_derived")),
                    parent_unit_id_erp=_norm(first.get("parent_unit_id_erp")),
                    external_data={**first.get("external_data", {}), "source": "edon2_csv"},
                )
                db.add(prop)
                await db.flush()
                if name:
                    add_property_alias(prop, name, source="edon2_csv")
                    flag_modified(prop, "external_data")
                    stats["aliases_added"] += 1
                stats["properties_created"] += 1

            if dry_run:
                continue

            # Units: hver rad med EnhetID = avdeling
            existing_units = await db.execute(
                select(Unit).where(Unit.property_id == prop.property_id)
            )
            existing_by_dept = {
                (u.department_code or "").strip(): u
                for u in existing_units.scalars().all()
                if u.department_code
            }

            for m in group:
                enhet_id = m.get("unit_id_erp")
                dept_str = str(enhet_id).strip() if enhet_id else None
                if not dept_str:
                    continue

                unit_name = _norm(m.get("name"))
                affiliation = _norm(m.get("affiliation"))
                approved = m.get("approved_places")
                budgeted = m.get("budgeted_places")

                if dept_str in existing_by_dept:
                    u = existing_by_dept[dept_str]
                    u.purpose = unit_name or u.purpose
                    u.affiliation = affiliation or u.affiliation
                    u.approved_places = approved if approved is not None else u.approved_places
                    u.budgeted_places = budgeted if budgeted is not None else u.budgeted_places
                else:
                    u = Unit(
                        property_id=prop.property_id,
                        department_code=dept_str,
                        purpose=unit_name,
                        affiliation=affiliation,
                        approved_places=approved,
                        budgeted_places=budgeted,
                        external_data={"source": "edon2_csv"},
                    )
                    db.add(u)
                    stats["units_created"] += 1

        if not dry_run:
            await db.commit()

    return {
        "rows": len(rows),
        "mapped": len(mapped),
        "properties": len(by_lok),
        **stats,
    }


def main():
    parser = argparse.ArgumentParser(description="Import e-don2/BIRK CSV til BEFS")
    parser.add_argument("--csv", default="data/birk_institusjoner.csv", help="Sti til CSV (fra backend/)")
    parser.add_argument("--dry-run", action="store_true", help="Kun vis hva som ville blitt importert")
    parser.add_argument("--parse-only", action="store_true", help="Kun parse CSV, ingen DB")
    args = parser.parse_args()

    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"Fil ikke funnet: {csv_path}")
        print("Kopier BIRK-uttrekket til backend/data/birk_institusjoner.csv eller bruk --csv /sti/til/fil.csv")
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
