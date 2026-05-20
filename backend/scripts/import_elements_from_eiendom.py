import asyncio
import sys
import os
import csv
import re

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base 
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

# CSV Delimiter is ';', assuming standard encoding
CSV_PATH = "backend/docs/Eiendom.csv"

def normalize_address(addr):
    if not addr:
        return ""
    # Remove city part if comma exists??
    # CSV Address example: "Abel Meyers gate 10"; "Abel Meyers gate 10, 7800 Namsos"
    # DB Address example: "Abel Meyers gate 10"
    
    # Try to take first part before comma
    parts = addr.split(',')
    a = parts[0].strip()
    
    # Lowercase
    return a.lower()

async def import_eiendom_data():
    db = SessionLocal()
    try:
        print(f"Reading {CSV_PATH}...")
        
        # Pre-load all properties to memory
        stmt = select(Contract).join(Contract.unit).join(Unit.property).options(
            joinedload(Contract.unit).joinedload(Unit.property)
        )
        result = await db.execute(stmt)
        all_contracts = result.scalars().all()
        print(f"Loaded {len(all_contracts)} contracts from DB.")
        
        updates_made = 0
        matches_found = 0
        
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            # Use semi-colon delimiter
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            
        print(f"Loaded {len(rows)} rows from CSV.")
        
        for row in rows:
            # Column name might have trailing space "Elements "
            elements_val = row.get("Elements ") or row.get("Elements")
            
            # Address columns to try
            addr1 = row.get("Adresselinje 1") # "Abel Meyers gate 10"
            
            if not elements_val or not addr1:
                continue
            
            # Clean elements ID: extract first YYYY/XXXX pattern
            match = re.search(r'(\d{4}/\d+)', elements_val)
            if match:
                clean_id = match.group(1)
            else:
                continue
            
            # Matching Logic
            csv_addr_norm = normalize_address(addr1)
            
            best_match = None
            for c in all_contracts:
                prop = c.unit.property
                db_addr_norm = normalize_address(prop.address)
                
                if not db_addr_norm: continue
                
                # Check match
                if csv_addr_norm == db_addr_norm:
                    best_match = c
                    break
                elif csv_addr_norm.startswith(db_addr_norm) and len(db_addr_norm) > 5:
                    best_match = c
                    break
                elif db_addr_norm.startswith(csv_addr_norm) and len(csv_addr_norm) > 5:
                    best_match = c
                    break
            
            if best_match:
                matches_found += 1
                prop = best_match.unit.property
                
                # Check if update needed
                current_val = best_match.elements
                if current_val != clean_id:
                     print(f"UPDATING {best_match.contract_id}: {current_val} -> {clean_id} (Address: {addr1})")
                     
                     stmt = update(Contract).where(Contract.contract_id == best_match.contract_id).values(elements=clean_id)
                     await db.execute(stmt)
                     updates_made += 1
                else:
                    pass
            else:
                pass

        await db.commit()
        print(f"\nMigration Complete.")
        print(f"Matches Found: {matches_found}")
        print(f"Updates Made: {updates_made}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(import_eiendom_data())
