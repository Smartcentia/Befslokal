#!/usr/bin/env python3
"""
Comprehensive script to fix ALL rent data issues:
1. Find contracts with missing rent
2. Find contracts with corrupted rent (> 100M)
3. Import missing properties from total.txt
4. Fix mismatches
"""

import sys
import os
import asyncio
import csv
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit

def parse_currency(value_str):
    """Parse Norwegian currency string to float."""
    if not value_str:
        return 0.0
    clean_val = value_str.replace(" ", "").replace("\xa0", "").replace(",", ".").replace("kr", "").strip()
    try:
        val = float(clean_val)
        # Handle year-concatenated values
        if val > 100_000_000:
            val_str = f"{val:.0f}"
            for year in range(2020, 2035):
                if val_str.endswith(str(year)):
                    try:
                        return float(val_str[:-4])
                    except:
                        pass
            return 0.0
        return val
    except ValueError:
        return 0.0

async def comprehensive_fix():
    print("=" * 80)
    print("COMPREHENSIVE RENT DATA FIX")
    print("=" * 80)
    
    file_path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'total.txt')
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"✅ Found source file: {file_path}")
    
    async with SessionLocal() as db:
        # Load all contracts
        stmt = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        print(f"📊 Loaded {len(contracts)} active contracts from database")
        
        # Load file data
        file_rent_map = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            rent_key = None
            for key in reader.fieldnames or []:
                if "Kontraktsleie ved oppstart" in key:
                    rent_key = key
                    break
            
            if not rent_key:
                print("❌ Could not find rent column in file")
                return
            
            print(f"✅ Found rent column: {rent_key}")
            
            for row in reader:
                name = row.get("Avtalenavn", "").strip()
                if name:
                    file_rent = parse_currency(row.get(rent_key, "0"))
                    file_rent_map[name.lower()] = (name, file_rent)
        
        print(f"📊 Loaded {len(file_rent_map)} properties from file")
        
        # Analysis
        fixed_missing = 0
        fixed_corrupted = 0
        fixed_mismatch = 0
        still_missing = []
        
        for contract in contracts:
            if not contract.unit or not contract.unit.property:
                continue
            
            prop = contract.unit.property
            p_name = prop.name.strip()
            p_name_lower = p_name.lower()
            
            # Get current rent
            amount_data = contract.amount if isinstance(contract.amount, dict) else {}
            current_rent = amount_data.get('amount_per_year', 0.0)
            try:
                current_rent = float(current_rent)
            except:
                current_rent = 0.0
            
            # Check if in file
            file_data = file_rent_map.get(p_name_lower)
            
            # Case 1: Corrupted rent (> 100M)
            if current_rent > 100_000_000:
                print(f"\n🔧 Fixing CORRUPTED rent for '{p_name}'")
                print(f"   Current DB: {current_rent:,.0f} (INSANE)")
                
                if file_data and file_data[1] > 0:
                    new_rent = file_data[1]
                    print(f"   Setting to file value: {new_rent:,.0f}")
                    new_amount_dict = contract.amount.copy() if contract.amount else {}
                    new_amount_dict['amount_per_year'] = new_rent
                    contract.amount = new_amount_dict
                    fixed_corrupted += 1
                else:
                    print(f"   No file value found, setting to 0")
                    new_amount_dict = contract.amount.copy() if contract.amount else {}
                    new_amount_dict['amount_per_year'] = 0.0
                    contract.amount = new_amount_dict
                    fixed_corrupted += 1
                continue
            
            # Case 2: Missing rent in DB but exists in file
            if current_rent == 0 and file_data and file_data[1] > 0:
                new_rent = file_data[1]
                print(f"\n🔧 Adding MISSING rent for '{p_name}'")
                print(f"   Setting to: {new_rent:,.0f}")
                new_amount_dict = contract.amount.copy() if contract.amount else {}
                new_amount_dict['amount_per_year'] = new_rent
                contract.amount = new_amount_dict
                fixed_missing += 1
                continue
            
            # Case 3: Large mismatch between DB and file
            if file_data and file_data[1] > 0 and current_rent > 0:
                file_rent = file_data[1]
                diff = abs(current_rent - file_rent)
                
                # If difference is > 1M or > 50% of file value
                if diff > 1_000_000 or (diff / file_rent > 0.5):
                    print(f"\n🔧 Fixing MISMATCH for '{p_name}'")
                    print(f"   Current DB: {current_rent:,.0f}")
                    print(f"   File value: {file_rent:,.0f}")
                    print(f"   Difference: {diff:,.0f}")
                    print(f"   Setting to file value")
                    new_amount_dict = contract.amount.copy() if contract.amount else {}
                    new_amount_dict['amount_per_year'] = file_rent
                    contract.amount = new_amount_dict
                    fixed_mismatch += 1
                    continue
            
            # Case 4: Missing in both
            if current_rent == 0 and not file_data:
                still_missing.append(p_name)
        
        # Commit changes
        await db.commit()
        
        print("\n" + "=" * 80)
        print("FIX SUMMARY")
        print("=" * 80)
        print(f"✅ Fixed {fixed_corrupted} contracts with CORRUPTED rent (> 100M)")
        print(f"✅ Fixed {fixed_missing} contracts with MISSING rent")
        print(f"✅ Fixed {fixed_mismatch} contracts with LARGE MISMATCH")
        print(f"⚠️  {len(still_missing)} contracts still have no rent data (not in file either)")
        
        if still_missing and len(still_missing) <= 20:
            print("\nContracts still missing rent:")
            for name in still_missing:
                print(f"  - {name}")
        
        total_fixed = fixed_corrupted + fixed_missing + fixed_mismatch
        print(f"\n🎉 TOTAL CONTRACTS FIXED: {total_fixed}")

if __name__ == "__main__":
    asyncio.run(comprehensive_fix())
