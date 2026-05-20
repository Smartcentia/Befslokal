import sys
import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

sys.path.append(os.getcwd())

from app.domains.core.models.property import Property
from app.domains.core.models.property_annual_cost import PropertyAnnualCost

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Mangler DATABASE_URL miljøvariabel.")
    sys.exit(1)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with AsyncSessionLocal() as session:
        # Telle hvor mange elementer som gjelder for 2025
        count_query = select(func.count()).select_from(PropertyAnnualCost).where(PropertyAnnualCost.year == 2025)
        count_result = await session.execute(count_query)
        total_count = count_result.scalar()
        
        print(f"\n--- Oppsummering 2025 Eiendomsportefølje ---")
        print(f"Antall innleste kostnadsposter for 2025: {total_count}")

        # Summere KPI-justert leie
        sum_query = select(func.sum(PropertyAnnualCost.kpi_adjusted_rent)).where(PropertyAnnualCost.year == 2025)
        sum_result = await session.execute(sum_query)
        total_kpi_rent = sum_result.scalar() or 0.0

        print(f"Total KPI-justert leie (for alle poster): {total_kpi_rent:,.2f} kr")
        
        # Sjekk 5 tilfeldige poster
        print("\n--- Eksempler på innhold (opptil 5) ---")
        sample_query = select(Property, PropertyAnnualCost)\
            .join(PropertyAnnualCost, Property.property_id == PropertyAnnualCost.property_id)\
            .limit(5)
            
        sample_result = await session.execute(sample_query)
        for prop, ac in sample_result:
            print(f"- Lokalisering {prop.lokalisering_id} ({prop.address}):")
            print(f"    KPI-justert leie: {ac.kpi_adjusted_rent}")
            print(f"    Felleskostnader: {ac.common_costs}")
            print(f"    Indre vedlikehold: {ac.internal_maintenance}")
            print("")

if __name__ == "__main__":
    asyncio.run(main())
