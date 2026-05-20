#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, '/Volumes/KINGSTON/BEFS3/KNOWME/backend')

from app.services.external.osm_client import OSMClient

async def test_osm():
    client = OSMClient()
    
    print("Testing OpenStreetMap Overpass API...")
    print()
    
    # Test hospitals
    print("1. Sykehus i Oslo sentrum (2km radius):")
    hospitals = await client.get_nearby_places(59.9139, 10.7522, radius=2000, service_type="hospital")
    print(f"   Funnet: {len(hospitals)}")
    for h in hospitals[:3]:
        print(f"   - {h['name']}: {h['distance_meters']}m")
    print()
    
    # Test pharmacies
    print("2. Apotek i Oslo sentrum (1km radius):")
    pharmacies = await client.get_nearby_places(59.9139, 10.7522, radius=1000, service_type="pharmacy")
    print(f"   Funnet: {len(pharmacies)}")
    if pharmacies:
        print(f"   Nærmeste: {pharmacies[0]['name']} - {pharmacies[0]['distance_meters']}m")
    print()
    
    # Test schools
    print("3. Skoler i Oslo sentrum (1.5km radius):")
    schools = await client.get_nearby_places(59.9139, 10.7522, radius=1500, service_type="school")
    print(f"   Funnet: {len(schools)}")
    print()
    
    print("✓ OpenStreetMap fungerer! GRATIS og utmerket data!")

if __name__ == "__main__":
    asyncio.run(test_osm())
