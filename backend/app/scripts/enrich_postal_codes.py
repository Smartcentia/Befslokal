"""
Slår opp postnummer for alle eiendommer via Kartverkets adresse-API.
Oppdaterer postal_code og city i properties-tabellen.

API: https://ws.geonorge.no/adresser/v1/sok
Gratis, ingen API-nøkkel nødvendig.

Kjøring:
    cd backend
    python -m app.scripts.enrich_postal_codes [--dry-run]
"""
import asyncio
import sys
import os
import httpx
import json
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from sqlalchemy import text
from app.db.session import SessionLocal

KARTVERKET_URL = "https://ws.geonorge.no/adresser/v1/sok"

DRY_RUN = "--dry-run" in sys.argv


def _normalize_str(s: str) -> str:
    """Fjern ekstra mellomrom og normaliser unicode."""
    return " ".join(s.strip().split())


def _strip_floor(address: str) -> str:
    """Fjern etasje-suffikser som '3. etg', '5.etg', '2.etg', 'u.etg' etc."""
    import re
    address = re.sub(r',?\s*\d+\.?\s*etg.*$', '', address, flags=re.IGNORECASE)
    address = re.sub(r',?\s*u\.etg.*$', '', address, flags=re.IGNORECASE)
    address = re.sub(r',?\s*\d+\.\s*etasje.*$', '', address, flags=re.IGNORECASE)
    return address.strip().rstrip(',').strip()


async def lookup_postal(client: httpx.AsyncClient, address: str, city: str | None) -> dict | None:
    """Slår opp adresse i Kartverket. Returnerer dict med postnummer og poststed."""
    clean_addr = _strip_floor(_normalize_str(address))
    params = {
        "sok": clean_addr,
        "treffPerSide": 5,
        "side": 0,
    }
    if city:
        params["kommunenavn"] = _normalize_str(city)

    try:
        resp = await client.get(KARTVERKET_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("adresser", [])
        if not hits:
            # Retry uten kommunenavn
            if city:
                params.pop("kommunenavn", None)
                resp2 = await client.get(KARTVERKET_URL, params=params, timeout=10)
                resp2.raise_for_status()
                hits = resp2.json().get("adresser", [])

        if hits:
            best = hits[0]
            return {
                "postal_code": best.get("postnummer"),
                "city": best.get("poststed", "").title() if best.get("poststed") else None,
                "confidence": "exact" if len(hits) == 1 else "best_of_many",
                "raw": best.get("adressetekst"),
            }
    except Exception as e:
        return {"error": str(e)}

    return None


async def enrich():
    async with SessionLocal() as db:
        result = await db.execute(text("""
            SELECT property_id::text, name, address, postal_code, city
            FROM properties
            WHERE address IS NOT NULL AND address != ''
            ORDER BY address
        """))
        props = result.mappings().all()

    print(f"Eiendommer med adresse: {len(props)}")
    print(f"Modus: {'DRY-RUN' if DRY_RUN else 'LIVE OPPDATERING'}\n")

    updated = []
    failed = []
    skipped = []

    async with httpx.AsyncClient() as client:
        for i, prop in enumerate(props):
            pid = prop["property_id"]
            addr = prop["address"]
            city = prop["city"]
            existing_postal = prop["postal_code"]

            if existing_postal:
                skipped.append(pid)
                continue

            result = await lookup_postal(client, addr, city)

            if result and result.get("postal_code"):
                postal = result["postal_code"]
                new_city = result.get("city") or city
                conf = result.get("confidence", "?")
                print(f"[{i+1}/{len(props)}] ✅ {addr}, {city} → {postal} {new_city} ({conf})")
                updated.append({
                    "property_id": pid,
                    "postal_code": postal,
                    "city": new_city,
                    "name": prop["name"],
                })
            else:
                err = result.get("error", "ingen treff") if result else "ingen treff"
                print(f"[{i+1}/{len(props)}] ❌ {addr}, {city} → {err}")
                failed.append({"property_id": pid, "address": addr, "city": city})

            # Litt pause for å ikke overbelaste Kartverket
            await asyncio.sleep(0.15)

    print(f"\n--- Oppsummering ---")
    print(f"Oppdatert:  {len(updated)}")
    print(f"Feilet:     {len(failed)}")
    print(f"Hoppet over (hadde allerede postnummer): {len(skipped)}")

    if not DRY_RUN and updated:
        print(f"\nSkriver {len(updated)} oppdateringer til database...")
        async with SessionLocal() as db:
            for row in updated:
                await db.execute(text("""
                    UPDATE properties
                    SET postal_code = :postal, city = :city
                    WHERE property_id = CAST(:pid AS uuid)
                """), {
                    "postal": row["postal_code"],
                    "city": row["city"],
                    "pid": row["property_id"],
                })
            await db.commit()
        print("✅ Database oppdatert.")

    if failed:
        fail_file = os.path.join(os.path.dirname(__file__), "postal_lookup_failed.json")
        with open(fail_file, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Feilede oppslag lagret: {fail_file}")


if __name__ == "__main__":
    asyncio.run(enrich())
