import asyncio
import os
from dotenv import load_dotenv
from app.db.session import SessionLocal
from app.services.agent_memory_service import AgentMemoryService

# Load environment variables
load_dotenv()

async def seed_persona():
    print("--- Seeding Agent Persona ---")
    
    persona_content = """Identitet: Du er 'KI Kollega', en avansert AI-assistent utviklet for BEFS Eiendom.
Rolle: Ekspert på norsk eiendomsforvaltning, kontraktsanalyse og HMS.
Personlighet: Profesjonell, analytisk, men vennlig og løsningsorientert.
Kommunikasjon: Du svarer på norsk. Du er nøyaktig og ærlig - hvis du ikke vet svaret, sier du ifra.
Mål: Hjelpe ansatte i BEFS med å få rask innsikt i eiendomsporteføljen, dokumenter og daglig drift."""

    metadata = {
        "type": "persona_definition",
        "name": "KI Kollega",
        "version": "1.0"
    }
    
    async with SessionLocal() as db:
        # Clear old persona if needed (optional)
        print("Saving persona definition to permanent memory...")
        await AgentMemoryService.add_memory(db, persona_content, metadata)
        print("\n✅ Persona successfully seeded!")

if __name__ == "__main__":
    asyncio.run(seed_persona())
