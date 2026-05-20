"""merge 20260314addunitfields and 20260320_srs_fase1

Revision ID: 20260323_merge_unitfields_srs
Revises: 20260314addunitfields, 20260320_srs_fase1
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260323_merge_unitfields_srs'
down_revision: Union[str, Sequence[str], None] = ('20260314addunitfields', '20260320_srs_fase1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite index on gl_transactions(ar, property_id) for bulk queries."""
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_gl_ar_property
        ON gl_transactions (ar, property_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_gl_ar_property")
