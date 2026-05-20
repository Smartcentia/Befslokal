import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal

async def fetch_real_data():
    # Import inside function to avoid circular dependency issues at module level
    from app.domains.core.models.property import Property
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.party import Party
    from app.domains.core.models.unit import Unit
    # Ensure related models are loaded to prevent registry errors
    import app.domains.hms.models.risk

    async with SessionLocal() as db:
        # 1. Properties
        props = (await db.execute(select(Property).limit(10))).scalars().all()
        prop_names = [p.name for p in props]
        prop_addrs = [p.address for p in props]

        # 2. Parties (Tenants)
        parties = (await db.execute(select(Party).limit(10))).scalars().all()
        party_names = [p.name for p in parties]

        # 3. Contract Keywords (from Units)
        units = (await db.execute(select(Unit).where(Unit.purpose != None).limit(10))).scalars().all()
        purposes = list(set([u.purpose for u in units if u.purpose]))

        print("\n=== REAL DATA FROM DB ===")
        print(f"Properties: {prop_names}")
        print(f"Addresses: {prop_addrs}")
        print(f"Parties: {party_names}")
        print(f"Purposes: {purposes}")

if __name__ == "__main__":
    asyncio.run(fetch_real_data())
