
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.domains.hms.services.internal_control import InternalControlService
from app.domains.core.models.property import Property
from app.domains.core.models.user import User

@pytest.mark.asyncio
async def test_generate_daily_tasks_logic():
    # 1. Setup Mock DB Session
    mock_db = AsyncMock()
    
    # 2. Key: Use MagicMock for the result scalar/all chain
    # We mock the sequence: db.execute() -> result.scalars() -> result.all()
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    
    # 3. Create Mock Properties with Tags
    # Property 1: Tærudgata (Institution + RKL6) -> Should trigger 2 critical tasks
    prop_taeru = Property(
        property_id="uuid-1", 
        name="Tærudgata 16", 
        external_data={"tags": {"type": "Institusjon", "risk_class": "RKL6"}}
    )
    
    # Property 2: Office (Kontor) -> Should trigger 1 medium task
    prop_office = Property(
        property_id="uuid-2", 
        name="Alexanders gate", 
        external_data={"tags": {"type": "Kontor", "risk_class": "RKL4"}}
    )
    
    # Property 3: Empty -> Should trigger 0 tasks
    prop_empty = Property(
        property_id="uuid-3", 
        name="Empty Plot", 
        external_data={}
    )

    # Configure the mock return
    mock_result.scalars.return_value.all.return_value = [prop_taeru, prop_office, prop_empty]
    
    # 4. Initialize Service
    service = InternalControlService(mock_db)
    
    # 5. Run Logic
    count = await service.generate_daily_tasks()
    
    # 6. Verify Results
    # Tærudgata: Brannsentral (High) + Rømning (Critical) + Nødåpner (Critical for RKL6) = 3 tasks
    # Office: Ergonomi (Medium) = 1 task
    # Total = 4 tasks expected
    
    # Note: My implementation had:
    # Rule 1 (Inst): Brannsentral + Rømning
    # Rule 2 (RKL6): Nødåpner
    # Rule 3 (Kontor): Ergonomi
    
    print(f"\nTasks Created: {mock_db.add.call_count}") 
    # db.add is called for WorkOrder AND Task. So 4 tasks = 8 db.add calls.
    
    # Let's inspect the actual Task objects passed to db.add
    added_objects = [args[0] for args, _ in mock_db.add.call_args_list]
    tasks = [obj for obj in added_objects if hasattr(obj, 'title')]
    
    print("Generated Tasks:")
    for t in tasks:
        print(f"- {t.title} [Priority: {t.payload.get('priority')}]")
        
    titles = [t.title for t in tasks]
    
    # Assertions
    assert "Sjekk brannsentral (Grønt lys?)" in titles
    assert "Test av nødåpner på dører (Sikkerhet vs Rømning)" in titles
    assert "HMS Runde: Sjekk ergonomi og belysning" in titles
    assert len(tasks) == 4

@pytest.mark.asyncio
async def test_handle_deviation_tenant():
    mock_db = AsyncMock()
    service = InternalControlService(mock_db)
    
    # Mock finding the property
    mock_result = MagicMock()
    mock_db.execute.return_value = mock_result
    
    prop_leased = Property(
        property_id="uuid-1", 
        name="Leid Bygg AS", 
        external_data={"tags": {"ownership": "Leid"}}
    )
    mock_result.scalar_one_or_none.return_value = prop_leased
    
    result = await service.handle_deviation({"property_id": "uuid-1"}, None)
    
    assert result["action"] == "notify_landlord"
    assert "Venter på ekstern utbedring" in result["message"]
