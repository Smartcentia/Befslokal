import asyncio
import httpx
from app.services.mcp_service import mcp_service
from app.core.config import settings

async def verify_mcp():
    print(f"--- Verifying MCP Integration ---")
    print(f"Gateway URL: {settings.DOCKER_MCP_GATEWAY_URL}")
    print(f"Use Local AI: {settings.USE_LOCAL_AI}")
    print(f"Local Model: {settings.LOCAL_MODEL_NAME}")
    
    # Test 1: List Tools
    print("\nTesting list_tools()...")
    try:
        tools = await mcp_service.list_tools()
        print(f"Found {len(tools)} tools.")
        for tool in tools[:3]:
            print(f"- {tool.get('name')}: {tool.get('description', 'No description')[:50]}...")
    except Exception as e:
        print(f"Error listing tools: {e}")

    # Test 2: AI Client Initialization
    print("\nTesting AI Client Initialization...")
    from app.services.ki_kollega.service import KIKollegaService
    ki_service = KIKollegaService()
    print(f"KI Service Client: {'Initialized' if ki_service.client else 'Failed'}")
    print(f"KI Service Model: {ki_service.model}")

    await mcp_service.close()

if __name__ == "__main__":
    asyncio.run(verify_mcp())
