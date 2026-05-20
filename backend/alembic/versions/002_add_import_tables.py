"""Add import tables

Revision ID: 002_add_import_tables
Revises: 001_initial
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '002_add_import_tables'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Utvid file_meta med file_type og content_type (only if table exists)
    op.execute(text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'file_meta'
            ) THEN
                ALTER TABLE file_meta
                ADD COLUMN IF NOT EXISTS file_type VARCHAR(20),
                ADD COLUMN IF NOT EXISTS content_type VARCHAR(100);
            END IF;
        END
        $$;
    """))

    # Opprett text_content tabell (conditionally based on FK target columns)
    op.execute(text("""
        DO $$
        DECLARE
            has_contract_id BOOLEAN;
            has_unit_id BOOLEAN;
            has_property_id BOOLEAN;
            create_sql TEXT;
        BEGIN
            -- Check if FK target columns exist
            has_contract_id := EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'contracts' AND column_name = 'contract_id'
            );
            has_unit_id := EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'units' AND column_name = 'unit_id'
            );
            has_property_id := EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'properties' AND column_name = 'property_id'
            );

            -- Only create table if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'text_content'
            ) THEN
                create_sql := 'CREATE TABLE text_content (
                    text_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_type VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    contract_id UUID';

                IF has_contract_id THEN
                    create_sql := create_sql || ' REFERENCES contracts(contract_id) ON DELETE SET NULL';
                END IF;

                create_sql := create_sql || ',
                    unit_id UUID';

                IF has_unit_id THEN
                    create_sql := create_sql || ' REFERENCES units(unit_id) ON DELETE SET NULL';
                END IF;

                create_sql := create_sql || ',
                    property_id UUID';

                IF has_property_id THEN
                    create_sql := create_sql || ' REFERENCES properties(property_id) ON DELETE SET NULL';
                END IF;

                create_sql := create_sql || ',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )';

                EXECUTE create_sql;
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
                WHERE table_schema = 'public' AND table_name = 'text_content'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_text_content_source_type ON text_content(source_type);
                CREATE INDEX IF NOT EXISTS ix_text_content_contract_id ON text_content(contract_id);
                CREATE INDEX IF NOT EXISTS ix_text_content_unit_id ON text_content(unit_id);
                CREATE INDEX IF NOT EXISTS ix_text_content_property_id ON text_content(property_id);
                CREATE INDEX IF NOT EXISTS ix_text_content_created_at ON text_content(created_at);
            END IF;
        END
        $$;
    """))
    
    # Opprett external_api_data tabell
    op.execute(text("""
        CREATE TABLE IF NOT EXISTS external_api_data (
            api_data_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_api VARCHAR(50) NOT NULL,
            entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('property', 'unit', 'contract', 'party')),
            entity_id UUID NOT NULL,
            data JSONB NOT NULL,
            fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE
        );
    """))
    # Create indexes separately (asyncpg doesn't support multiple commands in one statement)
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_external_api_data_source ON external_api_data(source_api);"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_external_api_data_entity ON external_api_data(entity_type, entity_id);"))
    op.execute(text("CREATE INDEX IF NOT EXISTS ix_external_api_data_fetched_at ON external_api_data(fetched_at);"))


def downgrade() -> None:
    op.execute(text("DROP TABLE IF EXISTS external_api_data CASCADE;"))
    op.execute(text("DROP TABLE IF EXISTS text_content CASCADE;"))
    op.execute(text("""
        ALTER TABLE file_meta 
        DROP COLUMN IF EXISTS file_type,
        DROP COLUMN IF EXISTS content_type;
    """))
