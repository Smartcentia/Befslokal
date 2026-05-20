#!/usr/bin/env python3
"""
Complete geocoding solution for all properties.
Fetches properties from database, geocodes them, and generates SQL updates.
"""

import requests
import time
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "KNOWME Property Management (frank@befs.no)"}
RATE_LIMIT = 1.1  # seconds

# Database project details
PROJECT_ID = "dry-bonus-10076605"
DATABASE_NAME = os.getenv("DATABASE_NAME", "befs")

def geocode_address(address: str, city: str) -> tuple:
    """Geocode using Nominatim API."""
    query = f"{address}, {city}, Norway"
    
    try:
        response = requests.get(
            NOMINATIM_API,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "no"},
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        if data and len(data) > 0:
            result = data[0]
            lat = float(result["lat"])
            lon = float(result["lon"])
            return lat, lon, "OK"
        
        return None, None, "NO_RESULTS"
        
    except Exception as e:
        return None, None, f"ERROR: {str(e)[:30]}"


def main():
    print("="*80)
    print("GEOCODING ALL PROPERTIES")
    print("="*80)
    print()
    
    # Read properties from stdin (JSON array)
    properties_json = sys.stdin.read()
    properties = json.loads(properties_json)
    
    total = len(properties)
    print(f"Processing {total} properties...")
    print(f"Estimated time: ~{int(total * RATE_LIMIT / 60)} minutes")
    print()
    
    sql_updates = []
    failed_properties = []
    success_count = 0
    
    for i, prop in enumerate(properties, 1):
        prop_id = prop["property_id"]
        name = prop.get("name", "Unknown")
        address = prop.get("address")
        city = prop.get("city")
        
        if not address or not city:
            failed_properties.append({
                "id": prop_id,
                "name": name,
                "reason": "Missing address or city"
            })
            print(f"[{i}/{total}] ⚠️  {name}: Missing data")
            continue
        
        print(f"[{i}/{total}] {address}, {city}...", end=" ")
        
        lat, lon, status = geocode_address(address, city)
        
        if lat and lon:
            sql_updates.append(
                f"UPDATE properties SET latitude = {lat}, longitude = {lon} "
                f"WHERE property_id = '{prop_id}';"
            )
            print(f"✅ {lat:.6f}, {lon:.6f}")
            success_count += 1
        else:
            failed_properties.append({
                "id": prop_id,
                "name": name,
                "address": address,
                "city": city,
                "status": status
            })
            print(f"❌ {status}")
        
        # Rate limiting
        if i < total:
            time.sleep(RATE_LIMIT)
        
        # Save progress every 20 properties
        if i % 20 == 0:
            with open("/tmp/geocode_progress.sql", "w") as f:
                f.write(f"-- Progress: {i}/{total} ({i/total*100:.1f}%)\\n")
                f.write(f"-- Success: {success_count}, Failed: {len(failed_properties)}\\n\\n")
                f.write("\\n".join(sql_updates))
            print(f"   💾 Progress saved ({i}/{total})")
    
    # Final output
    print()
    print("="*80)
    print("GEOCODING COMPLETE")
    print("="*80)
    print(f"Total: {total}")
    print(f"Success: {success_count} ({success_count/total*100:.1f}%)")
    print(f"Failed: {len(failed_properties)}")
    print()
    
    # Write SQL file
    output_file = "/tmp/geocode_all_updates.sql"
    with open(output_file, "w") as f:
        f.write(f"-- Geocoding Updates for BEFS Properties\\n")
        f.write(f"-- Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"-- Total: {total}, Success: {success_count}, Failed: {len(failed_properties)}\\n")
        f.write(f"-- Success rate: {success_count/total*100:.1f}%\\n\\n")
        f.write("\\n".join(sql_updates))
        f.write("\\n\\n-- Failed properties:\\n")
        for fail in failed_properties:
            f.write(f"-- {fail.get('name', fail['id'])}: {fail.get('status', fail.get('reason'))}\\n")
    
    print(f"SQL updates written to: {output_file}")
    print(f"\\nTo apply updates, run:")
    print(f"  Use MCP API to execute the SQL statements")
    
    # Also write failed properties as JSON
    with open("/tmp/geocode_failed.json", "w") as f:
        json.dump(failed_properties, f, indent=2)
    
    print(f"\\nFailed properties saved to: /tmp/geocode_failed.json")


if __name__ == "__main__":
    main()
