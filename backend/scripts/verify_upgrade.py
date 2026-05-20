import asyncio
import httpx
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv("KNOWME/backend/.env")

# Sample questions from the new set to verify domains
SAMPLE_QUESTIONS = [
    "Hvem er utleier for Havnegata 9?", # Masterdata
    "Hva var de totale bokførte kostnadene for 'Sogn Bosenter' i 2024?", # Finance (requires SQL)
    "Hva er kriminalitetsraten per 1000 innbyggere i området rundt Storgata 1?", # Socioeconomic (requires SQL)
    "Hva sier Husleieloven om indeksregulering av husleie?" # Lovdata
]

async def ask_question(client, question, idx):
    print(f"\n--- Test {idx+1}: {question} ---")
    payload = {
        "messages": [
            {"role": "user", "content": question}
        ]
    }
    try:
        # Note: Using the backend URL from settings or default localhost
        # Assuming the backend is running on localhost:8000 for local verification
        url = "http://localhost:8000/api/v1/ai/assistant/chat"
        response = await client.post(url, json=payload, timeout=60.0)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Svar: {data['response']}")
        else:
            print(f"Feil {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Unntak: {e}")

async def main():
    async with httpx.AsyncClient() as client:
        for i, q in enumerate(SAMPLE_QUESTIONS):
            await ask_question(client, q, i)

if __name__ == "__main__":
    asyncio.run(main())
