import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("KNOWME/backend/.env")
os.environ["FORCE_API_KEY"] = "true"

# Ensure backend path is in sys.path
sys.path.append(os.path.abspath("KNOWME/backend"))

from app.services.mcp.handler import sync_tools_to_registry

if __name__ == "__main__":
    print("Starting sync of upgraded tools...")
    sync_tools_to_registry()
    print("Sync process completed.")
