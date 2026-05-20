import asyncio
import argparse
from sqlalchemy import delete, text
from app.db.session import SessionLocal
from app.models.financial_models import Budget, GLTransaction

async def clear_economic_data(dry_run: bool = True):
    async with SessionLocal() as session:
        # Count existing records
        budget_count_query = await session.execute(text(f"SELECT COUNT(*) FROM {Budget.__tablename__}"))
        budget_count = budget_count_query.scalar()
        
        gl_count_query = await session.execute(text(f"SELECT COUNT(*) FROM {GLTransaction.__tablename__}"))
        gl_count = gl_count_query.scalar()
        
        print(f"Found {budget_count} records in Budget table.")
        print(f"Found {gl_count} records in GLTransaction table.")
        
        if dry_run:
            print("DRY RUN: No data will be deleted. Use --force to delete.")
            return

        print("Deleting data...")
        
        await session.execute(delete(Budget))
        await session.execute(delete(GLTransaction))
        
        await session.commit()
        
        # Verify deletion
        budget_count_query = await session.execute(text(f"SELECT COUNT(*) FROM {Budget.__tablename__}"))
        budget_count_after = budget_count_query.scalar()
        
        gl_count_query = await session.execute(text(f"SELECT COUNT(*) FROM {GLTransaction.__tablename__}"))
        gl_count_after = gl_count_query.scalar()
        
        print(f"Deleted. Remaining records in Budget: {budget_count_after}")
        print(f"Deleted. Remaining records in GLTransaction: {gl_count_after}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clear economic data (Budget and GLTransaction).")
    parser.add_argument("--force", action="store_true", help="Actually execute the deletion.")
    args = parser.parse_args()
    
    dry_run = not args.force
    asyncio.run(clear_economic_data(dry_run=dry_run))
