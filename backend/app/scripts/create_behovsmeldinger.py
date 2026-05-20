"""
Create behovsmeldinger table directly via SQL.
Run: railway run --service BEFS1 python3 backend/app/scripts/create_behovsmeldinger.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS behovsmeldinger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tittel VARCHAR(255) NOT NULL,
    beskrivelse TEXT,
    kategori VARCHAR(50),
    prioritet VARCHAR(20),
    status VARCHAR(30) NOT NULL DEFAULT 'Ny',
    opprettet_av VARCHAR(255) NOT NULL,
    eiendom_navn VARCHAR(255),
    admin_kommentar TEXT,
    er_arkivert BOOLEAN DEFAULT false,
    opprettet_dato TIMESTAMPTZ DEFAULT now(),
    oppdatert_dato TIMESTAMPTZ DEFAULT now()
)
"""

CREATE_IDX1 = "CREATE INDEX IF NOT EXISTS ix_behovsmeldinger_opprettet_av ON behovsmeldinger (opprettet_av)"
CREATE_IDX2 = "CREATE INDEX IF NOT EXISTS ix_behovsmeldinger_status ON behovsmeldinger (status)"
INSERT_VER = "INSERT INTO alembic_version (version_num) SELECT '20260510c_create_behovsmeldinger' WHERE NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '20260510c_create_behovsmeldinger')"

async def run():
    async with SessionLocal() as db:
        await db.execute(text(CREATE_TABLE))
        await db.execute(text(CREATE_IDX1))
        await db.execute(text(CREATE_IDX2))
        await db.execute(text(INSERT_VER))
        await db.commit()
        print("behovsmeldinger table created/verified OK")

if __name__ == "__main__":
    asyncio.run(run())
