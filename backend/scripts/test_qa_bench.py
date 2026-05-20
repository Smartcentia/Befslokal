
import asyncio
import os
import sys
from dotenv import load_dotenv
from typing import List, Dict

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import SessionLocal
from app.services.ki_kollega.service import ki_kollega_service
from app.services.logger import get_logger

# Disable excessive logging
import logging
logging.getLogger("app.services.search_service").setLevel(logging.WARNING)

async def run_bench():
    print("🚀 Starting QA Benchmark...")
    
    if not ki_kollega_service.client:
        print("❌ Client not ready")
        return

    questions = [
        # 1. Concrete / Lookup
        {
            "category": "CONCRETE",
            "q": "Hva er adressen til Storgata 1?",
            "expect": "Address lookup"
        },
        {
            "category": "CONCRETE",
            "q": "Vis meg kontrakter for eiendommen i Brugata.",
            "expect": "Contract listing"
        },
        
        # 2. Semantic / Hybrid
        {
            "category": "SEMANTIC",
            "q": "Hvilke krav stilles til brannvern og internkontroll?",
            "expect": "Document retrieval (Fire/Safety)"
        },
        {
            "category": "SEMANTIC",
            "q": "Hvordan skal vi håndtere vedlikehold av uteområder?",
            "expect": "Document retrieval (Maintenance)"
        },

        # 3. Analysis / Cost
        {
            "category": "ANALYSIS",
            "q": "Hvilke eiendommer er de dyreste å leie?",
            "expect": "Cost sorting/listing"
        },
        {
            "category": "ANALYSIS",
            "q": "Sammenlign leiekostnadene for regionene.",
            "expect": "Regional cost comparison"
        }
    ]

    async with SessionLocal() as session:
        for i, item in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] Category: {item['category']}")
            print(f"❓ Q: {item['q']}")
            
            try:
                # Call Chat Service
                response = await ki_kollega_service.chat(
                    message=item['q'],
                    db=session
                )
                
                answer = response.get('answer', '')
                sources = response.get('sources', [])
                
                print(f"🤖 A: {answer[:300]}..." if len(answer) > 300 else f"🤖 A: {answer}")
                print(f"   Sources: {len(sources)}")
                for s in sources:
                    print(f"    - {s.get('name')} ({s.get('type')})")
                    
            except Exception as e:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_bench())
