import sys
import os
import asyncio
from sqlalchemy import select
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

async def enrich_financial_metadata():
    print("Starting financial metadata enrichment...")
    
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        
        updated_count = 0
        
        for p in properties:
            ext = dict(p.external_data or {})
            financials = ext.get('financials')
            
            if financials:
                # 1. Calculate Transaction Count
                manual_expenses = financials.get('manual_expenses', [])
                # Also count CSV items if they were stored separately (though we merged them)
                # In current logic, usually merged into manual_expenses
                tx_count = len(manual_expenses)
                
                # 2. Aggregates Accounts (Types)
                # Create a dict: { "Strøm": 12, "Husleie": 4 }
                accounts_summary = {}
                for exp in manual_expenses:
                    t = exp.get('type', 'Annet')
                    accounts_summary[t] = accounts_summary.get(t, 0) + 1
                
                # Update Metadata
                financials['transaction_count'] = tx_count
                financials['accounts'] = accounts_summary
                
                ext['financials'] = financials
                p.external_data = ext
                updated_count += 1
                
                if updated_count % 10 == 0:
                    print(f"Updated {p.name}: {tx_count} txs, Accounts: {list(accounts_summary.keys())}")
        
        if updated_count > 0:
            await db.commit()
            print(f"Successfully enriched metadata for {updated_count} properties.")
        else:
            print("No properties with financial data found to enrich.")

if __name__ == "__main__":
    asyncio.run(enrich_financial_metadata())
