import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def verify_postgis():
    async with SessionLocal() as db:
        print("--- Verifying PostGIS ---")
        try:
            # 1. Check Extension
            result = await db.execute(text("SELECT PostGIS_Version()"))
            version = result.scalar()
            print(f"PostGIS Version: {version}")

            # 2. Test Spatial Query
            # Insert a dummy property with geometry (if not exists)
            # Or just update the one we used in previous tests if key constraints allow
            # For safety, let's just query existing data or select a constant.
            
            # Distance between Oslo and Bergen (rough coords)
            # oslo = (10.7522, 59.9139)
            # bergen = (5.3221, 60.3913)
            
            query = """
                SELECT ST_Distance(
                    ST_SetSRID(ST_MakePoint(10.7522, 59.9139), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(5.3221, 60.3913), 4326)::geography
                ) as dist_meters;
            """
            result = await db.execute(text(query))
            dist = result.scalar()
            print(f"Distance Test (Oslo-Bergen): {dist:.2f} meters")
            
            if dist > 300000: # Approx 300km? (Actually air distance is ~300km, so > 100km is safe check)
                print("SUCCESS: PostGIS spatial calculation works.")
            else:
                print("WARNING: Distance seems low.")

        except Exception as e:
            print(f"FAILED: PostGIS verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_postgis())
