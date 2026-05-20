import sys
import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy import select, func, cast, Float, text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User

async def debug_query():
    print("Starting metrics query debug...")
    async with SessionLocal() as db:
        try:
            print("1. Testing Maintenance Sum Query...")
            # Use the EXACT logic from metrics_service
            maint_manual = func.coalesce(func.nullif(Property.external_data['financials']['total_manual_expenses'].astext, ''), '0')
            maint_csv = func.coalesce(func.nullif(Property.external_data['financials']['total_spend_csv'].astext, ''), '0')
            
            maint_sum = cast(maint_manual, Float) + cast(maint_csv, Float)

            p_stmt = select(
                func.count(Property.property_id),
                func.sum(maint_sum)
            )
            
            # Print compiled SQL for sanity check
            print("SQL:", p_stmt)

            p_res = await db.execute(p_stmt)
            count, total = p_res.one()
            print(f"Success! Count: {count}, Total: {total}")
            
        except Exception as e:
            print("QUERY FAILED:")
            print(e)
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_query())
