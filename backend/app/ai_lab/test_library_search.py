import asyncio
import pytest
from dotenv import load_dotenv
load_dotenv()
from app.ai_lab.main_mvp import AILab

@pytest.mark.asyncio
async def test_library_search():
    lab = AILab()
    await lab.initialize()
    
    # 1. Create a known tool
    print("🧪 Creating Test Tool...")
    create_result = await lab.process_request("Create a tool called 'RentEst' that multiplies area by 200 NOK")
    assert create_result["status"] == "created"
    
    # Wait a moment for indexing (optional, but good practice in async/vector world)
    await asyncio.sleep(1)
    
    # 2. Search for it semantically
    print("🔍 Searching for 'leiepris beregning' (Semantic Search)...")
    search_results = await lab.search_tools("leiepris beregning", limit=3)
    
    print(f"   Found {len(search_results)} results")
    found = False
    for tool in search_results:
        print(f"   - Tool: {tool.name} ({tool.id})")
        
    tool_id = create_result.get("tool_id")
    
    if tool_id == "temp":
        print("⚠️ Tool ID is 'temp'. Creation logs:")
        for log in create_result.get("logs", []):
            print(f"   {log}")
            
    assert tool_id is not None and tool_id != "temp"
    
    # Verify ID is in search matching IDs
    found_ids = [str(t.id) for t in search_results]
    if str(tool_id) in found_ids:
        print("✅ Success: Created tool found via semantic search!")
        found = True
    else:
        print(f"❌ Failure: Tool ID {tool_id} not found in {found_ids}")
        
    assert found

if __name__ == "__main__":
    from app.db.base import Base
    from app.db.session import engine
    
if __name__ == "__main__":
    from app.db.base import Base
    from app.db.session import engine
    
    async def run_all():
        # Ensure tables exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        await test_library_search()

    asyncio.run(run_all())
