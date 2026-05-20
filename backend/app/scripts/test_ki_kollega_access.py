import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.getcwd())
if os.path.exists("backend"):
    sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
if os.path.exists(os.path.join(os.getcwd(), 'backend', '.env')):
    load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
else:
    load_dotenv(os.path.join(os.getcwd(), '.env'))

from app.db.session import SessionLocal
from app.services.intelligence.ki_kollega.service import ki_kollega_service

async def test_ki_kollega():
    print("Testing KI Kollega Access...")
    
    # Test 1: Search Documents
    print("\n--- Test 1: Document Search ---")
    session1 = SessionLocal()
    try:
        query = "Hva er kravene til barnevernsinstitusjoner?"
        print(f"Query: {query}")
        result = await ki_kollega_service._tool_search_documents(session1, query)
        print(f"Result length: {len(result)}")
        print(f"Snippet: {result[:200]}...")
        
        if "Feil" not in result and len(result) > 20:
            print("✅ Document search successful")
        else:
            print("❌ Document search flagged potential error")
    except Exception as e:
        print(f"❌ Document search error: {e}")
    finally:
        await session1.close()

    await asyncio.sleep(1)

    # Test 2: SQL Query
    print("\n--- Test 2: SQL Query ---")
    session2 = SessionLocal()
    try:
        question = "Hvor mange eiendommer har vi?"
        print(f"Query: {question}")
        result = await ki_kollega_service._tool_run_sql(session2, question)
        print(f"Result: {result}")
        
        if "DATABASE RAPPORT" in result or "199" in result:
             print("✅ SQL query successful")
        else:
             print("❌ SQL query result unexpected")
    except Exception as e:
        print(f"❌ SQL query error: {e}")
    finally:
        await session2.close()

if __name__ == "__main__":
    try:
        asyncio.run(test_ki_kollega())
    except Exception as e:
        print(f"Test failed with error: {e}")
