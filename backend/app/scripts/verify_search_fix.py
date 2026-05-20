import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from app.db.session import SessionLocal
from app.services.search.search_service import search_fulltext

async def verify_fix():
    async with SessionLocal() as db:
        print("Testing search_fulltext with 'parkering'...")
        # We expect results because we know the text exists (from alt.md)
        results = await search_fulltext(db, "parkering", limit=5)
        
        print(f"Found {len(results)} results.")
        for r in results:
            print(f"- {r['source_file']}: Match Rank {r['rank']}")
            # If rank is 0 or low, it might be an ILIKE match (ts_rank might be 0 if only ILIKE matched? No, strictly speaking ts_rank depends on vector match. 
            # If valid ts_vector match: rank > 0.
            # If only ILIKE match: rank calculation plainto_tsquery might yield 0 if no vector match? 
            # Let's see output.

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify_fix())
