
import asyncio
import sys
import os
from uuid import uuid4

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import all models to ensure registry is populated
import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.unit # Fix: Contract depends on Unit
import app.domains.core.models.party # Fix: Contract depends on Party
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
# Import new checklist models
from app.domains.hms.models.checklist import ChecklistTemplate, ChecklistExecution

from app.db.session import engine
from app.db.base_class import Base
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    # 1. Create Tables
    print("Creating tables for Checklists...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    # 2. Seed Data
    print("Seeding Checklist Templates...")
    
    # Create session factory bound to the engine
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Check if templates exist
        result = await session.execute(select(ChecklistTemplate))
        existing = result.scalars().first()
        
        if not existing:
            templates = [
                ChecklistTemplate(
                    template_id=uuid4(),
                    title="Brannvernrunde",
                    description="Månedlig sjekk av brannvarslere, slukkere og rømningsveier.",
                    category="brannvern",
                    frequency="monthly",
                    items=[
                        {"id": "1", "label": "Er alle rømningsveier frie for hindringer?"},
                        {"id": "2", "label": "Er merking av rømningsveier synlig og intakt (nødlys)?"},
                        {"id": "3", "label": "Er manuelt slokkeutstyr (brannslange/apparat) lett tilgjengelig og kontrollert?"},
                        {"id": "4", "label": "Er brannalarmsentralen grønn (ingen feilmeldinger)?"},
                        {"id": "5", "label": "Er branndører lukket og ikke kilt åpne?"}
                    ]
                ),
                ChecklistTemplate(
                    template_id=uuid4(),
                    title="Utvendig Inspeksjon",
                    description="Kvartalsvis sjekk av fasade, tak og uteområder.",
                    category="byggteknisk",
                    frequency="quarterly",
                    items=[
                        {"id": "1", "label": "Er det skader på fasade eller kledning?"},
                        {"id": "2", "label": "Er takrenner og nedløp åpne og hele?"},
                        {"id": "3", "label": "Er det fare for takras (snø/is)?"},
                        {"id": "4", "label": "Er utebelysning fungerende?"},
                        {"id": "5", "label": "Er avfallshåndtering ryddig og sikret?"}
                    ]
                ),
                 ChecklistTemplate(
                    template_id=uuid4(),
                    title="Vann og Rør",
                    description="Månedlig avlesning og inspeksjon.",
                    category="VVS",
                    frequency="monthly",
                    items=[
                        {"id": "1", "label": "Er hovedstoppekran merket og tilgjengelig?"},
                        {"id": "2", "label": "Er vannmåler avlest? (Noter stand i kommentar)"},
                        {"id": "3", "label": "Er det tegn til lekkasje i teknisk rom?"},
                        {"id": "4", "label": "Fungerer sluk på våtrom som de skal?"}
                    ]
                )
            ]
            session.add_all(templates)
            await session.commit()
            print(f"Inserted {len(templates)} templates.")
        else:
            print("Templates already exist. Skipping.")

if __name__ == "__main__":
    asyncio.run(main())
