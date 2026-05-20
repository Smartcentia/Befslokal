
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

async def test_top_tenants():
    # Use env var or default local
    export_db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/befs")
    # os.environ["DATABASE_URL"] = export_db_url # Don't override if already set, just use it

    
    try:
        from app.db.session import SessionLocal
        from app.domains.core.models.contract import Contract
        from app.domains.core.models.party import Party
        from sqlalchemy import select, func, cast, Float, desc
        
        async with SessionLocal() as db:
            # Replicating the logic from dashboard.py
            rent_yearly = func.coalesce(
                Contract.amount['total_per_year'].astext,
                Contract.amount['amount_per_year'].astext
            )
            rent_monthly = func.coalesce(
                Contract.amount['monthly_rent'].astext,
                Contract.amount['amount'].astext
            )
            final_rent = func.coalesce(
                cast(rent_yearly, Float),
                cast(rent_monthly, Float) * 12,
                0.0
            )

            stmt = (
                select(
                    Party.name,
                    func.sum(final_rent).label("total_revenue"),
                    func.count(Contract.contract_id).label("contract_count")
                )
                .join(Party, Contract.party_id == Party.party_id)
                .where(Contract.status == 'active')
                .group_by(Party.party_id, Party.name)
                .order_by(desc("total_revenue"))
                .limit(10)
            )
            
            print("Executing query...")
            result = await db.execute(stmt)
            rows = result.all()
            
            print(f"Found {len(rows)} top tenants:")
            for r in rows:
                print(f"- {r.name}: {r.total_revenue} ({r.contract_count} contracts)")

            if not rows:
                print("Checking raw data...")
                # Check for active contracts and parties
                res_c = await db.execute(select(func.count(Contract.contract_id)).where(Contract.status == 'active'))
                print(f"Active contracts: {res_c.scalar()}")
                
                # Check for any contract with amount data
                res_a = await db.execute(select(Contract.amount).limit(5))
                print(f"Sample amount data: {[row[0] for row in res_a.all()]}")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_top_tenants())
