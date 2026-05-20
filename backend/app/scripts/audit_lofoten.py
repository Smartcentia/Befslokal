
import asyncio
import sys
import os
from sqlalchemy import select
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

async def audit_lofoten():
    async with SessionLocal() as db:
        res = await db.execute(select(Property).where(Property.name.ilike('%Lofoten%')))
        p = res.scalars().first()
        if p:
            print(f"Name: {p.name}")
            print(f"Address: {p.address}")
            print(f"Financials: {json.dumps(p.external_data.get('financials', {}), indent=2)}")
        else:
            print("Not found")

if __name__ == "__main__":
    import json
    asyncio.run(audit_lofoten())
