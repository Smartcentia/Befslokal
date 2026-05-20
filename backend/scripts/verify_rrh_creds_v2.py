
import asyncio
import httpx
import sys

async def verify_credentials_v2(username, password, org_nr="986128433"):
    # Potential endpoints based on search results
    endpoints = [
        f"https://rrh.brreg.no/api/oppslag/rettighetshavere/{org_nr}",
        f"https://rrh.brreg.no/api/oppslag/enhet/{org_nr}/rettighetshavere",
        "https://rrh.brreg.no/api/oppslag",
        # Try simplified paths just in case
        f"https://rrh.brreg.no/api/rettighetshavere/{org_nr}"
    ]

    print(f"Testing access with user '{username}'...")
    
    async with httpx.AsyncClient() as client:
        for url in endpoints:
            print(f"\nTesting URL: {url}")
            try:
                response = await client.get(
                    url, 
                    auth=(username, password),
                    timeout=10.0
                )
                print(f"Status Code: {response.status_code}")
                if response.status_code == 200:
                    print("✅ Success! Found working endpoint.")
                    print("Response preview:", response.text[:200])
                    return
                elif response.status_code in (401, 403):
                    print("❌ Auth failed or forbidden. Connection successful, but credentials/scope rejected.")
                elif response.status_code == 404:
                    print("⚠️ End point not found (404).")
                else:
                    print(f"⚠️ Unexpected status: {response.status_code}")
            except Exception as e:
                print(f"❌ Connection/Request Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_rrh_creds_v2.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    if sys.platform == 'win32':
         asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_credentials_v2(username, password))
