"""
Slår opp manglende forelder (parent) for eiendommer via Brønnøysund Enhetsregisteret.

For eiendommer som mangler parent_unit_id_erp (eller der forelder ikke finnes i DB):
hvis eiendommen har org_number, kalles Brønnøysund API underenheter/{orgnr}.
Hvis underenheten har overordnetEnhet, sjekkes det om vi har en eiendom i DB med
org_number = overordnetEnhet. Da får vi et «treff» som kan brukes til manuell
kobling eller senere lagring (f.eks. parent_org_number).

Krever ikke API-nøkkel (Brønnøysund er åpent). Supabase: SUPABASE_SERVICE_ROLE_KEY.

Kjør: SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/slaa_opp_manglende_parent_brreg.py [--csv UTFIL]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time

import requests

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vwvhxcqxadblrftuvsds.supabase.co")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
REST_URL = f"{SUPABASE_URL}/rest/v1"
HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}
BRREG_UNDERENHET = "https://data.brreg.no/enhetsregisteret/api/underenheter"


def _norm_org(s: str | None) -> str | None:
    if not s:
        return None
    t = "".join(c for c in (s or "").strip() if c.isdigit())
    if len(t) == 9:
        return t
    if len(t) == 6:
        return "0" + t  # no leading zero
    return t if t else None


def _check_supabase_resp(resp: requests.Response, context: str = "") -> None:
    if resp.status_code == 401:
        print("Feil: 401 Unauthorized fra Supabase.")
        print("Bruk service_role-nøkkel (ikke anon key). Sett SUPABASE_SERVICE_ROLE_KEY i miljøet eller i backend/.env")
        print("Supabase Dashboard → Project Settings → API → service_role (secret)")
        resp.raise_for_status()
    resp.raise_for_status()


def get_properties_with_org() -> list[dict]:
    """Hent alle properties med org_number (Supabase REST)."""
    params = {"select": "property_id,name,address,org_number,parent_unit_id_erp,unit_id_erp", "org_number": "not.is.null"}
    resp = requests.get(f"{REST_URL}/properties", headers=HEADERS, params=params, timeout=60)
    _check_supabase_resp(resp)
    return resp.json()


def get_all_properties_for_parent_map() -> list[dict]:
    """Hent alle properties (for å bygge org_number → property_id)."""
    # PostgREST pagination: get in chunks
    out = []
    offset = 0
    page_size = 1000
    while True:
        params = {"select": "property_id,name,org_number", "offset": offset, "limit": page_size}
        resp = requests.get(f"{REST_URL}/properties", headers=HEADERS, params=params, timeout=60)
        _check_supabase_resp(resp)
        data = resp.json()
        if not data:
            break
        out.extend(data)
        if len(data) < page_size:
            break
        offset += page_size
    return out


def brreg_get_underenhet(orgnr: str) -> dict | None:
    """Hent underenhet fra Brønnøysund. Returnerer None ved 404 eller feil."""
    o = _norm_org(orgnr)
    if not o or len(o) != 9:
        return None
    try:
        r = requests.get(f"{BRREG_UNDERENHET}/{o}", timeout=10)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Slå opp manglende parent via Brønnøysund")
    parser.add_argument("--csv", default="", help="Skriv treff til CSV-fil (sti)")
    parser.add_argument("--delay", type=float, default=0.2, help="Pause mellom Brønnøysund-kall (sek)")
    args = parser.parse_args()

    if not SERVICE_KEY:
        print("Mangler SUPABASE_SERVICE_ROLE_KEY / SUPABASE_SERVICE_KEY.")
        sys.exit(1)

    print("Henter alle eiendommer fra Supabase...")
    all_props = get_all_properties_for_parent_map()
    org_to_property = {}
    for p in all_props:
        o = _norm_org(p.get("org_number"))
        if o and o not in org_to_property:
            org_to_property[o] = {"property_id": str(p["property_id"]), "name": p.get("name") or p.get("address") or ""}

    print("Henter eiendommer med org_number (kandidater for oppslag)...")
    with_org = get_properties_with_org()

    # «Mangler parent»: har ikke parent_unit_id_erp satt (eller vi ignorerer om de allerede har)
    missing = [p for p in with_org if not (p.get("parent_unit_id_erp") or "").strip()]
    print(f"Antall med org_number som mangler parent_unit_id_erp: {len(missing)}")

    treff = []
    for p in missing:
        orgnr = _norm_org(p.get("org_number"))
        if not orgnr:
            continue
        time.sleep(args.delay)
        data = brreg_get_underenhet(orgnr)
        if not data:
            continue
        overordnet = data.get("overordnetEnhet")
        if not overordnet:
            continue
        overordnet = _norm_org(overordnet) or overordnet
        parent_candidate = org_to_property.get(overordnet) if overordnet else None
        treff.append({
            "property_id": str(p["property_id"]),
            "name": p.get("name") or p.get("address") or "",
            "org_number": orgnr,
            "overordnetEnhet": overordnet,
            "parent_property_id": parent_candidate["property_id"] if parent_candidate else "",
            "parent_name": parent_candidate["name"] if parent_candidate else "",
        })

    print(f"\nTreff (underenhet med overordnetEnhet i Brønnøysund): {len(treff)}")
    for t in treff[:30]:
        parent_info = f" -> {t['parent_name']} ({t['parent_property_id']})" if t.get("parent_property_id") else " (ingen eiendom i DB med dette orgnr)"
        print(f"  {t['name'][:50]} orgnr {t['org_number']} overordnet {t['overordnetEnhet']}{parent_info}")
    if len(treff) > 30:
        print(f"  ... og {len(treff) - 30} til.")

    if args.csv and treff:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["property_id", "name", "org_number", "overordnetEnhet", "parent_property_id", "parent_name"])
            w.writeheader()
            w.writerows(treff)
        print(f"\nSkrevet {len(treff)} rader til {args.csv}.")


if __name__ == "__main__":
    main()
