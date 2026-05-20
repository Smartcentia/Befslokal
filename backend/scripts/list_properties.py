import asyncio
import sys
import os

# Ensure backend directory is in path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from sqlalchemy import select

async def main():
    async with SessionLocal() as db:
        result = await db.execute(select(Property).limit(50))
        props = result.scalars().all()
        print(f"Found {len(props)} properties.")
        for p in props:
            print(f"Prop: {p.name}, Addr: {p.address}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
