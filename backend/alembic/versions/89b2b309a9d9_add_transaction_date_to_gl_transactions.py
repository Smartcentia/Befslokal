"""add_transaction_date_to_gl_transactions

Revision ID: 89b2b309a9d9
Revises: 20260303_gl_nullable
Create Date: 2026-03-09 11:52:32.238773

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89b2b309a9d9'
down_revision: Union[str, Sequence[str], None] = '20260303_gl_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('gl_transactions', sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('gl_transactions', 'transaction_date')
