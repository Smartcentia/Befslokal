"""
Geocode ERA Birk institution_plasser records via Kartverket address API.

Kjør:
  cd /path/to/BEFS_CLEAN
  railway run --service BEFS1 python3 backend/app/scripts/geocode_era_birk.py
"""
import sys
import os
import asyncio
import aiohttp
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

KARTVERKET_URL = "https://ws.geonorge.no/adresser/v1/sok"
BATCH_SIZE = 20  # concurrent requests
DATA_KILDE = "era_birk_2026"


async def geocode_address(session: aiohttp.ClientSession, adresse: str, kommune=None):
    """Try to geocode an address using Kartverket's API."""
    # First try with full address
    query = adresse
    params = {"sok": query, "fuzzy": "true", "treffPerSide": "1"}
    if kommune:
        params["kommunenavn"] = kommune

    try:
        async with session.get(KARTVERKET_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                hits = data.get("adresser", [])
                if hits:
                    pt = hits[0].get("representasjonspunkt", {})
                    lat = pt.get("lat")
                    lon = pt.get("lon")
                    if lat and lon:
                        return float(lat), float(lon)
    except Exception:
        pass

    # Fallback: just address without kommune filter
    if kommune:
        try:
            params2 = {"sok": query, "fuzzy": "true", "treffPerSide": "1"}
            async with session.get(KARTVERKET_URL, params=params2, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    hits = data.get("adresser", [])
                    if hits:
                        pt = hits[0].get("representasjonspunkt", {})
                        lat = pt.get("lat")
                        lon = pt.get("lon")
                        if lat and lon:
                            return float(lat), float(lon)
        except Exception:
            pass

    return None, None


async def run():
    async with SessionLocal() as db:
        # Get all ERA rows without coordinates
        r = await db.execute(text("""
            SELECT id, avdelings_navn, adresse, kommune, fylke, eierskap
            FROM institution_plasser
            WHERE data_kilde = :kilde
              AND adresse IS NOT NULL
              AND (latitude IS NULL OR latitude = 0)
            ORDER BY eierskap, id
        """), {"kilde": DATA_KILDE})
        rows = r.fetchall()
        print(f"Found {len(rows)} ERA rows to geocode")

        if not rows:
            print("Nothing to geocode — all already have coordinates.")
            return

        geocoded = 0
        failed = 0

        async with aiohttp.ClientSession() as session:
            # Process in batches
            for i in range(0, len(rows), BATCH_SIZE):
                batch = rows[i:i + BATCH_SIZE]
                tasks = [geocode_address(session, row.adresse, row.kommune) for row in batch]
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
                        failed += 1
                        if failed <= 10:  # only log first 10 failures
                            print(f"  FAILED: {row.avdelings_navn} | {row.adresse}")

                await db.commit()

                done = min(i + BATCH_SIZE, len(rows))
                print(f"  Progress: {done}/{len(rows)} — geocoded: {geocoded}, failed: {failed}")

        print(f"\nDone. Geocoded: {geocoded}, Failed: {failed}")

        # Summary per eierskap
        r2 = await db.execute(text("""
            SELECT eierskap, COUNT(*) total, COUNT(latitude) with_coords
            FROM institution_plasser
            WHERE data_kilde = :kilde
            GROUP BY eierskap ORDER BY total DESC
        """), {"kilde": DATA_KILDE})
        print("\nCoordinate coverage per eierskap:")
        for row in r2.fetchall():
            print(f"  {row.eierskap}: {row.with_coords}/{row.total} with coords")


if __name__ == "__main__":
    asyncio.run(run())
