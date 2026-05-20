
import asyncio
import sys
from app.db.session import engine
from sqlalchemy import inspect
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract

async def inspect_schema():
    print("--- Inspecting Schema ---")
    
    # We need to use sync engine for inspect, or run in executor? 
    # SQLAlchemy inspect works with sync engine usually.
    # But app.db.session provides AsyncEngine.
    
    # Let's try raw SQL via the async session to be safe/simple
    from app.db.session import SessionLocal
    from sqlalchemy import text
    
    async with SessionLocal() as db:
        print("Checking 'properties' columns:")
        res = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'properties';"))
        cols = [r[0] for r in res.fetchall()]
        print(cols)
        
        print("\nChecking 'contracts' columns:")
        res = await db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'contracts';"))
        cols = [r[0] for r in res.fetchall()]
        print(cols)
        
        if 'contract_number' in cols:
            print("\n✅ 'contract_number' exists in 'contracts'")
        else:
            print("\n❌ 'contract_number' matches NO column in 'contracts'")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect_schema())
