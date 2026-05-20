import asyncio
import sys
import os

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.db.session import SessionLocal, engine
from app.db.base_class import Base
from app.ai_lab.main_mvp import lab_service

async def test_marketplace():
    print("🏪 Testing Tool Marketplace (Governance)...")
    
    # Ensure Tables Exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 1. List All Tools
    print("\n[1] Listing All Tools...")
    all_tools = await lab_service.list_tools()
    print(f"found {len(all_tools)} tools.")
    
    experimental_tool = None
    for t in all_tools:
        print(f" - {t.name} [{t.status.value}] (ID: {t.id})")
        if t.status.value == "experimental":
            experimental_tool = t
            
    if not experimental_tool:
        print("⚠️ No experimental tools found to promote. Run test_shared_library.py first.")
        return

    # 2. Publish (Promote) a Tool
    target_id = str(experimental_tool.id)
    print(f"\n[2] Promoting Tool: {experimental_tool.name} ({target_id})...")
    
    res = await lab_service.publish_tool(target_id)
    if res["status"] == "success":
        print("✅ Promotion Successful!")
    else:
        print(f"❌ Promotion Failed: {res.get('message')}")
        return

    # 3. Verify Status
    print("\n[3] Verifying Status...")
    # Fetch specifically verified tools
    verified_tools = await lab_service.list_tools(status="verified")
    
    is_verified = any(str(t.id) == target_id for t in verified_tools)
    
    if is_verified:
        print(f"✅ Verified! Tool {target_id} is now in the Global Library.")
    else:
        print(f"❌ Failed. Tool {target_id} is NOT in the verified list.")

if __name__ == "__main__":
    asyncio.run(test_marketplace())
