#!/usr/bin/env python3
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from sqlalchemy import text

async def check_schema():
    async with SessionLocal() as db:
        for table in ['risk_assessments', 'internal_control_cases', 'deviations', 'checklists']:
            result = await db.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position
            """))
            cols = [r[0] for r in result.fetchall()]
            print(f"{table}: {', '.join(cols)}")

asyncio.run(check_schema())
