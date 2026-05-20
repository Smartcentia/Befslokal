import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def check_schema():
    async with SessionLocal() as db:
        print("--- Checking Schema ---")
        
        # Check ns3451_codes
        try:
            result = await db.execute(text("SELECT * FROM ns3451_codes LIMIT 1"))
            print("Table 'ns3451_codes' EXISTS.")
        except Exception as e:
             print(f"Table 'ns3451_codes' does NOT exist ({e}).")
             
        # Check properties.geom
        try:
            result = await db.execute(text("SELECT geom FROM properties LIMIT 1"))
            print("Column 'properties.geom' EXISTS.")
        except Exception as e:
            print(f"Column 'properties.geom' does NOT exist ({e}).")

        # Check index idx_properties_geom
        try:
            result = await db.execute(text("SELECT indexname FROM pg_indexes WHERE indexname = 'idx_properties_geom'"))
            row = result.fetchone()
            if row:
                print("Index 'idx_properties_geom' EXISTS.")
            else:
                print("Index 'idx_properties_geom' does NOT exist.")
        except Exception as e:
            print(f"Error checking index: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
