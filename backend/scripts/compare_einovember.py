#!/usr/bin/env python3
"""
Compare Einovember.xls with database data to find discrepancies
"""

import sys
import os
import asyncio
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import joinedload

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit

def clean_name(name):
    """Normalize property name for comparison."""
    if pd.isna(name):
        return ""
    return str(name).strip().lower()

async def compare_with_database():
    print("=" * 80)
    print("COMPARING EINOVEMBER.XLS WITH DATABASE")
    print("=" * 80)
    
    # Read Excel file
    file_path = '/Users/frank/BEFS3/KNOWME/docs/Einovember.xls'
    df = pd.read_excel(file_path, sheet_name=0)
    
    print(f"\n📊 Excel file: {len(df)} contracts")
    
    # Get database data
    async with SessionLocal() as db:
        # Get all properties
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        # Get all contracts with property info
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        print(f"📊 Database: {len(properties)} properties, {len(contracts)} active contracts")
        
        # Create lookup maps
        db_properties_by_name = {}
        for prop in properties:
            clean = clean_name(prop.name)
            db_properties_by_name[clean] = prop
        
        # Excel data
        excel_data = {}
        for _, row in df.iterrows():
            name = clean_name(row['Avtalenavn'])
            if name:
                excel_data[name] = row
        
        # Compare
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        # 1. Properties in Excel but not in DB
        missing_in_db = []
        for name in excel_data.keys():
            if name not in db_properties_by_name:
                missing_in_db.append(name)
        
        print(f"\n1. PROPERTIES IN EXCEL BUT NOT IN DATABASE: {len(missing_in_db)}")
        if missing_in_db:
            print("\n   Top 10:")
            for name in sorted(missing_in_db)[:10]:
                row = excel_data[name]
                region = row.get('Lok: Distrikt', 'Unknown')
                print(f"     - {name[:60]} (Region: {region})")
        
        # 2. Properties in DB but not in Excel
        missing_in_excel = []
        for name in db_properties_by_name.keys():
            if name and name not in excel_data:
                missing_in_excel.append(name)
        
        print(f"\n2. PROPERTIES IN DATABASE BUT NOT IN EXCEL: {len(missing_in_excel)}")
        if missing_in_excel:
            print("\n   Top 10:")
            for name in sorted(missing_in_excel)[:10]:
                prop = db_properties_by_name[name]
                print(f"     - {name[:60]} (Region: {prop.region})")
        
        # 3. Compare regions for matching properties
        region_mismatches = []
        for name in excel_data.keys():
            if name in db_properties_by_name:
                excel_region = excel_data[name].get('Lok: Distrikt', 'Unknown')
                db_region = str(db_properties_by_name[name].region or 'Unknown')
                
                # Normalize for comparison
                excel_reg_clean = str(excel_region).strip()
                db_reg_clean = db_region.strip()
                
                if excel_reg_clean and db_reg_clean and excel_reg_clean.lower() != db_reg_clean.lower():
                    if db_reg_clean.lower() != 'unknown':  # Skip Unknown in DB
                        region_mismatches.append({
                            'name': name,
                            'excel_region': excel_reg_clean,
                            'db_region': db_reg_clean
                        })
        
        print(f"\n3. REGION MISMATCHES (matching properties): {len(region_mismatches)}")
        if region_mismatches:
            print("\n   Top 10:")
            for mismatch in region_mismatches[:10]:
                print(f"     - {mismatch['name'][:50]}")
                print(f"       Excel: {mismatch['excel_region']}")
                print(f"       DB: {mismatch['db_region']}")
        
        # 4. Properties with "Unknown" region in DB that have region in Excel
        can_update_region = []
        for name in excel_data.keys():
            if name in db_properties_by_name:
                excel_region = excel_data[name].get('Lok: Distrikt', 'Unknown')
                db_region = str(db_properties_by_name[name].region or 'Unknown')
                
                if db_region.lower() == 'unknown' and str(excel_region).strip() and str(excel_region).lower() != 'unknown':
                    can_update_region.append({
                        'name': name,
                        'excel_region': str(excel_region).strip(),
                        'property_id': db_properties_by_name[name].property_id
                    })
        
        print(f"\n4. PROPERTIES WITH UNKNOWN REGION IN DB (can update from Excel): {len(can_update_region)}")
        if can_update_region:
            print("\n   Top 10:")
            for item in can_update_region[:10]:
                print(f"     - {item['name'][:60]}")
                print(f"       Can set region to: {item['excel_region']}")
        
        # 5. Compare rent data for contracts
        rent_comparison = []
        for contract in contracts:
            if not contract.unit or not contract.unit.property:
                continue
            
            prop_name = clean_name(contract.unit.property.name)
            if prop_name in excel_data:
                excel_rent = excel_data[prop_name].get('Kontraktsleie ved oppstart (per år)', 0)
                try:
                    excel_rent = float(excel_rent) if not pd.isna(excel_rent) else 0
                except:
                    excel_rent = 0
                
                db_rent = contract.amount.get('amount_per_year', 0) if contract.amount else 0
                try:
                    db_rent = float(db_rent)
                except:
                    db_rent = 0
                
                diff = abs(db_rent - excel_rent)
                if diff > 1000:  # More than 1000 NOK difference
                    rent_comparison.append({
                        'name': prop_name,
                        'excel_rent': excel_rent,
                        'db_rent': db_rent,
                        'diff': diff
                    })
        
        print(f"\n5. RENT MISMATCHES (>1000 NOK difference): {len(rent_comparison)}")
        if rent_comparison:
            print("\n   Top 10 largest differences:")
            sorted_rent = sorted(rent_comparison, key=lambda x: -x['diff'])
            for item in sorted_rent[:10]:
                print(f"     - {item['name'][:50]}")
                print(f"       Excel: {item['excel_rent']:>12,.0f} NOK")
                print(f"       DB:    {item['db_rent']:>12,.0f} NOK")
                print(f"       Diff:  {item['diff']:>12,.0f} NOK")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Excel contracts: {len(excel_data)}")
        print(f"DB properties: {len(db_properties_by_name)}")
        print(f"Missing in DB: {len(missing_in_db)}")
        print(f"Missing in Excel: {len(missing_in_excel)}")
        print(f"Region mismatches: {len(region_mismatches)}")
        print(f"Can update region from Excel: {len(can_update_region)}")
        print(f"Rent mismatches: {len(rent_comparison)}")
        
        # Store results for potential fix script
        return {
            'missing_in_db': missing_in_db,
            'missing_in_excel': missing_in_excel,
            'region_mismatches': region_mismatches,
            'can_update_region': can_update_region,
            'rent_comparison': rent_comparison
        }

if __name__ == "__main__":
    asyncio.run(compare_with_database())
