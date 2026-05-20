
import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

async def check_totals():
    from app.db.session import SessionLocal
    import app.db.base
    from app.domains.core.models.property import Property
    from sqlalchemy import select

    async with SessionLocal() as db:
        res = await db.execute(select(Property))
        properties = res.scalars().all()
        
        totals = {2025: 0.0, 2024: 0.0, 2023: 0.0}
        for prop in properties:
            history = prop.external_data.get('financial_history', {}) if prop.external_data else {}
            for year in [2025, 2024, 2023]:
                year_data = history.get(str(year), {})
                totals[year] += float(year_data.get('total_costs', 0))
        
        print(f'Totals (NOK): {totals}')
        mnok = {y: round(t/1000000, 1) for y, t in totals.items()}
        print(f'Totals (MNOK): {mnok}')

if __name__ == '__main__':
    asyncio.run(check_totals())
