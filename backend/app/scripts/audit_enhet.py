
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

async def audit_enhet():
    async with SessionLocal() as db:
        res = await db.execute(select(Property).where(Property.name.ilike('%Enhet for%')))
        props = res.scalars().all()
        
        for p in props:
            print(f"Name: {p.name} | ID: {p.property_id}")

if __name__ == "__main__":
    asyncio.run(audit_enhet())
