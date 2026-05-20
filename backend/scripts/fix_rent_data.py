
import sys
import os
import asyncio
import csv
import re
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit

def sanitize_rent(value_str):
    if not value_str:
        return 0.0
    
    # 1. Clean basic formatting
    clean_val = value_str.replace(" ", "").replace("\xa0", "").replace(",", ".").replace("kr", "").strip()
    
    # Check if empty
    if not clean_val:
        return 0.0
        
    try:
        val = float(clean_val)
    except ValueError:
        return 0.0
        
    # 2. Heuristic for Year Concatenation (e.g., 40258422023 -> 4025842)
    # Most rents are likely under 50M.
    
    # Check for scientific notation or huge numbers from Excel exports
    if val > 100_000_000:
        val_str = "{:.0f}".format(val) # Convert to string without scientific notation
        
        # Check for year suffixes (2020-2030)
        found_suffix = False
        for year in range(2020, 2035):
            year_str = str(year)
            if val_str.endswith(year_str):
                # Attempt to split
                potential_rent_str = val_str[:-4]
                if potential_rent_str:
                    try:
                        p_val = float(potential_rent_str)
                        if p_val < 100_000_000:
                            return p_val
                    except:
                        pass
        
        # If still insane, reject it
        if val > 100_000_000:
            return 0.0 # Reject insane values
                    
    return val

async def fix_rent_data():
    file_path = "docs/total.txt"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print("Starting Rent Data Fix (Phase 2 - Safety)...")

    async with SessionLocal() as db:
        # Pre-fetch all active contracts
        stmt = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        # Map Property Name -> Contract(s)
        file_map = {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rent_key = None
            for key in reader.fieldnames:
                if "Kontraktsleie ved oppstart" in key:
                    rent_key = key
                    break
            
            if not rent_key:
                print("Column not found!")
                return
                
            for row in reader:
                name = row.get("Avtalenavn", "").strip()
                if not name:
                    continue
                raw_rent = row.get(rent_key, "0")
                cleaned_rent = sanitize_rent(raw_rent)
                file_map[name.lower()] = cleaned_rent

        updates_count = 0
        reverts_count = 0
        
        for contract in contracts:
            if not contract.unit or not contract.unit.property:
                continue
                
            p_name = contract.unit.property.name.strip()
            p_name_lower = p_name.lower()
            
            # 1. Check for CURRENT Insane Value (Self-Healing)
            current_amount_data = contract.amount if isinstance(contract.amount, dict) else {}
            current_rent = current_amount_data.get('amount_per_year', 0.0)
            try: 
                current_rent = float(current_rent) 
            except: 
                current_rent = 0.0
                
            if current_rent > 100_000_000:
                print(f"Detected INSANE DB Value for '{p_name}': {current_rent}. Resetting.")
                # Try to get from file
                new_file_rent = file_map.get(p_name_lower, 0.0)
                if new_file_rent > 0 and new_file_rent < 100_000_000:
                     print(f"  -> Recovered from file: {new_file_rent}")
                     val_to_set = new_file_rent
                else:
                     print(f"  -> No valid file value found. Setting to 0.")
                     val_to_set = 0.0
                
                new_amount_dict = contract.amount.copy() if contract.amount else {}
                new_amount_dict['amount_per_year'] = val_to_set
                contract.amount = new_amount_dict
                reverts_count += 1
                continue # Done with this one

            # 2. Standard Update logic
            new_rent = file_map.get(p_name_lower)
            
            if new_rent is not None and new_rent > 0:
                # Update if different AND SANITY CHECKED
                if abs(current_rent - new_rent) > 1.0:
                    if new_rent < 100_000_000:
                        print(f"Updating '{p_name}': {current_rent} -> {new_rent}")
                        new_amount_dict = contract.amount.copy() if contract.amount else {}
                        new_amount_dict['amount_per_year'] = new_rent
                        contract.amount = new_amount_dict
                        updates_count += 1
                    else:
                        print(f"Skipping insane update for '{p_name}': {new_rent}")

        await db.commit()
        print(f"Updated {updates_count} contracts. Reverted {reverts_count} insane values.")

if __name__ == "__main__":
    asyncio.run(fix_rent_data())
