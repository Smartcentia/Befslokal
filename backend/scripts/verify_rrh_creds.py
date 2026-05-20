
import asyncio
import httpx
import os
import sys

async def verify_credentials(username, password, org_nr="986128433"): # Bufdir's org nr
    url = f"https://gw.brreg.no/felles/rr/api/v1/rettighetshavere/{org_nr}"
    print(f"Testing access to {url} with user '{username}'...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                auth=(username, password),
                timeout=10.0
            )
            
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Success! Authentication worked.")
            print("Response:", response.text[:200])
        elif response.status_code == 401:
            print("❌ Authentication Failed (401 Unauthorized).")
        elif response.status_code == 403:
             print("❌ Access Forbidden (403). Credentials might be valid but missing scopes.")
        else:
            print(f"⚠️ Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_rrh_creds.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_credentials(username, password))
