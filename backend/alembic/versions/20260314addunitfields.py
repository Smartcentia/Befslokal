"""Add unit fields (stub – applied directly to DB, file was missing)

Revision ID: 20260314addunitfields
Revises: 20260312_dept_code_name
Create Date: 2026-03-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260314addunitfields'
down_revision: Union[str, Sequence[str], None] = '20260312_dept_code_name'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Schema changes were applied directly – no-op stub."""
    pass


def downgrade() -> None:
    """No-op stub."""
    pass
