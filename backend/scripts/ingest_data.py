import asyncio
import os
import json
import csv
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.domains.core.models.property import Property
from app.domains.core.models.center import Center
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.models.text_content import TextContent
from typing import List

# PDF & AI dependencies
import pypdf
from pypdf import PdfReader
from openai import AsyncOpenAI
from app.core.config import settings

# Initialize OpenAI Client (Direct)
aclient = None
if settings.OPENAI_API_KEY:
    aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data_import")

# --- Helpers ---
async def get_embedding(text: str) -> List[float]:
    """Generates embedding using OpenAI directly."""
    if not aclient:
        print("⚠️  Ingen OpenAI API Key funnet. Skipper embedding.")
        return None
    try:
        # Truncate if too long (rough check)
        if len(text) > 8000: 
            text = text[:8000]
        
        resp = await aclient.embeddings.create(
            input=text.replace("\n", " "),
            model="text-embedding-3-small" # Cost effective
        )
        return resp.data[0].embedding
    except Exception as e:
        print(f"❌  Embedding feilet: {e}")
        return None

# --- Ingestion Functions ---

async def ingest_centers(session: AsyncSession):
    """Laster inn centers.csv"""
    file_path = os.path.join(DATA_DIR, "centers.csv")
    if not os.path.exists(file_path):
        return

    print("🏢  Laster sentre...")
    df = pd.read_csv(file_path)
    count = 0
    for _, row in df.iterrows():
        data = row.where(pd.notnull(row), None).to_dict()
        
        stmt = select(Center).where(Center.center_id == data.get('center_id'))
        if (await session.execute(stmt)).scalar_one_or_none():
            continue
            
        center = Center(
            center_id=data.get('center_id'),
            name=data.get('name'),
            region=data.get('region'),
            description=data.get('description')
        )
        session.add(center)
        count += 1
    await session.commit()
    print(f"✅  La til {count} nye sentre.")


async def ingest_properties(session: AsyncSession):
    """Laster inn properties.csv og oppretter Default Unit."""
    file_path = os.path.join(DATA_DIR, "properties.csv")
    if not os.path.exists(file_path):
        print(f"⚠️  Hopper over eiedommer: {file_path} mangler.")
        return

    print("🏠  Laster eiendommer...")
    df = pd.read_csv(file_path)
    count = 0
    for _, row in df.iterrows():
        data = row.where(pd.notnull(row), None).to_dict()
        addr = data.get('address')
        
        # Check existence
        stmt = select(Property).where(Property.address == addr)
        result = await session.execute(stmt)
        existing_prop = result.scalar_one_or_none()
        
        if existing_prop:
            prop = existing_prop
        else:
            prop = Property(
                address=addr,
                city=data.get('city'),
                postal_code=str(data.get('postal_code')),
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                gnr=data.get('gnr'),
                bnr=data.get('bnr'),
                name=data.get('name') or addr,
                usage=data.get('usage'),
                total_area=data.get('total_area'),
                construction_year=data.get('construction_year'),
                owner_name=data.get('owner_name'),
                center_id=data.get('center_id')
            )
            session.add(prop)
            await session.flush() # Få ID
            count += 1

        # Check/Create Default Unit (Needed for Contracts)
        # We assume 1 property = 1 unit for simplicity in this migration unless units.csv exists
        stmt_unit = select(Unit).where(Unit.property_id == prop.property_id)
        unit = (await session.execute(stmt_unit)).scalar_one_or_none()
        
        if not unit:
            unit = Unit(
                property_id=prop.property_id,
                unit_number="H0101", # Default
                floor=1,
                area=prop.total_area
            )
            session.add(unit)

    await session.commit()
    print(f"✅  Behandlet {len(df)} eiendommer (La til {count} nye).")


async def ingest_contracts(session: AsyncSession):
    """Laster inn contracts.csv"""
    file_path = os.path.join(DATA_DIR, "contracts.csv")
    if not os.path.exists(file_path):
        return

    print("📜  Laster kontrakter...")
    df = pd.read_csv(file_path)
    count = 0
    
    for _, row in df.iterrows():
        data = row.where(pd.notnull(row), None).to_dict()
        
        # Finn eiendom først
        prop_addr = data.get('property_address')
        if not prop_addr:
            continue
            
        stmt = select(Property).where(Property.address == prop_addr)
        prop = (await session.execute(stmt)).scalar_one_or_none()
        
        if not prop:
            print(f"⚠️  Ingen eiendom funnet for kontrakt: {prop_addr}")
            continue
            
        # Finn Unit (tar første tilgjengelige)
        stmt_unit = select(Unit).where(Unit.property_id == prop.property_id)
        unit = (await session.execute(stmt_unit)).scalars().first()
        
        if not unit:
            print(f"⚠️  Ingen enhet funnet for eiendom: {prop_addr}")
            continue

        # Sjekk om kontrakt finnes (for å unngå duplikater ved re-kjøring)
        # Vi sjekker Unit + Startdato som unik "nøkkel" for denne importen
        stmt_check = select(Contract).where(
            Contract.unit_id == unit.unit_id,
            Contract.start_date == (pd.to_datetime(data.get('start_date')).date() if data.get('start_date') else None)
        )
        existing_contract = (await session.execute(stmt_check)).scalars().first()
        
        if existing_contract:
            # Kan oppdatere her hvis nødvendig, men skipper for nå
             continue

        # Create Contract
        contract = Contract(
            unit_id=unit.unit_id,
            category=data.get('category', 'Leiekontrakt'),
            status=data.get('status', 'active'),
            start_date=pd.to_datetime(data.get('start_date')).date() if data.get('start_date') else None,
            end_date=pd.to_datetime(data.get('end_date')).date() if data.get('end_date') else None,
            # Costs
            amount={"total": data.get('rent_amount')},
            caretaker_cost=data.get('caretaker_cost'),
            cleaning_cost=data.get('cleaning_cost'),
            parking_cost=data.get('parking_cost'),
            external_data={"tenant_name": data.get('tenant_name')}
        )
        session.add(contract)
        count += 1
        
    await session.commit()
    print(f"✅  La til {count} nye kontrakter.")


async def ingest_documents(session: AsyncSession):
    """Rekursivt søk etter PDF-er i properties-mappen."""
    props_dir = os.path.join(DATA_DIR, "properties")
    if not os.path.exists(props_dir):
        return

    print("📄  Scanner dokumenter...")
    count = 0
    
    # Walk: properties/[Adresse]/[Mappe]/fil.pdf
    for root, dirs, files in os.walk(props_dir):
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue
                
            full_path = os.path.join(root, file)
            # Prøv å utlede adresse fra mappenavn
            # Antar struktur: .../properties/Adresse/Undermappe/fil.pdf
            rel_path = os.path.relpath(full_path, props_dir)
            parts = rel_path.split(os.sep)
            
            if len(parts) < 2:
                continue
                
            address_folder = parts[0]
            category_folder = parts[1] if len(parts) > 1 else "Dokumenter"
            
            # Finn eiendom
            stmt = select(Property).where(Property.address == address_folder)
            prop = (await session.execute(stmt)).scalar_one_or_none()
            
            if not prop:
                # Kan hende mappenavnet er "Storgata_1" men adressen er "Storgata 1"
                normalized = address_folder.replace("_", " ")
                stmt = select(Property).where(Property.address == normalized)
                prop = (await session.execute(stmt)).scalar_one_or_none()
                
            if not prop:
                print(f"⚠️  Fant ikke eiendom for mappe: {address_folder}")
                continue

            # Les PDF
            try:
                reader = PdfReader(full_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            except Exception as e:
                print(f"❌  Kunne ikke lese {file}: {e}")
                continue
                
            if not text.strip():
                continue

            # Embed & Store
            print(f"   > Prosesserer: {file} ({len(text)} tegn)")
            embedding = await get_embedding(text)
            
            doc = TextContent(
                property_id=prop.property_id,
                source_type="file_upload",
                source_file=file,
                category=category_folder,
                content=text,
                embedding=embedding,
                additional_metadata={"original_path": rel_path}
            )
            session.add(doc)
            count += 1
            
            # Commit hver 10. fil for å spare minne/tid
            if count % 10 == 0:
                await session.commit()
                print(f"   Saved {count} so far...")

    await session.commit()
    print(f"✅  La til {count} dokumenter med AI-embeddings.")


async def main():
    async with async_session_factory() as session:
        print("🚀  Starter datainlasting (REBUILD)...")
        
        await ingest_centers(session)
        await ingest_properties(session)
        await ingest_contracts(session)
        await ingest_documents(session)
        
        print("🏁  Hele importjobben er ferdig!")

if __name__ == "__main__":
    asyncio.run(main())
