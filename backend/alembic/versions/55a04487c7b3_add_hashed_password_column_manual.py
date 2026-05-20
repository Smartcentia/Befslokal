"""add hashed_password column manual

Revision ID: 55a04487c7b3
Revises: b41edf14a7be
Create Date: 2026-02-06 13:40:58.855464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55a04487c7b3'
down_revision: Union[str, Sequence[str], None] = 'b41edf14a7be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'hashed_password')
