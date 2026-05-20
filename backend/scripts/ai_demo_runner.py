
import asyncio
import httpx
import json
import os
import sys

# Define the scenarios
SCENARIOS = [
    {
        "name": "The Lease Contract Detective (Semantic Search)",
        "question": "Hva er ansvarsfordelingen for utvendig vedlikehold på Storgata 1?",
        "context": "Probing Vector Search (PostgreSQL) for legal clauses."
    },
    {
        "name": "The HMS Risk Advisor (Strategic Logic)",
        "question": "Vi har oppdaget løse fliser i inngangspartiet på Havnegata 9. Hva er risikoen?",
        "context": "Probing Risk Classification tool logic."
    },
    {
        "name": "The Proactive Operations Assistant (IoT & Action)",
        "question": "Sjekk status på teknisk anlegg på Storgata 1 og fiks eventuelle feil.",
        "context": "Probing full Observe-Think-Act loop with IoT tools and Work Order creation."
    }
]

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/ai/assistant/chat")

async def run_scenario(client, scenario):
    print(f"\n{'='*60}")
    print(f"SCENARIO: {scenario['name']}")
    print(f"Goal: {scenario['context']}")
    print(f"User: {scenario['question']}")
    print(f"{'-'*60}")
    
    try:
        response = await client.post(
            API_URL,
            json={
                "messages": [
                    {"role": "user", "content": scenario['question']}
                ]
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"AI Response:\n{result['response']}")
            if result.get("usage"):
                print(f"\n(Usage: {result['usage'].get('total_tokens')} tokens)")
            return True
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error executing scenario: {str(e)}")
        return False

async def main():
    print("Starting AI Integration Demonstration for BEFS...")
    print(f"Target API: {API_URL}")
    
    async with httpx.AsyncClient() as client:
        # Check if backend is alive
        try:
            health = await client.get(API_URL) 
        except:
            pass
            
        success_count = 0
        for scenario in SCENARIOS:
            if await run_scenario(client, scenario):
                success_count += 1
                
        print(f"\n{'='*60}")
        print(f"Demonstration Summary: {success_count}/{len(SCENARIOS)} scenarios completed successfully.")
        print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())
