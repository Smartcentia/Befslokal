import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from app.services.tools.contract_tools import search_contracts

async def run_verification():
    queries = [
        "Finn leiekontrakten til Bakeriet i Storgata AS",
        "Hva er den årlige leien for Kaigata 4?",
        "Når går kontrakten til Bakeriet i Storgata AS ut?",
        "Hvor mange kvadratmeter leier Bakeriet?",
        "Hvem har ansvar for snømåking i kontrakten til Bakeriet?"
    ]

    print("=== STARTING VERIFICATION OF 5 REAL QUERIES ===\n")

    for i, q in enumerate(queries, 1):
        print(f"Query {i}: {q}")
        try:
            result = await search_contracts(q)
            print(f"Result Length: {len(result)} chars")
            print("--- Snippet ---")
            print(result[:300].replace("\n", " ") + "...")
            print("--------------------------------------------------\n")
        except Exception as e:
            print(f"FAILED: {e}\n")

if __name__ == "__main__":
    asyncio.run(run_verification())
