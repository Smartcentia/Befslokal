#!/usr/bin/env python3
"""
Export complete financial data table for all properties
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

async def export_complete_table():
    print("=" * 80)
    print("EXPORTING COMPLETE FINANCIAL DATA TABLE")
    print("=" * 80)
    
    async with SessionLocal() as db:
        # Get all properties
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        # Get all active contracts
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        print(f"\n📊 Processing {len(properties)} properties...")
        
        # Build property -> contract mapping
        property_contracts = {}
        for contract in contracts:
            if contract.unit and contract.unit.property:
                prop_id = contract.unit.property.property_id
                if prop_id not in property_contracts:
                    property_contracts[prop_id] = []
                property_contracts[prop_id].append(contract)
        
        # Build data for export
        data = []
        
        for prop in properties:
            prop_id = prop.property_id
            
            # Get rent data
            total_rent = 0
            num_contracts = 0
            if prop_id in property_contracts:
                num_contracts = len(property_contracts[prop_id])
                for contract in property_contracts[prop_id]:
                    amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                    rent = amount_data.get('amount_per_year', 0)
                    try:
                        rent = float(rent) if rent else 0
                    except:
                        rent = 0
                    total_rent += rent
            
            # Get cost data
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            total_costs = 0
            num_expenses = len(expenses)
            for exp in expenses:
                try:
                    amount = float(exp.get('amount', 0) or 0)
                    total_costs += amount
                except:
                    pass
            
            # Determine status
            has_rent = total_rent > 0
            has_costs = num_expenses > 0
            
            if has_rent and has_costs:
                status = "Komplett"
                priority = 1
            elif has_rent and not has_costs:
                status = "Mangler kostnader"
                priority = 2
            elif not has_rent and has_costs:
                status = "Mangler husleie"
                priority = 3
            else:
                status = "Mangler alt"
                priority = 4
            
            # Add to data
            data.append({
                'Eiendom': prop.name,
                'Region': prop.region or 'Unknown',
                'Adresse': prop.address or '',
                'Årlig Husleie (kr)': round(total_rent, 2),
                'Årlige Kostnader (kr)': round(total_costs, 2),
                'Antall Kontrakter': num_contracts,
                'Antall Kostnadstransaksjoner': num_expenses,
                'Status': status,
                'Priority': priority,
                'Property ID': str(prop_id)
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Sort by priority (worst first), then by rent amount
        df = df.sort_values(['Priority', 'Årlig Husleie (kr)'], ascending=[False, False])
        
        # Export to Excel
        excel_path = '/Users/frank/BEFS3/KNOWME/docs/Fullstendig_Finansiell_Oversikt.xlsx'
        print(f"\n📝 Exporting to Excel...")
        df.to_excel(excel_path, index=False, sheet_name='Finansiell Oversikt')
        
        # Export to CSV
        csv_path = '/Users/frank/BEFS3/KNOWME/docs/Fullstendig_Finansiell_Oversikt.csv'
        print(f"📝 Exporting to CSV...")
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ Export complete!")
        print(f"\n   Excel file: {excel_path}")
        print(f"   CSV file: {csv_path}")
        
        # Print summary statistics
        print(f"\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        status_counts = df['Status'].value_counts()
        print(f"\nStatus breakdown:")
        for status, count in status_counts.items():
            pct = (count / len(df)) * 100
            print(f"   {status}: {count} ({pct:.1f}%)")
        
        # Regional breakdown
        print(f"\nRegional breakdown:")
        for region in sorted(df['Region'].unique()):
            region_df = df[df['Region'] == region]
            total = len(region_df)
            komplett = len(region_df[region_df['Status'] == 'Komplett'])
            pct = (komplett / total * 100) if total > 0 else 0
            print(f"   {region}: {komplett}/{total} komplett ({pct:.1f}%)")
        
        # Financial totals
        print(f"\nFinansielle totaler:")
        total_rent = df['Årlig Husleie (kr)'].sum()
        total_costs = df['Årlige Kostnader (kr)'].sum()
        print(f"   Total årlig husleie: {total_rent:,.0f} kr")
        print(f"   Total årlige kostnader: {total_costs:,.0f} kr")
        print(f"   Total: {total_rent + total_costs:,.0f} kr")
        
        # Missing data impact
        missing_costs = df[df['Status'].isin(['Mangler kostnader', 'Mangler alt'])]
        missing_rent = df[df['Status'].isin(['Mangler husleie', 'Mangler alt'])]
        
        print(f"\nManglende data:")
        print(f"   Husleie uten kostnader: {missing_costs['Årlig Husleie (kr)'].sum():,.0f} kr")
        print(f"   Kostnader uten husleie: {missing_rent['Årlige Kostnader (kr)'].sum():,.0f} kr")

if __name__ == "__main__":
    asyncio.run(export_complete_table())
