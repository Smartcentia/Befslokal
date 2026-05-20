import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.services.mcp.handler import mcp_handler

# Ensure tools are loaded
# Depending on imports in handler.py, might need explicit import here if not auto-loaded
# but we added import to handler.py so it should be fine.

async def test_playwright_tools():
    print("🚀 Testing Playwright MCP Tools...")
    
    tools = mcp_handler.get_tools()
    tool_names = [t.name for t in tools]
    
    if "browser_navigate" not in tool_names:
        print("❌ 'browser_navigate' tool not found!")
        return
        
    print(f"✅ Found {len(tools)} tools registered.")
    
    print("\n🌐 Testing Navigation to example.com...")
    res = await mcp_handler.execute_tool("browser_navigate", {"url": "https://example.com"})
    print(f"Result: {res}")
    
    print("\n📄 Testing Get Content...")
    content = await mcp_handler.execute_tool("browser_get_content", {})
    print(f"Content (first 100 chars): {content[:100]}...")
    
    # print("\n📸 Testing Screenshot...")
    # screenshot_res = await mcp_handler.execute_tool("browser_screenshot", {})
    # print(f"Screenshot Result: {screenshot_res[:50]}...")

    # Cleanup handled by singleton or OS process termination for this test script
    # Real app would keep it open.
    
if __name__ == "__main__":
    asyncio.run(test_playwright_tools())
