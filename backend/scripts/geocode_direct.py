#!/usr/bin/env python3
import os
import sys
import time
import requests
import psycopg2
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manual fallback for .env loading
    try:
        with open('.env') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1)
                    if k not in os.environ:
                        os.environ[k] = v
    except:
        pass

# Get database URL and fix it for psycopg2
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

# Remove asyncpg driver if present
db_url = db_url.replace("+asyncpg", "")

# Fix sslmode if it's missing a value
if db_url.endswith("sslmode"):
    db_url += "=require"
elif "sslmode" not in db_url:
    if "?" in db_url:
        db_url += "&sslmode=require"
    else:
        db_url += "?sslmode=require"

print(f"Connecting to database...", flush=True)

try:
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Get properties to geocode
    cur.execute("SELECT property_id, address, city FROM properties WHERE latitude IS NULL OR longitude IS NULL")
    rows = cur.fetchall()
    total = len(rows)
    print(f"Found {total} properties to geocode.", flush=True)
    
    if total == 0:
        print("✅ All properties already geocoded.", flush=True)
        sys.exit(0)
        
    for i, (pid, addr, city) in enumerate(rows, 1):
        if not addr or not city:
            print(f"[{i}/{total}] ⚠️  Skipping: missing address/city", flush=True)
            continue
            
        print(f"[{i}/{total}] Geocoding {addr}, {city}...", end=" ", flush=True)
        
        try:
            # Nominatim API (1 req/sec limit)
            headers = {'User-Agent': 'KNOWME Property Manager'}
            q = f"{addr}, {city}, Norway"
            r = requests.get("https://nominatim.openstreetmap.org/search", 
                           params={'q': q, 'format': 'json', 'limit': 1},
                           headers=headers, timeout=10)
            
            data = r.json()
            if data:
                lat = data[0]['lat']
                lon = data[0]['lon']
                
                cur.execute("UPDATE properties SET latitude = %s, longitude = %s WHERE property_id = %s", (lat, lon, pid))
                print(f"✅ {lat}, {lon}", flush=True)
            else:
                print("❌ No results", flush=True)
                
        except Exception as e:
            print(f"❌ Error: {e}", flush=True)
            
        # Respect rate limit
        time.sleep(1.1)

    print("\n✅ Geocoding complete!", flush=True)
    conn.close()

except Exception as e:
    print(f"\n❌ Fatal error: {e}", flush=True)
    sys.exit(1)
