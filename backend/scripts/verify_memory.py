import os
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# We need to import the models so SQLAlchemy knows about them
# But for a script we can just use the Service which imports them
from app.services.agent_memory_service import AgentMemoryService
from app.core.config import settings

async def verify_memory():
    # Setup database connection
    url = os.getenv("DATABASE_URL")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # engine = create_async_engine(url, echo=False)
    # AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # We'll use a mocked session if we don't want to mess with the real DB, 
    # but the user said "go", so we're doing it for real.
    
    from app.db.session import SessionLocal
    
    async with SessionLocal() as db:
        print("--- Agent Memory Verification ---")
        
        # 1. Clear existing test memory (optional but good for clean test)
        # await AgentMemoryService.clear_memory(db)
        
        # 2. Add some "memories"
        test_data = [
            ("Taket på eiendommen i Storgata 10 ble utbedret i juni 2023 for 450.000 kr.", {"property": "Storgata 10", "type": "maintenance"}),
            ("Leieavtalen med Bunnpris utløper den 31. desember 2025.", {"property": "Sjøsiden Senter", "type": "contract"}),
            ("Frank foretrekker at rapporter fokuserer på avvik i driftsutgifter.", {"user": "Frank", "type": "preference"}),
            ("Det er planlagt utskifting av heis i bygg B i løpet av Q1 2024.", {"property": "Bygg B", "type": "maintenance"})
        ]
        
        print("Adding test memories...")
        for content, meta in test_data:
            await AgentMemoryService.add_memory(db, content, meta)
        
        print("Waiting for database to sync...")
        await asyncio.sleep(1)
        
        # 3. Test semantic search
        queries = [
            "Hva skjedde med taket nylig?",
            "Når slutter kontrakten med matbutikken?",
            "Hva liker Frank å se i rapportene sine?",
            "Er det noen heiser som skal fikses?"
        ]
        
        print("\nTesting Semantic Search:")
        for query in queries:
            print(f"\nQuery: '{query}'")
            results = await AgentMemoryService.search_memory(db, query, limit=1)
            if results:
                print(f"Result: {results[0]['content']}")
                print(f"Metadata: {results[0]['metadata']}")
            else:
                print("No results found.")

        print("\n✅ Verification complete!")

if __name__ == "__main__":
    asyncio.run(verify_memory())
