import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy import text
from app.db.session import SessionLocal

async def check_properties():
    async with SessionLocal() as db:
        result = await db.execute(text('SELECT COUNT(*) FROM properties'))
        count = result.scalar()
        print(f"✅ Antall eiendommer i database: {count}")
        
        # Get a few examples
        result = await db.execute(text('SELECT address, city FROM properties LIMIT 5'))
        print("\nEksempel eiendommer:")
        for row in result:
            print(f"  - {row[0]}, {row[1]}")

if __name__ == "__main__":
    asyncio.run(check_properties())
