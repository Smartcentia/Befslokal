#!/usr/bin/env python3
"""Show complete database schema with all tables and fields"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

async def show_database_schema():
    async with SessionLocal() as db:
        print("=" * 80)
        print("📊 KNOWME DATABASE SCHEMA")
        print("=" * 80)
        
        # Get all tables
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        tables = [row[0] for row in result.fetchall()]
        
        print(f"\n✅ Fant {len(tables)} tabeller i databasen\n")
        
        for table_name in tables:
            # Get columns for each table
            result = await db.execute(text("""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = :table_name
                ORDER BY ordinal_position
            """), {"table_name": table_name})
            
            columns = result.fetchall()
            
            # Get row count
            try:
                count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.scalar()
            except:
                row_count = "N/A"
            
            print(f"\n{'=' * 80}")
            print(f"📋 {table_name.upper()}")
            print(f"{'=' * 80}")
            print(f"Antall rader: {row_count}")
            print(f"\nKolonner ({len(columns)}):")
            print(f"{'-' * 80}")
            
            for col_name, data_type, max_length, nullable, default in columns:
                # Format data type
                if max_length:
                    type_str = f"{data_type}({max_length})"
                else:
                    type_str = data_type
                
                # Nullable indicator
                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                
                # Default value
                default_str = f" DEFAULT {default}" if default else ""
                
                print(f"  • {col_name:30} {type_str:25} {null_str:10}{default_str}")
        
        # Summary
        print(f"\n\n{'=' * 80}")
        print("📊 OPPSUMMERING")
        print(f"{'=' * 80}")
        
        # Get total rows across key tables
        key_tables = {
            'properties': 'Eiendommer',
            'contracts': 'Kontrakter',
            'parties': 'Parter/Utleiere',
            'units': 'Enheter',
            'users': 'Brukere',
        }
        
        print("\nAntall rader i hovedtabeller:")
        for table, description in key_tables.items():
            if table in tables:
                result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {description:20} {count:6} rader")
        
        print(f"\n{'=' * 80}")

if __name__ == "__main__":
    asyncio.run(show_database_schema())
