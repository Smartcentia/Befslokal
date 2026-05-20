
import asyncio
import json
from sqlalchemy import select, String
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

async def check_ids():
    async with SessionLocal() as session:
        # Search for Name 'Molde'
        stmt = select(Property).where(Property.name.ilike("%Molde%"))
        result = await session.execute(stmt)
        props = result.scalars().all()
        
        print(f"Properties with Molde: {len(props)}")
        for p in props:
            # Inspection
            print(f"Prop: {p}")
            # Try to print id if available, or just dir
            try:
                print(f"ID: {getattr(p, 'id', 'No ID')}")
            except Exception as e:
                print(f"Error accessing ID: {e}")
                
            if p.external_data:
                print(f"External Data Keys: {p.external_data.keys()}")
                print(f"External Data Full: {json.dumps(p.external_data, indent=2)}")

        # Also get a sample property to see how we identify them
        stmt2 = select(Property).limit(1)
        res2 = await session.execute(stmt2)
        p2 = res2.scalar_one_or_none()
        if p2:
           print(f"\nSample Property: {p2.id} {p2.name}")
           print(f"External Data: {json.dumps(p2.external_data, indent=2)}")

if __name__ == "__main__":
    asyncio.run(check_ids())
