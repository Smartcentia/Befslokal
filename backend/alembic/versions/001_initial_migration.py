"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for contract status (safe, won't fail if exists)
    op.execute(text("""
        DO $$ BEGIN
            CREATE TYPE contractstatus AS ENUM ('active', 'terminated');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """))
    
    # Create all tables using raw SQL to avoid SQLAlchemy's automatic enum creation
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS properties (
            property_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            address VARCHAR NOT NULL,
            postal_code VARCHAR(4) NOT NULL,
            city VARCHAR NOT NULL,
            latitude FLOAT,
            longitude FLOAT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """))
    
    # Create units table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS units (
            unit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            property_id UUID NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
            purpose VARCHAR NOT NULL,
            area_sqm FLOAT NOT NULL,
            floor INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """))
    # Create index separately (asyncpg doesn't support multiple commands in one statement)
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_units_property_id ON units(property_id);"))
    
    # Create parties table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS parties (
            party_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            orgnr VARCHAR(9) UNIQUE NOT NULL,
            contact_email VARCHAR,
            contact_phone VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """))
    # Create index separately (asyncpg doesn't support multiple commands in one statement)
    op.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_parties_orgnr ON parties(orgnr);"))
    
    # Create contracts table
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            unit_id UUID NOT NULL REFERENCES units(unit_id) ON DELETE CASCADE,
            party_id UUID NOT NULL REFERENCES parties(party_id) ON DELETE CASCADE,
            status contractstatus NOT NULL,
            periods JSON NOT NULL,
            amount JSON NOT NULL,
            signed_at TIMESTAMP WITH TIME ZONE,
            terminated_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """))
    # Create indexes separately and guard for column existence (restored schema may differ)
    op.execute(text(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'contracts' AND column_name = 'unit_id'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_contracts_unit_id ON contracts(unit_id);
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'contracts' AND column_name = 'party_id'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_contracts_party_id ON contracts(party_id);
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'contracts' AND column_name = 'status'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_contracts_status ON contracts(status);
            END IF;
        END
        $$;
        """
    ))
    
    # Create file_meta table (conditionally based on contracts.contract_id existence)
    op.execute(text("""
        DO $$
        BEGIN
            -- Only create file_meta if contracts table has contract_id column
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'contracts'
                    AND column_name = 'contract_id'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                    AND table_name = 'file_meta'
            ) THEN
                CREATE TABLE file_meta (
                    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    contract_id UUID NOT NULL REFERENCES contracts(contract_id) ON DELETE CASCADE,
                    path VARCHAR NOT NULL,
                    sha256 VARCHAR(64) UNIQUE NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            END IF;
        END
        $$;
    """))
    # Create indexes separately (only if table exists)
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'file_meta'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_file_meta_contract_id ON file_meta(contract_id);
                CREATE UNIQUE INDEX IF NOT EXISTS ix_file_meta_sha256 ON file_meta(sha256);
            END IF;
        END
        $$;
    """))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS file_meta CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS contracts CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS parties CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS units CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS properties CASCADE;"))
    op.execute(text("DROP TYPE IF EXISTS contractstatus CASCADE;"))
