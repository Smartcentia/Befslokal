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

async def dry_run_eiendom_import():
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
        
        updates_planned = 0
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
            addr2 = row.get("Adresse og Postnummer ") # "Abel Meyers gate 10, 7800 Namsos"
            
            if not elements_val or not addr1:
                continue
                
            # Clean elements ID
            # Some look like "2005/7144 og 2016/52812" -> Handle multiple?
            # ideally pick first valid one or store as is? 
            # Current model is String, maybe just take the first if multiple?
            # Or just take the raw string if it fits?
            
            # Let's clean it up slightly
            # If multiple, maybe just take the first one for now or keep as text?
            # User wants "Elements ID". usually singular.
            # Example: "2005/7144 og 2016/52812" -> "2005/7144"
            
            match = re.search(r'(\d{4}/\d+)', elements_val)
            if match:
                clean_id = match.group(1)
            else:
                # If no pattern match, skip? or use raw?
                # skipping for safety to imply strict format 'YYYY/XXXX'
                continue
            
            # Matching Logic
            # Try addr1 first (Adresselinje 1 seems cleaner)
            csv_addr_norm = normalize_address(addr1)
            
            best_match = None
            for c in all_contracts:
                prop = c.unit.property
                db_addr_norm = normalize_address(prop.address)
                
                if not db_addr_norm: continue
                
                # Check match
                # 1. Exact
                # 2. Startswith
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
                     print(f"MATCH: '{addr1}' -> '{prop.name}' (Contract {best_match.contract_id})")
                     print(f"   Action: UPDATE '{current_val}' -> '{clean_id}'")
                     updates_planned += 1
                else:
                    # print(f"MATCH: '{addr1}' already has correct ID '{clean_id}'")
                    pass
            else:
                print(f"NO MATCH for CSV Address: '{addr1}' (ID: {clean_id})")

        print(f"\nSummary:")
        print(f"Total Rows with ID: {len([r for r in rows if r.get('Elements ')])}")
        print(f"Matches Found: {matches_found}")
        print(f"Updates Planned: {updates_planned}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(dry_run_eiendom_import())
