import sys
import os
import asyncio
import re
from sqlalchemy import select, update
from dotenv import load_dotenv

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(BACKEND_DIR)

# Load environment variables
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Full model set for SQLAlchemy relationship resolution
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.core.models.center import Center
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.models.file_meta import FileMeta
from app.domains.core.models.user import User
from app.domains.core.models.audit import AuditLog

_MISSING_IDS = {"", "nan", "none", "null"}
def _normalize_id(val):
    if val is None: return None
    s = str(val).strip()
    if not s or s.lower() in _MISSING_IDS: return None
    
    # Normalize whitespace
    s = s.replace("\u00A0", " ").strip()
    
    # Remove .0 suffix if it's a whole number
    if re.fullmatch(r"[-+]?\d+\.0", s):
        return s.rsplit('.0', 1)[0]
    
    # If pure digits, return as is
    if re.fullmatch(r"\d+", s):
        return s
    
    return s

async def scrub_ids():
    print("Connecting to database for ID normalization...")
    async with SessionLocal() as db:
        # Fetch all properties that have IDs
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        print(f"Checking {len(properties)} properties for ID anomalies...")
        updated_count = 0
        
        for prop in properties:
            needs_update = False
            
            clean_lok = _normalize_id(prop.lokalisering_id)
            if clean_lok != prop.lokalisering_id:
                print(f"  - Normalizing Lokasjonskode: {prop.lokalisering_id} -> {clean_lok} (Prop: {prop.name})")
                prop.lokalisering_id = clean_lok
                needs_update = True
                
            clean_erp = _normalize_id(prop.unit_id_erp)
            if clean_erp != prop.unit_id_erp:
                print(f"  - Normalizing EnhetID_ERP: {prop.unit_id_erp} -> {clean_erp}")
                prop.unit_id_erp = clean_erp
                needs_update = True
                
            if needs_update:
                updated_count += 1
        
        if updated_count > 0:
            print(f"\nFinalizing {updated_count} updates...")
            await db.commit()
            print("Database cleanup completed successfully.")
        else:
            print("\nNo normalization needed. All IDs are already clean.")

if __name__ == "__main__":
    asyncio.run(scrub_ids())
