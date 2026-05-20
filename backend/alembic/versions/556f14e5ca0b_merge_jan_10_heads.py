"""merge_jan_10_heads

Revision ID: 556f14e5ca0b
Revises: add_gl_transactions, scheduled_activities_2026_01_10
Create Date: 2026-01-12 21:41:28.200573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '556f14e5ca0b'
down_revision: Union[str, Sequence[str], None] = ('add_gl_transactions', 'scheduled_activities_2026_01_10')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
