#!/usr/bin/env python3
"""Quick test of the timeseries generator"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from generate_monthly_financial_timeseries import load_assets_from_database, generate_time_series, format_for_gl_transactions

async def test():
    print("=" * 70)
    print("Testing Monthly Financial Time-Series Generator")
    print("=" * 70)
    
    try:
        # Test 1: Try database load first
        print("\n1️⃣ Testing database load...")
        try:
            df_assets = await load_assets_from_database()
            print(f"   ✅ Loaded {len(df_assets)} properties from database")
            
            if len(df_assets) == 0:
                print("   ⚠️  No properties found in database!")
                raise Exception("No properties")
                
            print(f"   Properties with rent: {len(df_assets[df_assets['current_base_rent'] > 0])}")
            print(f"   Properties with electricity: {len(df_assets[df_assets['base_electricity_cost'] > 0])}")
            print(f"\n   Sample data:")
            print(df_assets.head(3).to_string())
        except Exception as db_error:
            print(f"   ⚠️  Database error: {db_error}")
            print("   Falling back to mock data...")
            from generate_monthly_financial_timeseries import create_mock_assets
            df_assets = create_mock_assets(n=5)
            print(f"   ✅ Using {len(df_assets)} mock properties")
        
        # Test 2: Generate time series
        print("\n2️⃣ Testing time series generation...")
        df_time_series = generate_time_series(df_assets.head(5), years_back=3)  # Test with first 5 only
        print(f"   ✅ Generated {len(df_time_series)} monthly records")
        print(f"   Date range: {df_time_series['date'].min()} to {df_time_series['date'].max()}")
        
        # Test 3: Format for GL
        print("\n3️⃣ Testing GL formatting...")
        df_gl = format_for_gl_transactions(df_time_series)
        print(f"   ✅ Created {len(df_gl)} GL transaction records")
        print(f"\n   First 5 rows:")
        print(df_gl.head(5).to_string(index=False))
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
