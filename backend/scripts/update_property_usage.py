#!/usr/bin/env python3
"""
Update property usage types from CSV Type lokasjon field.
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
from app.domains.core.models.property import Property

import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.models.file_meta

CSV_PATH = "/Volumes/KINGSTON/csv/Bufetat_leiedata_renset.csv"

# Mapping from CSV Type lokasjon to database usage
TYPE_MAPPING = {
    'Formålsbygg': 'Barnevernsinstitusjon',
    'Kontor': 'Kontor',
    'Familievernkontor': 'Familievernkontor'
}

async def update_property_usage():
    print("🏢 Updating Property Usage Types")
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
                # Normalize address for matching
                addr_key = prop.address.lower().strip()
                prop_by_address[addr_key] = prop
        
        # Process CSV rows
        print("\n🔄 Matching and updating...")
        updated = 0
        not_found = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            csv_address = str(row.get('Adresselinje 1', '')).strip()
            csv_type = str(row.get('Type lokasjon', '')).strip()
            
            if not csv_address or not csv_type:
                continue
            
            # Skip if type not in mapping
            if csv_type not in TYPE_MAPPING:
                skipped += 1
                continue
            
            # Find matching property
            csv_addr_key = csv_address.lower().strip()
            
            # Try exact match first
            matched_prop = prop_by_address.get(csv_addr_key)
            
            # If no exact match, try fuzzy matching
            if not matched_prop:
                best_match = None
                best_score = 0
                
                for db_addr, prop in prop_by_address.items():
                    score = fuzz.ratio(csv_addr_key, db_addr)
                    if score > best_score and score >= 85:  # 85% similarity threshold
                        best_score = score
                        best_match = prop
                
                matched_prop = best_match
            
            if matched_prop:
                # Update usage
                new_usage = TYPE_MAPPING[csv_type]
                old_usage = matched_prop.usage
                
                if old_usage != new_usage:
                    matched_prop.usage = new_usage
                    updated += 1
                    
                    if updated <= 5:  # Show first 5 examples
                        print(f"  ✓ {matched_prop.address}: {old_usage or 'NULL'} → {new_usage}")
            else:
                not_found += 1
                if not_found <= 3:  # Show first 3 not found
                    print(f"  ⚠️  Not found: {csv_address}")
        
        # Commit changes
        await db.commit()
        
        print(f"\n✅ Update complete!")
        print(f"  Updated: {updated}")
        print(f"  Not found: {not_found}")
        print(f"  Skipped (unknown type): {skipped}")
        
        # Show final distribution
        print(f"\n📊 Final usage distribution:")
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        
        usage_counts = {}
        for p in properties:
            usage = p.usage or "NULL"
            usage_counts[usage] = usage_counts.get(usage, 0) + 1
        
        for usage, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
            print(f"  {usage}: {count}")

if __name__ == "__main__":
    asyncio.run(update_property_usage())
