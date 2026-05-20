
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir) # tests/ -> backend/
sys.path.append(backend_dir)
print(f"Added to sys.path: {backend_dir}")

from app.domains.hms.services.internal_control import InternalControlService
from app.domains.core.models.property import Property
# Import dependent models to satisfy SQLAlchemy relationships
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

async def test_generate_daily_tasks_logic():
    print("--- Testing Daily Task Generation Logic ---")
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    
    # 1. Setup Mock Properties
    prop_taeru = Property(
        property_id="uuid-1", 
        name="Tærudgata 16", 
        external_data={"tags": {"type": "Institusjon", "risk_class": "RKL6"}}
    )
    prop_office = Property(
        property_id="uuid-2", 
        name="Alexanders gate", 
        external_data={"tags": {"type": "Kontor", "risk_class": "RKL4"}}
    )
    prop_empty = Property(
        property_id="uuid-3", 
        name="Empty Plot", 
        external_data={}
    )

    mock_result.scalars.return_value.all.return_value = [prop_taeru, prop_office, prop_empty]
    
    # 2. Run Service
    service = InternalControlService(mock_db)
    count = await service.generate_daily_tasks()
    
    # 3. Analyze Results
    inputs = [args[0] for args, _ in mock_db.add.call_args_list]
    tasks = [obj for obj in inputs if hasattr(obj, 'title')]
    
    titles = [t.title for t in tasks]
    print(f"Generated {len(tasks)} tasks:")
    for t in titles:
        print(f" - {t}")

    # 4. Assertions
    expected = [
        "Sjekk brannsentral (Grønt lys?)", 
        "Test av nødåpner på dører (Sikkerhet vs Rømning)",
        "Sjekk at rømningveier er fri for rot/lager"
    ]
    
    missing = [e for e in expected if e not in titles]
    if missing:
        print(f"FAILED: Missing expected tasks: {missing}")
        sys.exit(1)
        
    print("SUCCESS: All Institution/RKL6 tasks generated correctly.")

async def test_tenant_deviation_workflow():
    print("\n--- Testing Tenant Deviation Workflow ---")
    mock_db = AsyncMock()
    service = InternalControlService(mock_db)
    
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    
    prop_leased = Property(
        property_id="uuid-1", 
        name="Leid Bygg AS", 
        external_data={"tags": {"ownership": "Leid"}}
    )
    mock_result.scalar_one_or_none.return_value = prop_leased
    
    result = await service.handle_deviation({"property_id": "uuid-1"}, None)
    print(f"Workflow Action: {result['action']}")
    
    if result["action"] == "notify_landlord":
        print("SUCCESS: Correctly triggered landlord notification workflow.")
    else:
        print(f"FAILED: Expected 'notify_landlord', got {result['action']}")
        sys.exit(1)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_generate_daily_tasks_logic())
    loop.run_until_complete(test_tenant_deviation_workflow())
