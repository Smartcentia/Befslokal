
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.external.brreg_service import BrregService

async def verify_enhet_lookup(org_nr="986128433"): # Bufdir as example
    print(f"--- Verifying Public BRREG Lookup for {org_nr} ---")
    
    result = await BrregService.get_enhet(org_nr)
    
    if result:
        print("✅ Lookup Successful!")
        print(f"Name: {result.get('name')}")
        print(f"Address: {result.get('address')}")
        print(f"Source: {result.get('source')}")
    else:
        print("❌ Lookup Failed.")

if __name__ == "__main__":
    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_enhet_lookup())
