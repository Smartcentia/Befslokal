#!/usr/bin/env python3
"""
Generate monthly financial time-series for ALL properties in database.

This script:
1. Connects to database
2. Loads all properties with their rent and electricity costs
3. Generates 3 years of monthly financial data
4. Exports to CSV files
"""

import asyncio
import sys
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env BEFORE importing app modules
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

# Ensure DATABASE_URL is set in environment for pydantic_settings
if not os.environ.get('DATABASE_URL'):
    raise ValueError("DATABASE_URL is not set in .env file!")

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models to ensure relationships are resolved
import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Import other models
import app.domains.core.models.user
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control

# Import time series functions
from generate_monthly_financial_timeseries import (
    generate_time_series,
    format_for_gl_transactions
)
import numpy as np
from app.models.financial_models import GLTransaction
from uuid import UUID as UUIDType


async def load_all_properties_from_database() -> pd.DataFrame:
    """
    Load all properties from database with their current rent and electricity costs.
    
    Returns:
        DataFrame with columns: id, sqm, current_base_rent, base_electricity_cost
    """
    print("=" * 70)
    print("📊 Loading properties from database...")
    print("=" * 70)
    
    try:
        async with SessionLocal() as db:
            # Get all properties
            stmt_prop = select(Property)
            result_prop = await db.execute(stmt_prop)
            properties = result_prop.scalars().all()
            
            print(f"\n✅ Found {len(properties)} properties in database")
            
            if len(properties) == 0:
                print("⚠️  No properties found in database!")
                return pd.DataFrame(columns=['id', 'sqm', 'current_base_rent', 'base_electricity_cost'])
            
            # Get all active contracts with units and properties
            print("📋 Loading active contracts...")
            stmt_contract = (
                select(Contract)
                .where(Contract.status == 'active')
                .options(
                    joinedload(Contract.unit).joinedload(Unit.property)
                )
            )
            result_contract = await db.execute(stmt_contract)
            contracts = result_contract.scalars().all()
            
            print(f"✅ Found {len(contracts)} active contracts")
            
            # Build property -> contracts mapping
            property_contracts = {}
            for contract in contracts:
                if contract.unit and contract.unit.property:
                    prop_id = contract.unit.property.property_id
                    if prop_id not in property_contracts:
                        property_contracts[prop_id] = []
                    property_contracts[prop_id].append(contract)
            
            # Build assets DataFrame
            print("\n📊 Processing property data...")
            assets_data = []
            properties_with_rent = 0
            properties_with_electricity = 0
            
            for prop in properties:
                prop_id = str(prop.property_id)
                
                # Get total area (sqm)
                sqm = prop.total_area if prop.total_area else 0
                
                # Get current rent from active contracts
                current_base_rent = 0.0
                if prop.property_id in property_contracts:
                    for contract in property_contracts[prop.property_id]:
                        if contract.amount and isinstance(contract.amount, dict):
                            rent = contract.amount.get('amount_per_year', 0)
                            try:
                                current_base_rent += float(rent) if rent else 0
                            except (ValueError, TypeError):
                                pass
                
                if current_base_rent > 0:
                    properties_with_rent += 1
                
                # Get electricity cost from external_data
                base_electricity_cost = 0.0
                if prop.external_data and isinstance(prop.external_data, dict):
                    financials = prop.external_data.get('financials', {})
                    expenses = financials.get('manual_expenses', [])
                    
                    # Look for electricity/energy expenses
                    for exp in expenses:
                        exp_type = str(exp.get('type', '')).lower()
                        if 'strøm' in exp_type or 'elektri' in exp_type or 'energi' in exp_type:
                            amount = exp.get('amount', 0) or exp.get('amount_parsed', 0)
                            try:
                                base_electricity_cost += float(amount) if amount else 0
                            except (ValueError, TypeError):
                                pass
                    
                    # Fallback: check for energy_cost field
                    if base_electricity_cost == 0:
                        energy_cost = financials.get('energy_cost', 0) or financials.get('energi_kost', 0)
                        try:
                            base_electricity_cost = float(energy_cost) if energy_cost else 0
                        except (ValueError, TypeError):
                            pass
                
                if base_electricity_cost > 0:
                    properties_with_electricity += 1
                
                # Estimate electricity if missing (based on area)
                if base_electricity_cost == 0 and sqm > 0:
                    # Rough estimate: ~50-100 NOK per m² per år
                    base_electricity_cost = sqm * np.random.uniform(50, 100)
                
                # Include all properties (even if they have 0 rent/area)
                assets_data.append({
                    'id': prop_id,
                    'sqm': sqm,
                    'current_base_rent': current_base_rent,
                    'base_electricity_cost': base_electricity_cost,
                    'address': prop.address or prop.name or 'Unknown',
                    'city': prop.city or 'Unknown'
                })
            
            df_assets = pd.DataFrame(assets_data)
            
            print(f"\n📊 Summary:")
            print(f"   Total properties: {len(df_assets)}")
            print(f"   Properties with rent: {properties_with_rent}")
            print(f"   Properties with electricity cost: {properties_with_electricity}")
            print(f"   Properties with area data: {len(df_assets[df_assets['sqm'] > 0])}")
            
            return df_assets
            
    except Exception as e:
        print(f"\n❌ Error loading from database: {e}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main execution function."""
    print("=" * 70)
    print("Monthly Financial Time-Series Generator for ALL Properties")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Step 1: Load all properties from database
        df_assets = await load_all_properties_from_database()
        
        if len(df_assets) == 0:
            print("\n⚠️  No properties found. Exiting.")
            return
        
        # Step 2: Generate time series
        print("\n" + "=" * 70)
        print("2️⃣ Generating monthly time-series data (3 years)...")
        print("=" * 70)
        
        df_time_series = generate_time_series(df_assets, years_back=3)
        
        print(f"\n✅ Generated {len(df_time_series):,} monthly records")
        print(f"   Date range: {df_time_series['date'].min().strftime('%Y-%m-%d')} to {df_time_series['date'].max().strftime('%Y-%m-%d')}")
        print(f"   Records per property: {len(df_time_series) // len(df_assets)} months")
        
        # Step 3: Format for GL transactions
        print("\n" + "=" * 70)
        print("3️⃣ Formatting for General Ledger transactions...")
        print("=" * 70)
        
        df_gl = format_for_gl_transactions(df_time_series)
        
        print(f"\n✅ Created {len(df_gl):,} GL transaction records")
        print(f"   (4 transactions per property per month: Rent, Electricity, Parking, Cleaning)")
        
        # Step 3b: Save to database
        print("\n" + "=" * 70)
        print("3️⃣b Saving GL transactions to database...")
        print("=" * 70)
        
        # Always save to database
        print(f"   Preparing to insert {len(df_gl):,} transactions...")
        
        try:
            async with SessionLocal() as db:
                print(f"   Inserting {len(df_gl):,} transactions...")
                
                # Map account codes to categories
                account_to_category = {
                    '3000': 'Rent',
                    '6000': 'Electricity',
                    '6100': 'Parking',
                    '6200': 'Cleaning'
                }
                
                batch_size = 1000
                inserted_count = 0
                error_count = 0
                total_batches = (len(df_gl) + batch_size - 1) // batch_size
                
                print(f"   Processing {len(df_gl):,} transactions in {total_batches} batches of {batch_size}...")
                print(f"   Starting insertion...")
                
                for i in range(0, len(df_gl), batch_size):
                    batch = df_gl.iloc[i:i+batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    gl_objects = []
                    for idx, row in batch.iterrows():
                        try:
                            # Parse property_id
                            property_id = UUIDType(row['AssetID'])
                            
                            # Parse transaction date and convert to Python datetime
                            trans_date = pd.to_datetime(row['TransactionDate'])
                            if pd.isna(trans_date):
                                error_count += 1
                                continue
                            # Convert pandas Timestamp to Python datetime (asyncpg requires this)
                            trans_date = trans_date.to_pydatetime()
                            
                            # Get category from account code
                            account_code = str(row['AccountCode'])
                            category = account_to_category.get(account_code, 'Other')
                            
                            # Validate amount
                            amount = float(row['Amount'])
                            if pd.isna(amount):
                                error_count += 1
                                continue
                            
                            gl_obj = GLTransaction(
                                property_id=property_id,
                                transaction_date=trans_date,
                                year=int(trans_date.year),
                                month=int(trans_date.month),
                                amount=amount,
                                category=category,
                                description=str(row['Description'])[:500] if pd.notna(row['Description']) else None,
                                account_code=account_code,
                                source_system='synthetic_timeseries'
                            )
                            gl_objects.append(gl_obj)
                        except Exception as e:
                            error_count += 1
                            if error_count <= 5:  # Only show first 5 errors
                                print(f"   ⚠️  Error processing row {idx}: {e}")
                            continue
                    
                    if gl_objects:
                        try:
                            db.add_all(gl_objects)
                            await db.flush()  # Flush to catch errors early
                            
                            # Commit immediately after flush
                            await db.commit()
                            
                            # Only increment count after successful commit
                            inserted_count += len(gl_objects)
                            
                            # Show progress more frequently
                            if batch_num % 5 == 0 or batch_num == total_batches:
                                print(f"   ✅ Batch {batch_num}/{total_batches}: {inserted_count:,} transactions inserted...")
                        except Exception as e:
                            print(f"   ❌ Error in batch {batch_num}: {e}")
                            await db.rollback()
                            error_count += len(gl_objects)
                            # Continue to next batch
                            if batch_num <= 3:  # Show first few errors in detail
                                import traceback
                                traceback.print_exc()
                            continue
                    else:
                        # No objects in this batch (all failed validation)
                        if batch_num <= 3:
                            print(f"   ⚠️  Batch {batch_num}: No valid transactions (all failed validation)")
                
                print(f"\n✅ Successfully inserted {inserted_count:,} GL transactions to database")
                if error_count > 0:
                    print(f"⚠️  Skipped {error_count:,} transactions due to errors")
                    
        except Exception as e:
            print(f"\n❌ Error saving to database: {e}")
            print("   CSV files are still available for manual import")
            import traceback
            print("\n" + "=" * 70)
            print("Full Error Traceback:")
            print("=" * 70)
            traceback.print_exc()
            print("=" * 70)
        
        # Step 4: Summary statistics
        print("\n" + "=" * 70)
        print("4️⃣ Summary Statistics")
        print("=" * 70)
        
        total_income = df_gl[df_gl['Amount'] > 0]['Amount'].sum()
        total_expenses = abs(df_gl[df_gl['Amount'] < 0]['Amount'].sum())
        net = df_gl['Amount'].sum()
        
        print(f"\n💰 Financial Summary:")
        print(f"   Total Income (Rent): {total_income:,.2f} NOK")
        print(f"   Total Expenses: {total_expenses:,.2f} NOK")
        print(f"   Net: {net:,.2f} NOK")
        
        print(f"\n📊 By Account Code:")
        for code in sorted(df_gl['AccountCode'].unique()):
            code_total = df_gl[df_gl['AccountCode'] == code]['Amount'].sum()
            code_name = {
                '3000': 'Rent (Income)',
                '6000': 'Electricity (Expense)',
                '6100': 'Parking (Expense)',
                '6200': 'Cleaning (Expense)'
            }.get(code, 'Unknown')
            print(f"   {code} - {code_name}: {code_total:,.2f} NOK")
        
        # Step 5: Export to CSV
        print("\n" + "=" * 70)
        print("5️⃣ Exporting to CSV files...")
        print("=" * 70)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent.parent / 'data' / 'timeseries'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export files
        gl_file = output_dir / f'gl_transactions_{timestamp}.csv'
        monthly_file = output_dir / f'monthly_financials_{timestamp}.csv'
        assets_file = output_dir / f'properties_summary_{timestamp}.csv'
        
        df_gl.to_csv(gl_file, index=False)
        df_time_series.to_csv(monthly_file, index=False)
        df_assets.to_csv(assets_file, index=False)
        
        print(f"\n✅ Files exported:")
        print(f"   📄 GL Transactions: {gl_file}")
        print(f"   📄 Monthly Financials: {monthly_file}")
        print(f"   📄 Properties Summary: {assets_file}")
        
        # Step 6: Show sample data
        print("\n" + "=" * 70)
        print("6️⃣ Sample Data (First 5 GL transactions)")
        print("=" * 70)
        print(df_gl.head(5).to_string(index=False))
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! All done.")
        print("=" * 70)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return df_time_series, df_gl
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        df_time_series, df_gl = asyncio.run(main())
        print("\n✅ Script completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        sys.exit(1)
