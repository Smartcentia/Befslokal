#!/usr/bin/env python3
"""
Verify that synthetic data covers multiple calendar years.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from collections import defaultdict

# Load .env BEFORE importing app modules
load_dotenv(Path(__file__).parent.parent / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models
import app.db.base
from app.db.session import SessionLocal
from sqlalchemy import text

async def verify_years_coverage():
    """Check which calendar years are covered by GL transactions."""
    print("=" * 70)
    print("Verifying Calendar Years Coverage")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with SessionLocal() as db:
        # Check GL transactions by year
        print("📅 Checking GL transactions by calendar year...")
        
        stmt = text("""
            SELECT 
                EXTRACT(YEAR FROM transaction_date) as year,
                COUNT(*) as transaction_count,
                COUNT(DISTINCT property_id) as property_count,
                COUNT(DISTINCT DATE_TRUNC('month', transaction_date)) as month_count
            FROM gl_transactions
            GROUP BY EXTRACT(YEAR FROM transaction_date)
            ORDER BY year
        """)
        
        result = await db.execute(stmt)
        year_data = result.all()
        
        if not year_data:
            print("❌ No GL transactions found in database!")
            return
        
        print(f"\n✅ Found transactions covering {len(year_data)} calendar year(s):\n")
        
        total_transactions = 0
        total_properties = set()
        all_months = set()
        
        for row in year_data:
            year = int(row[0])
            transactions = row[1]
            properties = row[2]
            months = int(row[3])
            
            total_transactions += transactions
            
            print(f"📆 {year}:")
            print(f"   - Transactions: {transactions:,}")
            print(f"   - Properties: {properties}")
            print(f"   - Months covered: {months}/12")
            
            # Check if full year
            if months == 12:
                print(f"   ✅ Complete year")
            elif months >= 6:
                print(f"   ⚠️  Partial year ({months} months)")
            else:
                print(f"   ⚠️  Limited data ({months} months)")
        
        # Check date range
        print("\n" + "=" * 70)
        print("📊 Date Range Analysis")
        print("=" * 70)
        
        stmt = text("""
            SELECT 
                MIN(transaction_date) as min_date,
                MAX(transaction_date) as max_date,
                MAX(transaction_date) - MIN(transaction_date) as date_range
            FROM gl_transactions
        """)
        
        result = await db.execute(stmt)
        date_row = result.fetchone()
        
        if date_row and date_row[0]:
            min_date = date_row[0]
            max_date = date_row[1]
            date_range = date_row[2]
            
            print(f"\n📅 Overall Date Range:")
            print(f"   From: {min_date.strftime('%Y-%m-%d')}")
            print(f"   To: {max_date.strftime('%Y-%m-%d')}")
            print(f"   Span: {date_range.days} days ({date_range.days/365.25:.1f} years)")
            
            # Calculate expected months
            from dateutil.relativedelta import relativedelta
            months_span = (max_date.year - min_date.year) * 12 + (max_date.month - min_date.month) + 1
            print(f"   Expected months: {months_span}")
            
            # Check month coverage
            stmt = text("""
                SELECT 
                    DATE_TRUNC('month', transaction_date) as month,
                    COUNT(*) as count
                FROM gl_transactions
                GROUP BY DATE_TRUNC('month', transaction_date)
                ORDER BY month
            """)
            
            result = await db.execute(stmt)
            month_data = result.all()
            
            print(f"\n📈 Month-by-Month Coverage:")
            print(f"   Total unique months: {len(month_data)}")
            
            # Group by year for summary
            years_summary = defaultdict(int)
            for row in month_data:
                month = row[0]
                years_summary[month.year] += 1
            
            print(f"\n   Months per year:")
            for year in sorted(years_summary.keys()):
                months = years_summary[year]
                print(f"   {year}: {months} months")
        
        # Check properties coverage
        print("\n" + "=" * 70)
        print("🏢 Properties Coverage")
        print("=" * 70)
        
        stmt = text("""
            SELECT 
                property_id,
                COUNT(*) as transaction_count,
                MIN(transaction_date) as first_transaction,
                MAX(transaction_date) as last_transaction,
                COUNT(DISTINCT DATE_TRUNC('month', transaction_date)) as month_count
            FROM gl_transactions
            GROUP BY property_id
            ORDER BY transaction_count DESC
        """)
        
        result = await db.execute(stmt)
        prop_data = result.all()
        
        if prop_data:
            total_props = len(prop_data)
            props_with_full_coverage = sum(1 for row in prop_data if row[4] >= 36)  # 36 months = 3 years
            
            print(f"\nTotal properties with GL transactions: {total_props}")
            print(f"Properties with 36+ months (3 years): {props_with_full_coverage} ({props_with_full_coverage/total_props*100:.1f}%)")
            
            # Show sample
            print(f"\n📋 Sample (first 5 properties):")
            for i, row in enumerate(prop_data[:5], 1):
                prop_id = str(row[0])
                trans_count = row[1]
                first = row[2]
                last = row[3]
                months = row[4]
                
                print(f"\n{i}. Property {prop_id[:8]}...")
                print(f"   Transactions: {trans_count}")
                print(f"   Date range: {first.strftime('%Y-%m')} to {last.strftime('%Y-%m')}")
                print(f"   Months: {months}")
                print(f"   Years covered: {len(set(range(first.year, last.year + 1)))}")
        
        print("\n" + "=" * 70)
        print("✅ Verification completed!")
        print("=" * 70)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main execution function."""
    try:
        await verify_years_coverage()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    asyncio.run(main())
