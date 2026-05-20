import asyncio
import sys
import os
import httpx
import json

# Ensure app is in pythonpath
sys.path.append(os.getcwd())

# Import Maskinporten Client (Mock check to see if we can get token)
# In this environment, we might not have a real cert, but let's check the client logic.
# Wait, BrregService.get_reelle_rettighetshavere uses MaskinportenClient.
from app.services.auth.maskinporten_client import MaskinportenClient

async def check_losore():
    # Test with a known company 
    org_nr = "923609016" 
    
    print(f"Fetching Løsøre (Mortgages) for {org_nr}...")
    
    # Endpoint guess based on similar APIs
    # https://data.brreg.no/losore/oppslag/rettigheter?organisasjonsnummer={orgnr}
    url = f"https://data.brreg.no/losore/oppslag/rettigheter?organisasjonsnummer={org_nr}"
    
    try:
        # 1. Try generic public access first (unlikely)
        print("--- Attempt 1: Public Access ---")
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                print(resp.json())
                return

        # 2. Try Maskinporten if Public fails
        print("--- Attempt 2: Maskinporten ---")
        token = await MaskinportenClient.get_access_token()
        if not token:
            print("Could not get Maskinporten token (likely missing cert/config in this env).")
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10)
            print(f"Status: {resp.status_code}")
            print(resp.text[:500])

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(check_losore())
