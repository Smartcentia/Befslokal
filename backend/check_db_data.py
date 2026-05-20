#!/usr/bin/env python3
"""Quick script to check database connection and retrieve data overview."""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def get_database_url():
    """Get database URL from settings, convert to psycopg2 if needed."""
    url = settings.DATABASE_URL
    # Convert asyncpg to psycopg2 for synchronous access
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url

async def check_connection_and_data():
    """Check database connection and retrieve data overview."""
    try:
        # Create synchronous engine for this quick check
        engine = create_engine(get_database_url())
        
        print("=" * 60)
        print("DATABASE CONNECTION CHECK")
        print("=" * 60)
        print(f"Database URL: {get_database_url().split('@')[1] if '@' in get_database_url() else 'local'}")
        print()
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connection successful!")
            print(f"PostgreSQL version: {version}")
            print()
            
            # Get all tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            print("=" * 60)
            print(f"TABLES IN DATABASE ({len(tables)} total)")
            print("=" * 60)
            print()
            
            # Count rows in each table
            table_data = []
            for table in sorted(tables):
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    table_data.append((table, count))
                except Exception as e:
                    table_data.append((table, f"Error: {str(e)[:50]}"))
            
            # Print table overview
            for table, count in table_data:
                if isinstance(count, int):
                    print(f"  {table:35} | {count:>10} rows")
                else:
                    print(f"  {table:35} | {count}")
            
            print()
            print("=" * 60)
            print("SAMPLE DATA FROM KEY TABLES")
            print("=" * 60)
            print()
            
            # Sample from properties table
            if 'properties' in tables:
                print("📍 PROPERTIES (columns):")
                columns = inspector.get_columns('properties')
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")
                print()
            
            # Sample from contracts table
            if 'contracts' in tables:
                print("📄 CONTRACTS (columns):")
                columns = inspector.get_columns('contracts')
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")
                print()
            
            # Sample from users table
            if 'users' in tables:
                print("👤 USERS (columns):")
                columns = inspector.get_columns('users')
                for col in columns:
                    print(f"  - {col['name']} ({col['type']})")
                print()
            
            # Check NextAuth tables (from Prisma migration)
            nextauth_tables = ['Account', 'Session', 'User', 'VerificationToken']
            print("🔐 NEXTAUTH TABLES:")
            for table in nextauth_tables:
                if table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
                    count = result.scalar()
                    print(f"  {table:25} | {count:>5} rows")
            print()

            # Check internal_control_cases property_ids
            if 'internal_control_cases' in tables:
                print("📋 INTERNAL CONTROL CASES (first 5 IDs):")
                result = conn.execute(text("""
                    SELECT case_id, property_id, title 
                    FROM internal_control_cases 
                    LIMIT 5
                """))
                for row in result:
                    print(f"  Case: {row[0]} | Prop: {row[1]} | Title: {row[2]}")
                print()
            
        print("=" * 60)
        print("✅ Database check complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(check_connection_and_data())
    sys.exit(0 if success else 1)
