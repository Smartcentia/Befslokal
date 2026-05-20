"""
Sjekk om alle kostnader er slettet og kun husleie gjenstår.

Via Supabase REST API. Krever SUPABASE_SERVICE_ROLE_KEY.

Kostnader = gl_transactions, budget, property_annual_costs,
            contracts (caretaker_cost, cleaning_cost, parking_cost, card_reader_cost, external_data),
            properties.external_data.financials.manual_expenses

Husleie = contracts.amount.amount_per_year (eller tilsvarende)
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


def get_count(table: str, params: Optional[dict] = None) -> int:
    try:
        p = {"select": "*", "limit": "1", **(params or {})}
        resp = requests.get(f"{REST_URL}/{table}", headers=HEADERS, params=p, timeout=30)
        if resp.status_code != 200:
            return -1
        cr = resp.headers.get("Content-Range", "")
        if "/" in cr:
            return int(cr.split("/")[1])
        return 0
    except Exception:
        return -1


def main():
    if not SERVICE_KEY:
        print("Mangler SUPABASE_SERVICE_ROLE_KEY.")
        sys.exit(1)

    print("Sjekker kostnader vs husleie (Supabase REST)...\n")

    # 1. Regnskapstabeller (skal være tomme)
    print("=== Regnskapstabeller (skal være tomme) ===")
    for table, desc in [
        ("gl_transactions", "GL-transaksjoner"),
        ("budget", "Budsjett"),
        ("property_annual_costs", "Årlige kostnader per eiendom"),
    ]:
        n = get_count(table)
        status = "✅ tom" if n == 0 else f"⚠️  {n} rader"
        print(f"  {desc:40} {status}")

    # 2. Kontrakter med kostnadsfelter (caretaker, cleaning, parking, card_reader)
    print("\n=== Kontrakter med kostnadsfelter ===")
    cost_fields = ["caretaker_cost", "cleaning_cost", "parking_cost", "card_reader_cost"]
    contracts_with_costs = 0
    for field in cost_fields:
        resp = requests.get(
            f"{REST_URL}/contracts",
            headers={**HEADERS, "Prefer": "count=exact"},
            params={"select": "contract_id", "limit": "1", field: "not.is.null"},
            timeout=30,
        )
        if resp.status_code == 200:
            cr = resp.headers.get("Content-Range", "")
            n = int(cr.split("/")[1]) if "/" in cr else 0
            if n > 0:
                contracts_with_costs = max(contracts_with_costs, n)  # minst ett felt har data
                print(f"  {field:25} {n} kontrakter har verdi")
    if contracts_with_costs == 0:
        print("  ✅ Ingen kontrakter med caretaker/cleaning/parking/card_reader kost")

    # 3. Kontrakter med husleie (amount.amount_per_year)
    print("\n=== Husleie (kontrakter med amount) ===")
    resp = requests.get(
        f"{REST_URL}/contracts",
        headers=HEADERS,
        params={"select": "contract_id,amount", "limit": "5000"},
        timeout=60,
    )
    if resp.status_code != 200:
        print("  Kunne ikke hente kontrakter")
    else:
        contracts = resp.json()
        with_rent = 0
        total_rent = 0.0
        for c in contracts:
            amt = c.get("amount") or {}
            rent = amt.get("amount_per_year") or amt.get("amount_per_month")
            if rent:
                try:
                    r = float(rent)
                    if r > 0:
                        with_rent += 1
                        total_rent += r if "year" in str(amt.keys()).lower() or "amount_per_year" in str(amt) else r * 12
                except (TypeError, ValueError):
                    pass
        print(f"  Kontrakter med husleie: {with_rent}")
        print(f"  Total årlig husleie (sample): {total_rent:,.0f} kr")
        if with_rent > 0:
            print("  ✅ Husleie finnes i kontrakter")

    # 4. Eiendommer med manual_expenses i external_data
    with_manual = 0
    print("\n=== Eiendommer med manual_expenses (kostnader) ===")
    resp = requests.get(
        f"{REST_URL}/properties",
        headers=HEADERS,
        params={"select": "property_id,external_data", "limit": "5000"},
        timeout=60,
    )
    if resp.status_code != 200:
        print("  Kunne ikke hente eiendommer")
    else:
        props = resp.json()
        for p in props:
            ext = p.get("external_data") or {}
            fin = ext.get("financials") or {}
            manual = fin.get("manual_expenses") or []
            total_man = fin.get("total_manual_expenses") or 0
            if manual or (total_man and float(total_man) > 0):
                with_manual += 1
        print(f"  Eiendommer med manual_expenses: {with_manual}")
        if with_manual == 0:
            print("  ✅ Ingen eiendommer med manuelle kostnader")

    print("\n=== Oppsummering ===")
    gl = get_count("gl_transactions")
    bud = get_count("budget")
    pac = get_count("property_annual_costs")
    regnskap_tom = gl == 0 and bud == 0 and pac == 0
    if regnskap_tom and contracts_with_costs == 0 and with_manual == 0:
        print("✅ Alle kostnader er slettet. Kun husleie (i kontrakter) gjenstår.")
    else:
        print("⚠️  Det finnes fortsatt kostnader:")
        if not regnskap_tom:
            print("   - Regnskapstabeller har data")
        if contracts_with_costs > 0:
            print("   - Kontrakter har caretaker/cleaning/parking/card_reader")
        if with_manual > 0:
            print("   - Eiendommer har manual_expenses i external_data")


if __name__ == "__main__":
    main()
