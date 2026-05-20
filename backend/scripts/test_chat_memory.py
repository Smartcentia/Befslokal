import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.db import base # Ensure all models are loaded for SQLAlchemy mapper
from app.services.intelligence.ki_kollega.service import ki_kollega_service
from app.db.session import SessionLocal

async def test_chat_memory():
    print("--- Testing KI Kollega Integration with Agent Memory ---")
    
    # We'll use the memory we seeded in verify_memory.py:
    # "Taket på eiendommen i Storgata 10 ble utbedret i juni 2023 for 450.000 kr."
    
    question = "Hva vet du om vedlikehold av taket i Storgata 10?"
    print(f"\nUser Question: '{question}'")
    
    async with SessionLocal() as db:
        try:
            # Call the integrated chat method
            result = await ki_kollega_service.chat(
                message=question,
                db=db
            )
            
            print("\nKI Kollega Response:")
            print("-" * 50)
            print(result.get("answer"))
            print("-" * 50)
            
            # Check if it mentions the roof/450k
            answer = result.get("answer", "").lower()
            if "tak" in answer and "2023" in answer:
                print("\n✅ Verification SUCCESS: KI Kollega recalled information from Agent Memory!")
            else:
                print("\n❌ Verification FAILED: Information was not reflected in the response.")
                
        except Exception as e:
            print(f"\n❌ Error during chat: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_memory())
