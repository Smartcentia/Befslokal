"""merge cbbce3b08ed4 and af8471b92406

Revision ID: merge_cbb_af84
Revises: cbbce3b08ed4, af8471b92406
Create Date: 2026-02-10 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'merge_cbb_af84'
down_revision: Union[str, Sequence[str], None] = ('cbbce3b08ed4', 'af8471b92406')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
