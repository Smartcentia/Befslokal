import asyncio
import sys
import os
import httpx
import json

# Ensure app is in pythonpath
sys.path.append(os.getcwd())

async def check_kunngjoringer():
    org_nr = "923609016" # Equinor (Likely NOT bankrupt)
    # Generic bankrupt company? Hard to guess active one.
    
    # Konkursregisteret API
    # Docs: https://data.brreg.no/konkurs/
    # Endpoint: https://data.brreg.no/konkurs/enhet?organisasjonsnummer={orgnr}
    
    urls = [
        f"https://data.brreg.no/konkurs/enhet?organisasjonsnummer={org_nr}",
    ]
    
    headers = {
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for url in urls:
            print(f"--- Probing {url} ---")
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                print(f"Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                
                if response.status_code == 200:
                    print("JSON FOUND!")
                    print(json.dumps(response.json(), indent=2))
                elif response.status_code == 404:
                    print("Not found (Expected for non-bankrupt company).")
                else:
                    print(f"Error: {response.text}")
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(check_kunngjoringer())
