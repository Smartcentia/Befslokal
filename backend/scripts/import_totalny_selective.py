
import sys
import os
import asyncio
import csv
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property

def parse_currency(value_str):
    if not value_str:
        return 0.0
    clean_val = value_str.replace(" ", "").replace("\xa0", "").replace(",", ".").replace("kr", "").strip()
    try:
        return float(clean_val)
    except ValueError:
        return 0.0

async def import_totalny_selective():
    print("Starting Selective Import of totalny.txt...")
    
    file_path = "docs/totalny.txt"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    async with SessionLocal() as db:
        # Pre-fetch all active contracts
        stmt = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        # Build File Map
        file_map = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            # Identify columns
            rent_key = None
            kpi_key = None
            for key in reader.fieldnames:
                if "Kontraktsleie ved oppstart" in key and "gyldig" not in key:
                    rent_key = key
                if "KPI-justert" in key and "2025" in key:
                    kpi_key = key
            
            if not rent_key:
                print("Could not find 'Kontraktsleie ved oppstart' column.")
                return
            
            print(f"Using Rent Key: {rent_key}")
            if kpi_key:
                print(f"Found Optional KPI Key: {kpi_key}")

            for row in reader:
                name = row.get("Avtalenavn", "").strip()
                if not name:
                    continue
                
                # We use the START RENT as primary, but could fallback?
                # For this script we stick to Start Rent to be consistent with previous structure
                val = parse_currency(row.get(rent_key, "0"))
                file_map[name.lower()] = val

        updated_count = 0
        skipped_count = 0
        
        for contract in contracts:
            if not contract.unit or not contract.unit.property:
                continue
                
            p_name = contract.unit.property.name.strip()
            p_name_lower = p_name.lower()
            
            # Get Current DB Value
            current_amount_data = contract.amount if isinstance(contract.amount, dict) else {}
            current_rent = float(current_amount_data.get('amount_per_year', 0.0))
            
            # Get File Value
            file_rent = file_map.get(p_name_lower)
            
            if file_rent is None:
                continue
            
            # LOGIC:
            # 1. If DB has valid value (> 0 AND < 100M) -> KEEP DB (Skip)
            # 2. If DB is 0 OR DB is Insane -> UPDATE from File (if File > 0 and File < 100M)
            
            # Is DB Valid?
            db_valid = (current_rent > 1.0 and current_rent < 100_000_000)
            
            if db_valid:
                # User Requirement: "vi endrer ikke Røvika..., resten fikser"
                # If valid in DB, assume it's one of the preserved ones or manually corrected ones.
                # However, if it DIFFERENT?
                # Given the user specifically named examples of where DB was OK and File was 0 (Røvika),
                # trusting DB for valid values seems correct.
                # print(f"Skipping '{p_name}' (DB: {current_rent} | File: {file_rent}) - Preserving DB")
                skipped_count += 1
                continue
            
            # DB is NOT valid (0 or Insane)
            # Is File Valid?
            file_valid = (file_rent > 1.0 and file_rent < 100_000_000)
            
            if file_valid:
                print(f"Updating '{p_name}': DB({current_rent}) -> File({file_rent})")
                
                new_amount_dict = contract.amount.copy() if contract.amount else {}
                new_amount_dict['amount_per_year'] = file_rent
                contract.amount = new_amount_dict
                updated_count += 1
            else:
                # Both invalid/zero
                pass

        await db.commit()
        print(f"Import Complete.")
        print(f"Updated: {updated_count} properties.")
        print(f"Skipped (Preserved DB): {skipped_count} properties.")

if __name__ == "__main__":
    asyncio.run(import_totalny_selective())
