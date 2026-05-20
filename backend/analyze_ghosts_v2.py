
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from dotenv import load_dotenv

# Ensure we can import from app
sys.path.append(os.getcwd())

from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.models.financial_models import GLTransaction

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "@db:5432" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("@db:5432", "@localhost:5432")

async def main():
    if not DATABASE_URL:
        print("DATABASE_URL not set.")
        return

    print("Connecting to DB...")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        result = await session.execute(select(Property))
        properties = result.scalars().all()
        print(f"Found {len(properties)} properties. Scanning for ghosts...")

        ghosts = []

        for p in properties:
            score = 0
            reasons = []

            # 1. Structural Checks
            is_empty_area = (p.total_area is None or p.total_area < 1)
            is_missing_year = (p.construction_year is None)
            is_missing_label = (p.energy_label is None)

            if is_empty_area:
                score += 2
                reasons.append("Zero Area")
            if is_missing_year:
                score += 1
            if is_missing_label:
                score += 1

            # 2. Relationship Checks
            # Units
            res_u = await session.execute(select(Unit.unit_id).where(Unit.property_id == p.property_id))
            unit_ids = res_u.scalars().all()
            unit_count = len(unit_ids)

            if unit_count == 0:
                score += 2
                reasons.append("No Units")

            # Contracts (via Units)
            contract_count = 0
            if unit_ids:
                res_c = await session.execute(select(func.count(Contract.contract_id)).where(Contract.unit_id.in_(unit_ids)))
                contract_count = res_c.scalar()
            
            if contract_count == 0:
                score += 3
                reasons.append("No Contracts")

            # GL Transactions
            res_gl = await session.execute(select(func.count(GLTransaction.transaction_id)).where(GLTransaction.property_id == p.property_id))
            gl_count = res_gl.scalar()

            if gl_count == 0:
                score += 3
                reasons.append("No Costs")

            # Threshold
            # Max score: 2+1+1+2+3+3 = 12
            # Let's say anything >= 8 is a critical ghost (e.g. No Contracts + No Costs + Zero Area)
            if score >= 7:
                ghosts.append({
                    "name": p.name or "Unknown",
                    "id": str(p.property_id),
                    "score": score,
                    "reasons": ", ".join(reasons),
                    "area": p.total_area,
                    "contracts": contract_count,
                    "gl": gl_count
                })

        ghosts.sort(key=lambda x: x['score'], reverse=True)

        print("\n" + "="*120)
        print(f"{'NAME':<30} | {'SCORE':<5} | {'AREA':<8} | {'CONTRACTS':<10} | {'GL_TX':<6} | {'REASONS'}")
        print("-" * 120)
        for g in ghosts:
            print(f"{g['name'][:30]:<30} | {g['score']:<5} | {str(g['area']):<8} | {g['contracts']:<10} | {g['gl']:<6} | {g['reasons']}")
        print("="*120)
        print(f"Total Ghosts Found: {len(ghosts)}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
