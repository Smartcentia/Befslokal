
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

async def check_prop():
    from app.db.session import SessionLocal
    import app.db.base
    from app.domains.core.models.property import Property
    from sqlalchemy import select

    async with SessionLocal() as db:
        res = await db.execute(select(Property).limit(1))
        prop = res.scalar()
        print(f'Property: {prop.address}')
        f = prop.external_data.get("financials", {})
        print(f'Financials: {f}')
        h = prop.external_data.get("financial_history", {})
        print(f'History 2025: {h.get("2025")}')

if __name__ == '__main__':
    asyncio.run(check_prop())
