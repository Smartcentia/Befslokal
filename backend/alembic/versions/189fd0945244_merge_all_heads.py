"""merge_all_heads

Revision ID: 189fd0945244
Revises: add_pgvector, 20260122_forecast, 5a365ed3fbd8, add_email_verification_mfa, add_infrastructure_costs
Create Date: 2026-01-29 10:10:03.703588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '189fd0945244'
down_revision: Union[str, Sequence[str], None] = ('add_pgvector', '20260122_forecast', '5a365ed3fbd8', 'add_email_verification_mfa', 'add_infrastructure_costs')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
