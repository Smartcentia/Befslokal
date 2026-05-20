import asyncio
import os
import sys
import random
import uuid
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))

env_path = Path(__file__).resolve().parent.parent / ".env"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:Sunnyowl_6533@db.vwvhxcqxadblrftuvsds.supabase.co:5432/postgres"

from app.db.session import SessionLocal
import app.db.base
from app.domains.core.models.user import User, UserRole
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.security.pwd import get_password_hash

FORNAVN_KVINNER = [
    "Anne", "Ingrid", "Kari", "Marit", "Liv", "Eva", "Berit", "Astrid", "Bjørg", "Hilde",
    "Anna", "Solveig", "Marianne", "Ida", "Linn", "Silje", "Hanne", "Tone", "Bente", "Heidi"
]
FORNAVN_MENN = [
    "Jan", "Per", "Bjørn", "Ole", "Lars", "Kjell", "Svein", "Knut", "Arne", "Geir",
    "Thomas", "Morten", "Martin", "Hans", "Erik", "Terje", "Odd", "John", "Rune", "Trond"
]
ETTERNAVN = [
    "Hansen", "Johansen", "Olsen", "Larsen", "Andersen", "Pedersen", "Nilsen", "Kristiansen",
    "Jensen", "Karlsen", "Johnsen", "Pettersen", "Eriksen", "Berg", "Haugen", "Hagen", "Johannessen",
    "Andreassen", "Jacobsen", "Halvorsen", "Lund", "Moen", "Gundersen", "Jørgensen", "Strand",
    "Solberg", "Sørensen", "Vik", "Tveit", "Eide"
]

def generate_random_user(role: UserRole, region: str = None) -> User:
    gender = random.choice(['M', 'F'])
    first_name = random.choice(FORNAVN_MENN) if gender == 'M' else random.choice(FORNAVN_KVINNER)
    last_name = random.choice(ETTERNAVN)
    full_name = f"{first_name} {last_name}"
    
    email_prefix = f"{first_name.lower()}.{last_name.lower()}{random.randint(100, 9999)}"
    email_prefix = email_prefix.replace("æ", "ae").replace("ø", "o").replace("å", "aa")
    email = f"{email_prefix}@viken-eiendom.no"
    
    user = User(
        user_id=uuid.uuid4(),
        email=email,
        name=full_name,
        role=role,
        region=region,
        hashed_password=get_password_hash("Sommer2024!"),
        is_active=True,
        email_verified=True,
        mfa_enabled=False
    )
    return user

async def seed_users():
    print("📋 Starter generering av fantasifulle brukere (eiendomsledere og vaktmestere)...")
    db = SessionLocal()
    try:
        # Hent alle eiendommer med managers pga append
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        users_added = 0
        props_updated = 0
        
        for prop in properties:
            # Vi vil bruke fantasien! Hvis det alt er brukere der, fjern de gamle kanskje?
            # La oss bare sjekke om det er ekte brukere, vi legger dem bare til om de ikke har for mange.
            if hasattr(prop, 'managers') and prop.managers and len(prop.managers) >= 3:
                continue
                
            region = prop.region if prop.region else "Region Øst"
            
            # Legg til 1 eiendomsleder
            manager = generate_random_user(UserRole.PROPERTY_MANAGER, region=region)
            manager.properties.append(prop)
            db.add(manager)
            users_added += 1
            
            # 70% sjanse for at det også er en vaktmester
            if random.random() < 0.70:
                janitor = generate_random_user(UserRole.JANITOR, region=region)
                janitor.properties.append(prop)
                db.add(janitor)
                users_added += 1
            
            props_updated += 1
            print(f"La til brukere for eiendom: {prop.name}")
            
        await db.commit()
        print(f"\n✅ Vellykket! La til totalt {users_added} nye brukere fordelt på {props_updated} eiendommer.")
        
    except Exception as e:
        print(f"❌ Feil: {e}")
        import traceback
        traceback.print_exc()
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(seed_users())
