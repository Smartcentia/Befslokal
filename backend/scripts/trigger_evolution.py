
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../backend"))
# Also try standard path if script is run from project root
sys.path.append(os.getcwd())

from app.tasks.evolution_tasks import run_evolution_job

if __name__ == "__main__":
    print("🚀 Triggering Evolution Job manually...")
    asyncio.run(run_evolution_job())
