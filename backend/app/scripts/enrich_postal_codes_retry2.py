"""
Runde 3: Suffix-ekspansjon for 37 gjenværende adresser.
Forkortelsene sitter fast på gatenavnet (Alfheimvn, Rønvikvn, Håkøyvn).

Kjøring:
    cd backend
    python -m app.scripts.enrich_postal_codes_retry2
"""
import asyncio, sys, os, httpx, json, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
from sqlalchemy import text
from app.db.session import SessionLocal

KARTVERKET_URL = "https://ws.geonorge.no/adresser/v1/sok"

# Suffix-erstatninger – orden er viktig (lengst/mest spesifikk først)
SUFFIX_RULES = [
    # Possessiv + gate (Tordenskjoldsgt, Schweigaardsgt, Torolv Kveldulvsonsgt)
    (r'sgt\.?\s*(\d)',     r's gate \1'),
    (r'sSgt\.?\s*(\d)',    r's gate \1'),
    # Vanlige gate-forkortelser
    (r'gt\.?\s*(\d)',      r'gate \1'),
    (r'gata\s*(\d)',       r'gate \1'),
    # Vei-forkortelser limt på
    (r'vn\s*(\d)',         r'veien \1'),
    (r'vei\s*(\d)',        r'veien \1'),   # "vei" → "veien"
    (r'vg\s*(\d)',         r'vegen \1'),
    # "og N" i husnummer
    (r'\s+og\s+\d+',       r''),
    # "D/E", "A/B" husnummer
    (r'(\d+[A-Za-z]?)/[A-Za-z]', r'\1'),
    # Doble husnumre
    (r'(\d+[A-Za-z]?)-\d+', r'\1'),
    # "- ikke oppmålt" og lignende
    (r'\s*-\s*ikke.*$',    r''),
    # Komma-varianter som "9A,C"
    (r'(\d+[A-Za-z]),\s*[A-Za-z]', r'\1'),
    # Etasjeinfo
    (r',?\s*\d+\.?\s*etg.*$', r''),
]


def _expand(address: str) -> str:
    a = address.strip()
    for pattern, replacement in SUFFIX_RULES:
        a = re.sub(pattern, replacement, a, flags=re.IGNORECASE)
    return a.strip().rstrip(',').strip()


# Noen adresser trenger manuell korrigering
MANUAL_FIXES = {
    "Alfheimvn 6":             "Alfheimveien 6",
    "Håkøyvn 339":             "Håkøyveien 339",
    "Heimlyvn 5":              "Heimlyveien 5",
    "Idrettsvn 5":             "Idrettsveien 5",
    "Rønvikvn 9A,C":           "Rønvikveien 9A",
    "Strandvn 6":              "Strandveien 6",
    "Uglevn 1":                "Ugleveien 1",
    "Ljåmovein 10":            "Ljåmoveien 10",
    "Markedsgt 20":            "Markedsgata 20",
    "Egge gård":               "Egge",
    "Lindøy 9 - ikke oppmålt": "Lindøy 9",
    "Nygardsvegen 2 og 4":     "Nygardsvegen 2",
    "Østmarkveien 26 D/E":     "Østmarkveien 26D",
}


async def lookup(client, address, city):
    for attempt_city in ([city, None] if city else [None]):
        params = {"sok": address, "treffPerSide": 3, "side": 0}
        if attempt_city:
            params["kommunenavn"] = attempt_city
        try:
            r = await client.get(KARTVERKET_URL, params=params, timeout=10)
            hits = r.json().get("adresser", [])
            if hits:
                b = hits[0]
                return {
                    "postal_code": b.get("postnummer"),
                    "city": (b.get("poststed") or "").title() or city,
                }
        except Exception:
            pass
    return None


async def retry2():
    fail_file = os.path.join(os.path.dirname(__file__), "postal_lookup_failed2.json")
    with open(fail_file, encoding="utf-8") as f:
        failed = json.load(f)

    print(f"Runde 3 – {len(failed)} adresser...\n")

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

            # Prøv manuell fix først, så automatisk ekspansjon
            manual = MANUAL_FIXES.get(orig_addr)
            expanded = manual or _expand(orig_addr)

            hit = await lookup(client, expanded, orig_city)

            if hit and hit.get("postal_code"):
                postal = hit["postal_code"]
                new_city = hit.get("city") or orig_city
                pid = no_postal.get((orig_addr, orig_city))
                src = "manuell" if manual else "auto"
                print(f"[{i+1}/{len(failed)}] ✅ [{src}] '{orig_addr}' → '{expanded}' → {postal} {new_city}")
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

    print(f"\n--- Oppsummering runde 3 ---")
    print(f"Funnet:          {len(updated)}")
    print(f"Fortsatt feilet: {len(still_failed)}")

    if updated:
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
        out = os.path.join(os.path.dirname(__file__), "postal_lookup_failed3.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(still_failed, f, ensure_ascii=False, indent=2)
        print(f"\nGjenstående (krever manuell registrering):")
        for r in still_failed:
            print(f"  - {r['address']}, {r['city']}")

    # Endelig status
    async with SessionLocal() as db:
        r = await db.execute(text("SELECT COUNT(*) FROM properties WHERE postal_code IS NOT NULL"))
        have = r.scalar()
        r2 = await db.execute(text("SELECT COUNT(*) FROM properties"))
        total = r2.scalar()
    print(f"\n📊 Totalt: {have}/{total} eiendommer har nå postnummer ({have/total*100:.0f}%)")


if __name__ == "__main__":
    asyncio.run(retry2())
