
import asyncio
import httpx

async def main():
    # Pattern: https://api01.nve.no/hydrology/forecast/landslide/{version}/api/Warning/County/03
    base_template = "https://api01.nve.no/hydrology/forecast/landslide/{}/api/Warning/County/03"
    
    versions = [
        "v1.0.0", "v1.0.1", "v1.0.2", "v1.0.3", "v1.0.4", 
        "v1.0.5", "v1.0.6", "v1.0.7", "v1.0.8", "v1.0.9", "v1.0.10",
        "v1.1.0", "v2.0.0"
    ]
    
    async with httpx.AsyncClient() as client:
        for v in versions:
            url = base_template.format(v)
            print(f"Testing {url}...")
            try:
                resp = await client.get(url, timeout=5)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"SUCCESS! Found version: {v}")
                    break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
