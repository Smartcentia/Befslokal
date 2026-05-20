import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def setup_memory():
    # Convert sqlalchemy-style asyncpg URL to standard postgres URL if needed
    # (asyncpg doesn't like the +asyncpg prefix in some versions)
    url = DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to database...")
    conn = await asyncpg.connect(url)
    try:
        print("Enabling pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        print("Recreating agent_memory table...")
        await conn.execute("DROP TABLE IF EXISTS agent_memory CASCADE;")
        await conn.execute("""
            CREATE TABLE agent_memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content TEXT NOT NULL,
                additional_metadata JSONB DEFAULT '{}'::jsonb,
                embedding VECTOR(1536), -- Optimized for OpenAI text-embedding-3-small/ada-002
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        print("Creating index for vector search (HNSW)...")
        # Note: We use HNSW for better performance on large datasets
        try:
            await conn.execute("""
                CREATE INDEX ON agent_memory USING hnsw (embedding vector_cosine_ops);
            """)
        except Exception as e:
            if "already exists" in str(e).lower():
                print("Index already exists.")
            else:
                print(f"Warning: Could not create HNSW index: {e}")
                print("Attempting to create basic IVFFLAT index instead...")
                await conn.execute("""
                    CREATE INDEX ON agent_memory USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                """)
        
        print("✅ Database setup complete!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_memory())
