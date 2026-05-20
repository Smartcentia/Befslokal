import asyncio
import sys
import os
import time
import httpx
from typing import List, Dict, Any, Callable
from dataclasses import dataclass


# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import clients
# Note: We import inside functions or try-except blocks where possible to avoid crashing on missing deps
# But since this is checking the backend, we assume deps are installed.

@dataclass
class CheckResult:
    service: str
    function: str
    status: str  # OK, FAIL, SKIPPED
    latency_ms: int
    message: str = ""

results: List[CheckResult] = []


async def check_kartverket():
    from app.services.external.api_clients.kartverket_client import KartverketClient
    from app.core.config import settings
    # Kartverket might not need key, but pass if we have it
    client = KartverketClient(api_key=settings.KARTVERKET_API_KEY)
    start = time.perf_counter()
    try:
        # Test 1: Get Kommune (Oslo coords)
        # 59.9139, 10.7522
        data = await client.get_kommune_from_point(59.9139, 10.7522)
        elapsed = int((time.perf_counter() - start) * 1000)
        
        if data.get("kommunenummer") == "0301": # Oslo
            results.append(CheckResult("Kartverket", "KommuneInfo (Oslo)", "OK", elapsed, f"Found {data.get('kommunenavn')}"))
        else:
            results.append(CheckResult("Kartverket", "KommuneInfo (Oslo)", "FAIL", elapsed, f"Unexpected data: {data}"))
            
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("Kartverket", "KommuneInfo (Oslo)", "FAIL", elapsed, str(e)))

    start = time.perf_counter()
    try:
        # Test 2: Search Address
        addr = await client.search_address("Storgata 1")
        elapsed = int((time.perf_counter() - start) * 1000)
        if addr and addr.get("latitude"):
             results.append(CheckResult("Kartverket", "Address Search", "OK", elapsed, f"Found coords: {addr}"))
        else:
             results.append(CheckResult("Kartverket", "Address Search", "FAIL", elapsed, "No results found"))
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("Kartverket", "Address Search", "FAIL", elapsed, str(e)))

async def check_frost():
    from app.services.external.api_clients.frost_client import FrostClient
    from app.core.config import settings
    
    # Frost ID should be in settings now
    client_id = settings.FROST_CLIENT_ID
    
    start = time.perf_counter()
    if not client_id:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("Frost API", "Init", "SKIPPED", elapsed, "No FROST_CLIENT_ID configured in settings"))
        return

    client = FrostClient(client_id=client_id)
    try:
        station = await client.find_nearest_station(59.9139, 10.7522)
        elapsed = int((time.perf_counter() - start) * 1000)
        if station.get("station_id"):
             results.append(CheckResult("Frost API", "Nearest Station", "OK", elapsed, f"Found {station.get('name')} ({station['station_id']})"))
        else:
             results.append(CheckResult("Frost API", "Nearest Station", "FAIL", elapsed, f"No station found. Response: {station}"))
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("Frost API", "Nearest Station", "FAIL", elapsed, str(e)))

async def check_nve():
    from app.services.external.api_clients.nve_client import NVEClient
    from app.core.config import settings
    
    # Inject API Key from settings
    api_key = settings.NVE_API_KEY
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key and len(api_key) > 8 else "None"
    
    # Note: NVEClient uses X-API-Key header
    client = NVEClient(api_key=api_key)
    
    start = time.perf_counter()
    try:
        if not api_key:
             results.append(CheckResult("NVE HydAPI", "Config", "WARN", 0, "No NVE_API_KEY in settings"))

        stations = await client.fetch_nearby_stations(59.9139, 10.7522)
        elapsed = int((time.perf_counter() - start) * 1000)
        if hasattr(stations, "__iter__"):
            results.append(CheckResult("NVE HydAPI", "Nearby Stations", "OK", elapsed, f"Found {len(stations)} stations (Key: {masked_key})"))
        else:
             results.append(CheckResult("NVE HydAPI", "Nearby Stations", "FAIL", elapsed, f"Unexpected response type: {type(stations)}"))
    except Exception as e:
         elapsed = int((time.perf_counter() - start) * 1000)
         results.append(CheckResult("NVE HydAPI", "Nearby Stations", "FAIL", elapsed, f"Error (Key: {masked_key}): {str(e)}"))
    
    start = time.perf_counter()
    try:    
        # Flood Forecast 
        # Note: County 03 for Oslo.
        forecast = await client.fetch_flood_forecast(county_code="03")
        elapsed = int((time.perf_counter() - start) * 1000)
        if forecast and not forecast.get("error"):
             items = forecast.get("warnings", [])
             results.append(CheckResult("NVE Flood", "Forecast (Oslo)", "OK", elapsed, f"Found {len(items)} warnings"))
        else:
             results.append(CheckResult("NVE Flood", "Forecast (Oslo)", "FAIL", elapsed, f"Response: {forecast}"))
    except Exception as e:
         elapsed = int((time.perf_counter() - start) * 1000)
         results.append(CheckResult("NVE Flood", "Forecast (Oslo)", "FAIL", elapsed, str(e)))

    start = time.perf_counter()
    try:
        # Grid Time Series (GTS)
        # Test coords: Oslo area approx UTM33N X=262000, Y=6650000
        # Dates: 2024-01-01 to 2024-01-02
        gts = await client.fetch_grid_time_series(262000, 6650000, "2024-01-01", "2024-01-02")
        elapsed = int((time.perf_counter() - start) * 1000)
        if gts and not gts.get("error") and "Data" in gts:
             data_points = gts.get("Data", [])
             results.append(CheckResult("NVE GTS", "GridTimeSeries", "OK", elapsed, f"Found {len(data_points)} data points (Precip)"))
        else:
             results.append(CheckResult("NVE GTS", "GridTimeSeries", "FAIL", elapsed, f"Response: {gts}"))
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("NVE GTS", "GridTimeSeries", "FAIL", elapsed, str(e)))

    start = time.perf_counter()
    try:
        # Landslide Forecast (Jordskred)
        landslide = await client.fetch_landslide_forecast(59.91, 10.75) # Oslo coords
        elapsed = int((time.perf_counter() - start) * 1000)
        if landslide and not landslide.get("error"):
            items = landslide.get("warnings", [])
            results.append(CheckResult("NVE Landslide", "Forecast (Oslo)", "OK", elapsed, f"Found {len(items)} warnings"))
        else:
             results.append(CheckResult("NVE Landslide", "Forecast (Oslo)", "FAIL", elapsed, f"Response: {landslide}"))
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("NVE Landslide", "Forecast (Oslo)", "FAIL", elapsed, str(e)))

async def check_regobs_api(results: List[CheckResult]):
    from app.services.external.api_clients.regobs_client import RegObsClient
    start = time.perf_counter()
    try:
        client = RegObsClient()
        # Test near Finse or a mountain area where obs likely exist, OR just Oslo
        # Oslo: 59.91, 10.75
        obs_data = await client.fetch_observations(59.91, 10.75, radius=10000)
        elapsed = int((time.perf_counter() - start) * 1000)
        
        if obs_data and not obs_data.get("error"):
            count = obs_data.get("count", 0)
            results.append(CheckResult("RegObs (Test)", "Observations", "OK", elapsed, f"Found {count} recs"))
        else:
            results.append(CheckResult("RegObs (Test)", "Observations", "FAIL", elapsed, f"Response: {obs_data}"))
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("RegObs (Test)", "Observations", "FAIL", elapsed, str(e)))


async def check_mapbox():
    # Mapbox is removed.
    results.append(CheckResult("Mapbox", "Nearby Search", "SKIPPED", 0, "Mapbox removed in favor of Kartverket/Leaflet"))

async def check_miljodir():
    from app.core.config import settings
    start = time.perf_counter()
    url = "https://api.miljodirektoratet.no"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            elapsed = int((time.perf_counter() - start) * 1000)
            if resp.status_code < 500:
                results.append(CheckResult("Miljødirektoratet", "Base URL Ping", "OK", elapsed, f"Status {resp.status_code}"))
            else:
                 results.append(CheckResult("Miljødirektoratet", "Base URL Ping", "FAIL", elapsed, f"Status {resp.status_code}"))
    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        results.append(CheckResult("Miljødirektoratet", "Base URL Ping", "FAIL", elapsed, str(e)))


async def main():
    print("Starting External API Checks...")
    
    await check_kartverket()
    await check_frost()
    await check_nve()
    await check_regobs_api(results)
    # await check_mapbox()
    await check_miljodir()
    

    # Print Report
    print(f"\n{'SERVICE':<20} | {'FUNCTION':<25} | {'STATUS':<8} | {'TIME (ms)':<10} | {'MESSAGE'}")
    print("-" * 100)
    for r in results:
        status_disp = r.status
        if r.status == "OK":
            status_disp = f"\033[92m{r.status}\033[0m"
        elif r.status == "FAIL":
            status_disp = f"\033[91m{r.status}\033[0m"
        elif r.status == "SKIPPED":
            status_disp = f"\033[93m{r.status}\033[0m"
        elif r.status == "WARN":
            status_disp = f"\033[93m{r.status}\033[0m" # Yellow for warn too

        print(f"{r.service:<20} | {r.function:<25} | {status_disp:<17} | {r.latency_ms:<10} | {r.message}")


    print("\n--- .env File Analysis ---")
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
            found_keys = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=')[0].strip()
                    if any(x in key.upper() for x in ["NVE", "FROST", "KARTVERKET", "SEARCH", "API_KEY"]):
                        found_keys.append(key)
            
            if found_keys:
                print(f"Keys found in .env file: {', '.join(found_keys)}")
            else:
                print("No relevant keys found in .env file.")
    except Exception as e:
        print(f"Could not read .env file: {e}")

if __name__ == "__main__":

    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    asyncio.run(main())
