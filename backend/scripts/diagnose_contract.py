import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text

async def check():
    async with SessionLocal() as db:
        target_id = "3390b75a-b8de-4592-9f33-20b2af2efbd3"
        print(f"Bypassing Trigger to Update: {target_id}")

        try:
             # 1. Disable Trigger
             await db.execute(text("ALTER TABLE contracts DISABLE TRIGGER tsvectorupdate_contracts"))
             
             # 2. Update Data
             new_amount = {"amount_per_year": 2450000, "currency": "NOK", "vat_included": False}
             new_periods = [{"start_date": "2024-01-01T00:00:00", "end_date": "2029-12-31T23:59:59", "notice_period_months": 6}]
             
             await db.execute(text("UPDATE contracts SET amount = :amt, periods = :per WHERE contract_id = :cid"), 
                                {"amt": str(new_amount).replace("'", '"').replace("False", "false"), 
                                 "per": str(new_periods).replace("'", '"'), 
                                 "cid": target_id})
             
             # 3. Enable Trigger
             await db.execute(text("ALTER TABLE contracts ENABLE TRIGGER tsvectorupdate_contracts"))
             
             await db.commit()
             print("SUCCESS: Contract updated (Trigger bypassed).")
        
        except Exception as e:
             print(f"Failed with trigger bypass: {e}")
             await db.rollback()
             # Try re-enabling just in case
             try:
                 await db.execute(text("ALTER TABLE contracts ENABLE TRIGGER tsvectorupdate_contracts"))
                 await db.commit()
             except:
                 pass
             raise e

if __name__ == "__main__":
    asyncio.run(check())
