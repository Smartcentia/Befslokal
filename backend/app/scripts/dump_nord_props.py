
import asyncio
import sys
import os
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

async def dump_nord():
    async with SessionLocal() as db:
        res = await db.execute(select(Property))
        props = res.scalars().all()
        nord = [p for p in props if (p.region and 'Nord' in p.region) or (p.name and 'Nord' in p.name) or (p.name and 'FHT RN' in p.name)]
        
        print(f"Found {len(nord)} properties related to Nord:")
        for p in nord:
            fin = (p.external_data or {}).get('financials', {})
            manual_total = fin.get('total_manual_expenses', 0)
            print(f"- {p.name} | {p.address} | Manual Cost: {manual_total:,.0f} kr")

if __name__ == "__main__":
    asyncio.run(dump_nord())
