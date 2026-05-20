"""Merge all heads 2026-05-08

Revision ID: 20260508_merge2
Revises: 20260505_merge_all_heads, 20260507_institution_plasser, 20260508_lydia_enrich
Create Date: 2026-05-08
"""
from alembic import op

revision = '20260508_merge2'
down_revision = ('20260505_merge_all_heads', '20260507_institution_plasser', '20260508_lydia_enrich')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
