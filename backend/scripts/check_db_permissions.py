#!/usr/bin/env python3
"""
Check database write permissions and test insertion.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env BEFORE importing app modules
load_dotenv(Path(__file__).parent.parent / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models
import app.db.base
from app.db.session import SessionLocal
from app.models.financial_models import GLTransaction
from app.domains.core.models.property import Property
from sqlalchemy import select, text
from uuid import UUID as UUIDType

async def check_permissions():
    """Check database permissions and test write access."""
    print("=" * 70)
    print("Checking Database Write Permissions")
    print("=" * 70)
    
    async with SessionLocal() as db:
        # Check current user and permissions
        print("\n1️⃣ Checking database user and permissions...")
        
        try:
            stmt = text("SELECT current_user, session_user")
            result = await db.execute(stmt)
            user_info = result.fetchone()
            print(f"   Current user: {user_info[0]}")
            print(f"   Session user: {user_info[1]}")
        except Exception as e:
            print(f"   ⚠️  Could not check user: {e}")
        
        # Check if we can read from gl_transactions
        print("\n2️⃣ Testing read access to gl_transactions...")
        try:
            stmt = text("SELECT COUNT(*) FROM gl_transactions")
            result = await db.execute(stmt)
            count = result.scalar()
            print(f"   ✅ Can read: Found {count} transactions")
        except Exception as e:
            print(f"   ❌ Cannot read: {e}")
            return False
        
        # Check if we can write to gl_transactions
        print("\n3️⃣ Testing write access to gl_transactions...")
        
        # Get first property
        stmt = select(Property).limit(1)
        result = await db.execute(stmt)
        prop = result.scalar_one_or_none()
        
        if not prop:
            print("   ❌ No properties found!")
            return False
        
        print(f"   Using property: {prop.address or prop.name}")
        
        # Try to insert a test transaction
        test_trans = GLTransaction(
            property_id=prop.property_id,
            transaction_date=datetime.now(),
            year=2026,
            month=1,
            amount=999.99,
            category='PermissionTest',
            description='Testing write permissions',
            account_code='9999',
            source_system='permission_test'
        )
        
        try:
            db.add(test_trans)
            await db.flush()
            print(f"   ✅ Flush successful (can add to session)")
            
            await db.commit()
            print(f"   ✅ Commit successful (can write to database)")
            
            # Verify it was saved
            stmt = text("SELECT COUNT(*) FROM gl_transactions WHERE source_system = 'permission_test'")
            result = await db.execute(stmt)
            count = result.scalar()
            
            if count > 0:
                print(f"   ✅ Verification: Found {count} test transaction(s)")
                
                # Clean up test transaction
                stmt = text("DELETE FROM gl_transactions WHERE source_system = 'permission_test'")
                await db.execute(stmt)
                await db.commit()
                print(f"   ✅ Cleaned up test transaction")
                
                return True
            else:
                print(f"   ❌ Transaction not found after commit!")
                return False
                
        except Exception as e:
            print(f"   ❌ Write failed: {e}")
            await db.rollback()
            import traceback
            print("\n   Full error:")
            traceback.print_exc()
            return False
        
        # Check table ownership
        print("\n4️⃣ Checking table ownership...")
        try:
            stmt = text("""
                SELECT 
                    table_name,
                    tableowner
                FROM pg_tables
                WHERE schemaname = 'public' 
                AND table_name = 'gl_transactions'
            """)
            result = await db.execute(stmt)
            table_info = result.fetchone()
            
            if table_info:
                print(f"   Table owner: {table_info[1]}")
            else:
                print(f"   ⚠️  Table not found in pg_tables")
        except Exception as e:
            print(f"   ⚠️  Could not check ownership: {e}")

if __name__ == "__main__":
    success = asyncio.run(check_permissions())
    
    print("\n" + "=" * 70)
    if success:
        print("✅ Database write permissions: OK")
    else:
        print("❌ Database write permissions: FAILED")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
