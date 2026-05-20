#!/usr/bin/env python3
"""
Check which properties have synthetic monthly financial data.

This script verifies that all properties have generated time-series data
and reports which ones are missing data.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

# Load .env BEFORE importing app modules
load_dotenv(Path(__file__).parent.parent / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models to ensure relationships are resolved
import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

# Import other models
import app.domains.core.models.user
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control


async def check_synthetic_data_coverage():
    """
    Check which properties have synthetic financial time-series data.
    
    Checks for:
    1. financial_history in external_data (from generate_historical_financials.py)
    2. Monthly time-series data in external_data
    3. GL transactions in gl_transactions table
    """
    print("=" * 70)
    print("Checking Synthetic Data Coverage for All Properties")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with SessionLocal() as db:
        # Get all properties
        print("📊 Loading all properties from database...")
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        print(f"✅ Found {len(properties)} properties\n")
        
        if len(properties) == 0:
            print("⚠️  No properties found in database!")
            return
        
        # Check each property
        print("🔍 Checking synthetic data for each property...\n")
        
        stats = {
            'total': len(properties),
            'with_financial_history': 0,
            'with_monthly_timeseries': 0,
            'with_gl_transactions': 0,
            'with_any_data': 0,
            'missing_all_data': 0,
            'properties_missing_data': []
        }
        
        # Check GL transactions count per property
        print("📋 Checking GL transactions table...")
        gl_stmt = text("""
            SELECT property_id, COUNT(*) as transaction_count
            FROM gl_transactions
            GROUP BY property_id
        """)
        gl_result = await db.execute(gl_stmt)
        gl_counts = {str(row[0]): row[1] for row in gl_result.all()}
        print(f"   Found {len(gl_counts)} properties with GL transactions\n")
        
        # Process each property
        for prop in properties:
            prop_id = str(prop.property_id)
            has_financial_history = False
            has_monthly_timeseries = False
            has_gl_transactions = False
            
            # Check external_data for financial_history (from generate_historical_financials.py)
            if prop.external_data and isinstance(prop.external_data, dict):
                # Check for financial_history (yearly data)
                financial_history = prop.external_data.get('financial_history')
                if financial_history and isinstance(financial_history, dict):
                    has_financial_history = len(financial_history) > 0
                    if has_financial_history:
                        stats['with_financial_history'] += 1
                
                # Check for monthly_timeseries (monthly data)
                monthly_timeseries = prop.external_data.get('monthly_timeseries')
                if monthly_timeseries:
                    has_monthly_timeseries = True
                    stats['with_monthly_timeseries'] += 1
                
                # Check for timeseries_data (alternative name)
                timeseries_data = prop.external_data.get('timeseries_data')
                if timeseries_data:
                    has_monthly_timeseries = True
                    if not stats['with_monthly_timeseries']:
                        stats['with_monthly_timeseries'] += 1
            
            # Check GL transactions
            if prop_id in gl_counts:
                has_gl_transactions = gl_counts[prop_id] > 0
                if has_gl_transactions:
                    stats['with_gl_transactions'] += 1
            
            # Check if property has any synthetic data
            if has_financial_history or has_monthly_timeseries or has_gl_transactions:
                stats['with_any_data'] += 1
            else:
                stats['missing_all_data'] += 1
                stats['properties_missing_data'].append({
                    'id': prop_id,
                    'address': prop.address or prop.name or 'Unknown',
                    'city': prop.city or 'Unknown',
                    'has_rent': False,  # Will check below
                    'has_area': bool(prop.total_area and prop.total_area > 0)
                })
        
        # Check which properties missing data have contracts/rent
        print("📋 Checking contracts for properties missing data...")
        from app.domains.core.models.contract import Contract
        from app.domains.core.models.unit import Unit
        
        for prop_info in stats['properties_missing_data']:
            prop_id = prop_info['id']
            # Check if property has active contracts
            stmt_contract = (
                select(Contract)
                .join(Unit)
                .where(Unit.property_id == prop_id)
                .where(Contract.status == 'active')
            )
            result = await db.execute(stmt_contract)
            contracts = result.scalars().all()
            
            if contracts:
                prop_info['has_rent'] = True
                # Get total rent
                total_rent = 0
                for contract in contracts:
                    if contract.amount and isinstance(contract.amount, dict):
                        rent = contract.amount.get('amount_per_year', 0)
                        try:
                            total_rent += float(rent) if rent else 0
                        except:
                            pass
                prop_info['total_rent'] = total_rent
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 Coverage Summary")
        print("=" * 70)
        
        print(f"\n📦 Total properties in database: {stats['total']}")
        
        print(f"\n✅ Properties WITH synthetic data:")
        print(f"   - With financial_history (yearly): {stats['with_financial_history']} ({stats['with_financial_history']/stats['total']*100:.1f}%)")
        print(f"   - With monthly_timeseries: {stats['with_monthly_timeseries']} ({stats['with_monthly_timeseries']/stats['total']*100:.1f}%)")
        print(f"   - With GL transactions: {stats['with_gl_transactions']} ({stats['with_gl_transactions']/stats['total']*100:.1f}%)")
        print(f"   - With ANY synthetic data: {stats['with_any_data']} ({stats['with_any_data']/stats['total']*100:.1f}%)")
        
        print(f"\n❌ Properties MISSING synthetic data:")
        print(f"   - Missing all data: {stats['missing_all_data']} ({stats['missing_all_data']/stats['total']*100:.1f}%)")
        
        # Coverage percentage
        coverage_pct = (stats['with_any_data'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"\n📈 Overall Coverage: {coverage_pct:.1f}%")
        
        # Additional statistics
        if stats['with_gl_transactions'] > 0:
            total_transactions = sum(gl_counts.values())
            avg_transactions = total_transactions / stats['with_gl_transactions']
            print(f"\n💾 GL Transactions Statistics:")
            print(f"   - Total transactions: {total_transactions:,}")
            print(f"   - Average per property: {avg_transactions:.1f}")
            print(f"   - Expected (36 months × 4 types): 144 per property")
        else:
            print(f"\n⚠️  GL Transactions: None found in database")
            print(f"   - This means monthly transaction data hasn't been generated yet")
            print(f"   - But {stats['with_financial_history']} properties have yearly financial_history")
            print(f"\n   To generate monthly GL transactions, run:")
            print(f"   python3 generate_timeseries_for_all_properties.py")
        
        # List properties missing data
        if stats['properties_missing_data']:
            print("\n" + "=" * 70)
            print("📋 Properties Missing Synthetic Data")
            print("=" * 70)
            
            # Group by whether they have rent/area (priority for generation)
            priority_props = [p for p in stats['properties_missing_data'] if p.get('has_rent') or p.get('has_area')]
            other_props = [p for p in stats['properties_missing_data'] if not (p.get('has_rent') or p.get('has_area'))]
            
            if priority_props:
                print(f"\n🔴 Priority Properties (have rent or area): {len(priority_props)}")
                print("-" * 70)
                for i, prop in enumerate(priority_props[:20], 1):  # Show first 20
                    rent_info = f"Rent: {prop.get('total_rent', 0):,.0f} NOK" if prop.get('has_rent') else "No rent"
                    area_info = f"Area: {prop.get('has_area', False)}" if prop.get('has_area') else "No area"
                    print(f"{i:3d}. {prop['address']}, {prop['city']}")
                    print(f"     ID: {prop['id']} | {rent_info} | {area_info}")
                
                if len(priority_props) > 20:
                    print(f"     ... and {len(priority_props) - 20} more")
            
            if other_props:
                print(f"\n🟡 Other Properties (no rent/area): {len(other_props)}")
                print("-" * 70)
                for i, prop in enumerate(other_props[:10], 1):  # Show first 10
                    print(f"{i:3d}. {prop['address']}, {prop['city']} (ID: {prop['id']})")
                
                if len(other_props) > 10:
                    print(f"     ... and {len(other_props) - 10} more")
        
        # Recommendations
        print("\n" + "=" * 70)
        print("💡 Recommendations")
        print("=" * 70)
        
        if stats['missing_all_data'] > 0:
            print(f"\n⚠️  {stats['missing_all_data']} properties are missing synthetic data.")
            print("\nTo generate data for all properties, run:")
            print("   python3 generate_timeseries_for_all_properties.py")
            print("\nOr to generate only for missing properties:")
            print("   python3 generate_timeseries_for_all_properties.py --only-missing")
        else:
            print(f"\n✅ All {stats['total']} properties have SOME synthetic data!")
            print(f"\n📊 Breakdown:")
            print(f"   - {stats['with_financial_history']} have yearly historical data (financial_history)")
            print(f"   - {stats['with_gl_transactions']} have GL transactions (monthly)")
            if stats['with_monthly_timeseries'] > 0:
                print(f"   - {stats['with_monthly_timeseries']} have monthly timeseries")
            
            # Check if data looks complete
            if stats['with_gl_transactions'] == stats['total']:
                print(f"\n🎉 Perfect! All {stats['total']} properties have GL transactions.")
            elif stats['with_gl_transactions'] == 0 and stats['with_financial_history'] == stats['total']:
                print(f"\n📊 Status: All properties have yearly data (financial_history)")
                print(f"   But monthly GL transactions haven't been generated yet.")
                print(f"\n   To generate monthly GL transactions for all properties:")
                print(f"   python3 generate_timeseries_for_all_properties.py")
            elif stats['with_gl_transactions'] / stats['total'] > 0.9:
                print(f"\n✅ Excellent coverage! {stats['with_gl_transactions']}/{stats['total']} properties have GL transactions.")
        
        # Data quality check
        print("\n" + "=" * 70)
        print("🔍 Data Quality Check")
        print("=" * 70)
        
        # Check GL transactions date range
        if gl_counts:
            date_stmt = text("""
                SELECT 
                    MIN(transaction_date) as min_date,
                    MAX(transaction_date) as max_date,
                    COUNT(DISTINCT DATE_TRUNC('month', transaction_date)) as month_count
                FROM gl_transactions
            """)
            date_result = await db.execute(date_stmt)
            date_row = date_result.fetchone()
            
            if date_row and date_row[0]:
                print(f"\n📅 GL Transactions Date Range:")
                print(f"   From: {date_row[0]}")
                print(f"   To: {date_row[1]}")
                print(f"   Months covered: {date_row[2]}")
        
        print("\n" + "=" * 70)
        print("✅ Check completed!")
        print("=" * 70)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return stats


async def main():
    """Main execution function."""
    try:
        stats = await check_synthetic_data_coverage()
        return stats
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        stats = asyncio.run(main())
        # Exit with error code if properties are missing data
        if stats and stats.get('missing_all_data', 0) > 0:
            print(f"\n⚠️  Warning: {stats['missing_all_data']} properties missing data")
            sys.exit(1)
        else:
            print("\n✅ All properties have data")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        sys.exit(1)
