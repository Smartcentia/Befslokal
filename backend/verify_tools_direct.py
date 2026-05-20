
import asyncio
import sys
import json
from uuid import UUID

sys.path.append("/Users/frank/BEFS3/KNOWME/backend")

async def verify_tools():
    from app.db.session import SessionLocal
    from sqlalchemy import select
    from app.domains.core.models.property import Property
    from app.services.mcp.handler import mcp_handler

    print("--- 1. Fetching a Valid Property ID ---")
    property_id = None
    async with SessionLocal() as db:
        # Get ANY property using RAW SQL to avoid ORM relationship errors in script
        from sqlalchemy import text
        res = await db.execute(text("SELECT property_id FROM properties LIMIT 1"))
        row = res.fetchone()
        if row:
            property_id = str(row[0])
            print(f"Found Property ID: {property_id}")
        else:
            print("No properties found in DB.")
            return

    if not property_id:
        return

    print(f"\n--- 2. Testing get_nearby_services for {property_id} ---")
    try:
        res = await mcp_handler.execute_tool("get_nearby_services", {"property_id": property_id})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"FAILED: {e}")

    print(f"\n--- 3. Testing check_internal_control for {property_id} ---")
    try:
        res = await mcp_handler.execute_tool("check_internal_control", {"property_id": property_id})
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(verify_tools())
