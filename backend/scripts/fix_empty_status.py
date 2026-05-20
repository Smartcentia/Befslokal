"""
Fix Invalid Contract Status Values

Some contracts have status="" (empty string) which violates the contractstatus enum.
This script fixes them to 'active' before we can update their metadata.

Usage:
    python3 scripts/fix_empty_status.py
"""

import sys
import os
import asyncio

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

async def fix_empty_statuses():
    """Fix contracts with empty or invalid status values."""
    
    print("=" * 80)
    print("FIX INVALID CONTRACT STATUS VALUES")
    print("=" * 80)
    
    async with SessionLocal() as session:
        # Find contracts with empty status using raw SQL
        print("\n1. Finding contracts with invalid status...")
        
        # Check for empty strings - we need to query the raw column
        result = await session.execute(
            text("SELECT contract_id, status FROM contracts WHERE status = ''")
        )
        invalid_contracts = result.fetchall()
        
        if not invalid_contracts:
            print("   ✓ No contracts with empty status found!")
            return 0
        
        print(f"   Found {len(invalid_contracts)} contracts with empty status")
        
        # Fix each one
        print("\n2. Fixing invalid statuses...")
        for contract_id, status in invalid_contracts:
            print(f"   Fixing contract {contract_id}...")
            await session.execute(
                text("""
                    UPDATE contracts 
                    SET status = 'active'
                    WHERE contract_id = CAST(:contract_id AS uuid)
                """),
                {"contract_id": str(contract_id)}
            )
        
        # Commit changes
        await session.commit()
        print(f"\n✅ Fixed {len(invalid_contracts)} contracts")
        
        return len(invalid_contracts)

async def main():
    try:
        count = await fix_empty_statuses()
        
        if count > 0:
            print("\n" + "=" * 80)
            print("NEXT STEPS")
            print("=" * 80)
            print("Now you can run the CSV enrichment script:")
            print("  python3 scripts/update_from_csv_sql.py")
            print("=" * 80)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
