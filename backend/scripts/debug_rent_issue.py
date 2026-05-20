import sys
import os
import csv
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

import app.db.base # Register all models
from app.db.session import SessionLocal
from app.domains.core.models.party import Party
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property

def normalize_address(addr):
    if not addr:
        return ""
    addr = addr.split(',')[0]
    addr = addr.lower().strip()
    return addr

def parse_currency(value):
    if not value:
        return 0.0
    clean = str(value).replace("kr", "").replace(" ", "").replace("\xa0", "").replace(",", ".")
    try:
        return float(clean)
    except ValueError:
        return 0.0

async def debug_rent():
    db = SessionLocal()
    try:
        # 1. Check DB Values
        print("--- DB VALUES ---")
        targets = ["Kaigata 4", "Brennstadmoen 23"]
        
        stmt = select(Contract).join(Contract.unit).join(Unit.property).options(
            joinedload(Contract.unit).joinedload(Unit.property)
        )
        result = await db.execute(stmt)
        all_contracts = result.scalars().all()
        
        for c in all_contracts:
            prop = c.unit.property
            normalized = normalize_address(prop.address)
            
            for t in targets:
                if t.lower() in normalized:
                    print(f"FOUND DB MATCH: {prop.name} (Addr: {prop.address})")
                    print(f"   Rent: {c.amount}")
                    print(f"   Contract ID: {c.contract_id}")

        # 2. Check CSV Parsing
        print("\n--- CSV PARSING ---")
        csv_path = os.path.join(os.getcwd(), 'backend', 'docs', 'Eiendom.csv')
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            headers = reader.fieldnames
            print("HEADERS:", headers)
            
            rows = list(reader)
            
            found_rows = []
            for row in rows:
                addr = row.get("Adresselinje 1", "")
                if any(t.lower() in addr.lower() for t in targets):
                    found_rows.append(row)
                    
            for row in found_rows:
                print(f"\nAnalyzing Row: {row.get('Adresselinje 1')}")
                
                # Check problematic keys
                key1 = "Kontaktsleie ved oppstart (per år)" # Script version (Typo?)
                key2 = "Kontraktsleie ved oppstart (per år)" # Likely CSV version
                key3 = "KPI-justert kontraktsleie til okt 2025"
                
                print(f"   RAW '{key1}': '{row.get(key1)}'")
                print(f"   RAW '{key2}': '{row.get(key2)}'")
                print(f"   RAW '{key3}': '{row.get(key3)}'")
                
                val1 = parse_currency(row.get(key1))
                val3 = parse_currency(row.get(key3))
                
                rent_annual = val3 if val3 > 0 else val1
                print(f"   Parsed Rent Annual: {rent_annual}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(debug_rent())
