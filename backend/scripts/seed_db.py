import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.models.property import Property
from app.models.contract import Contract
from app.models.risk import RiskAssessment, RiskFactor

from sqlalchemy import text

async def seed():
    async with SessionLocal() as session:
        # Check if data exists
        existing = await session.execute(text("SELECT COUNT(*) FROM properties"))
        if existing.scalar() > 0:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding database...")
        
        # 1. Create Properties
        prop1_id = uuid.uuid4()
        prop1 = Property(
            property_id=prop1_id,
            address="Storgata 1",
            postal_code="0155",
            city="Oslo",
            latitude=59.9127,
            longitude=10.7461,
            external_data={"type": "Commercial", "size_m2": 1200}
        )

        prop2_id = uuid.uuid4()
        prop2 = Property(
            property_id=prop2_id,
            address="Dronning Eufemias gate 30",
            postal_code="0191",
            city="Oslo",
            latitude=59.9075,
            longitude=10.7580,
            external_data={"type": "Mixed Use", "size_m2": 5500}
        )
        
        session.add(prop1)
        session.add(prop2)
        
        # 2. Create Contracts
        contract1 = Contract(
            contract_id=uuid.uuid4(),
            unit_id=None, # Simplifying for now
            party_id=None,
            status="active",
            periods={"start": "2024-01-01", "end": "2029-01-01"},
            amount={"rent": 450000, "currency": "NOK"},
            signed_at=datetime.now()
        )
        session.add(contract1)

        # 3. Create Risks
        risk1 = RiskAssessment(
            assessment_id=uuid.uuid4(),
            property_id=prop1_id,
            methodology="NS 5814",
            overall_risk_score=3.5,
            risk_category="Medium",
            assessed_by="Auto-generated",
            notes="Seeded risk assessment"
        )
        session.add(risk1)

        await session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
