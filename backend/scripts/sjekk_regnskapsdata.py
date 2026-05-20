"""
Sjekk om regnskapsdata er tømt i Supabase.

Henter antall rader i gl_transactions, budget, property_annual_costs via REST API.
Krever SUPABASE_SERVICE_ROLE_KEY.

Kjør: SUPABASE_SERVICE_ROLE_KEY=... python3 scripts/sjekk_regnskapsdata.py
"""
import os
import sys
from typing import Optional

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
    "Prefer": "count=exact",
}


def get_count(table: str) -> Optional[int]:
    """Hent antall rader i tabell via Content-Range header."""
    try:
        resp = requests.get(
            f"{REST_URL}/{table}",
            headers=HEADERS,
            params={"select": "*", "limit": "1"},
            timeout=30,
        )
        if resp.status_code == 401:
            print("401 Unauthorized – bruk SUPABASE_SERVICE_ROLE_KEY (service_role, ikke anon)")
            return None
        if resp.status_code == 404:
            return -1  # tabell finnes ikke
        resp.raise_for_status()
        cr = resp.headers.get("Content-Range")
        if cr and "/" in cr:
            return int(cr.split("/")[1])
        return 0
    except Exception as e:
        print(f"Feil ved {table}: {e}")
        return None


def main():
    if not SERVICE_KEY:
        print("Mangler SUPABASE_SERVICE_ROLE_KEY / SUPABASE_SERVICE_KEY.")
        sys.exit(1)

    print("Sjekker regnskapsdata i Supabase...\n")

    tables = [
        ("gl_transactions", "GL-transaksjoner (faktiske kostnader)"),
        ("budget", "Budsjett"),
        ("property_annual_costs", "Årlige kostnader per eiendom"),
    ]

    all_empty = True
    for table, desc in tables:
        n = get_count(table)
        if n is None:
            sys.exit(1)
        if n == -1:
            print(f"  {desc:45} tabell finnes ikke")
            continue
        status = "✅ tom" if n == 0 else f"⚠️  {n} rader"
        print(f"  {desc:45} {status}")
        if n > 0:
            all_empty = False

    print()
    if all_empty:
        print("Regnskapsdata er tømt (gl_transactions, budget, property_annual_costs har 0 rader).")
    else:
        print("Det finnes fortsatt regnskapsdata i en eller flere tabeller.")


if __name__ == "__main__":
    main()
