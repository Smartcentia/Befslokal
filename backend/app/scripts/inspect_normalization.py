import sys
import os
import asyncio
import re
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv

# Path setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
sys.path.append(BACKEND_DIR)

# Load environment variables
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

_MISSING_IDS = {"", "nan", "none", "null"}
def _normalize_id(val):
    if val is None: return None
    s = str(val).strip()
    if not s or s.lower() in _MISSING_IDS: return None
    s = s.replace("\u00A0", " ").strip()
    if re.fullmatch(r"[-+]?\d+\.0", s):
        return s.rsplit('.0', 1)[0]
    if re.fullmatch(r"\d+", s):
        return s
    return s

async def inspect():
    async with SessionLocal() as db:
        stmt = select(Property).limit(20)
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        print(f"Inspecting {len(props)} properties:")
        for p in props:
            raw = p.lokalisering_id
            norm = _normalize_id(raw)
            print(f"  - DB: '{raw}' -> Norm: '{norm}' {'(MATCHES)' if raw == norm else '(NEEDS CLEAN)'}")

if __name__ == "__main__":
    asyncio.run(inspect())
