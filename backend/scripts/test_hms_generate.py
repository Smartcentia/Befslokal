import asyncio
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.domains.hms.services.activity_generator import ActivityGenerator

async def main():
    print("Starting test script...")
    async with SessionLocal() as session:
        print("Session created.")
        generator = ActivityGenerator()
        try:
            stats = await generator.generate_activities_for_all_properties(session)
            print("Success:", stats)
        except Exception as e:
            print("Error occurred!")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
