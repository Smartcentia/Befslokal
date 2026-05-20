import asyncio
import os
from dotenv import load_dotenv
from app.db.session import SessionLocal
from app.services.agent_memory_service import AgentMemoryService
from app.services.intelligence.ki_kollega.service import ki_kollega_service

# Load environment variables
load_dotenv()

async def register_tools():
    print("--- Registering Tools in Agent Toolbox ---")
    
    # Existing tools from KIKollegaService.TOOLS
    tools = ki_kollega_service.TOOLS
    
    async with SessionLocal() as db:
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name")
            description = func.get("description")
            
            if not name or not description:
                continue
                
            print(f"Registering tool: {name}...")
            
            # Create a rich content for embedding
            content = f"VERKTØY: {name}\nBESKRIVELSE: {description}"
            
            # Metadata to identify this as a tool definition
            metadata = {
                "type": "tool_definition",
                "tool_name": name,
                "parameters": func.get("parameters", {})
            }
            
            # Check if already exists (optional, but good for clean run)
            # For simplicity, we just add it (search_memory would find it)
            await AgentMemoryService.add_memory(db, content, metadata)
            
        print("\n✅ All tools registered in memory!")

if __name__ == "__main__":
    asyncio.run(register_tools())
