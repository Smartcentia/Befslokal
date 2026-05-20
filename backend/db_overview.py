#!/usr/bin/env python3
"""Check database schema and data."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def get_database_url():
    """Get database URL from settings, convert to psycopg2 if needed."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url

def main():
    engine = create_engine(get_database_url())
    
    print("=" * 80)
    print("DATABASE CONNECTION AND OVERVIEW")
    print("=" * 80)
    
    with engine.connect() as conn:
        # Connection info
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connected to: PostgreSQL")
        print(f"Version: {version.split(',')[0]}")
        print()
        
        # Get all tables with row counts
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📊 TABLES ({len(tables)} total)")
        print("-" * 80)
        
        table_info = []
        for table in sorted(tables):
            try:
                result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                count = result.scalar()
                table_info.append((table, count))
            except Exception as e:
                table_info.append((table, f"Error"))
        
        # Print non-empty tables first
        non_empty = [(t, c) for t, c in table_info if isinstance(c, int) and c > 0]
        empty = [(t, c) for t, c in table_info if isinstance(c, int) and c == 0]
        errors = [(t, c) for t, c in table_info if not isinstance(c, int)]
        
        if non_empty:
            print("\n🟢 NON-EMPTY TABLES:")
            for table, count in non_empty:
                print(f"   {table:40} | {count:>8,} rows")
        
        if empty:
            print(f"\n⚪ EMPTY TABLES ({len(empty)}):")
            for table, count in empty[:10]:  # Show first 10
                print(f"   {table:40} | {count:>8} rows")
            if len(empty) > 10:
                print(f"   ... and {len(empty) - 10} more empty tables")
        
        # Detailed info for non-empty tables
        if non_empty:
            print("\n" + "=" * 80)
            print("DETAILED DATA FROM NON-EMPTY TABLES")
            print("=" * 80)
            
            for table, count in non_empty:
                print(f"\n📋 Table: {table} ({count} rows)")
                print("-" * 80)
                
                # Get column names
                columns = inspector.get_columns(table)
                col_names = [col['name'] for col in columns]
                
                # Select first few rows
                col_list = ', '.join([f'"{c}"' for c in col_names[:8]])  # First 8 columns
                query = f'SELECT {col_list} FROM "{table}" LIMIT 5'
                
                try:
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                    
                    # Print column headers
                    headers = col_names[:8]
                    print("Columns:", ", ".join(headers))
                    print()
                    
                    # Print rows
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, str):
                                values.append(val[:40])  # Truncate strings
                            else:
                                values.append(str(val))
                        print("  " + " | ".join(values))
                        
                except Exception as e:
                    print(f"  Error reading data: {e}")
        
        # Check alembic version
        print("\n" + "=" * 80)
        print("DATABASE MIGRATION STATUS")
        print("=" * 80)
        try:
            result = conn.execute(text('SELECT version_num FROM alembic_version'))
            version = result.scalar()
            print(f"Current Alembic version: {version}")
        except:
            print("No alembic version found")
        
        print("\n" + "=" * 80)
        print("✅ Database check complete!")
        print("=" * 80)

if __name__ == "__main__":
    main()
