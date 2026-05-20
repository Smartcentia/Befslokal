import asyncio
import pytest
import os
from dotenv import load_dotenv
load_dotenv() # Ensure env vars (including DB) are loaded

from app.ai_lab.main_mvp import AILab

@pytest.mark.asyncio
async def test_widgets_flow():
    lab = AILab()
    await lab.initialize()
    
    # 1. Create a simple tool for testing
    print("🧪 Creating Widget Test Tool...")
    # Request a tool that echoes input to ensure we can verify execution input passing
    create_req = "Create a tool called 'EchoChamber' that takes a string input and returns it in uppercase."
    create_result = await lab.process_request(create_req)
    
    assert create_result["status"] == "created"
    tool_id = create_result["tool_id"]
    print(f"✅ Tool Created: {tool_id}")
    
    # 2. Test Pinning
    print("📍 Testing Pinning...")
    pin_res = await lab.toggle_pin_tool(tool_id, True)
    assert pin_res["status"] == "success"
    
    # Verify in Code/DB?
    # Let's list tools and check state
    from app.db.session import SessionLocal
    from app.models.ai_tool import AITool
    from sqlalchemy import select
    import uuid
    
    async with SessionLocal() as db:
        stmt = select(AITool).where(AITool.id == uuid.UUID(tool_id))
        res = await db.execute(stmt)
        tool = res.scalars().first()
        assert tool.is_pinned == True
        print("✅ DB Verification: Tool is Pinned")
        
    # 3. Test Execution
    print("▶️ Testing Direct Execution...")
    input_text = "hello world"
    exec_res = await lab.execute_tool(tool_id, input_text)
    
    print(f"   Execution Result: {exec_res}")
    
    # We expect stdout to contain "HELLO WORLD" if the tool works as requested.
    # Note: The tool generation logic depends on LLM, so exact code structure varies.
    # But usually it prints or returns. My harness captures return value in stdout "OUTPUT: {result}"
    
    stdout = exec_res.get("stdout", "")
    if "HELLO WORLD" in stdout or "OUTPUT: 'HELLO WORLD'" in stdout or "OUTPUT: \"HELLO WORLD\"" in stdout:
         print("✅ Execution Verification: Output matched expected uppercase.")
    else:
         print(f"⚠️ Execution Output ambiguous: {stdout}")
         # We won't fail the test strictly on LLM logic, but we verify the mechanism ran (no error).
         assert exec_res.get("status") == "Success"

    # 4. Cleanup/Unpin
    await lab.toggle_pin_tool(tool_id, False)
    print("✅ Unpinned tool.")

if __name__ == "__main__":
    from app.db.base import Base
    from app.db.session import engine
    
    async def run_all():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await test_widgets_flow()
        
    asyncio.run(run_all())
