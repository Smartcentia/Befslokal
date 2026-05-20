#!/usr/bin/env python3
"""
Script to find and remove duplicate financial transactions (manual_expenses)
from property external_data
"""

import sys
import os
import asyncio
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import attributes

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

async def remove_duplicates():
    print("=" * 80)
    print("REMOVING DUPLICATE FINANCIAL TRANSACTIONS")
    print("=" * 80)
    
    async with SessionLocal() as db:
        # Fetch all properties with external data
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        total_duplicates_removed = 0
        properties_cleaned = 0
        
        for prop in properties:
            ext = prop.external_data or {}
            fin = ext.get('financials', {})
            expenses = fin.get('manual_expenses', [])
            
            if not expenses:
                continue
            
            # Track seen transactions
            seen = set()
            unique_expenses = []
            duplicates_in_property = 0
            
            for exp in expenses:
                try:
                    amount_raw = exp.get('amount', 0)
                    amount = float(amount_raw) if amount_raw is not None else 0.0
                except (ValueError, TypeError):
                    amount = 0.0
                
                provider = exp.get('provider', 'Ukjent')
                category = exp.get('type', 'Ukjent')
                date = exp.get('date', 'Unknown')
                
                # Create signature
                sig = (amount, provider, category, date)
                
                if sig not in seen:
                    seen.add(sig)
                    unique_expenses.append(exp)
                else:
                    duplicates_in_property += 1
            
            # Update if duplicates were found
            if duplicates_in_property > 0:
                print(f"\n🔧 Cleaning '{prop.name}'")
                print(f"   Original: {len(expenses)} transactions")
                print(f"   Duplicates removed: {duplicates_in_property}")
                print(f"   Remaining: {len(unique_expenses)} unique transactions")
                
                # Update the property - CRITICAL: Make a NEW dict to trigger SQLAlchemy update
                new_ext = dict(ext)  # Create a copy
                new_fin = dict(new_ext.get('financials', {}))
                new_fin['manual_expenses'] = unique_expenses
                
                # Recalculate total
                total = sum(float(e.get('amount', 0) or 0) for e in unique_expenses)
                new_fin['total_manual_expenses'] = total
                
                new_ext['financials'] = new_fin
                prop.external_data = new_ext
                
                # CRITICAL: Flag as modified for JSONB
                attributes.flag_modified(prop, 'external_data')
                
                total_duplicates_removed += duplicates_in_property
                properties_cleaned += 1
        
        # Commit changes
        await db.commit()
        
        print("\n" + "=" * 80)
        print("CLEANUP SUMMARY")
        print("=" * 80)
        print(f"✅ Properties cleaned: {properties_cleaned}")
        print(f"✅ Total duplicate transactions removed: {total_duplicates_removed}")
        print(f"\n🎉 Database cleaned successfully!")

if __name__ == "__main__":
    asyncio.run(remove_duplicates())
