#!/usr/bin/env python3
"""Test database connection"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env first
load_dotenv(Path(__file__).parent.parent / '.env')

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from sqlalchemy import select

async def test():
    try:
        async with SessionLocal() as db:
            result = await db.execute(select(Property))
            props = result.scalars().all()
            print(f'✅ Database connection OK! Found {len(props)} properties')
            if len(props) > 0:
                print(f'   First property: {props[0].address or props[0].name}')
            return True
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
