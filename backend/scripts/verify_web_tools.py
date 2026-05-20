
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add backend to path and load env
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from app.services.mcp.handler import search_web_tool, fetch_web_content_tool
from app.core.config import settings

async def verify_web_tools():
    print("--- Verifying Web Tools ---")
    
    # 1. Testing Web Search
    print("\n1. Testing Web Search (search_web)...")
    try:
        query = "Bufdir statlige satser barnevern 2024"
        print(f"   Query: '{query}'")
        results = await search_web_tool(query, max_results=3)
        
        if isinstance(results, str) and results.startswith("Error"):
            print(f"   FAILED: {results}")
        elif isinstance(results, list) and len(results) > 0:
            print(f"   SUCCESS: Found {len(results)} results.")
            print(f"   Top result: {results[0]['title']} ({results[0]['href']})")
        else:
            print(f"   WARNING: No results or unexpected format: {results}")
    except Exception as e:
        print(f"   ERROR executing search_web_tool: {e}")

    # 1b. Ekstra søk for å bekrefte treff (mer generelt søk)
    print("\n1b. Ekstra søk (markedsleie kontor Oslo)...")
    try:
        query2 = "markedsleie kontor Oslo"
        print(f"   Query: '{query2}'")
        results2 = await search_web_tool(query2, max_results=3)
        if isinstance(results2, list) and len(results2) > 0:
            print(f"   SUCCESS: {len(results2)} treff.")
            for i, r in enumerate(results2[:2], 1):
                print(f"      {i}. {r.get('title', '')[:55]}...")
                print(f"         {r.get('href', '')[:65]}...")
        else:
            print(f"   Ingen treff (listen var tom eller uventet format).")
    except Exception as e:
        print(f"   ERROR: {e}")

    # 2. Test Fetch Content (No Ingest for safety in test)
    print("\n2. Testing Web Fetch (fetch_web_content)...")
    try:
        # Use a safe, stable URL (e.g., example.com or a government page)
        url = "https://www.example.com" 
        print(f"   Fetching: {url}")
        
        # Test without ingest first to check parsing
        content = await fetch_web_content_tool(url, ingest=False)
        
        if "Source:" in content and "Example Domain" in content:
            print("   SUCCESS: Fetched and parsed content correctly.")
            print(f"   Snippet: {content[:100]}...")
        else:
            print(f"   FAILED/WARNING: Unexpected content content:\n{content[:200]}")
            
    except Exception as e:
        print(f"   ERROR executing fetch_web_content_tool: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_web_tools())
