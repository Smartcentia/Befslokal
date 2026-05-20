"""merge_heads_for_synthetic_flag

Revision ID: 4f1eeccfdd2a
Revises: 20260210_add_syn_fin, bb7c02b45f5a
Create Date: 2026-02-10 13:28:33.990320

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f1eeccfdd2a'
down_revision: Union[str, Sequence[str], None] = ('20260210_add_syn_fin', 'bb7c02b45f5a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
