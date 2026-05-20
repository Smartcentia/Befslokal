import asyncio
import os
import sys

# Legg til backend-mappen i path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

async def check():
    from app.db.session import SessionLocal
    from sqlalchemy import text
    import time

    print("--- BEFS System Status Sjekk ---")
    
    # 1. Database Sjekk
    print("Database: Sjekker tilkobling...", end="", flush=True)
    start = time.time()
    try:
        async with SessionLocal() as db:
            # Ping
            await db.execute(text("SELECT 1"))
            duration = (time.time() - start) * 1000
            print(f" OK ({duration:.1f}ms)")
            
            # Tellersjekk
            user_count = (await db.execute(text("SELECT count(*) FROM users"))).scalar()
            prop_count = (await db.execute(text("SELECT count(*) FROM properties"))).scalar()
            case_count = (await db.execute(text("SELECT count(*) FROM internal_control_cases"))).scalar()
            
            print(f"Brukere:    {user_count}")
            print(f"Eiendommer: {prop_count}")
            print(f"HMS-saker:  {case_count}")
            
    except Exception as e:
        print(f" FEIL!")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check())
