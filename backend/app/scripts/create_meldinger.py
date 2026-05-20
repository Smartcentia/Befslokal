"""
Create meldinger table directly via SQL.
Run: railway run --service BEFS1 python3 backend/app/scripts/create_meldinger.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS meldinger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    avsender_email VARCHAR(255) NOT NULL,
    avsender_navn VARCHAR(255),
    mottaker_email VARCHAR(255) NOT NULL,
    mottaker_navn VARCHAR(255),
    emne VARCHAR(500) NOT NULL,
    innhold TEXT NOT NULL,
    lest BOOLEAN NOT NULL DEFAULT false,
    arkivert_avsender BOOLEAN NOT NULL DEFAULT false,
    arkivert_mottaker BOOLEAN NOT NULL DEFAULT false,
    svar_til_id UUID,
    sendt_dato TIMESTAMPTZ NOT NULL DEFAULT now(),
    lest_dato TIMESTAMPTZ
)
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_meldinger_avsender ON meldinger (avsender_email)",
    "CREATE INDEX IF NOT EXISTS ix_meldinger_mottaker ON meldinger (mottaker_email)",
    "CREATE INDEX IF NOT EXISTS ix_meldinger_lest ON meldinger (mottaker_email, lest) WHERE lest = false",
    "CREATE INDEX IF NOT EXISTS ix_meldinger_sendt ON meldinger (sendt_dato DESC)",
]

INSERT_VER = "INSERT INTO alembic_version (version_num) SELECT '20260510d_create_meldinger' WHERE NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '20260510d_create_meldinger')"

async def run():
    async with SessionLocal() as db:
        await db.execute(text(CREATE_TABLE))
        for idx in INDEXES:
            await db.execute(text(idx))
        await db.execute(text(INSERT_VER))
        await db.commit()
        print("meldinger table created/verified OK")

if __name__ == "__main__":
    asyncio.run(run())
