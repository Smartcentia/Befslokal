"""
Oppdater properties.parent_unit_id_erp (og evt. unit_short_type, region) fra
Birk Enhetsregister-CSV (Institusjoner i og utenfor staten - Formålsbygg).

Bruker Supabase REST API – ingen direkte DB-tilkobling.

For hver eiendom med unit_id_erp: finn raden i CSV der EnhetID = unit_id_erp.
Hvis TilhørighetEnhetID er satt i CSV, sett property.parent_unit_id_erp = TilhørighetEnhetID.
Med --oppdater-felter oppdateres også unit_short_type og region fra CSV.

Kjør fra backend:
  SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/oppdater_parent_erp_fra_birk_csv.py [--csv PATH] [--dry-run] [--oppdater-felter]

Eller med .env som inneholder SUPABASE_URL og SUPABASE_SERVICE_ROLE_KEY.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

import requests

# Optional: load .env for SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
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
    "Prefer": "return=minimal",
}


def _norm(s: str | None) -> str | None:
    if s is None:
        return None
    t = (s or "").strip()
    return t if t else None


def load_birk_csv(csv_path: str) -> dict[str, dict]:
    """
    Les Birk CSV. Returnerer dict: EnhetID (normalisert string) -> { parent, unit_short_type, region, ... }.
    Prøver utf-8-sig, deretter latin-1 (vanlig for norske Excel-eksporter).
    """
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            with open(csv_path, newline="", encoding=enc) as f:
                next(f)  # skip first line (empty/semicolons)
                reader = csv.DictReader(f, delimiter=";")
                return _read_birk_rows(reader)
        except UnicodeDecodeError:
            continue
    with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
        next(f)
        return _read_birk_rows(csv.DictReader(f, delimiter=";"))


def _read_birk_rows(reader) -> dict[str, dict]:
    out = {}
    for row in reader:
        enhet_id = _norm(row.get("EnhetID"))
        if not enhet_id:
            continue
        parent = _norm(row.get("TilhørighetEnhetID"))
        unit_short_type = _norm(row.get("Enhetskorttype"))
        region = _norm(row.get("Region"))
        out[enhet_id] = {
            "parent": parent,
            "unit_short_type": unit_short_type,
            "region": region,
            "enhetsnavn": _norm(row.get("Enhetsnavn")),
        }
    return out


def api_get_properties_with_unit_id_erp() -> list[dict]:
    """Hent alle properties der unit_id_erp er satt (Supabase REST)."""
    # PostgREST: unit_id_erp=not.is.null for "is not null"
    params = {
        "select": "property_id,unit_id_erp,parent_unit_id_erp,unit_short_type,region,name,address",
        "unit_id_erp": "not.is.null",
    }
    resp = requests.get(f"{REST_URL}/properties", headers=HEADERS, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def api_patch_property(property_id: str, data: dict) -> None:
    """Oppdater én property via Supabase REST PATCH."""
    resp = requests.patch(
        f"{REST_URL}/properties",
        headers=HEADERS,
        params={"property_id": f"eq.{property_id}"},
        json=data,
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"PATCH properties {property_id}: {resp.status_code} {resp.text[:300]}")


def main():
    parser = argparse.ArgumentParser(description="Oppdater parent_unit_id_erp fra Birk CSV (Supabase REST)")
    default_csv = os.path.expanduser(
        "~/Downloads/Institusjoner  i og utenfor staten - Formålsbygg(ERA-01 Enhetsregister (Birk) Fl).csv"
    )
    parser.add_argument(
        "--csv",
        default=default_csv,
        help="Full path til Birk CSV",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Vis kun hva som ville blitt endret, lagre ikke.",
    )
    parser.add_argument(
        "--oppdater-felter",
        action="store_true",
        help="Oppdater også unit_short_type og region fra CSV.",
    )
    args = parser.parse_args()

    if not SERVICE_KEY:
        print("Mangler SUPABASE_SERVICE_ROLE_KEY eller SUPABASE_SERVICE_KEY i miljøet.")
        sys.exit(1)

    if not os.path.isfile(args.csv):
        print(f"Fil ikke funnet: {args.csv}")
        sys.exit(1)

    birk = load_birk_csv(args.csv)
    print(f"Lest {len(birk)} enheter fra Birk CSV.")

    print("Henter properties fra Supabase (unit_id_erp not null)...")
    props = api_get_properties_with_unit_id_erp()
    print(f"Fant {len(props)} eiendommer med unit_id_erp.")

    updated = 0
    skipped_no_row = 0
    for p in props:
        uid = _norm(p.get("unit_id_erp"))
        if not uid:
            continue
        row = birk.get(uid)
        if not row:
            skipped_no_row += 1
            continue
        parent = row["parent"]
        payload = {}
        if parent is not None and (p.get("parent_unit_id_erp") or "").strip() != parent:
            payload["parent_unit_id_erp"] = parent
        if args.oppdater_felter:
            if (row.get("unit_short_type") or "") != (p.get("unit_short_type") or ""):
                if row.get("unit_short_type") is not None:
                    payload["unit_short_type"] = row["unit_short_type"]
            if (row.get("region") or "") != (p.get("region") or ""):
                if row.get("region") is not None:
                    payload["region"] = row["region"]
        if not payload:
            continue
        updated += 1
        name = p.get("name") or p.get("address") or str(p.get("property_id"))
        if args.dry_run:
            print(f"  [dry-run] {name} (unit_id_erp={uid}) | {payload}")
        else:
            api_patch_property(str(p["property_id"]), payload)

    if not args.dry_run and updated:
        print(f"Oppdatert {updated} eiendommer.")
    elif args.dry_run:
        print(f"Ville oppdatere {updated} eiendommer (dry-run).")
    else:
        print("Ingen endringer.")

    if skipped_no_row:
        print(f"Eiendommer med unit_id_erp som ikke finnes i CSV: {skipped_no_row}")


if __name__ == "__main__":
    main()
