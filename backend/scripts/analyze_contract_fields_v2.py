
import asyncio
import os
import sys
from sqlalchemy import text
from collections import Counter

# Add backend root to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import SessionLocal

async def analyze_fields():
    async with SessionLocal() as db:
        # 1. Analyze Core Columns
        print("Analyserer 'contracts' tabellen...")
        result = await db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(status) as status_count,
                COUNT(category) as category_count,
                COUNT(start_date) as start_date_count,
                COUNT(end_date) as end_date_count,
                COUNT(signed_at) as signed_at_count,
                COUNT(caretaker_cost) as caretaker_count,
                COUNT(cleaning_cost) as cleaning_count,
                COUNT(parking_cost) as parking_count,
                COUNT(card_reader_cost) as card_reader_count
            FROM contracts
        """))
        row = result.fetchone()
        
        print(f"\n--- STANDARD DATABASEFELTER (Totalt {row[0]} kontrakter) ---")
        print(f"- Status: {row[1]}")
        print(f"- Kategori: {row[2]}")
        print(f"- Startdato: {row[3]}")
        print(f"- Sluttdato: {row[4]}")
        print(f"- Signert dato: {row[5]}")
        print(f"- Vaktmesterkostnad: {row[6]}")
        print(f"- Renholdskostnad: {row[7]}")
        print(f"- Parkeringsleie (felt): {row[8]}")
        
        # 2. Analyze External Data (JSONB)
        print("\n--- TILLEGGSFELTER (Import/External Data) ---")
        result = await db.execute(text("SELECT external_data FROM contracts WHERE external_data IS NOT NULL"))
        rows = result.fetchall()
        
        key_counter = Counter()
        for r in rows:
            data = r[0]
            if data:
                for key in data.keys():
                    if data[key]: # Only count if value is not null/empty
                        key_counter[key] += 1
                        
        for key, count in key_counter.most_common():
            print(f"- {key}: {count}")

if __name__ == "__main__":
    asyncio.run(analyze_fields())
