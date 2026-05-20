import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.services.intelligence.ki_kollega.service import KIKollegaService
from app.domains.fdv.models.fdv import BuildingComponent
from app.domains.core.models.property import Property
# Import Center to resolve relationship
from app.domains.core.models.center import Center 
# Ensure base models are loaded
import app.db.base 

from uuid import uuid4

async def verify_ai_semantic():
    db = SessionLocal()
    service = KIKollegaService()
    
    print("--- SETUP: Creating Test Data ---")
    # 1. Create a dummy property
    try:
        pid = uuid4()
        prop = Property(property_id=pid, name="AI Test Property", address="Testveien 1")
        db.add(prop)
        
        # 2. Create parent component
        parent_id = uuid4()
        parent = BuildingComponent(
            component_id=parent_id, 
            property_id=pid, 
            name="Main Ventilation Unit", 
            system_code="360.01", 
            brick_class="brick:Air_Handler_Unit"
        )
        db.add(parent)
        
        # 3. Create child component
        child = BuildingComponent(
            property_id=pid,
            name="Filter Bank A",
            parent_id=parent_id,
            brick_class="brick:Filter"
        )
        db.add(child)
        
        await db.commit()
        print("Test data created.")
        
        print("\n--- TEST: Running Tool ---")
        # 4. Run the tool search
        result = await service._tool_lookup_building_components(db, "Ventilation")
        print(f"Result (Ventilation): {result['formatted']}")
        assert "Main Ventilation Unit" in result['formatted'], "Failed to find parent"
        
        result_child = await service._tool_lookup_building_components(db, "Filter")
        print(f"Result (Filter): {result_child['formatted']}")
        assert "Filter Bank A" in result_child['formatted'], "Failed to find child"
        assert "Tilhører: Main Ventilation Unit" in result_child['formatted'], "Failed to find hierarchy"
        
        print("\nSUCCESS: AI Tool correctly identifies Semantic Data & Hierarchy!")
        
    except Exception as e:
        print(f"FAILED: {e}")
        await db.rollback()
    finally:
        # Cleanup
        try:
            await db.execute(text(f"DELETE FROM building_components WHERE property_id = '{pid}'"))
            await db.execute(text(f"DELETE FROM properties WHERE property_id = '{pid}'"))
            await db.commit()
            print("Cleanup done.")
        except:
            pass
        await db.close()

if __name__ == "__main__":
    from sqlalchemy import text # Import here to ensure context
    asyncio.run(verify_ai_semantic())
