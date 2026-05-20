#!/usr/bin/env python3
"""
Update property names from CSV Avtalenavn field.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select
import pandas as pd
from fuzzywuzzy import fuzz

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

CSV_PATH = "/Volumes/KINGSTON/csv/Bufetat_leiedata_renset.csv"

async def update_property_names():
    print("📝 Updating Property Names from CSV")
    print("=" * 60)
    
    # Load CSV
    print("\n📊 Loading CSV data...")
    df = pd.read_csv(CSV_PATH, sep=';', encoding='utf-8-sig')
    print(f"  Loaded {len(df)} rows")
    
    # Get all properties from database
    print("\n🗄️  Loading properties from database...")
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        print(f"  Loaded {len(properties)} properties")
        
        # Create address lookup for properties
        prop_by_address = {}
        for prop in properties:
            if prop.address:
                addr_key = prop.address.lower().strip()
                prop_by_address[addr_key] = prop
        
        # Update names
        updated = 0
        skipped = 0
        
        print("\n🔄 Updating names...")
        for idx, row in df.iterrows():
            csv_address = str(row.get('Adresselinje 1', '')).strip()
            csv_name = str(row.get('Avtalenavn', '')).strip()
            
            if not csv_address or not csv_name:
                continue
            
            # Find matching property
            csv_addr_key = csv_address.lower().strip()
            matched_prop = prop_by_address.get(csv_addr_key)
            
            # Try fuzzy matching if exact match fails
            if not matched_prop:
                best_match = None
                best_score = 0
                for db_addr, prop in prop_by_address.items():
                    score = fuzz.ratio(csv_addr_key, db_addr)
                    if score > best_score and score >= 85:
                        best_score = score
                        best_match = prop
                matched_prop = best_match
            
            if matched_prop:
                # Update name if different and looks like a real name (not just address)
                # Avoid overwriting if usage suggests it might not be relevant, but user wants everything cleaned
                
                # Check if csv_name is just the address repeated (approx)
                name_is_addr_ratio = fuzz.ratio(csv_name.lower(), csv_address.lower())
                
                if name_is_addr_ratio < 80: # If name is significantly different from address
                    if matched_prop.name != csv_name:
                        # Fix encoding issues if any (common in some CSVs)
                        matched_prop.name = csv_name
                        updated += 1
                        if updated <= 5:
                            print(f"  ✓ {matched_prop.address}: '{matched_prop.name}' → '{csv_name}'")
                else:
                    skipped += 1
            else:
                # print(f"  ⚠️  Not found: {csv_address}")
                pass
        
        await db.commit()
        print(f"\n✅ Updated {updated} property names")
        print(f"  Skipped {skipped} where name ≈ address")

if __name__ == "__main__":
    asyncio.run(update_property_names())
