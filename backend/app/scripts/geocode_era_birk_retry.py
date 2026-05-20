"""
Retry geocoding for ERA Birk institutions that failed the first pass.
Uses smarter address cleaning + name-based fallback search.

Kjør:
  railway run --service BEFS1 python3 backend/app/scripts/geocode_era_birk_retry.py
"""
import sys, os, asyncio, aiohttp, re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

KARTVERKET_URL = "https://ws.geonorge.no/adresser/v1/sok"
BATCH_SIZE = 10
DATA_KILDE = "era_birk_2026"


def clean_address(adresse: str) -> list[str]:
    """Return list of address candidates to try (best first)."""
    candidates = []

    # Fix encoding artifacts (ã -> æ, etc.)
    adresse = adresse.replace("ã", "æ").replace("Ã¦", "æ").replace("Ã¸", "ø").replace("Ã¥", "å")

    # Remove postbox parts appended after physical address
    # e.g. "Haugboveien 39, Pb. 422, ASKER" → "Haugboveien 39"
    stripped = re.sub(r',?\s*(Pb\.?|Postboks)\s*\d+.*', '', adresse, flags=re.IGNORECASE).strip()
    stripped = re.sub(r',\s*$', '', stripped).strip()
    if stripped and stripped.lower() != adresse.lower():
        candidates.append(stripped)

    # Split "addr1 og addr2" — take first
    if ' og ' in adresse.lower():
        part1 = re.split(r'\s+og\s+', adresse, flags=re.IGNORECASE)[0].strip()
        part1 = re.sub(r',\s*$', '', part1).strip()
        if part1:
            candidates.append(part1)

    # Split on comma — take first part (the physical part)
    parts = [p.strip() for p in adresse.split(',')]
    if len(parts) > 1 and not parts[0].lower().startswith('postboks'):
        candidates.append(parts[0])

    # Full original (if not already covered)
    if adresse not in candidates:
        candidates.append(adresse)

    return candidates


async def geocode_with_fallback(session, avd_navn, inst_navn, adresse, kommune):
    """Try multiple strategies to geocode."""

    async def try_address(query, kom=None):
        params = {"sok": query, "fuzzy": "true", "treffPerSide": "1"}
        if kom:
            params["kommunenavn"] = kom.title()
        try:
            async with session.get(KARTVERKET_URL, params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    hits = data.get("adresser", [])
                    if hits:
                        pt = hits[0].get("representasjonspunkt", {})
                        lat, lon = pt.get("lat"), pt.get("lon")
                        if lat and lon:
                            return float(lat), float(lon)
        except Exception:
            pass
        return None, None

    # Skip pure postbox addresses → go straight to name search
    is_postbox_only = bool(re.match(r'postboks', adresse.strip(), re.IGNORECASE))

    if not is_postbox_only:
        # Strategy 1: cleaned address candidates
        for cand in clean_address(adresse):
            lat, lon = await try_address(cand, kommune)
            if lat:
                return lat, lon

        # Strategy 2: cleaned address without municipality filter
        for cand in clean_address(adresse):
            lat, lon = await try_address(cand)
            if lat:
                return lat, lon

    # Strategy 3: institution name + municipality (Kartverket knows named places)
    for name in [avd_navn, inst_navn]:
        if name:
            lat, lon = await try_address(name, kommune)
            if lat:
                return lat, lon

    return None, None


async def run():
    async with SessionLocal() as db:
        r = await db.execute(text("""
            SELECT id, avdelings_navn, institusjons_navn, adresse, kommune, fylke, eierskap
            FROM institution_plasser
            WHERE data_kilde = :kilde
              AND eierskap != 'Statlig'
              AND adresse IS NOT NULL
              AND (latitude IS NULL OR latitude = 0)
            ORDER BY eierskap, avdelings_navn
        """), {"kilde": DATA_KILDE})
        rows = r.fetchall()
        print(f"Retrying {len(rows)} failed ERA geocoding entries")

        geocoded = 0
        still_failed = 0

        async with aiohttp.ClientSession() as session:
            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i:i + BATCH_SIZE]
                tasks = [
                    geocode_with_fallback(
                        session,
                        row.avdelings_navn,
                        row.institusjons_navn,
                        row.adresse,
                        row.kommune,
                    )
                    for row in batch
                ]
                results = await asyncio.gather(*tasks)

                for row, (lat, lon) in zip(batch, results):
                    if lat and lon:
                        await db.execute(text("""
                            UPDATE institution_plasser
                            SET latitude = :lat, longitude = :lon
                            WHERE id = :id
                        """), {"lat": lat, "lon": lon, "id": str(row.id)})
                        geocoded += 1
                    else:
                        still_failed += 1
                        print(f"  STILL FAILED: {row.avdelings_navn} | {row.adresse} | {row.kommune}")

                await db.commit()
                done = min(i + BATCH_SIZE, len(rows))
                print(f"  {done}/{len(rows)} — new geocoded: {geocoded}, still failed: {still_failed}")

        print(f"\nRetry done. Newly geocoded: {geocoded}, Still failed: {still_failed}")

        r2 = await db.execute(text("""
            SELECT eierskap,
                   COUNT(*) total,
                   COUNT(CASE WHEN latitude IS NOT NULL AND latitude != 0 THEN 1 END) with_coords
            FROM institution_plasser
            WHERE data_kilde = :kilde AND eierskap != 'Statlig'
            GROUP BY eierskap ORDER BY total DESC
        """), {"kilde": DATA_KILDE})
        print("\nFinal coverage per eierskap (private):")
        for row in r2.fetchall():
            print(f"  {row.eierskap}: {row.with_coords}/{row.total} with coords")


if __name__ == "__main__":
    asyncio.run(run())
