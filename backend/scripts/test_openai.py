import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load env from backend/.env
load_dotenv("backend/.env")

async def test_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env")
        return

    print(f"Testing OpenAI with model: {model}...")
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello, respond with 'OK' if you see this."}],
            max_tokens=10
        )
        print(f"Response: {response.choices[0].message.content}")
        print("OpenAI Status: OK")
    except Exception as e:
        print(f"OpenAI Status: FAILED - {e}")

if __name__ == "__main__":
    asyncio.run(test_openai())
