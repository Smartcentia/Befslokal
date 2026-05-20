import asyncio
import sys
import os

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.db.session import SessionLocal, engine
from app.models.ai_tool import AITool
from app.db.base_class import Base
from app.ai_lab.main_mvp import lab_service

async def test_shared_library():
    print("📚 Testing Shared Library Integration...")
    
    # Ensure Tables Exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 0. Cleanup (Optional, for clean test)
    query = "Create a tool that returns the string 'SHARED_LIB_TEST'"
    
    # 1. Initialize
    await lab_service.initialize()
    
    # 2. First Call -> Creation
    print("\n[1] Creating Tool (First Run)...")
    res1 = await lab_service.process_request(query)
    
    if res1.get("status") != "created":
        print(f"❌ Failed to create tool: {res1.get('error')}")
        # Identify if it was 'found' instead (from previous run)
        if res1.get("status") == "found":
             print("⚠️ Tool already existed. That's okay, we'll verify retrieval.")
    else:
        print(f"✅ Tool Created. ID: {res1.get('tool_id')}")
        
    # 3. Verify DB Persistence
    # Wait a moment for DB commit if async implementation is flaky (it awaited commit, so should be fine)
    tool_id = res1.get("tool_id")
    
    import uuid
    try:
        t_uuid = uuid.UUID(tool_id)
        async with SessionLocal() as db:
            from sqlalchemy import select
            stmt = select(AITool).where(AITool.id == t_uuid)
            db_res = await db.execute(stmt)
            tool_in_db = db_res.scalars().first()
            
            if tool_in_db:
                print(f"✅ Verified in DB: {tool_in_db.name} | Status: {tool_in_db.status}")
            else:
                print(f"❌ Tool {tool_id} NOT found in DB!")
    except Exception as e:
        print(f"❌ DB Check Failed: {e}")

    # 4. Second Call -> Retrieval
    print("\n[2] Requesting SAME Tool (Second Run)...")
    res2 = await lab_service.process_request(query)
    
    status2 = res2.get("status")
    if status2 == "found":
        print(f"✅ Successfully Retrieved from Library! Tool ID matches: {res2.get('tool_id') == tool_id}")
    else:
        print(f"❌ Failed to retrieve. Status: {status2}")

if __name__ == "__main__":
    asyncio.run(test_shared_library())
