import asyncio
import os
import sys
from pprint import pprint

# Add backend to path - assuming running from backend dir
sys.path.append(os.getcwd())

from dotenv import load_dotenv

# Explicitly load .env
load_dotenv('.env', override=True)

# Patch environment for Pydantic if missing
if not os.getenv("POSTGRES_SERVER"):
    print("⚠️ POSTGRES_SERVER not found in env, using default 'localhost'")
    os.environ["POSTGRES_SERVER"] = "localhost"
if not os.getenv("POSTGRES_USER"):
    os.environ["POSTGRES_USER"] = "postgres"
if not os.getenv("POSTGRES_PASSWORD"):
    os.environ["POSTGRES_PASSWORD"] = "password"
if not os.getenv("POSTGRES_DB"):
    os.environ["POSTGRES_DB"] = "knowme"

from app.db.session import SessionLocal
from app.services.analytics.financial_analysis_service import FinancialAnalysisService
# Import models to register them with SQLAlchemy
from app.domains.core.models.property import Property
from app.domains.core.models.center import Center
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.hms.models.scheduled_activity import ScheduledActivity

async def main():
    print("🚀 Starting Supplier Data Reproduction")
    async with SessionLocal() as db:
        try:
            print("Running get_global_supplier_stats...")
            stats = await FinancialAnalysisService.get_global_supplier_stats(db)
            print("\n📊 Results:")
            print(f"Total Portfolio Cost: {stats.get('total_portfolio_cost')}")
            print(f"Supplier Count: {stats.get('supplier_count')}")
            print(f"Suppliers found: {len(stats.get('suppliers', []))}")
            
            if stats.get('suppliers'):
                print("\nTop 5 Suppliers:")
                for i, supplier in enumerate(stats['suppliers'][:5]):
                    print(f"{i+1}. {supplier['name']}: {supplier['total_amount']} (Category: {supplier['category']})")
                    print(f"   Properties count: {supplier['property_count']}")
            else:
                print("\n❌ No suppliers found in the result!")
                
        except Exception as e:
            print(f"\n❌ Error executing service: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
