import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine

# Import for registry
import app.domains.hms.models.risk 
import app.domains.core.models.contract
import app.domains.core.models.unit 
import app.domains.core.models.party 
import app.domains.core.models.user # Fix: InternalControlCase depends on User
import app.domains.hms.models.internal_control # Fix: Property depends on InternalControlCase
from app.domains.core.models.property import Property
from app.domains.hms.models.checklist import ChecklistExecution

async def verify_checklists():
    print("Verifying checklist data...")
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Count total checklists
        result = await session.execute(select(func.count(ChecklistExecution.execution_id)))
        total_checklists = result.scalar()
        print(f"Total Checklists: {total_checklists}")
        
        # Count checklists per status
        result = await session.execute(
            select(ChecklistExecution.status, func.count(ChecklistExecution.execution_id))
            .group_by(ChecklistExecution.status)
        )
        for status, count in result.all():
            print(f"Status '{status}': {count}")
            
        # Verify coverage (properties with checklists)
        # This query counts distinct properties that have a checklist
        result = await session.execute(
            select(func.count(func.distinct(ChecklistExecution.property_id)))
        )
        props_with_checklists = result.scalar()
        
        result = await session.execute(select(func.count(Property.property_id)))
        total_props = result.scalar()
        
        print(f"Properties with checklists: {props_with_checklists} / {total_props}")
        
        if props_with_checklists == 0:
            print("WARNING: No properties have checklists!")
        elif props_with_checklists < total_props:
            print(f"WARNING: Only {props_with_checklists} out of {total_props} properties have checklists.")
        else:
            print("SUCCESS: All properties have at least one checklist.")

if __name__ == "__main__":
    asyncio.run(verify_checklists())
