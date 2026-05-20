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
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
# Import base to register all models (Party, RiskAssessment, etc.)
import app.db.base 
from sqlalchemy import select
from sqlalchemy.orm import joinedload

def parse_elements_id(filename):
    # Pattern: start with YY-XXXXX-XX or similar
    # Example: 04-12010-14 -> 2004/12010
    # Example: 23-72720-14 -> 2023/72720
    
    match = re.match(r'^(\d{2})-(\d+)-', filename)
    if match:
        year_short = match.group(1)
        seq = match.group(2)
        # Assume 20xx
        return f"20{year_short}/{seq}"
    return None

async def dry_run_import():
    db = SessionLocal()
    try:
        csv_path = "contracts.csv"
        print(f"Reading {csv_path}...")
        
        matches_found = 0
        ids_extracted = 0
        
        # Load all contracts with property info to memory for efficient matching
        # Or just query one by one if dataset is small (160 rows is small)
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        print(f"Loaded {len(rows)} rows from CSV.")
        
        for row in rows:
            filename = row.get("Filnavn (Kilde)")
            address = row.get("Adresse")
            
            if not filename or not address:
                continue
                
            elements_id = parse_elements_id(filename)
            if not elements_id:
                # print(f"Skipping row: No ID parsed from '{filename}'")
                continue
            
            ids_extracted += 1
            
            # Clean address for matching (simple fuzzy or direct?)
            # CSV: "Aurdalslia 96, Sandsli"
            # DB Property Property: "Aurdalslia 96" or "Aurdalslia 96, Sandsli"
            
            # Try to match by address in DB
            # We search for properties where address is like the start of CSV address
            search_addr = address.split(',')[0].strip() # "Aurdalslia 96"
            
            stmt = select(Contract).join(Contract.unit).join(Unit.property).where(
                Property.address.ilike(f"%{search_addr}%")
            ).options(
                joinedload(Contract.unit).joinedload(Unit.property)
            )
            
            result = await db.execute(stmt)
            contracts = result.scalars().all()
            
            if contracts:
                matches_found += 1
                # If multiple, take first? or list?
                c = contracts[0]
                prop_name = c.unit.property.name
                current_el = c.elements
                
                print(f"MATCH: CSV '{address}' -> DB Property '{prop_name}' (Contract {c.contract_id})")
                print(f"  Extracted ID: {elements_id}")
                if current_el:
                    print(f"  Current DB value: {current_el}")
                print(f"  Action: Would UPDATE to '{elements_id}'")
                print("-" * 20)
            else:
                print(f"NO MATCH: Could not find property/contract for address '{address}' (Search: '{search_addr}')")
        
        print(f"\nSummary:")
        print(f"Rows with parsed ID: {ids_extracted}")
        print(f"Matched to DB Contracts: {matches_found}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(dry_run_import())
