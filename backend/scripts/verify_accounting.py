import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend/.env'))

# Pre-import all models via base to ensure registry is populated
import app.db.base
from app.models.financial_models import GLTransaction

from app.db.session import SessionLocal
from app.api.v1.accounting import get_transactions
from sqlalchemy import text, select

async def verify_accounting_api():
    print("Verifying Accounting API...")
    async with SessionLocal() as db:
        # 1. Check if we have any transactions
        result = await db.execute(text("SELECT count(*) FROM gl_transactions"))
        count = result.scalar()
        print(f"Total transactions in DB: {count}")
        
        if count == 0:
            print("No transactions found. Inserting a dummy transaction for verification...")
            import uuid
            from datetime import datetime
            
            # Fetch an existing property ID
            result = await db.execute(text("SELECT property_id FROM properties LIMIT 1"))
            property_id = result.scalar()
            
            if not property_id:
                print("No properties found. Cannot verify accounting without a property.")
                return

            # Create dummy transaction with new fields
            dummy_tx = GLTransaction(
                transaction_id=uuid.uuid4(),
                property_id=property_id,
                amount=1000.0,
                transaction_date=datetime.now(),
                year=2024,
                month=1,
                account_code="3000",
                account_name="Salgsinntekter",
                supplier_name="Test Supplier AS",
                invoice_number="INV-12345",
                description="Test transaction for verification",
                region_name="Oslo",
                department_name="IT",
                period="202401",
                category="Test Category"
            )
            db.add(dummy_tx)
            await db.commit()
            print("Dummy transaction inserted.")
            
            # Re-fetch count
            result = await db.execute(text("SELECT count(*) FROM gl_transactions"))
            count = result.scalar()
            print(f"Total transactions in DB now: {count}")

        # 2. Call the service/logic used by the API (simulating the API call)
        # We can't easily call the API endpoint directly without a running server and HTTP client,
        # but we can call the function if we refactor, or just query the DB using the same model to ensure mapping works.
        
        stmt = select(GLTransaction).limit(1)
        result = await db.execute(stmt)
        tx = result.scalars().first()
        
        if tx:
            print("\nSuccessfully fetched a transaction via SQLAlchemy Model:")
            print(f"ID: {tx.transaction_id}")
            print(f"Supplier: {tx.supplier_name}")
            print(f"Amount: {tx.amount}")
            print(f"Region: {tx.region_name}")
            print(f"Department: {tx.department_name}")
            print(f"Account: {tx.account_code} - {tx.account_name}")
            
            # Check if new fields are populated (they might be None if data is old, but the field should exist)
            print(f"Has invoice_number attribute: {hasattr(tx, 'invoice_number')}")
            print(f"Has department_code attribute: {hasattr(tx, 'department_code')}")
            
        else:
            print("Failed to fetch transaction model.")

if __name__ == "__main__":
    asyncio.run(verify_accounting_api())
