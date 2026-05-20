#!/usr/bin/env python3
"""
Quick verification script to count transactions after cleanup
"""

import sys
import os
import asyncio
from sqlalchemy import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

async def verify():
    print("VERIFYING TRANSACTION COUNTS...")
    
    async with SessionLocal() as db:
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        total_transactions = 0
        for prop in properties:
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            total_transactions += len(expenses)
        
        print(f"Total properties with financial data: {len(properties)}")
        print(f"Total transactions: {total_transactions}")
        print(f"\nExpected after cleanup: ~8,224 (10,474 - 2,250)")
        print(f"Actual: {total_transactions}")
        
        if total_transactions < 9000:
            print("\n✅ Cleanup was SUCCESSFUL!")
        else:
            print("\n⚠️ Cleanup may not have been saved to database")

if __name__ == "__main__":
    asyncio.run(verify())
