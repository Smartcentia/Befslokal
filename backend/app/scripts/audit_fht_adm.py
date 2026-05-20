
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

async def audit_fht():
    async with SessionLocal() as db:
        res = await db.execute(select(Property).where(Property.name == 'FHT RN - adm'))
        p = res.scalars().first()
        if not p:
            print("Property FHT RN - adm not found")
            return
            
        fin = p.external_data.get('financials', {})
        expenses = fin.get('manual_expenses', [])
        
        print(f"Audit for {p.name}")
        print(f"Total Transactions: {len(expenses)}")
        
        by_source = {}
        by_type = {}
        for e in expenses:
            src = e.get('source', 'unk')
            by_source[src] = by_source.get(src, 0) + e.get('amount', 0)
            
            etype = e.get('type', 'unk')
            by_type[etype] = by_type.get(etype, 0) + e.get('amount', 0)
            
        print("\nBy Source:")
        for k, v in by_source.items():
            print(f"- {k}: {v:,.0f} kr")
            
        print("\nBy Type:")
        for k, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            print(f"- {k}: {v:,.0f} kr")
            
        print("\nBy Provider:")
        by_provider = {}
        for e in expenses:
            p = e.get('provider') or e.get('description') or 'unk'
            by_provider[p] = by_provider.get(p, 0) + e.get('amount', 0)
        for k, v in sorted(by_provider.items(), key=lambda x: x[1], reverse=True)[:30]:
            print(f"- {k}: {v:,.0f} kr")
            
        print("\nSample (first 10):")
        for e in expenses[:10]:
            print(f"- {e}")

if __name__ == "__main__":
    asyncio.run(audit_fht())
