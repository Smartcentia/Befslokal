import asyncio
import sys
import os

# Add the backend directory to sys.path so we can import app modules
sys.path.append(os.getcwd())

from app.services.tools.contract_tools import search_contracts

async def main():
    print("--- Starting Debug of search_contracts ---")
    query = "parkering"
    try:
        print(f"Executing search_contracts('{query}')...")
        result = await search_contracts(query)
        print("SUCCESS!")
        print(result)
    except Exception as e:
        print("\n!!! EXCEPTION CAUGHT !!!")
        print(f"Type: {type(e)}")
        print(f"Message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
