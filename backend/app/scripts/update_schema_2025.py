
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def update_schema():
    print("Starting schema update...")
    async with engine.begin() as conn:
        # 1. Properties - approved_places
        try:
            print("Checking properties table...")
            # Check if column exists
            # This is postgres specific syntax for checking column
            # For simplicity in raw SQL simply trying to add and catching error is also an option, 
            # or checking information_schema.
            
            # Using IF NOT EXISTS logic via catch or direct check.
            # Postgres supports "ADD COLUMN IF NOT EXISTS" in recent versions, but standard is just ADD COLUMN.
            # Let's try adding it.
            
            await conn.execute(text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS approved_places INTEGER;"))
            print("Added approved_places to properties.")
        except Exception as e:
            print(f"Error updating properties: {e}")

        # 2. Contracts - Cost columns
        cost_cols = [
            ("caretaker_cost", "FLOAT"),
            ("cleaning_cost", "FLOAT"), 
            ("parking_cost", "FLOAT"), 
            ("card_reader_cost", "FLOAT")
        ]
        
        for col_name, col_type in cost_cols:
            try:
                print(f"Adding {col_name} to contracts...")
                await conn.execute(text(f"ALTER TABLE contracts ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
            except Exception as e:
                print(f"Error adding {col_name}: {e}")

    print("Schema update completed.")

if __name__ == "__main__":
    asyncio.run(update_schema())
