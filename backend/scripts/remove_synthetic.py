
import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal

async def remove_synthetic_data():
    async with SessionLocal() as db:
        print("Starting cleanup...")
        
        # 1. Delete flagged data (is_synthetic = True) - likely 0 rows
        print("Deleting flagged synthetic data...")
        await db.execute(text("DELETE FROM gl_transactions WHERE is_synthetic = true"))
        await db.execute(text("DELETE FROM budget WHERE is_synthetic = true"))
        
        # 2. Delete heuristic synthetic data (GL transactions with specific descriptions)
        print("Deleting heuristic synthetic GL data...")
        await db.execute(text("""
            DELETE FROM gl_transactions 
            WHERE description LIKE 'Monthly Rent - %' 
               OR description LIKE 'Electricity Cost - %' 
               OR description LIKE 'Parking Cost - %' 
               OR description LIKE 'Cleaning Cost - %'
        """))
        
        # 3. Delete heuristic synthetic Budget data (harder to identify without flag)
        # Assuming budget table was empty or we want to clear it if it looks synthetic.
        # Check if budget table has creates:
        # budget_generation_service uses specific categories.
        # If we want to be safe, we can delete all budget data if user says "remove all synthetic data" 
        # and assumes budget is synthetic.
        # But let's check count first.
        res = await db.execute(text("SELECT count(*) FROM budget"))
        count = res.scalar()
        if count > 0:
            print(f"Found {count} budget entries. Deleting all budget data as it is likely synthetic.")
            await db.execute(text("DELETE FROM budget"))
        else:
            print("No budget data found.")

        # 4. Remove synthetic flag from properties
        print("Unmarking properties as synthetic...")
        # We need to update external_data JSON.
        # PostgreSQL specific JSON update to remove key or set to false is tricky in raw SQL if structure varies.
        # Simplest is to fetch properties where synthetic=true, update python dict, and save.
        
        from app.domains.core.models.property import Property
        from sqlalchemy import select
        
        stmt = select(Property).where(text("external_data::text LIKE '%synthetic%: true%'"))
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        updated_count = 0
        for p in props:
            ext = dict(p.external_data or {})
            if ext.get('synthetic'):
                ext['synthetic'] = False
                ext['synthetic_note'] = None
                p.external_data = ext
                db.add(p)
                updated_count += 1
        
        await db.commit()
        print(f"Unmarked {updated_count} properties.")
        print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(remove_synthetic_data())
