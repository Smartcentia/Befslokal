
import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock or Setup Env if needed
from dotenv import load_dotenv
load_dotenv('backend/.env')

# If no DB URL in env, warn or try default (but usually it's in .env)
print(f"DB URL present: {'DATABASE_URL' in os.environ}")

# Import all models to ensure ORM registry is populated
import app.db.base 

from app.domains.hms.services.risk_service import RiskService
from app.db.session import SessionLocal

async def main():
    print("Starting manual batch risk update...")
    try:
        async with SessionLocal() as session:
            # We call the service method directly
            result = await RiskService.batch_update_risks(session)
            print("Batch Update Result:", result)
    except Exception as e:
        print("Error running batch update:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(main())
