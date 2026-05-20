import asyncio
import json
import os
from memory import create_memory_store

APP_DIR = os.path.dirname(os.path.abspath(__file__))
TOOL_PATH = os.path.join(APP_DIR, "tools", "tool_hello.json")

async def test_memory():
    print("--- Starting Memory Test ---")
    
    # 1. Initialize
    try:
        memory = await create_memory_store()
    except Exception as e:
        print(f"❌ Failed to initialize memory: {e}")
        return

    # 2. Load Seed Data
    try:
        with open(TOOL_PATH, "r") as f:
            tool_data = json.load(f)
        print(f"✅ Loaded tool data: {tool_data['name']}")
    except Exception as e:
        print(f"❌ Failed to load tool json: {e}")
        return

    # 3. Save to Memory (Embedding Generation happens here)
    # We use the DESCRIPTION as the text to embed.
    # The ID is the tool ID.
    description = tool_data["description"]
    # Also add parameters to description for better matching
    param_desc = ", ".join([f"{k}: {v['description']}" for k, v in tool_data.get("parameters", {}).get("properties", {}).items()])
    text_to_embed = f"{tool_data['name']}: {description}. Parameters: {param_desc}"
    
    collection = "tool_library"
    
    print(f"💾 Saving to memory: '{text_to_embed}'...")
    try:
        await memory.save_information(
            collection=collection,
            id=tool_data["id"],
            text=text_to_embed,
            description=description # Metadata
        )
        print("✅ Saved successfully.")
    except Exception as e:
        print(f"❌ Failed to save to memory: {e}")
        return

    # 4. Search
    query = "I want to greet someone"
    print(f"🔍 Searching for: '{query}'...")
    
    try:
        results = await memory.search(
            collection=collection,
            query=query,
            limit=1,
            min_relevance_score=0.6
        )
        
        if results:
            match = results[0]
            print(f"✅ Found match: {match.id} (Score: {match.relevance})")
        else:
            print("⚠️ No match found (Score too low?)")

    except Exception as e:
         print(f"❌ Failed to search memory: {e}")

if __name__ == "__main__":
    asyncio.run(test_memory())
