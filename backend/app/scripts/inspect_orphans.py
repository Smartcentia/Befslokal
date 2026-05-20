import asyncio
import os
import sys
from sqlalchemy import select, or_

# Add backend to path
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file))) # .../backend
project_root = os.path.dirname(backend_dir) # .../KNOWME

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Helper to load DB URL matches from .env
def get_database_url():
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip('"').strip("'")
    return os.environ.get("DATABASE_URL")

db_url = get_database_url()
if db_url:
    os.environ["DATABASE_URL"] = db_url

try:
    from app.db.session import SessionLocal
    from app.domains.core.models.property import Property
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.unit import Unit
    from app.domains.core.models.party import Party
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
except ImportError:
    from backend.app.db.session import SessionLocal
    from backend.app.domains.core.models.property import Property
    from backend.app.domains.core.models.contract import Contract
    from backend.app.domains.core.models.unit import Unit
    from backend.app.domains.core.models.party import Party
    from backend.app.domains.hms.models.risk import RiskAssessment
    from backend.app.domains.hms.models.internal_control import InternalControlCase

async def inspect_orphans():
    print("Inspecting potential orphan properties...")
    async with SessionLocal() as db:
        # Fetch properties that have 'financials' but might be missing address/name
        stmt = select(Property)
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        orphans_found = 0
        for p in props:
            ext = p.external_data or {}
            
            # Check for specific orphans we saw in logs
            # 'Stenliveien 7'
            target_dim2 = "Stenliveien 7"
            
            dim2 = ext.get('Dim 2(T)') or ext.get('Dim 2')
            if not dim2:
                # check inside financials
                fin = ext.get('financials', {})
                if isinstance(fin, dict):
                    dim2 = fin.get('dim_2_original')
            
            if dim2 and target_dim2.lower() in str(dim2).lower():
                print(f"\n--- Found Orphan Candidate ---")
                print(f"ID: {p.property_id}")
                print(f"Name: {p.name}")
                print(f"Address: {p.address}")
                print(f"External Data Keys: {list(ext.keys())}")
                print(f"Dim 2 Value: {dim2}")
                orphans_found += 1
                
        print(f"\nTotal potential orphans inspected: {orphans_found}")

if __name__ == "__main__":
    asyncio.run(inspect_orphans())
