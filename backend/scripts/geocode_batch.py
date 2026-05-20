#!/usr/bin/env python3
"""
Batch geocode properties using Nominatim and generate SQL UPDATE statements.
Processes properties in chunks to allow for progress monitoring.
"""

import requests
import time
import json
import sys
import os

NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "KNOWME Property Management System (frank@befs.no)"}
BATCH_SIZE = 20
RATE_LIMIT = 1.1  # seconds between requests


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


def process_batch(properties, batch_num, total_batches):
    """Process a batch of properties."""
    updates = []
    failed = []
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"BATCH {batch_num}/{total_batches} - Processing {len(properties)} properties", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    for i, prop in enumerate(properties, 1):
        prop_id = prop["property_id"]
        name = prop.get("name", "Unknown")
        address = prop.get("address")
        city = prop.get("city")
        
        if not address or not city:
            failed.append({"id": prop_id, "name": name, "reason": "Missing data"})
            print(f"[{i}/{len(properties)}] ⚠️  {name}: Missing data", file=sys.stderr)
            continue
        
        print(f"[{i}/{len(properties)}] {address}, {city}", file=sys.stderr)
        
        lat, lon, status = geocode_address(address, city)
        
        if lat and lon:
            updates.append({
                "property_id": prop_id,
                "latitude": lat,
                "longitude": lon
            })
            print(f"   ✅ {lat:.6f}, {lon:.6f}", file=sys.stderr)
        else:
            failed.append({"id": prop_id, "name": name, "address": address, "city": city, "status": status})
            print(f"   ❌ {status}", file=sys.stderr)
        
        # Rate limiting
        if i < len(properties):
            time.sleep(RATE_LIMIT)
    
    return updates, failed


def main():
    # Read properties from stdin
    properties_json = sys.stdin.read()
    properties = json.loads(properties_json)
    
    total_properties = len(properties)
    total_batches = (total_properties + BATCH_SIZE - 1) // BATCH_SIZE
    
    all_updates = []
    all_failed = []
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"GEOCODING {total_properties} PROPERTIES", file=sys.stderr)
    print(f"Batch size: {BATCH_SIZE}", file=sys.stderr)
    print(f"Total batches: {total_batches}", file=sys.stderr)
    print(f"Estimated time: ~{int(total_properties * RATE_LIMIT / 60)} minutes", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    # Process in batches
    for batch_num in range(total_batches):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min((batch_num + 1) * BATCH_SIZE, total_properties)
        batch = properties[start_idx:end_idx]
        
        updates, failed = process_batch(batch, batch_num + 1, total_batches)
        all_updates.extend(updates)
        all_failed.extend(failed)
        
        # Save intermediate results
        intermediate = {
            "updates": all_updates,
            "failed": all_failed,
            "summary": {
                "processed": end_idx,
                "total": total_properties,
                "success": len(all_updates),
                "failed": len(all_failed),
                "success_rate": f"{(len(all_updates)/end_idx*100):.1f}%"
            }
        }
        
        with open(f"/tmp/geocode_progress_batch{batch_num+1}.json", "w") as f:
            json.dumps(intermediate, f, indent=2)
    
    # Final output
    result = {
        "updates": all_updates,
        "failed": all_failed,
        "summary": {
            "total": total_properties,
            "success": len(all_updates),
            "failed": len(all_failed),
            "success_rate": f"{(len(all_updates)/total_properties*100):.1f}%"
        }
    }
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
