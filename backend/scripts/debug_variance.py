import asyncio
import sys
import os
from dotenv import load_dotenv

# Load env variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import select, func, and_
from app.db.session import SessionLocal
import app.db.base  # Import all models to ensure relationships are known
from app.domains.core.models.property import Property
from app.models.financial_models import Budget, GLTransaction

async def debug_variance():
    async with SessionLocal() as session:
        # 1. Find the property
        res = await session.execute(select(Property).where(Property.name.ilike("%Kompani Linges vei 23%")))
        property = res.scalars().first()
        
        if not property:
            print("Property not found!")
            return

        print(f"Found Property: {property.name} (ID: {property.property_id})")
        property_id = property.property_id

        # 2. Check Budget Data for 2025
        res = await session.execute(select(func.count(Budget.budget_id)).where(
            and_(Budget.property_id == property_id, Budget.year == 2025)
        ))
        budget_count = res.scalar()
        print(f"Budget entries for 2025: {budget_count}")

        # 3. Check GLTransaction Data for 2025
        res = await session.execute(select(func.count(GLTransaction.transaction_id)).where(
            and_(GLTransaction.property_id == property_id, GLTransaction.year == 2025)
        ))
        gl_count = res.scalar()
        print(f"GLTransaction entries for 2025: {gl_count}")

        # 4. Check if we can reproduce the error
        try:
            from app.services.variance_service import VarianceService
            print("Attempting to run VarianceService.get_variance_report...")
            report = await VarianceService.get_variance_report(
                db=session,
                property_id=str(property_id),
                year=2025,
                period_type='ytd',
                period_value=6
            )
            print("Service call successful!")
            print("Summary:", report['summary'])
        except Exception as e:
            print(f"Service call FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_variance())
