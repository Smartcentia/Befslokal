import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.db.session import SessionLocal

async def alter_table():
    print("Altering properties table to add missing columns...")
    columns_to_add = [
        ("name", "VARCHAR"),
        ("usage", "VARCHAR"),
        ("total_area", "FLOAT"),
        ("construction_year", "INTEGER"),
        ("energy_label", "VARCHAR"),
        ("municipality", "VARCHAR"),
        ("municipality_code", "VARCHAR"),
        ("gnr", "INTEGER"),
        ("bnr", "INTEGER")
    ]
    
    async with SessionLocal() as db:
        for col_name, col_type in columns_to_add:
            try:
                # Use a specific syntax for PostgreSQL/SQLAlchemy to avoid errors if exists
                # However, for simplicity and since I know they are missing:
                await db.execute(text(f"ALTER TABLE properties ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"Added column {col_name}")
            except Exception as e:
                print(f"Error adding column {col_name}: {e}")
        
        await db.commit()
    print("Table alteration complete.")

if __name__ == "__main__":
    asyncio.run(alter_table())
