import sys
import os
import pandas as pd
import uuid
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import select, text

# Load environment variables
print("Importing modules and loading .env...")
sys.stdout.flush()
load_dotenv()
print("Modules imported.")
sys.stdout.flush()

# POOLER_URL for Supabase Transaction Pooler
POOLER_URL = "postgresql+asyncpg://postgres:Sunnyowl_6533@db.vwvhxcqxadblrftuvsds.supabase.co:6543/postgres"

# CRITICAL: Set environment variable before importing app.db.session
os.environ["DATABASE_URL"] = POOLER_URL

from app.core.config import settings
from app.db.session import SessionLocal, engine as session_engine

# Patch settings and session engine for the pooler host
settings.DATABASE_URL = POOLER_URL

# We need to manually point SessionLocal to a new engine with the pooler URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

new_engine = create_async_engine(
    POOLER_URL,
    connect_args={"ssl": ssl_context, "server_settings": {"application_name": "import-script"}},
    pool_pre_ping=True
)
SessionLocal.configure(bind=new_engine)

from app.models.financial_models import GLTransaction
from app.domains.core.models.property import Property
from app.models.text_content import TextContent
from app.services.embeddings import generate_embeddings

# Configuration
INPUT_FILE = "/tmp/01.txt"
FINANS_DIR = "/tmp"
LEVERANDOR_FILE = "/tmp/leverandoroversikt.csv"

async def get_property_map(session):
    """Fetch all properties to map names to IDs."""
    result = await session.execute(select(Property.property_id, Property.name))
    return {row.name.lower(): row.property_id for row in result.all()}

def parse_01_txt(file_path):
    """
    Parse the 01.txt file. 
    Format is tricky: Space separated but names contain spaces.
    """
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            parts = line.split()
            if len(parts) < 6: continue
            
            try:
                # Region: Parts 0-2 (e.g., "5 Region Midt-Norge")
                region_name = " ".join(parts[1:3])
                dept_code = parts[3]
                amount_str = parts[-1].replace(',', '.')
                amount = float(amount_str)
                
                rows.append({
                    "region_name": region_name,
                    "department_code": dept_code,
                    "amount": amount,
                    "raw_text": line
                })
            except Exception as e:
                # print(f"Error parsing line: {line[:50]}... -> {e}")
                pass
                
    return rows

async def main():
    # 1. Load enrichment data
    print("Loading enrichment data...")
    sys.stdout.flush()
    try:
        df_suppliers = pd.read_csv(LEVERANDOR_FILE)
        supplier_map = dict(zip(df_suppliers['name'], df_suppliers['recorded_types']))
    except Exception as e:
        print(f"Warning: Could not load supplier map: {e}")
        sys.stdout.flush()
        supplier_map = {}

    # 2. Parse raw data
    print(f"Parsing {INPUT_FILE}...")
    sys.stdout.flush()
    raw_rows = parse_01_txt(INPUT_FILE)
    print(f"Found {len(raw_rows)} rows.")
    if raw_rows:
        print(f"Første rad råtekst: {raw_rows[0]['raw_text']}")
    sys.stdout.flush()

    # 3. Database Sync
    async with SessionLocal() as session:
        print("Fetching property map...")
        sys.stdout.flush()
        prop_map = await get_property_map(session)
        print(f"Found {len(prop_map)} properties in DB.")
        print(f"Sample properties: {list(prop_map.keys())[:10]}")
        sys.stdout.flush()
        
        gl_entries = []
        text_entries = []
        narratives = []
        
        match_count = 0
        for i, row in enumerate(raw_rows):
            property_id = None
            raw_lower = row['raw_text'].lower()
            
            # TRY MATCHING: The property name in 01.txt is usually between dept_code and the next code
            # Example: "512003 Gilantunet ungdomshjem 151003"
            for name, pid in prop_map.items():
                if name.lower() in raw_lower:
                    property_id = pid
                    break
            
            if not property_id:
                if i < 10: # Debug more misses
                    print(f"Miss [{i}]: {row['raw_text']}")
                continue
            
            match_count += 1
                
            # Create GL entry
            trans = GLTransaction(
                transaction_id=uuid.uuid4(),
                property_id=property_id,
                amount=row['amount'],
                region_name=row['region_name'],
                department_code=row['department_code'],
                source_system="01.txt_import",
                description=row['raw_text'][:500],
                year=2024,
                created_at=datetime.utcnow()
            )
            
            # Enrich supplier
            for s_name, categories in supplier_map.items():
                if s_name.lower() in raw_lower:
                    trans.supplier_name = s_name
                    trans.vendor = s_name
                    trans.category = categories.split(',')[0]
                    break
            
            gl_entries.append(trans)
            
            # Prepare narrative for Vector DB
            narrative = f"Økonomisk transaksjon for {row['raw_text'].split(row['department_code'])[1].strip() if row['department_code'] in row['raw_text'] else 'eiendom'}. " 
            narrative += f"Beløp: {row['amount']} NOK. Region: {row['region_name']}."
            if hasattr(trans, 'supplier_name') and trans.supplier_name:
                narrative += f" Leverandør: {trans.supplier_name} ({trans.category})."
            
            narratives.append(narrative)
            text_entries.append({
                "property_id": property_id,
                "content": narrative,
                "source_file": "01.txt"
            })
            
        print("-" * 50)
        print("IMPORT SAMMENDRAG (DRY RUN)")
        print("-" * 50)
        print(f"Totalt antall rader funnet i 01.txt: {len(raw_rows)}")
        print(f"Rader som ble koblet til en eiendom: {match_count}")
        print(f"Rader som ble beriket med leverandørinfo: {sum(1 for e in gl_entries if e.supplier_name)}")
        print(f"Klargjorte narrativer for Vector DB: {len(narratives)}")
        print("-" * 50)
        sys.stdout.flush()
        
        if len(gl_entries) == 0:
            print("ADVARSEL: Ingen rader ble koblet. Sjekk om eiendomsnavn i 01.txt matcher databasen.")
        else:
            print("Suksess: Dataene er ferdig mappet og klare for import.")
            
        # Insertion logic (commented out for safety)
        # session.add_all(gl_entries)
        # await session.commit()

if __name__ == "__main__":
    asyncio.run(main())
