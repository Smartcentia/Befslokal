#!/usr/bin/env python3
"""
Verify that GL transactions have been generated correctly for all properties.

This script checks:
1. All properties have GL transactions
2. Correct number of transactions per property
3. Data covers multiple calendar years
4. Transaction structure is correct
5. Date ranges are correct
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
from app.domains.core.models.property import Property
from sqlalchemy import select, text, func
from sqlalchemy.orm import joinedload

# Import other models
import app.domains.core.models.user
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control


async def verify_gl_transactions():
    """
    Verify GL transactions are correctly generated.
    """
    print("=" * 70)
    print("Verifying GL Transactions Generation")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    async with SessionLocal() as db:
        # Get total properties
        print("📊 Loading properties...")
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        total_props = len(properties)
        
        print(f"✅ Found {total_props} properties\n")
        
        if total_props == 0:
            print("❌ No properties found!")
            return False
        
        # Check GL transactions
        print("📋 Checking GL transactions...")
        
        # Total count
        stmt = text("SELECT COUNT(*) FROM gl_transactions")
        result = await db.execute(stmt)
        total_transactions = result.scalar()
        
        # Transactions per property
        stmt = text("""
            SELECT 
                property_id,
                COUNT(*) as transaction_count,
                MIN(transaction_date) as first_date,
                MAX(transaction_date) as last_date,
                COUNT(DISTINCT DATE_TRUNC('month', transaction_date)) as month_count
            FROM gl_transactions
            GROUP BY property_id
            ORDER BY transaction_count DESC
        """)
        
        result = await db.execute(stmt)
        prop_transactions = result.all()
        
        props_with_transactions = len(prop_transactions)
        
        print(f"✅ Found {total_transactions:,} total transactions")
        print(f"✅ Found {props_with_transactions} properties with transactions\n")
        
        # Expected values
        expected_months = 36  # 3 years
        expected_transactions_per_month = 4  # Rent, Electricity, Parking, Cleaning
        expected_transactions_per_property = expected_months * expected_transactions_per_month  # 144
        
        print("=" * 70)
        print("📊 Coverage Analysis")
        print("=" * 70)
        
        print(f"\nProperties:")
        print(f"   Total: {total_props}")
        print(f"   With transactions: {props_with_transactions} ({props_with_transactions/total_props*100:.1f}%)")
        print(f"   Missing transactions: {total_props - props_with_transactions}")
        
        print(f"\nTransactions:")
        print(f"   Total: {total_transactions:,}")
        print(f"   Expected (if all complete): {total_props * expected_transactions_per_property:,}")
        print(f"   Coverage: {total_transactions/(total_props * expected_transactions_per_property)*100:.1f}%")
        
        if props_with_transactions > 0:
            avg_transactions = total_transactions / props_with_transactions
            print(f"   Average per property: {avg_transactions:.1f}")
            print(f"   Expected per property: {expected_transactions_per_property}")
        
        # Check transaction distribution
        print("\n" + "=" * 70)
        print("📅 Date Range Analysis")
        print("=" * 70)
        
        stmt = text("""
            SELECT 
                MIN(transaction_date) as min_date,
                MAX(transaction_date) as max_date,
                COUNT(DISTINCT DATE_TRUNC('year', transaction_date)) as year_count,
                COUNT(DISTINCT DATE_TRUNC('month', transaction_date)) as month_count
            FROM gl_transactions
        """)
        
        result = await db.execute(stmt)
        date_row = result.fetchone()
        
        if date_row and date_row[0]:
            min_date = date_row[0]
            max_date = date_row[1]
            year_count = date_row[2]
            month_count = date_row[3]
            
            print(f"\nDate Range:")
            print(f"   From: {min_date.strftime('%Y-%m-%d')}")
            print(f"   To: {max_date.strftime('%Y-%m-%d')}")
            print(f"   Years covered: {year_count}")
            print(f"   Months covered: {month_count}")
            print(f"   Expected months: {expected_months}")
            
            if month_count >= expected_months:
                print(f"   ✅ Sufficient month coverage")
            else:
                print(f"   ⚠️  Missing months (expected {expected_months}, got {month_count})")
        
        # Check by calendar year
        print("\n" + "=" * 70)
        print("📆 Calendar Year Breakdown")
        print("=" * 70)
        
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
        
        if year_data:
            print()
            for row in year_data:
                year = int(row[0])
                transactions = row[1]
                properties = row[2]
                months = int(row[3])
                
                status = "✅" if months == 12 else "⚠️" if months >= 6 else "❌"
                print(f"{status} {year}: {transactions:,} transactions, {properties} properties, {months} months")
        else:
            print("\n❌ No transactions found by year")
        
        # Check transaction types (AccountCode)
        print("\n" + "=" * 70)
        print("💰 Transaction Types (Account Codes)")
        print("=" * 70)
        
        stmt = text("""
            SELECT 
                account_code,
                COUNT(*) as count,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_expenses
            FROM gl_transactions
            GROUP BY account_code
            ORDER BY account_code
        """)
        
        result = await db.execute(stmt)
        account_data = result.all()
        
        account_names = {
            '3000': 'Rent (Income)',
            '6000': 'Electricity (Expense)',
            '6100': 'Parking (Expense)',
            '6200': 'Cleaning (Expense)'
        }
        
        if account_data:
            print()
            expected_accounts = set(['3000', '6000', '6100', '6200'])
            found_accounts = set()
            
            for row in account_data:
                code = str(row[0])
                count = row[1]
                income = row[2] or 0
                expenses = row[3] or 0
                
                found_accounts.add(code)
                name = account_names.get(code, 'Unknown')
                
                print(f"   {code} - {name}:")
                print(f"      Count: {count:,}")
                if income > 0:
                    print(f"      Total Income: {income:,.2f} NOK")
                if expenses > 0:
                    print(f"      Total Expenses: {expenses:,.2f} NOK")
            
            missing = expected_accounts - found_accounts
            if missing:
                print(f"\n   ⚠️  Missing account codes: {', '.join(missing)}")
            else:
                print(f"\n   ✅ All expected account codes present")
        else:
            print("\n❌ No transactions found by account code")
        
        # Check property-level completeness
        print("\n" + "=" * 70)
        print("🏢 Property-Level Completeness")
        print("=" * 70)
        
        if prop_transactions:
            complete_props = sum(1 for row in prop_transactions if row[1] >= expected_transactions_per_property * 0.9)
            incomplete_props = props_with_transactions - complete_props
            
            print(f"\nProperties with complete data (≥90% of expected): {complete_props}")
            print(f"Properties with incomplete data: {incomplete_props}")
            
            # Show sample of properties
            print(f"\n📋 Sample Properties (first 5):")
            for i, row in enumerate(prop_transactions[:5], 1):
                prop_id = str(row[0])
                trans_count = row[1]
                first_date = row[2]
                last_date = row[3]
                months = row[4]
                
                completeness = (trans_count / expected_transactions_per_property * 100) if expected_transactions_per_property > 0 else 0
                status = "✅" if completeness >= 90 else "⚠️" if completeness >= 50 else "❌"
                
                print(f"\n{status} Property {prop_id[:8]}...")
                print(f"   Transactions: {trans_count} (expected: {expected_transactions_per_property})")
                print(f"   Completeness: {completeness:.1f}%")
                print(f"   Date range: {first_date.strftime('%Y-%m')} to {last_date.strftime('%Y-%m')}")
                print(f"   Months: {months}")
        
        # Final verification
        print("\n" + "=" * 70)
        print("✅ Final Verification")
        print("=" * 70)
        
        all_checks_passed = True
        
        # Check 1: All properties have transactions
        if props_with_transactions == total_props:
            print(f"\n✅ Check 1: All {total_props} properties have transactions")
        else:
            print(f"\n❌ Check 1: Only {props_with_transactions}/{total_props} properties have transactions")
            all_checks_passed = False
        
        # Check 2: Sufficient transactions
        if total_transactions >= total_props * expected_transactions_per_property * 0.9:
            print(f"✅ Check 2: Sufficient transactions ({total_transactions:,} >= {int(total_props * expected_transactions_per_property * 0.9):,})")
        else:
            print(f"❌ Check 2: Insufficient transactions ({total_transactions:,} < {int(total_props * expected_transactions_per_property * 0.9):,})")
            all_checks_passed = False
        
        # Check 3: Multiple years
        if date_row and date_row[2] and date_row[2] >= 2:
            print(f"✅ Check 3: Data covers {date_row[2]} calendar years")
        else:
            print(f"❌ Check 3: Data doesn't cover multiple years")
            all_checks_passed = False
        
        # Check 4: All account codes present
        if account_data and len(found_accounts) == 4:
            print(f"✅ Check 4: All 4 account codes present")
        else:
            print(f"❌ Check 4: Missing account codes (found {len(found_accounts) if account_data else 0}/4)")
            all_checks_passed = False
        
        print("\n" + "=" * 70)
        if all_checks_passed:
            print("🎉 ALL CHECKS PASSED! GL transactions are correctly generated.")
        else:
            print("⚠️  SOME CHECKS FAILED. Review the details above.")
        print("=" * 70)
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return all_checks_passed


async def main():
    """Main execution function."""
    try:
        success = await verify_gl_transactions()
        return success
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        sys.exit(1)
