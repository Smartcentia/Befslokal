
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
import random

# Setup path
sys.path.append(os.getcwd())

# Imports
from dotenv import load_dotenv
load_dotenv() # Load .env file explicitly

from app.core.config import settings
# Ensure DB URL is set (mock if not for safety, but we want real here)
if not os.getenv("DATABASE_URL") and not settings.DATABASE_URL:
    print("WARNING: No DATABASE_URL found. Seeding skipped.")
    sys.exit(0)
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment, RiskFactor

async def seed_risk_data():
    print("Seeding Risk Data...")
    async with SessionLocal() as db:
        # 1. Get Properties
        from sqlalchemy import select
        result = await db.execute(select(Property))
        props = result.scalars().all()
        
        if not props:
            print("No properties found to seed risks for.")
            return

        print(f"Found {len(props)} properties. Generating risks...")
        
        # 2. Create Risks
        categories = ["low", "medium", "high", "critical"]
        factors_ext = ["Flomfare stor", "Skredfare", "Nærhet til NVE Stasjon", "Høy alder på bygningsmasse"]
        factors_ops = ["Manglende branninstruks", "Utgått el-kontroll", "Defekt ventilasjon", "Manglende internkontroll"]
        
        count = 0
        for p in props:
            # Delete existing
            # await db.execute(text(f"DELETE FROM risk_assessments WHERE property_id = '{p.property_id}'"))
            
            # Create fresh assessment
            cat = random.choice(categories)
            score_map = {"low": 10, "medium": 45, "high": 70, "critical": 90}
            score = score_map[cat] + random.randint(-5, 5)
            
            assessment_id = uuid.uuid4()
            ra = RiskAssessment(
                assessment_id=assessment_id,
                property_id=p.property_id,
                risk_category=cat,
                overall_risk_score=score,
                status="OPEN" if cat in ["high", "critical"] else "CLOSED",
                notes=f"Automatisk generert risikovurdering for {p.address}",
                assessment_date=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            db.add(ra)
            
            # Add Factors
            # 1-3 Operational
            for _ in range(random.randint(1, 3)):
                rf = RiskFactor(
                    factor_id=uuid.uuid4(),
                    assessment_id=assessment_id,
                    category="operational",
                    factor_name=random.choice(factors_ops),
                    severity=random.choice([1.0, 2.0, 3.0]),
                    weight=1.0,
                    data_source="InternalControl"
                )
                db.add(rf)
                
            # 0-2 External
            for _ in range(random.randint(0, 2)):
                rf_ext = RiskFactor(
                    factor_id=uuid.uuid4(),
                    assessment_id=assessment_id,
                    category="external",
                    factor_name=random.choice(factors_ext),
                    severity=random.choice([2.0, 4.0, 5.0]),
                    weight=1.0,
                    data_source="ExternalOrchestrator"
                )
                db.add(rf_ext)
            
            # 3. Create Internal Control Case (Measure) if risk is high/critical
            if cat in ["high", "critical"]:
                from app.domains.hms.models.internal_control import InternalControlCase
                
                case = InternalControlCase(
                    case_id=uuid.uuid4(),
                    property_id=p.property_id,
                    risk_assessment_id=assessment_id,
                    title=f"Tiltak: Utbedre {random.choice(factors_ops).lower()}",
                    description="Dette må utbedres snarest.",
                    case_type="corrective_action",
                    status="open",
                    priority="high",
                    due_date=datetime.now() + timedelta(days=7),
                    process_state="Opprettet"
                )
                db.add(case)
            
            count += 1
            
        await db.commit()
        print(f"Successfully seeded risk assessments for {count} properties.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(seed_risk_data())
