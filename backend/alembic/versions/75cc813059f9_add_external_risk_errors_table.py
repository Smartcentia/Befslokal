"""add_external_risk_errors_table

Revision ID: 75cc813059f9
Revises: 004_add_external_data_column
Create Date: 2025-11-10 11:48:11.669265

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '75cc813059f9'
down_revision = '004_add_external_data_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create external_risk_errors table (conditionally based on properties.property_id)
    op.execute(sa.text("""
        DO $$
        DECLARE
            has_property_id BOOLEAN;
        BEGIN
            has_property_id := EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'properties'
                    AND column_name = 'property_id'
            );

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'external_risk_errors'
            ) THEN
                IF has_property_id THEN
                    CREATE TABLE external_risk_errors (
                        error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL REFERENCES properties(property_id),
                        source VARCHAR(50) NOT NULL,
                        error_type VARCHAR(50) NOT NULL,
                        error_message VARCHAR(1000) NOT NULL,
                        error_details JSONB,
                        http_status_code INTEGER,
                        url VARCHAR(500),
                        latitude FLOAT,
                        longitude FLOAT,
                        retry_count INTEGER NOT NULL DEFAULT 0,
                        resolved VARCHAR(10) NOT NULL DEFAULT 'false',
                        resolved_at TIMESTAMP WITH TIME ZONE,
                        resolved_by VARCHAR(100),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                ELSE
                    CREATE TABLE external_risk_errors (
                        error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        property_id UUID NOT NULL,
                        source VARCHAR(50) NOT NULL,
                        error_type VARCHAR(50) NOT NULL,
                        error_message VARCHAR(1000) NOT NULL,
                        error_details JSONB,
                        http_status_code INTEGER,
                        url VARCHAR(500),
                        latitude FLOAT,
                        longitude FLOAT,
                        retry_count INTEGER NOT NULL DEFAULT 0,
                        resolved VARCHAR(10) NOT NULL DEFAULT 'false',
                        resolved_at TIMESTAMP WITH TIME ZONE,
                        resolved_by VARCHAR(100),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                END IF;
            END IF;
        END
        $$;
    """))
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'external_risk_errors'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_external_risk_errors_property_id ON external_risk_errors(property_id);
                CREATE INDEX IF NOT EXISTS ix_external_risk_errors_source ON external_risk_errors(source);
                CREATE INDEX IF NOT EXISTS ix_external_risk_errors_error_type ON external_risk_errors(error_type);
                CREATE INDEX IF NOT EXISTS ix_external_risk_errors_resolved ON external_risk_errors(resolved);
                CREATE INDEX IF NOT EXISTS ix_external_risk_errors_created_at ON external_risk_errors(created_at);
            END IF;
        END
        $$;
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS external_risk_errors CASCADE"))
