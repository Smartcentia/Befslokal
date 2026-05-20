import asyncio
import csv
import sys
import os
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

# Add backend to path
sys.path.append(os.getcwd())

# Load env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), '.env'))

from app.db.session import SessionLocal
# Import base to register all models
from app.db.base import Base 
from app.domains.core.models.property import Property

async def verify_csv_import():
    # Helper to check paths
    possible_paths = ["docs/Eie1212.csv", "backend/docs/Eie1212.csv", "../docs/Eie1212.csv"]
    csv_file_path = None
    for p in possible_paths:
        if os.path.exists(p):
            csv_file_path = p
            break
            
    if not csv_file_path:
        print(f"Error: CSV file not found in {possible_paths}")
        return

    print(f"Verifying import from: {csv_file_path}")
    
    properties_in_csv = []
    
    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        # Normalize headers
        reader.fieldnames = [name.lower().strip() for name in reader.fieldnames]
        
        for i, row in enumerate(reader):
            # Same logic as import_master_data.py to identify property
            loc_full = row.get("lokalisering", "").strip()
            # Skip empty rows (as found in analysis)
            if not loc_full and not row.get("avtalenavn"):
                continue
                
            properties_in_csv.append(loc_full)

    print(f"Found {len(properties_in_csv)} valid property records in CSV.")

    async with SessionLocal() as session:
        # Check count
        result = await session.execute(select(func.count(Property.property_id)))
        db_count = result.scalar()
        print(f"Total properties in DB: {db_count}")
        
        # Check match for a sample
        result = await session.execute(select(Property))
        db_props = result.scalars().all()
        
        # Create a set of normalized names/addresses from DB for matching
        db_prop_names = {p.name.lower() for p in db_props if p.name}
        db_prop_addresses = {p.address.lower() for p in db_props if p.address}
        
        missing_count = 0
        found_count = 0
        
        for loc in properties_in_csv:
            is_found = False
            # Try exact match strategies from import script logic
            # 1. Name match (assuming lokalisering often ends up in name or related)
            # The import script maps "lokalisering" to "address" primarily, but also tries name matching.
            
            # Simple check: is the string in address or name?
            norm_loc = loc.lower()
            
            # Note: The import script logic is complex, doing fuzzy matching.
            # Here we just check if we can find it reasonably well to gauge coverage.
            
            if norm_loc in db_prop_addresses:
                is_found = True
            elif norm_loc in db_prop_names:
                is_found = True
            else:
                # Try splitting ID - Name
                if " - " in norm_loc:
                    _, name_part = norm_loc.split(" - ", 1)
                    if name_part.strip().lower() in db_prop_names:
                        is_found = True
            
            if is_found:
                found_count += 1
            else:
                missing_count += 1
                if missing_count <= 5:
                    print(f"POSSIBLE MISSING: {loc}")

        print(f"Matched {found_count} properties directly.")
        print(f"Potential missing/mismatched: {missing_count}")
        
        if db_count >= len(properties_in_csv):
             print("SUCCESS: DB count is equal or higher than CSV count.")
        else:
             print("WARNING: DB count is lower than CSV count.")

if __name__ == "__main__":
    asyncio.run(verify_csv_import())
