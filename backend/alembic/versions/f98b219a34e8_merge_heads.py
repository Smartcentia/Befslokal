"""merge heads

Revision ID: f98b219a34e8
Revises: 20260219_create_budget_table, 20260222_add_edon2_fields
Create Date: 2026-02-22 11:29:15.108294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f98b219a34e8'
down_revision: Union[str, Sequence[str], None] = ('20260219_create_budget_table', '20260222_add_edon2_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
