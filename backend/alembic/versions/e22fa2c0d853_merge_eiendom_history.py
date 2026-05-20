"""merge_eiendom_history

Revision ID: e22fa2c0d853
Revises: 005_contract_filename, 556f14e5ca0b
Create Date: 2026-01-12 21:42:14.816205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e22fa2c0d853'
down_revision: Union[str, Sequence[str], None] = ('005_contract_filename', '556f14e5ca0b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
