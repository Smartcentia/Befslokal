import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
from uuid import uuid4

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine

# Import models
from app.domains.core.models.property import Property
from app.domains.core.models.user import User
from app.domains.hms.models.risk import RiskAssessment
import app.domains.hms.models.internal_control # Ensure registry
import app.domains.core.models.contract # Ensure registry
import app.domains.core.models.unit # Ensure registry
import app.domains.core.models.party # Ensure registry
from app.domains.hms.models.checklist import ChecklistTemplate, ChecklistExecution

async def seed_checklists():
    print("Seeding mock checklists for ALL properties...")
    
    # Create session factory
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # 1. Fetch all properties
        print("Fetching properties...")
        result = await session.execute(select(Property))
        properties = result.scalars().all()
        print(f"Found {len(properties)} properties.")
        
        if not properties:
            print("No properties found! Run seed_data.py first.")
            return

        # 2. Fetch all templates
        print("Fetching templates...")
        result = await session.execute(select(ChecklistTemplate))
        templates = result.scalars().all()
        print(f"Found {len(templates)} templates.")
        
        if not templates:
            print("No templates found! Run create_checklist_tables.py first.")
            return
            
        # 3. Fetch a default user (Plan B)
        # Ideally we want the caretaker for the property, but for mocking we might fall back
        # We select only user_id to avoid Enum validation issues if DB data mismatches
        result = await session.execute(select(User.user_id))
        user_ids = result.scalars().all()
        
        if not user_ids:
            print("No users found! Run seed_data.py first.")
            return

        checklist_count = 0
        
        for prop in properties:
            # Try to find a caretaker for this property if possible, else use default
            # In our simple model, we assume any user can "own" it for the mock, 
            # or we randomly pick a "property manager" type user from the list.
            # a simple heuristic: use default_user for now or random user
            user_id = random.choice(user_ids)
            
            # Create 1-3 checklists per property
            num_checklists = random.randint(1, 3)
            
            for _ in range(num_checklists):
                template = random.choice(templates)
                
                # Randomize status
                is_completed = random.choice([True, False])
                
                status = "completed" if is_completed else "in_progress"
                completed_at = datetime.now() - timedelta(days=random.randint(0, 30)) if is_completed else None
                
                responses = {}
                if is_completed:
                    # Mock full responses
                    # template.items is a list of dicts: [{"id": "1", "label": "..."}]
                    for item in template.items:
                        # Mostly all ok, sometimes a fail
                        responses[item["id"]] = random.choice([True, True, True, False]) 
                else:
                    # Partial responses for in_progress
                    if random.choice([True, False]):
                        for item in template.items[:2]: # First 2 items done
                             responses[item["id"]] = True
                
                execution = ChecklistExecution(
                    execution_id=uuid4(),
                    template_id=template.template_id,
                    property_id=prop.property_id,
                    user_id=user_id,
                    status=status,
                    responses=responses,
                    completed_at=completed_at,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 60))
                )
                session.add(execution)
                checklist_count += 1
        
        await session.commit()
        print(f"Successfully seeded {checklist_count} checklists for {len(properties)} properties.")

if __name__ == "__main__":
    asyncio.run(seed_checklists())
