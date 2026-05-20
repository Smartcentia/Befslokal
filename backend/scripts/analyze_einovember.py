#!/usr/bin/env python3
"""
Script to analyze Einovember.xls and compare with database data
"""

import sys
import os
import asyncio
import pandas as pd
from sqlalchemy import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit

async def analyze_einovember():
    print("=" * 80)
    print("ANALYZING EINOVEMBER.XLS")
    print("=" * 80)
    
    # Read the Excel file - file is in main docs folder, not backend
    file_path = '/Users/frank/BEFS3/KNOWME/docs/Einovember.xls'
    
    print(f"\n📁 Reading file: {file_path}")
    
    try:
        # Read all sheets to see what's available
        xls = pd.ExcelFile(file_path)
        print(f"\n📊 Found {len(xls.sheet_names)} sheet(s):")
        for i, sheet_name in enumerate(xls.sheet_names, 1):
            print(f"   {i}. {sheet_name}")
        
        # Read first sheet
        df = pd.read_excel(file_path, sheet_name=0)
        
        print(f"\n📋 Sheet structure:")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {len(df.columns)}")
        print(f"\n   Column names:")
        for col in df.columns:
            print(f"     - {col}")
        
        print(f"\n📝 First 5 rows preview:")
        print(df.head().to_string())
        
        # Analyze what type of data this is
        print(f"\n🔍 Data Analysis:")
        
        # Check for common column names
        col_names_lower = [str(c).lower() for c in df.columns]
        
        data_type = "Unknown"
        if any('eiendom' in c or 'property' in c for c in col_names_lower):
            data_type = "Property/Real Estate Data"
        if any('husleie' in c or 'leie' in c or 'rent' in c for c in col_names_lower):
            data_type = "Rent/Lease Data"
        if any('kostnad' in c or 'cost' in c or 'expense' in c for c in col_names_lower):
            data_type = "Cost/Expense Data"
        if any('region' in c for c in col_names_lower):
            data_type = "Regional Data"
        
        print(f"   Likely data type: {data_type}")
        
        # Count non-null values per column
        print(f"\n   Data completeness:")
        for col in df.columns:
            non_null = df[col].notna().sum()
            pct = (non_null / len(df)) * 100
            print(f"     {col}: {non_null}/{len(df)} ({pct:.1f}%)")
        
        # Now compare with database
        print(f"\n" + "=" * 80)
        print("COMPARING WITH DATABASE")
        print("=" * 80)
        
        async with SessionLocal() as db:
            # Get properties count
            result = await db.execute(select(Property))
            properties = result.scalars().all()
            print(f"\nDatabase has {len(properties)} properties")
            print(f"Excel has {len(df)} rows")
            
            # Try to identify matching column for property name
            name_col = None
            for col in df.columns:
                col_lower = str(col).lower()
                if 'navn' in col_lower or 'name' in col_lower or 'eiendom' in col_lower or 'avtalenavn' in col_lower:
                    name_col = col
                    break
            
            if name_col:
                print(f"\nUsing '{name_col}' as property name column")
                print(f"\nSample names from Excel:")
                for name in df[name_col].head(10):
                    print(f"  - {name}")
        
        print(f"\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
        return df, xls.sheet_names
        
    except Exception as e:
        print(f"\n❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    asyncio.run(analyze_einovember())
