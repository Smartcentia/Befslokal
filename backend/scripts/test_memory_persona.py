import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.db import base
from app.services.intelligence.ki_kollega.service import ki_kollega_service
from app.db.session import SessionLocal

async def test_memory_persona():
    print("--- Testing Agent Memory & Persona (Multi-turn / Persistence) ---")
    
    async with SessionLocal() as db:
        try:
            # 1. Turn 1: Tell the agent something personal
            print("\n--- TURN 1: Giving information ---")
            msg1 = "Hei, jeg heter Frank og min favorittfarge er mørkeblå."
            print(f"User: '{msg1}'")
            
            res1 = await ki_kollega_service.chat(message=msg1, db=db)
            print(f"KI Kollega: {res1.get('answer')}")
            
            # Wait a moment to ensure DB commit/index (though it's async)
            await asyncio.sleep(1)
            
            # 2. Turn 2: Ask back, but with a different phrasing
            print("\n--- TURN 2: Semantic Recall ---")
            msg2 = "Hvilken farge liker jeg best?"
            print(f"User: '{msg2}'")
            
            res2 = await ki_kollega_service.chat(message=msg2, db=db)
            print(f"KI Kollega: {res2.get('answer')}")
            
            # 3. Validation
            ans2 = res2.get("answer", "").lower()
            if "mørkeblå" in ans2 or "frank" in ans2:
                 print("\n✅ Verification SUCCESS: KI Kollega remembered the preference from the previous session/turn!")
            else:
                 print("\n❌ Verification FAILED: Information was not recalled.")
                 
        except Exception as e:
            print(f"\n❌ Error during memory test: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_memory_persona())
