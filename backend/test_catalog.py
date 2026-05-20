import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.services.governance.classification_service import data_classification_service

async def main():
    async with SessionLocal() as db:
        try:
            print("Fetching catalog...")
            catalog = await data_classification_service.get_catalog(db)
            print(f"Catalog fetched! Found {len(catalog)} items.")
            if catalog:
                print("First item:", catalog[0])
        except Exception as e:
            print("Error fetching catalog:", str(e))
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
