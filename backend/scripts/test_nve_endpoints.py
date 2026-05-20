
import asyncio
import httpx

async def main():
    base = "https://gts.nve.no/api"
    lat, lon = "59.91", "10.75" # Oslo
    # UTM 33N approx
    x, y = "262000", "6650000"
    params = f"?x={x}&y={y}&startdato=2024-01-01&sluttdato=2024-01-02&temalag=rr&format=json"
    
    endpoints = [
        f"/GridTimeSeries{params}",
        f"/gridtimeserie{params}"
    ]
    
    async with httpx.AsyncClient() as client:
        for ep in endpoints:
            url = f"{base}{ep}"
            print(f"Testing {url}...")
            try:
                resp = await client.get(url, timeout=10)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"SUCCESS! Response: {resp.text[:100]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
