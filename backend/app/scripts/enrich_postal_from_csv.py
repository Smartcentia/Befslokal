"""
Runde 4: Henter postnummer direkte fra Eie1212.csv for de 5 gjenværende
eiendommene som ikke ble løst via Kartverket-oppslag.

Postnummeret leses fra kolonnen "Adresse og Postnummer" i kildefilen.

Kjøring:
    cd backend
    python -m app.scripts.enrich_postal_from_csv
"""
import asyncio
import sys
import os
import csv
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from sqlalchemy import text
from app.db.session import SessionLocal

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../docs/Eie1212.csv")

# Disse er de 5 eiendommene som mangler postnummer (address, city i DB)
MISSING = [
    ("Bastian Withs gt 11",  "MOLDE"),
    ("Jernbaneveien 70",     "KIRKENÆR"),
    ("Okkenhaugveien 13B",   "LEVANGER"),
    ("Rokkeveien 502",       "HALDEN"),
    ("Ullsvei 16",           "HALDEN"),
]


def _extract_postal(adresse_og_postnummer: str) -> tuple[str | None, str | None]:
    """Trekk ut 4-sifret postnummer og poststed fra 'Adresse, XXXX Poststed'."""
    m = re.search(r'\b(\d{4})\b\s*(\S.*)?$', adresse_og_postnummer.strip())
    if m:
        postal = m.group(1)
        city = (m.group(2) or "").strip().title() or None
        return postal, city
    return None, None


async def main():
    # Les CSV og bygg oppslagstabell: adresselinje1.lower() → (postal, city)
    csv_lookup: dict[str, tuple[str, str]] = {}

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        # Normalize header names (strip whitespace) for lookup
        reader.fieldnames = [h.strip() for h in (reader.fieldnames or [])]
        for row in reader:
            addr1 = (row.get("Adresselinje 1") or "").strip()
            full  = (row.get("Adresse og Postnummer") or "").strip()
            if addr1 and full:
                postal, city = _extract_postal(full)
                if postal:
                    csv_lookup[addr1.lower()] = (postal, city or "")

    print(f"CSV-oppslag bygget: {len(csv_lookup)} adresser\n")

    updates = []
    for db_addr, db_city in MISSING:
        hit = csv_lookup.get(db_addr.lower())
        if hit:
            postal, city = hit
            print(f"✅  '{db_addr}' → {postal} {city}")
            updates.append((db_addr, db_city, postal, city or db_city))
        else:
            print(f"❌  '{db_addr}' ikke funnet i CSV")

    if not updates:
        print("\nIngen oppdateringer å gjøre.")
        return

    print(f"\nOppdaterer {len(updates)} eiendommer i databasen...")
    async with SessionLocal() as db:
        for db_addr, db_city, postal, new_city in updates:
            result = await db.execute(text("""
                UPDATE properties
                SET postal_code = :postal, city = :city
                WHERE LOWER(address) = LOWER(:addr)
                  AND postal_code IS NULL
                RETURNING property_id::text, name
            """), {"postal": postal, "city": new_city, "addr": db_addr})
            rows = result.fetchall()
            for row in rows:
                print(f"   ✔ [{row[0][:8]}…] {row[1]}")
        await db.commit()

    # Endelig status
    async with SessionLocal() as db:
        r = await db.execute(text(
            "SELECT COUNT(*) FROM properties WHERE postal_code IS NOT NULL"
        ))
        have = r.scalar()
        r2 = await db.execute(text("SELECT COUNT(*) FROM properties"))
        total = r2.scalar()
    print(f"\n📊 Totalt: {have}/{total} eiendommer har nå postnummer "
          f"({have/total*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())
