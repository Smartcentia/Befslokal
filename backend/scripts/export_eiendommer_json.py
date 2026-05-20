"""
Eksporter eiendommer, avdelinger (units), kontrakter og leietakere til én JSON-fil
for visuell gjennomgang. Valgfri flat CSV for tabellvisning i Excel/Sheets.

Kjør fra backend:
  cd backend && python scripts/export_eiendommer_json.py
  cd backend && python scripts/export_eiendommer_json.py --also-flat

Filsti: eiendommer_oversikt.json i repo root (overstyres med EXPORT_JSON_PATH).
Med --also-flat skrives også eiendommer_oversikt_flat.csv i samme mappe.

JSON-struktur:
  eiendommer: Liste eiendommer. Hver har har_avdelinger, antall_avdelinger,
    antall_kontrakter og avdelinger[]. Hver avdeling har kontrakter[] med
    leietaker (party). Brukes for eiendom → avdeling → kontrakt → leietaker.
  leietakere_oversikt: Liste leietakere (parties) med minst én kontrakt. Hver
    har party_id, name, orgnr, antall_kontrakter og kontrakter[] med
    contract_id, eiendom { property_id, name, address }, avdeling { unit_id, purpose }.
    Brukes for leietaker → kontrakter → eiendommer.
  sammendrag: antall_eiendommer, antall_avdelinger, antall_kontrakter,
    antall_leietakere_med_kontrakt, antall_eiendommer_uten_avdelinger,
    antall_kontrakter_uten_leietaker, eksportert (ISO-tid).

Flat CSV (--also-flat): Én rad per kontrakt (eller per avdeling uten kontrakt,
eller per eiendom uten avdelinger). Kolonner: eiendom_id, eiendom_navn,
avdeling_id, avdeling_formål, kontrakt_id, kontrakt_status, leietaker_id, leietaker_navn.
"""
import argparse
import asyncio
import csv
import json
import os
import sys
from datetime import date, datetime
from uuid import UUID

# Slik at app-moduler finnes når man kjører fra backend/
if __name__ == "__main__":
    _backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend not in sys.path:
        sys.path.insert(0, _backend)
    _root = os.path.dirname(_backend)
    if _root not in sys.path:
        sys.path.insert(0, _root)

# Last .env slik at DATABASE_URL er satt
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party


def _serial(obj):
    """Konverter UUID, date, datetime til JSON-vennlige typer."""
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, date) and not isinstance(obj, datetime):
        return obj.isoformat() if obj else None
    if isinstance(obj, datetime):
        return obj.isoformat() if obj else None
    return obj


def _property_to_dict(p, avdeling_count=0, kontrakt_count=0):
    return {
        "property_id": _serial(p.property_id),
        "name": p.name,
        "address": p.address,
        "postal_code": p.postal_code,
        "city": p.city,
        "region": p.region,
        "usage": p.usage,
        "lokalisering_id": p.lokalisering_id,
        "total_area": p.total_area,
        "har_avdelinger": avdeling_count > 0,
        "antall_avdelinger": avdeling_count,
        "antall_kontrakter": kontrakt_count,
        "avdelinger": [],
    }


def _unit_to_dict(u):
    return {
        "unit_id": _serial(u.unit_id),
        "address": u.address,
        "purpose": u.purpose,
        "area_sqm": u.area_sqm,
        "floor": u.floor,
        "zone_type": u.zone_type,
        "kontrakter": [],
    }


def _party_to_dict(party):
    if not party:
        return None
    return {
        "party_id": _serial(party.party_id),
        "name": party.name,
        "orgnr": party.orgnr,
        "contact_email": getattr(party, "contact_email", None),
    }


def _contract_to_dict(c):
    return {
        "contract_id": _serial(c.contract_id),
        "status": c.status,
        "category": c.category,
        "start_date": _serial(c.start_date),
        "end_date": _serial(c.end_date),
        "amount": c.amount,
        "has_option": c.has_option,
        "option_deadline": _serial(c.option_deadline),
        "leietaker": _party_to_dict(c.party),
    }


def _write_flat_csv(out_dir: str, eiendommer: list) -> str:
    """Skriv flat CSV: eiendom_id, eiendom_navn, avdeling_id, avdeling_formål, kontrakt_id, kontrakt_status, leietaker_id, leietaker_navn."""
    flat_path = os.path.join(out_dir, "eiendommer_oversikt_flat.csv")
    with open(flat_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
        w.writerow([
            "eiendom_id", "eiendom_navn", "avdeling_id", "avdeling_formål",
            "kontrakt_id", "kontrakt_status", "leietaker_id", "leietaker_navn",
        ])
        for e in eiendommer:
            eid = e.get("property_id") or ""
            enavn = (e.get("name") or "").replace("\n", " ")
            if not e.get("avdelinger"):
                w.writerow([eid, enavn, "", "", "", "", "", ""])
                continue
            for avd in e["avdelinger"]:
                aid = avd.get("unit_id") or ""
                aformaal = (avd.get("purpose") or "").replace("\n", " ")
                if not avd.get("kontrakter"):
                    w.writerow([eid, enavn, aid, aformaal, "", "", "", ""])
                    continue
                for k in avd["kontrakter"]:
                    kid = k.get("contract_id") or ""
                    kstatus = (k.get("status") or "").replace("\n", " ")
                    leietaker = k.get("leietaker") or {}
                    lid = leietaker.get("party_id") or ""
                    lnavn = (leietaker.get("name") or "").replace("\n", " ")
                    w.writerow([eid, enavn, aid, aformaal, kid, kstatus, lid, lnavn])
    return flat_path


async def main(also_flat: bool = False):
    out_path = os.environ.get("EXPORT_JSON_PATH")
    if not out_path:
        # Default: repo root
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.dirname(backend_dir)
        out_path = os.path.join(root_dir, "eiendommer_oversikt.json")

    async with SessionLocal() as session:
        # 1) Alle eiendommer
        result_p = await session.execute(select(Property).order_by(Property.name, Property.address))
        properties = result_p.scalars().all()

        # 2) Alle enheter (avdelinger) med property_id
        result_u = await session.execute(select(Unit).order_by(Unit.property_id, Unit.purpose))
        units = result_u.scalars().all()

        # 3) Alle kontrakter med party
        result_c = await session.execute(
            select(Contract).options(selectinload(Contract.party)).order_by(Contract.unit_id)
        )
        contracts = result_c.scalars().all()

    # Bygg mapping unit_id -> kontrakter
    unit_contracts = {}
    for c in contracts:
        if c.unit_id:
            uid = c.unit_id
            unit_contracts.setdefault(uid, []).append(c)

    # Bygg mapping property_id -> units
    prop_units = {}
    for u in units:
        pid = u.property_id
        prop_units.setdefault(pid, []).append(u)

    unit_map = {u.unit_id: u for u in units}
    prop_map = {p.property_id: p for p in properties}

    # Bygg nested struktur: eiendom -> avdelinger -> kontrakter -> leietaker
    eiendommer = []
    for p in properties:
        p_units = prop_units.get(p.property_id, [])
        kontrakt_count = sum(
            len(unit_contracts.get(u.unit_id, [])) for u in p_units
        )
        d = _property_to_dict(p, avdeling_count=len(p_units), kontrakt_count=kontrakt_count)
        for u in p_units:
            ud = _unit_to_dict(u)
            for c in unit_contracts.get(u.unit_id, []):
                ud["kontrakter"].append(_contract_to_dict(c))
            d["avdelinger"].append(ud)
        eiendommer.append(d)

    # Leietakere_oversikt: per party, alle kontrakter med eiendom og avdeling
    party_contracts = {}
    for c in contracts:
        if not c.party_id:
            continue
        pid = c.party_id
        unit = unit_map.get(c.unit_id) if c.unit_id else None
        prop = prop_map.get(unit.property_id) if unit else None
        entry = {
            "contract_id": _serial(c.contract_id),
            "status": c.status,
            "category": c.category,
            "eiendom": {
                "property_id": _serial(prop.property_id) if prop else None,
                "name": prop.name if prop else None,
                "address": prop.address if prop else None,
            } if prop else None,
            "avdeling": {
                "unit_id": _serial(unit.unit_id) if unit else None,
                "purpose": unit.purpose if unit else None,
            } if unit else None,
        }
        party_contracts.setdefault(pid, []).append(entry)

    all_party_ids = set(party_contracts.keys())
    party_id_to_party = {c.party_id: c.party for c in contracts if c.party}
    def _party_sort_key(pid):
        p = party_id_to_party.get(pid)
        return (getattr(p, "name", None) or "").lower()
    leietakere_oversikt = []
    for party_id in sorted(all_party_ids, key=_party_sort_key):
        party = party_id_to_party.get(party_id)
        leietakere_oversikt.append({
            "party_id": _serial(party_id),
            "name": party.name if party else None,
            "orgnr": party.orgnr if party else None,
            "contact_email": getattr(party, "contact_email", None) if party else None,
            "antall_kontrakter": len(party_contracts[party_id]),
            "kontrakter": party_contracts[party_id],
        })

    antall_eiendommer = len(eiendommer)
    antall_avdelinger = sum(len(e["avdelinger"]) for e in eiendommer)
    antall_kontrakter = sum(len(a["kontrakter"]) for e in eiendommer for a in e["avdelinger"])
    antall_eiendommer_uten_avdelinger = sum(1 for e in eiendommer if not e["har_avdelinger"])
    antall_kontrakter_uten_leietaker = sum(
        1 for c in contracts if not c.party_id
    )
    eksportert = datetime.utcnow().isoformat() + "Z"

    sammendrag = {
        "antall_eiendommer": antall_eiendommer,
        "antall_avdelinger": antall_avdelinger,
        "antall_kontrakter": antall_kontrakter,
        "antall_leietakere_med_kontrakt": len(all_party_ids),
        "antall_eiendommer_uten_avdelinger": antall_eiendommer_uten_avdelinger,
        "antall_kontrakter_uten_leietaker": antall_kontrakter_uten_leietaker,
        "eksportert": eksportert,
    }

    payload = {
        "eiendommer": eiendommer,
        "leietakere_oversikt": leietakere_oversikt,
        "sammendrag": sammendrag,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    if also_flat:
        out_dir = os.path.dirname(out_path)
        flat_path = _write_flat_csv(out_dir, eiendommer)
        print(f"Flat CSV: {flat_path}")

    print(f"Eksportert til {out_path}")
    print(f"  Eiendommer: {sammendrag['antall_eiendommer']}")
    print(f"  Avdelinger: {sammendrag['antall_avdelinger']}")
    print(f"  Kontrakter: {sammendrag['antall_kontrakter']}")
    print(f"  Leietakere (med minst én kontrakt): {sammendrag['antall_leietakere_med_kontrakt']}")
    print(f"  Eiendommer uten avdelinger: {sammendrag['antall_eiendommer_uten_avdelinger']}")
    print(f"  Kontrakter uten leietaker: {sammendrag['antall_kontrakter_uten_leietaker']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eksporter eiendommer, avdelinger, kontrakter og leietakere til JSON (og valgfri flat CSV).")
    parser.add_argument("--also-flat", action="store_true", help="Skriv i tillegg eiendommer_oversikt_flat.csv i samme mappe som JSON")
    args = parser.parse_args()
    asyncio.run(main(also_flat=args.also_flat))
