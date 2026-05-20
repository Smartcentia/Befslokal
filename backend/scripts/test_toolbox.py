import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.db import base
from app.services.intelligence.ki_kollega.service import ki_kollega_service
from app.db.session import SessionLocal

async def test_toolbox():
    print("--- Testing Agent Toolbox (Semantic Discovery) ---")
    
    # This query does NOT contain any keywords from the supervisor's old list:
    # Old keywords: ["søk", "hvor", "når", "ekstern", "google", "finn", "hent", "sjekk", "hvem", "hva"]
    question = "Hvilken adresse har Bunnpris-lokalet?"
    print(f"\nUser Question: '{question}'")
    
    async with SessionLocal() as db:
        try:
            # We want to see the logs specifically for discovery
            # The chat method will now perform discovery automatically
            result = await ki_kollega_service.chat(
                message=question,
                db=db
            )
            
            print("\nKI Kollega Response:")
            print("-" * 50)
            print(result.get("answer"))
            print("-" * 50)
            
            # If discovery worked, the log should show "Semantic match found in Toolbox"
            # and the answer should be based on property lookup results.
            
        except Exception as e:
            print(f"\n❌ Error during toolbox test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_toolbox())
