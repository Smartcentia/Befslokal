import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../"))

from app.db.session import SessionLocal
from app.services.data_health_service import data_health_service

async def verify_data():
    print("--- BEFS Data Integrity Verification ---")
    
    async with SessionLocal() as db:
        # 1. Connectivity
        from app.core.config import settings
        print(f"Connecting to: {settings.POSTGRES_SERVER} ({settings.POSTGRES_DB})")
        
        connected = await data_health_service.check_db_connection(db)
        if connected:
            print("✅ Database Connection: ONLINE")
        else:
            print("❌ Database Connection: OFFLINE")
            print(f"   Ensure Postgres is running at {settings.POSTGRES_SERVER}:5432")
            # We don't exit here anymore to allow printing empty stats if desired, 
            # but usually offline means we can't get stats.
            print("   Cannot proceed with volume checks.")
            return
            
        # 2. Stats
        print("\n--- Volume Metrics ---")
        stats = await data_health_service.get_data_stats(db)
        if stats.get("status") == "error":
            print(f"❌ Error fetching stats: {stats.get('error_message')}")
        else:
            print(f"Properties:     {stats.get('properties_count')}")
            print(f"Contracts:      {stats.get('contracts_count')}")
            print(f"Users:          {stats.get('users_count')}")
            print(f"Risks:          {stats.get('risks_count')}")
            print(f"IoT Readings:   {stats.get('iot_readings_count')}")

            # Simple heuristic
            if stats.get('properties_count') == 0:
                print("\n⚠️  WARNING: Database appears empty. Run 'seed.py'?")
            else:
                print("\n✅ Dataset appears populated.")

        # 3. Integrity
        print("\n--- Integrity Report ---")
        integrity = await data_health_service.check_integrity(db)
        issues = integrity.get("issues", [])
        
        if not issues:
            print("✅ No integrity issues found.")
        else:
            print(f"⚠️  Found {len(issues)} potential issues:")
            for issue in issues:
                print(f" - {issue}")

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(verify_data())
    except Exception as e:
        print(f"Fatal Error: {e}")
