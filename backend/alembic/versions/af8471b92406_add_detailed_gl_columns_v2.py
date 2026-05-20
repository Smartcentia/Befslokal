"""add_detailed_gl_columns_v2_restored

Revision ID: af8471b92406
Revises: 6b2bea70fd4d
Create Date: 2026-02-10 22:40:17.315591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'af8471b92406'
down_revision: Union[str, Sequence[str], None] = '6b2bea70fd4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    This migration is restored as a no-op to satisfy database history.
    The actual changes are assumed to be covered by cbbce3b08ed4 or manual application.
    """
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
