#!/usr/bin/env python3
"""
Check the actual structure of gl_transactions table in the database.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env BEFORE importing app modules
load_dotenv(Path(__file__).parent.parent / '.env')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models
import app.db.base
from app.db.session import SessionLocal
from sqlalchemy import text, inspect

async def check_table_structure():
    """Check the actual structure of gl_transactions table."""
    print("=" * 70)
    print("Checking gl_transactions Table Structure")
    print("=" * 70)
    
    async with SessionLocal() as db:
        # Check if table exists
        stmt = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'gl_transactions'
            );
        """)
        result = await db.execute(stmt)
        table_exists = result.scalar()
        
        if not table_exists:
            print("\n❌ Table 'gl_transactions' does not exist!")
            print("\nYou may need to run migrations:")
            print("   cd backend && alembic upgrade head")
            return
        
        print("\n✅ Table 'gl_transactions' exists")
        
        # Get column information
        stmt = text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'gl_transactions'
            ORDER BY ordinal_position;
        """)
        
        result = await db.execute(stmt)
        columns = result.all()
        
        print(f"\n📋 Table Structure ({len(columns)} columns):")
        print("-" * 70)
        
        expected_columns = {
            'transaction_date': False,
            'year': False,
            'month': False,
            'category': False,
            'account_code': False,
            'description': False,
            'source_system': False
        }
        
        for col in columns:
            col_name = col[0]
            col_type = col[1]
            nullable = col[2]
            default = col[3]
            
            status = "✅" if col_name in expected_columns else "ℹ️"
            if col_name in expected_columns:
                expected_columns[col_name] = True
            
            nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
            print(f"{status} {col_name:30s} {col_type:20s} {nullable_str}")
            if default:
                print(f"   Default: {default}")
        
        # Check what's missing
        print("\n" + "=" * 70)
        print("Missing Columns Analysis")
        print("=" * 70)
        
        missing = [col for col, found in expected_columns.items() if not found]
        if missing:
            print(f"\n❌ Missing columns needed by GLTransaction model:")
            for col in missing:
                print(f"   - {col}")
            
            print(f"\n💡 The table structure doesn't match the model.")
            print(f"   You may need to:")
            print(f"   1. Create a migration to add these columns")
            print(f"   2. Or update the model to match existing structure")
        else:
            print(f"\n✅ All required columns are present!")
        
        # Check for old structure columns
        old_structure_cols = ['period', 'region_code', 'dim2_code', 'purpose_code']
        found_old = [col[0] for col in columns if col[0] in old_structure_cols]
        
        if found_old:
            print(f"\n⚠️  Found old structure columns: {', '.join(found_old)}")
            print(f"   The table may have both old and new structure")
        
        # Check row count
        stmt = text("SELECT COUNT(*) FROM gl_transactions")
        result = await db.execute(stmt)
        row_count = result.scalar()
        
        print(f"\n📊 Current Data:")
        print(f"   Total rows: {row_count:,}")
        
        if row_count > 0:
            # Check sample data
            stmt = text("SELECT * FROM gl_transactions LIMIT 1")
            result = await db.execute(stmt)
            sample = result.fetchone()
            
            if sample:
                print(f"\n📋 Sample row columns:")
                col_names = [col[0] for col in columns]
                for i, val in enumerate(sample):
                    if val is not None:
                        print(f"   {col_names[i]}: {val}")

if __name__ == "__main__":
    asyncio.run(check_table_structure())
