"""One-time script: normalize Formålsbygg ↔ Barnevernsinstitusjon data"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def run():
    async with AsyncSessionLocal() as db:
        # 1. Fill unit_type_derived for all Formålsbygg where it's NULL
        r1 = await db.execute(text("""
            UPDATE properties
            SET unit_type_derived = 'Barnevernsinstitusjon'
            WHERE usage = 'Formålsbygg'
              AND (unit_type_derived IS NULL OR unit_type_derived = '')
        """))
        print(f"unit_type_derived filled for Formålsbygg: {r1.rowcount} rows")

        # 2. Normalize 'Barnevernsinstitusjon' usage → 'Formålsbygg'
        r2 = await db.execute(text("""
            UPDATE properties
            SET usage = 'Formålsbygg'
            WHERE usage = 'Barnevernsinstitusjon'
        """))
        print(f"usage normalized Barnevernsinstitusjon→Formålsbygg: {r2.rowcount} rows")

        await db.commit()
        print("Done.")

asyncio.run(run())
