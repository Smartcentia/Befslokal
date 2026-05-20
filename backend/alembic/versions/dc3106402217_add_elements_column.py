"""add_elements_column

Revision ID: dc3106402217
Revises: e22fa2c0d853
Create Date: 2026-01-12 21:42:15.979267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc3106402217'
down_revision: Union[str, Sequence[str], None] = 'e22fa2c0d853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Guard: only add column if table exists and column not present
    op.execute(sa.text(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'contracts'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'contracts' AND column_name = 'elements'
            ) THEN
                ALTER TABLE contracts ADD COLUMN elements text;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'contracts' AND column_name = 'elements'
            ) THEN
                CREATE INDEX IF NOT EXISTS ix_contracts_elements ON contracts(elements);
            END IF;
        END
        $$;
        """
    ))


def downgrade() -> None:
    """Downgrade schema."""
    # Guarded drop to avoid errors if column/index doesn't exist
    op.execute(sa.text(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE schemaname = 'public' AND indexname = 'ix_contracts_elements'
            ) THEN
                DROP INDEX IF EXISTS ix_contracts_elements;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'contracts' AND column_name = 'elements'
            ) THEN
                ALTER TABLE contracts DROP COLUMN elements;
            END IF;
        END
        $$;
        """
    ))
