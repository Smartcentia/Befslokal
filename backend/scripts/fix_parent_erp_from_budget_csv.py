"""
fix_parent_erp_from_budget_csv.py

Bruker budsjett-CSV (2026-02) til å:
1. Sette parent_unit_id_erp på avdelinger via lokalisering_id-matching
2. Opsjonelt: oppdatere department_code = lokalisering_id (koststed for GL Dim1)

Funn: I BEFS DB er unit_id_erp = e-don2 EnhetID (f.eks. 51954 for Tjernlia),
      men department_code satt = unit_id_erp → feil for GL-matching.
      GL Dim1 (Koststed) = lokasjonskode = lokalisering_id (f.eks. 236105).
      Matching skal derfor skje på lokalisering_id, ikke department_code.

CSV-format (semikolon-separert, Latin-1):
  "Region " ; Målgruppe ; Enhetsnr. ; Enhetens/Institusjonens navn ;
  Avdelingens koststed ; Navn på avdeling ;
  Antall kvalitetssikrede plasser pr. 01.01 ; Antall budsjetterte plasser per 01.01

  NB: Header "Region " har trailing space!

Kjøres:
  python fix_parent_erp_from_budget_csv.py
"""
import csv
import os
import sys
import requests

SUPABASE_URL = "https://vwvhxcqxadblrftuvsds.supabase.co"
KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3dmh4Y3F4YWRibHJmdHV2c2RzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTMzODUwMiwiZXhwIjoyMDg2OTE0NTAyfQ.h071E-xhKw1uPPuNzxtyv2a1oAXK1eJF8NXZ9EpMlWc"
)
CSV_PATH = os.environ.get(
    "BUDGET_CSV_PATH",
    "/Users/frank/Downloads/2026-02 Regionenes budsjetterte plasser per månedsrapportering for januar 2026 (3)(Ark1) (2).csv"
)

# Sett til True for å også oppdatere department_code = lokalisering_id
UPDATE_DEPT_CODE = True

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

HEADERS_READ = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
}

updated_parent = 0
updated_dept = 0
no_change = 0
not_found = []


def get_property_by_lokalisering_id(lokalisering_id: str) -> list:
    """Finn eiendom via lokalisering_id (= koststed/lokasjonskode fra e-don2)."""
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/properties",
        params={
            "lokalisering_id": f"eq.{lokalisering_id}",
            "select": "property_id,name,region,parent_unit_id_erp,lokalisering_id,department_code",
        },
        headers=HEADERS_READ,
    )
    r.raise_for_status()
    return r.json()


def patch_property(property_id: str, updates: dict) -> None:
    r = requests.patch(
        f"{SUPABASE_URL}/rest/v1/properties",
        params={"property_id": f"eq.{property_id}"},
        json=updates,
        headers=HEADERS,
    )
    r.raise_for_status()


def main():
    global updated_parent, updated_dept, no_change

    print(f"Leser CSV: {CSV_PATH}")
    print(f"UPDATE_DEPT_CODE: {UPDATE_DEPT_CODE}\n")

    with open(CSV_PATH, encoding="latin-1") as f:
        content = f.read()

    # Parse CSV med strippede headers (fjern trailing spaces fra kolonnehoder)
    lines = content.splitlines()
    # Fix header: strip whitespace fra alle kolonnenavn
    raw_headers = lines[0].split(";")
    clean_headers = [h.strip() for h in raw_headers]

    reader = csv.DictReader(
        lines[1:],  # data-rader (uten header)
        fieldnames=clean_headers,
        delimiter=";"
    )

    for row in reader:
        koststed = row.get("Avdelingens koststed", "").strip()
        enhetsnr = row.get("Enhetsnr.", "").strip()
        region_raw = row.get("Region", "").strip()
        avd_navn = row.get("Navn på avdeling", "").strip()
        inst_navn = row.get("Enhetens/Institusjonens navn", "").strip()

        # Hopp over tomme/summary-rader
        if not koststed or not koststed.isdigit():
            continue

        # Finn property via lokalisering_id (= koststed i CSV)
        try:
            props = get_property_by_lokalisering_id(koststed)
        except Exception as e:
            print(f"  FEIL ved oppslag av lokalisering_id={koststed}: {e}")
            not_found.append(f"{koststed} ({inst_navn} / {avd_navn})")
            continue

        if not props:
            not_found.append(f"{koststed} ({inst_navn} / {avd_navn})")
            continue

        for prop in props:
            prop_id = prop["property_id"]
            prop_name = prop.get("name", "?")
            prop_parent = prop.get("parent_unit_id_erp")
            prop_dept = prop.get("department_code")

            updates = {}

            # 1. Sett parent_unit_id_erp hvis mangler
            if not prop_parent and enhetsnr:
                updates["parent_unit_id_erp"] = enhetsnr

            # 2. Oppdater department_code = koststed (lokalisering_id) for korrekt GL-matching
            if UPDATE_DEPT_CODE and prop_dept != koststed:
                updates["department_code"] = koststed

            if updates:
                try:
                    patch_property(prop_id, updates)
                    changes = []
                    if "parent_unit_id_erp" in updates:
                        changes.append(f"parent→{enhetsnr}")
                        updated_parent += 1
                    if "department_code" in updates:
                        changes.append(f"dept_code {prop_dept}→{koststed}")
                        updated_dept += 1
                    print(f"  ✓ [{koststed}] {prop_name}: {', '.join(changes)}")
                except Exception as e:
                    print(f"  ✗ FEIL {prop_name}: {e}")
            else:
                print(f"  – [{koststed}] {prop_name}: ingen endring")
                no_change += 1

    print("\n" + "=" * 60)
    print("FERDIG")
    print(f"  parent_unit_id_erp satt:   {updated_parent}")
    print(f"  department_code fikset:    {updated_dept}")
    print(f"  Ingen endring nødvendig:   {no_change}")
    print(f"  Ikke funnet i DB:          {len(not_found)}")

    if not_found:
        print(f"\nIKKE FUNNET ({len(not_found)} stk) – mangler i DB:")
        for nf in not_found:
            print(f"  - {nf}")


if __name__ == "__main__":
    main()
