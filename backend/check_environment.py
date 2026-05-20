#!/usr/bin/env python3
"""Check which environment we're connected to and verify data status."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from sqlalchemy import create_engine, text
import os

def main():
    print("=" * 80)
    print("ENVIRONMENT VERIFICATION")
    print("=" * 80)
    
    # Check database URL
    db_url = settings.DATABASE_URL
    
    # Parse the URL to show details (hide password)
    if '@' in db_url:
        parts = db_url.split('@')
        connection_part = parts[1] if len(parts) > 1 else "unknown"
        user_part = parts[0].split('://')[-1].split(':')[0] if len(parts) > 0 else "unknown"
    else:
        connection_part = "local/unknown"
        user_part = "unknown"
    
    print(f"\n🔌 DATABASE CONNECTION:")
    print(f"   Host: {connection_part}")
    print(f"   User: {user_part}")
    print(f"   Type: {'Cloud PostgreSQL' if 'cloud' in db_url or 'postgres.database' in db_url else 'Local/Other PostgreSQL'}")
    

    
    print("\n" + "=" * 80)
    print("ENVIRONMENT CHECK COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
