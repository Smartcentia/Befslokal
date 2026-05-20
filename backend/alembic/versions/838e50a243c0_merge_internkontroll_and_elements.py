"""merge_internkontroll_and_elements

Revision ID: 838e50a243c0
Revises: 20260203_checklist, e37b8113d0ea
Create Date: 2026-02-03 10:35:21.000831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '838e50a243c0'
down_revision: Union[str, Sequence[str], None] = ('20260203_checklist', 'e37b8113d0ea')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
