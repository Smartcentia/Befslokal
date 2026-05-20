#!/usr/bin/env python3
"""
Test script to verify GL transaction insertion works.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Load .env BEFORE importing app modules
load_dotenv(Path(__file__).parent.parent / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models
import app.db.base
from app.db.session import SessionLocal
from app.models.financial_models import GLTransaction
from app.domains.core.models.property import Property
from sqlalchemy import select
from uuid import UUID as UUIDType

async def test_insert():
    """Test inserting a single GL transaction."""
    print("=" * 70)
    print("Testing GL Transaction Insertion")
    print("=" * 70)
    
    async with SessionLocal() as db:
        # Get first property
        stmt = select(Property).limit(1)
        result = await db.execute(stmt)
        prop = result.scalar_one_or_none()
        
        if not prop:
            print("❌ No properties found in database!")
            return False
        
        print(f"\n✅ Found property: {prop.address or prop.name} (ID: {prop.property_id})")
        
        # Create a test transaction
        test_trans = GLTransaction(
            property_id=prop.property_id,
            transaction_date=datetime.now(),
            year=2026,
            month=1,
            amount=1000.0,
            category='Test',
            description='Test transaction',
            account_code='3000',
            source_system='test_script'
        )
        
        print(f"\n📝 Creating test transaction...")
        print(f"   Property ID: {test_trans.property_id}")
        print(f"   Date: {test_trans.transaction_date}")
        print(f"   Amount: {test_trans.amount}")
        print(f"   Category: {test_trans.category}")
        
        try:
            db.add(test_trans)
            await db.flush()
            print(f"\n✅ Transaction added to session (flush successful)")
            
            await db.commit()
            print(f"✅ Transaction committed to database")
            
            # Verify it was saved
            from sqlalchemy import text
            stmt = text("SELECT COUNT(*) FROM gl_transactions WHERE source_system = 'test_script'")
            result = await db.execute(stmt)
            count = result.scalar()
            
            print(f"\n✅ Verification: Found {count} test transaction(s) in database")
            
            if count > 0:
                print(f"\n🎉 SUCCESS! GL transaction insertion works!")
                return True
            else:
                print(f"\n❌ Transaction not found after commit!")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await db.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_insert())
    sys.exit(0 if success else 1)
