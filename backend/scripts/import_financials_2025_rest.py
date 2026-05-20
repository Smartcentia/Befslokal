"""
Import 2025 annual cost data via Supabase REST API (no direct DB connection needed).
Uses requests + PostgREST endpoint, authenticated with service role key.
"""
import sys
import os
import csv
import re
import uuid
import json
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vwvhxcqxadblrftuvsds.supabase.co")
SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # Sett i env – aldri hardkod nøkler i kode

HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

CSV_FILE = "/Users/frank/Documents/BEFS_CLEAN/finans/Eiendomsportefølje_ 2025.csv"
REST_URL = f"{SUPABASE_URL}/rest/v1"


def api_get(table: str, params: dict) -> list:
    resp = requests.get(f"{REST_URL}/{table}", headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()


def api_post(table: str, data: dict) -> None:
    resp = requests.post(f"{REST_URL}/{table}", headers=HEADERS, json=data)
    if not resp.ok:
        raise RuntimeError(f"POST {table} failed {resp.status_code}: {resp.text[:200]}")


def api_patch(table: str, filter_params: dict, data: dict) -> None:
    resp = requests.patch(f"{REST_URL}/{table}", headers=HEADERS, params=filter_params, json=data)
    if not resp.ok:
        raise RuntimeError(f"PATCH {table} failed {resp.status_code}: {resp.text[:200]}")


def parse_float(val: str):
    if not val or not val.strip():
        return None
    val = str(val).strip()
    # Remove NBSP and regular spaces used as thousands separators
    val = val.replace("\xa0", "").replace("\u00a0", "")
    # Remove spaces (thousand separator in Norwegian), replace comma with dot
    val = val.replace(" ", "").replace(",", ".")
    # Extract numeric part
    match = re.search(r"\d+\.?\d*", val)
    if match:
        try:
            result = float(match.group(0))
            return result if result != 0.0 else None
        except ValueError:
            return None
    return None


def main():
    if not os.path.exists(CSV_FILE):
        print(f"CSV not found: {CSV_FILE}")
        sys.exit(1)

    print("Testing Supabase REST connection...")
    test = api_get("properties", {"select": "property_id", "limit": "1"})
    print(f"  OK – got {len(test)} row(s) from properties table")

    print("Reading CSV...")
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row.get("Lokalisering"):
                rows.append(row)

    print(f"Found {len(rows)} rows with Lokalisering.\n")

    inserted = 0
    updated = 0
    skipped = 0

    for i, row in enumerate(rows, 1):
        lok_raw = row.get("Lokalisering", "").strip()
        match = re.match(r"^(\d{4})", lok_raw)
        if not match:
            print(f"  [{i}] SKIP: unknown lokalisering format: {lok_raw!r}")
            skipped += 1
            continue
        lok_id = match.group(1)

        # Find property by lokalisering_id
        props = api_get("properties", {
            "select": "property_id,name",
            "lokalisering_id": f"eq.{lok_id}",
        })
        if not props:
            print(f"  [{i}] SKIP: no property for lokalisering_id={lok_id} ({lok_raw[:50]})")
            skipped += 1
            continue

        property_id = props[0]["property_id"]
        prop_name = props[0].get("name", "")[:45]

        # Parse cost fields
        kpi_adjusted_rent    = parse_float(row.get("KPI-justert kontraktsleie til okt 2025", ""))
        internal_maintenance = parse_float(row.get("KPI-justert indre vedlikehold", ""))
        if internal_maintenance is None:
            internal_maintenance = parse_float(row.get("Indre vedlikehold", ""))
        common_costs    = parse_float(row.get("Felleskostnader per år (ved kontraktsinngåelse) ", ""))
        energy_costs    = parse_float(row.get("Energi til leieobjektet kr per år", ""))
        heating_costs   = parse_float(row.get("Oppvarming pr år", ""))
        cleaning_costs  = parse_float(row.get("Renhold pr år", ""))
        parking_rent    = parse_float(row.get("Parkeringsleie kr per år", ""))
        caretaker_cost  = parse_float(row.get("Vaktmestertjenester kr per år", ""))
        card_reader_cost = parse_float(row.get("Kost kortleser", ""))

        record = {
            "property_id": property_id,
            "year": 2025,
            "kpi_adjusted_rent": kpi_adjusted_rent,
            "internal_maintenance": internal_maintenance,
            "common_costs": common_costs,
            "energy_costs": energy_costs,
            "heating_costs": heating_costs,
            "cleaning_costs": cleaning_costs,
            "parking_rent": parking_rent,
            "caretaker_cost": caretaker_cost,
            "card_reader_cost": card_reader_cost,
            "external_data": dict(row),
        }

        # Check if record exists for year=2025
        existing = api_get("property_annual_costs", {
            "select": "property_annual_cost_id",
            "property_id": f"eq.{property_id}",
            "year": "eq.2025",
        })

        if existing:
            rec_id = existing[0]["property_annual_cost_id"]
            api_patch("property_annual_costs",
                      {"property_annual_cost_id": f"eq.{rec_id}"},
                      record)
            print(f"  [{i}] UPDATED {lok_id} ({prop_name}): leie={kpi_adjusted_rent}, felles={common_costs}")
            updated += 1
        else:
            record["property_annual_cost_id"] = str(uuid.uuid4())
            api_post("property_annual_costs", record)
            print(f"  [{i}] INSERTED {lok_id} ({prop_name}): leie={kpi_adjusted_rent}, felles={common_costs}")
            inserted += 1

    print(f"\nFerdig. Inserted={inserted}, Updated={updated}, Skipped={skipped}")


if __name__ == "__main__":
    main()
