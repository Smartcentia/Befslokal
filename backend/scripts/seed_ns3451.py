import asyncio
from sqlalchemy import text
from app.db.session import SessionLocal
from app.domains.core.models.ns3451 import NS3451Code
from app.domains.fdv.models.fdv import BuildingComponent # Required for mapper registration

NS3451_DATA = [
    # Level 1
    {"code": "200", "name": "Bygning", "level": 1, "parent_code": None},
    {"code": "300", "name": "VVS-installasjoner", "level": 1, "parent_code": None},
    {"code": "400", "name": "Elkraft", "level": 1, "parent_code": None},
    {"code": "500", "name": "Tele og automatisering", "level": 1, "parent_code": None},
    {"code": "600", "name": "Andre installasjoner", "level": 1, "parent_code": None},
    {"code": "700", "name": "Utendørs", "level": 1, "parent_code": None},

    # Level 2 (Examples)
    {"code": "360", "name": "Luftbehandling", "level": 2, "parent_code": "300"},
    {"code": "320", "name": "Sanitær", "level": 2, "parent_code": "300"},
    {"code": "330", "name": "Varme", "level": 2, "parent_code": "300"},
    {"code": "430", "name": "Lavspent fordeling", "level": 2, "parent_code": "400"},
    {"code": "440", "name": "Lys", "level": 2, "parent_code": "400"},

    # Level 3 (Examples)
    {"code": "360.01", "name": "Luftbehandlingsutstyr", "level": 3, "parent_code": "360"},
    {"code": "360.02", "name": "Luftfordelingssystem", "level": 3, "parent_code": "360"},
]

async def seed_ns3451():
    async with SessionLocal() as db:
        print("--- Seeding NS 3451 Codes ---")
        try:
            # Check if exists
            result = await db.execute(text("SELECT count(*) FROM ns3451_codes"))
            count = result.scalar()
            if count > 0:
                print(f"Table already has {count} entries. Skipping seed.")
                return

            for item in NS3451_DATA:
                code_obj = NS3451Code(
                    code=item["code"],
                    name=item["name"],
                    level=item["level"],
                    parent_code=item["parent_code"]
                )
                db.add(code_obj)
            
            await db.commit()
            print(f"Successfully inserted {len(NS3451_DATA)} codes.")
        except Exception as e:
            print(f"Error seeding data: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_ns3451())
