#!/usr/bin/env python3
"""
Check property details finding a good example.
"""
import sys
import os
from pathlib import Path
import asyncio
import json
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
# Import all models to ensure relationships are set up correctly
import app.domains.core.models.user
from app.domains.core.models.property import Property
import app.models.file_meta
# Add other imports if needed, but Property is main one

async def find_good_example():
    print("🔍 Searching for comprehensive example...")
    
    async with SessionLocal() as db:
        # Fetch properties with external data
        result = await db.execute(select(Property).where(Property.external_data.is_not(None)))
        props = result.scalars().all()
        
        found = False
        for prop in props:
            data = prop.external_data.get('bufdir_institution', {})
            legal_bases = data.get('legal_bases')
            owner_type = data.get('owner_type')
            
            if legal_bases and owner_type:
                print(f"\n📍 Property: {prop.name}")
                print(f"   Address: {prop.address}")
                print("-" * 40)
                print(f"1. Eierskap: {owner_type}")
                print(f"2. Plasseringstype:")
                for base in legal_bases:
                    print(f"   - {base}")
                print(f"3. Kapasitet: {prop.approved_places or 'Ikke angitt'} plasser")
                print(f"4. Sted: {prop.city}, {prop.municipality}")
                found = True
                break
        
        if not found:
            print("Could not find a property with ALL fields populated.")

if __name__ == "__main__":
    asyncio.run(find_good_example())
