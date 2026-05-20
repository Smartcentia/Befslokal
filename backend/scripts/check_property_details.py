#!/usr/bin/env python3
"""
Check specific property details to answer user query.
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
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.models.file_meta

async def check_property_details():
    print("🔍 Checking Property Details")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Find a property that has both Bufdir data and Approved Places
        result = await db.execute(
            select(Property)
            .where(Property.external_data.is_not(None))
            .where(Property.approved_places.is_not(None))
            .limit(1)
        )
        prop = result.scalar_one_or_none()
        
        if not prop:
            # Fallback to any property with external data
            result = await db.execute(
                select(Property)
                .where(Property.external_data.is_not(None))
                .limit(1)
            )
            prop = result.scalar_one_or_none()
        
        if prop:
            print(f"\n📍 Property: {prop.name}")
            print(f"   Address: {prop.address}")
            print("-" * 40)
            
            # 1. Eierskap (Privat/Statlig)
            # This comes from Bufdir external_data
            bufdir_data = prop.external_data.get('bufdir_institution', {})
            owner_type = bufdir_data.get('owner_type')
            print(f"1. Eierskap (fra Bufdir): {owner_type}")
            
            # 2. Plasseringstype (Legal Bases)
            # This comes from Bufdir external_data
            legal_bases = bufdir_data.get('legal_bases', [])
            print(f"2. Plasseringstype (fra Bufdir):")
            if legal_bases:
                for base in legal_bases:
                    print(f"   - {base}")
            else:
                print("   (Ingen registrert)")
            
            # 3. Kapasitet (Plasser)
            # This comes from CSV import (Property model field)
            print(f"3. Kapasitet (fra CSV): {prop.approved_places} plasser")
            
            # 4. Sted
            # This comes from Property model
            print(f"4. Sted (fra DB):")
            print(f"   By: {prop.city}")
            print(f"   Kommune: {prop.municipality}")
            print(f"   Region: {prop.region}")
            
            print("-" * 40)
            print("✅ Data sources confirmed:")
            print("   - Bufdir data -> external_data columns")
            print("   - CSV data -> property columns (approved_places, address)")
            
        else:
            print("❌ No enriched properties found to check.")

if __name__ == "__main__":
    asyncio.run(check_property_details())
