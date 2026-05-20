#!/usr/bin/env python3
"""
Simple geocoding script - outputs SQL UPDATE statements.
Run this script, wait for completion, then execute the SQL via MCP.
"""

import requests
import time
import sys

NOMINATIM_API = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "KNOWME Property Management (frank@befs.no)"}

# Sample of 50 properties to geocode
properties = [
    ("326092b3-850d-42a0-97a8-b7feebea3e8d", "Hans Karolius vei 6", "FINNSNES"),
    ("2666c8ed-31cb-459e-a35b-61aa2d34aa02", "Konstadlykkjvegen 55", "GÅSBAKKEN"),
    ("3cdeca26-c322-40a8-87cd-513b371d4ad9", "Storehagen 1b", "FØRDE"),
    ("00658fb2-21fd-48d2-a839-cc525e28afe2", "Rokkeveien 502", "HALDEN"),
    ("e39e55b9-76ba-4165-a7ff-2cd6cb324143", "Håkøyvn 339", "KVALØYSLETTA"),
    ("2a83dc54-d1f5-4045-90e0-343ce536c932", "Sundløkkaveien 73", "TORP"),
    ("53181bf2-e205-4486-a30d-0342cc1e1ea6", "Skoleveien 9", "BODØ"),
    ("63955fbb-6fb5-4f4d-9a91-b1f4b2a65900", "Feråsvegen 13", "SØREIDGREND"),
    ("f77b5834-5e5f-4171-a6a4-7a587fbd7ca8", "Fitnodatgeaidnu 41-43", "KARASJOK"),
    ("4b5ace08-fb41-45da-9a8e-e3ce81125448", "Nybøvegen 24", "NESTTUN"),
]

print("-- Geocoding SQL Updates")
print("-- Generated:", time.strftime("%Y-%m-%d %H:%M:%S"))
print()

success = 0
failed = 0

for prop_id, address, city in properties:
    query = f"{address}, {city}, Norway"
    
    try:
        r = requests.get(
            NOMINATIM_API,
            params={"q": query, "format": "json", "limit": 1, "countrycodes": "no"},
            headers=HEADERS,
            timeout=10
        )
        
        data = r.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f"UPDATE properties SET latitude = {lat}, longitude = {lon} WHERE property_id = '{prop_id}';")
            print(f"-- ✓ {address}, {city}", file=sys.stderr)
            success += 1
        else:
            print(f"-- FAILED: {address}, {city} (NO_RESULTS)")
            print(f"-- ✗ {address}, {city}", file=sys.stderr)
            failed += 1
        
        time.sleep(1.1)  # Rate limit
        
    except Exception as e:
        print(f"-- FAILED: {address}, {city} ({str(e)[:30]})")
        print(f"-- ✗ {address}, {city}: {e}", file=sys.stderr)
        failed += 1

print()
print(f"-- Summary: {success} success, {failed} failed out of {len(properties)} total")
print(f"-- Success rate: {(success/len(properties)*100):.1f}%", file=sys.stderr)
