
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

# Fix for MissingGreenlet/EventLoop issues in scripts
# We need to ensure the engine is created/used within the correct context or that we don't have loop contentions?
# Actually, the best way for a script is just to import and run.
# If MissingGreenlet persists, it might be due to how models are loaded or session is used.

from app.services.metrics_service import refresh_dashboard_metrics

async def main():
    print("Triggering Dashboard Metrics Refresh...")
    try:
        # We might need to ensure models are loaded fully? They are imported inside the function.
        result = await refresh_dashboard_metrics()
        print("Metrics Refresh Successful.")
        print("New Metrics State:")
        for k, v in result.items():
            print(f"  - {k}: {v}")
    except Exception as e:
        print(f"Error refreshing metrics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
    asyncio.run(main())
