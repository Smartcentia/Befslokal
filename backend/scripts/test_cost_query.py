
import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal

async def test_cost():
    print("🚀 Testing Cost Query...")
    async with SessionLocal() as session:
        try:
            print("   Executing SQL...")
            # Using cast to text for status to be safe
            cost_result = await session.execute(text("""
                SELECT p.name, p.city, (c.amount->>'amount_per_year')::float as cost, c.status::text
                FROM contracts c
                JOIN units u ON c.unit_id = u.unit_id
                JOIN properties p ON u.property_id = p.property_id
                WHERE (c.amount->>'amount_per_year')::float > 0
                ORDER BY (c.amount->>'amount_per_year')::float DESC
                LIMIT 5
            """))
            
            rows = cost_result.fetchall()
            print(f"   ✅ Got {len(rows)} rows.")
            for r in rows:
                print(f"   - {r.name}: {r.cost}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_cost())
