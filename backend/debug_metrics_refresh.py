import sys
import os
import asyncio
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
# Import models to register them
from app.domains.core.models.property import Property
from app.domains.core.models.center import Center # Added to resolve relationship
from app.domains.core.models.contract import Contract
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User
from app.models.metrics import DashboardMetrics

async def debug_refresh():
    print("Starting metrics refresh...")
    try:
        from app.services.metrics_service import refresh_dashboard_metrics
        result = await refresh_dashboard_metrics()
        print("Success:", result)
    except Exception as e:
        print("CRITICAL ERROR:")
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_refresh())
