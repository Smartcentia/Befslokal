
import asyncio
import sys
import os
import json
from sqlalchemy import select
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party

async def dump_properties():
    async with SessionLocal() as db:
        res = await db.execute(select(Property))
        props = res.scalars().all()
        
        data = []
        for p in props:
            data.append({
                "property_id": str(p.property_id),
                "name": p.name,
                "address": p.address,
                "city": p.city,
                "region": p.region
            })
            
        with open('backend/app/scripts/properties_dump.json', 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Dumped {len(data)} properties to backend/app/scripts/properties_dump.json")

if __name__ == "__main__":
    asyncio.run(dump_properties())
