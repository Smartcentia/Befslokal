
import asyncio
import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load .env manually if not set
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
print(f"Loading env from: {env_path}")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Remove 'export ' if present
            if line.lower().startswith('export '):
                line = line[7:].strip()
            
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and "DATABASE_URL" not in os.environ:
                os.environ[key] = value

if "DATABASE_URL" not in os.environ:
    print("ERROR: DATABASE_URL not found in env!")
    # Fallback for local development based on docker-compose
    default_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/eiendom"
    print(f"Falling back to default local URL: {default_url}")
    os.environ["DATABASE_URL"] = default_url
else:
    print("DATABASE_URL found.")

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import app.db.base # Register all models
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

DEVIATION_TEMPLATES = [
    # FIRE
    {"title": "Manglende brannslukker", "category": "critical", "notes": "Brannslukker mangler i 2. etasje gang."},
    {"title": "Blokkert rømningsvei", "category": "critical", "notes": "Lagret utstyr blokkerer nødutgang i kjeller."},
    {"title": "Utgått branninstruks", "category": "medium", "notes": "Branninstruks på vegg er fra 2018."},
    {"title": "Defekt nødlys", "category": "high", "notes": "Nødlys i trappeoppgang virker ikke ved test."},

    # WATER
    {"title": "Vannlekkasje i kjeller", "category": "high", "notes": "Observert fukt og drypp fra rør i teknisk rom."},
    {"title": "Tett sluk", "category": "medium", "notes": "Sluk på vaskerom drenerer sakte."},
    {"title": "Dryppende kran", "category": "low", "notes": "Kran på kjøkken drypper kontinuerlig."},

    # ELECTRICAL
    {"title": "Løs stikkontakt", "category": "high", "notes": "Stikkontakt henger løst ut av veggen på kontor 302."},
    {"title": "Utgått el-kontroll", "category": "medium", "notes": "Periodisk el-kontroll skulle vært utført for 3 mnd siden."},
    {"title": "Mangler deksel i sikringsskap", "category": "high", "notes": "Deksel foran kurser mangler."},

    # STRUCTURAL / BUILDING
    {"title": "Knust vindu", "category": "high", "notes": "Ytre vindu knust i 1. etasje mot gaten."},
    {"title": "Dør lukkes ikke", "category": "medium", "notes": "Ytterdør går ikke i lås uten makt."},
    {"title": "Løst gelender", "category": "high", "notes": "Gelender i hovedtrapp er løst."},
    {"title": "Manglende merking", "category": "low", "notes": "Mangler merking på glassdør."},

    # VENTILATION
    {"title": "Støy fra ventilasjon", "category": "low", "notes": "Klager på støy fra ventilasjonsanlegg i 4. etasje."},
    {"title": "Manglende filterbytte", "category": "medium", "notes": "Filter i ventilasjonsaggregat er ikke byttet ihht plan."},
    
    # EXTERIOR
    {"title": "Manglende strøing", "category": "high", "notes": "Glatt inngangsparti, strøkasse er tom."},
    {"title": "Søppel flyter", "category": "medium", "notes": "Avfallsdunker fulle, søppel på bakken."},
]

async def seed_varied_deviations():
    print("🚀 Starting Varied Deviations Seeding...")
    db = SessionLocal()
    try:
        # 1. Clear existing RiskAssessments
        print("🧹 Clearing existing RiskAssessments...")
        await db.execute(delete(RiskAssessment))
        await db.commit()
        print("   ✅ Cleared.")

        # 2. Get all properties
        print("Properties loading...")
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        print(f"   found {len(properties)} properties.")

        generated_count = 0

        # 3. Generate deviations
        print("🎲 Generating variations...")
        for prop in properties:
            # 70% chance of having deviations
            if random.random() > 0.3:
                # Generate 1-5 deviations
                num_deviations = random.randint(1, 5)
                
                for _ in range(num_deviations):
                    template = random.choice(DEVIATION_TEMPLATES)
                    
                    # Random date between 1 and 90 days ago
                    days_ago = random.randint(1, 90)
                    created_date = datetime.now() - timedelta(days=days_ago)

                    deviation = RiskAssessment(
                        property_id=prop.property_id,
                        # Use template title as notes/title proxy since RiskAssessment uses 'notes' often
                        # But verifying model: 
                        # risk_category -> category
                        # notes -> title/desc proxy
                        risk_category=template["category"],
                        notes=template["title"] + " - " + template["notes"],
                        methodology="Simulert Avviksgenerator",
                        overall_risk_score=random.choice([1.0, 2.0, 3.0, 4.0, 5.0]),
                        assessed_by="System Generator",
                        created_at=created_date,
                        # updated_at will handle itself or be null
                    )
                    db.add(deviation)
                    generated_count += 1
        
        await db.commit()
        print(f"✅ Successfully seeded {generated_count} varied deviations across {len(properties)} properties.")

    except Exception as e:
        print(f"❌ Error seeding deviations: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(seed_varied_deviations())
