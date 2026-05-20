
import asyncio
import os
import sys
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.db.session import SessionLocal
from app.models.financial_models import Budget, GLTransaction
from app.models.text_content import TextContent
from app.models.socioeconomic import SocioeconomicData
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract

async def verify():
    async with SessionLocal() as db:
        print("--- Database Cleanup Verification ---")
        
        # 1. Check Tables
        for model in [GLTransaction, Budget, TextContent, SocioeconomicData]:
            count = await db.scalar(select(func.count()).select_from(model))
            status = "EMPTY" if count == 0 else f"NOT EMPTY ({count} rows)"
            print(f"Table {model.__tablename__}: {status}")
            
        # 2. Check Property metadata
        prop_with_fin = await db.scalar(
            select(func.count(Property.property_id))
            .where(Property.external_data.has_key('financials'))
        )
        print(f"Properties with 'financials' metadata: {prop_with_fin}")
        
        # 3. Check Contract costs
        contract_with_costs = await db.scalar(
            select(func.count(Contract.contract_id))
            .where(
                (Contract.caretaker_cost != None) | 
                (Contract.cleaning_cost != None) | 
                (Contract.parking_cost != None) | 
                (Contract.card_reader_cost != None)
            )
        )
        print(f"Contracts with remaining cost data: {contract_with_costs}")
        
if __name__ == "__main__":
    try:
        asyncio.run(verify())
    except Exception as e:
        print(f"Verification failed: {e}")
