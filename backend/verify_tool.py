import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent
sys.path.append(str(backend_path))
load_dotenv(backend_path / ".env")

try:
    from app.services.tools.contract_tools import search_contracts
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

async def main():
    import sys
    query = "Hva er oppsigelsestiden for leietaker?"
    if len(sys.argv) > 1:
        query = sys.argv[1]
    
    print(f"Testing tool 'search_contracts' with query: '{query}'")
    
    try:
        result = await search_contracts(query)
        print("\n--- Tool Output ---")
        print(result)
        print("-------------------")
    except Exception as e:
        print(f"Tool Execution Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
