import asyncio
import os
import sys
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.external.api_clients.miljodir_client import MiljodirClient

async def main():
    print("--- Verifying Vannmiljø API Integration ---")
    
    client = MiljodirClient()
    print(f"Client Base URL: {client.base_url}")
    
    # Coordinates for Sognsvann, Oslo (Known water feature)
    lat = 59.971
    lon = 10.725
    print(f"Testing location: {lat}, {lon} (Sognsvann)")

    print("\n1. Fetching Water Features (GetWaterLocations)...")
    water = await client.fetch_water_features(lat, lon, radius_km=1.0)
    print(f"Result count: {len(water)}")
    if water:
        print("Sample Data:", json.dumps(water[0], indent=2))
    else:
        print("No water features found (or API error).")

    print("\n2. Fetching Species Registrations (GetRegistrations)...")
    species = await client.fetch_species_registrations(lat, lon, radius_km=1.0)
    print(f"Result count: {len(species)}")
    if species:
        print("Sample Data:", json.dumps(species[0], indent=2))

    print("\n3. Fetching Air Quality (NILU)...")
    air = await client.fetch_air_quality(lat, lon)
    print(f"Result count/length: {len(air) if air else 0}")
    if air:
        sample = air[0] if isinstance(air, list) else air
        print("Sample Data:", json.dumps(sample, indent=2))

    print("\n4. Fetching Contaminated Sites (ArcGIS)...")
    contam = await client.fetch_contaminated_sites(lat, lon)
    print(f"Result count/length: {len(contam) if contam else 0}")
    if contam:
        sample = contam[0] if isinstance(contam, list) else contam
        print("Sample Data:", json.dumps(sample, indent=2))

    print("\n5. Fetching Noise Data (ArcGIS)...")
    noise = await client.fetch_noise_data(lat, lon)
    print(f"Result count/length: {len(noise) if noise else 0}")
    if noise:
        sample = noise[0] if isinstance(noise, list) else noise
        print("Sample Data:", json.dumps(sample, indent=2))
        
    print("\n--- Done ---")

if __name__ == "__main__":
    asyncio.run(main())
