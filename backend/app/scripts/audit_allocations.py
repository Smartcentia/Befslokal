
import asyncio
import sys
import os
import json
from sqlalchemy import select
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Import related models to avoid Mapper initialization errors
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party

async def inspect_allocations():
    async with SessionLocal() as db:
        # Get properties that have financials
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        
        report = []
        for p in properties:
            fin = (p.external_data or {}).get('financials', {})
            expenses = fin.get('manual_expenses', [])
            
            if not expenses:
                continue
                
            total_calc = 0.0
            source_distribution = {}
            for e in expenses:
                try:
                    amt = float(e.get('amount', 0))
                except (ValueError, TypeError):
                    amt = 0.0
                total_calc += amt
                src = e.get('source', 'unknown')
                source_distribution[src] = source_distribution.get(src, 0.0) + amt
            
            report.append({
                "id": str(p.property_id),
                "name": p.name,
                "address": p.address,
                "total_manual_expenses": fin.get('total_manual_expenses'),
                "calculated_total": total_calc,
                "source_distribution": source_distribution,
                "sample_expenses": expenses[:3] # Just for debugging
            })
            
        # Sort by total cost descending to see the "big fish" from the screenshot
        report.sort(key=lambda x: x['total_manual_expenses'] or 0, reverse=True)
        
        print(json.dumps(report[:20], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(inspect_allocations())
