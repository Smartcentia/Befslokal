"""
Runde 2: Prøv igjen for de 44 eiendommene som feilet i første runde.
Ekspanderer forkortelser og renser adresser før nytt Kartverket-oppslag.

Kjøring:
    cd backend
    python -m app.scripts.enrich_postal_codes_retry
"""
import asyncio, sys, os, httpx, json, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from sqlalchemy import text
from app.db.session import SessionLocal

KARTVERKET_URL = "https://ws.geonorge.no/adresser/v1/sok"

# Vanlige forkortelser i norske adresser
ABBREV = [
    (r'\bvn\b',       'veien'),
    (r'\bvg\b',       'vegen'),
    (r'\bgt\.?\b',    'gate'),
    (r'\bgata\b',     'gate'),
    (r'\bgt\b',       'gate'),
    (r'\bplass\b',    'plass'),
    (r'\bpl\b',       'plass'),
    (r'\ball\b',      'allé'),
    (r'\bsgt\b',      'gate'),
]


def _expand(address: str) -> str:
    a = address.strip()
    for pattern, replacement in ABBREV:
        a = re.sub(pattern, replacement, a, flags=re.IGNORECASE)
    # Fjern etasjeinfo
    a = re.sub(r',?\s*\d+\.?\s*etg.*$', '', a, flags=re.IGNORECASE)
    # Rens doble husnumre: "11/13" → "11", "22-24" → "22", "9A,C" → "9A", "40A/B" → "40A"
    a = re.sub(r'(\d+[A-Za-z]?)[/\-]\d+.*', r'\1', a)
    a = re.sub(r'(\d+[A-Za-z]?),\s*[A-Za-z].*', r'\1', a)
    return a.strip().rstrip(',').strip()


async def lookup(client, address, city):
    params = {"sok": address, "treffPerSide": 3, "side": 0}
    if city:
        params["kommunenavn"] = city
    try:
        r = await client.get(KARTVERKET_URL, params=params, timeout=10)
        hits = r.json().get("adresser", [])
        if not hits and city:
            params.pop("kommunenavn")
            r2 = await client.get(KARTVERKET_URL, params=params, timeout=10)
            hits = r2.json().get("adresser", [])
        if hits:
            b = hits[0]
            return {
                "postal_code": b.get("postnummer"),
                "city": (b.get("poststed") or "").title() or city,
            }
    except Exception as e:
        return {"error": str(e)}
    return None


async def retry():
    fail_file = os.path.join(os.path.dirname(__file__), "postal_lookup_failed.json")
    with open(fail_file, encoding="utf-8") as f:
        failed = json.load(f)

    print(f"Prøver igjen for {len(failed)} eiendommer...\n")

    # Hent property_id for disse adressene
    async with SessionLocal() as db:
        result = await db.execute(text("""
            SELECT property_id::text, address, city
            FROM properties
            WHERE postal_code IS NULL
        """))
        no_postal = {(r["address"], r["city"]): r["property_id"]
                     for r in result.mappings().all()}

    updated = []
    still_failed = []

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(failed):
            orig_addr = row["address"]
            orig_city = row["city"]
            expanded = _expand(orig_addr)

            hit = await lookup(client, expanded, orig_city)

            if hit and hit.get("postal_code"):
                postal = hit["postal_code"]
                new_city = hit.get("city") or orig_city
                pid = no_postal.get((orig_addr, orig_city))
                print(f"[{i+1}/{len(failed)}] ✅ '{orig_addr}' → '{expanded}' → {postal} {new_city}")
                if pid:
                    updated.append({
                        "property_id": pid,
                        "postal_code": postal,
                        "city": new_city,
                    })
            else:
                print(f"[{i+1}/{len(failed)}] ❌ '{orig_addr}' (prøvde: '{expanded}')")
                still_failed.append(row)

            await asyncio.sleep(0.15)

    print(f"\n--- Oppsummering runde 2 ---")
    print(f"Funnet:          {len(updated)}")
    print(f"Fortsatt feilet: {len(still_failed)}")

    if updated:
        print(f"\nSkriver {len(updated)} oppdateringer til database...")
        async with SessionLocal() as db:
            for row in updated:
                await db.execute(text("""
                    UPDATE properties
                    SET postal_code = :postal, city = :city
                    WHERE property_id = CAST(:pid AS uuid)
                """), {"postal": row["postal_code"], "city": row["city"], "pid": row["property_id"]})
            await db.commit()
        print("✅ Database oppdatert.")

    if still_failed:
        out = os.path.join(os.path.dirname(__file__), "postal_lookup_failed2.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(still_failed, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Gjenstående feil: {out}")
        print("\nMangler fortsatt:")
        for r in still_failed:
            print(f"  - {r['address']}, {r['city']}")


if __name__ == "__main__":
    asyncio.run(retry())
