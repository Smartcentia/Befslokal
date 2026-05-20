"""Add department_code and department_name to properties

Revision ID: 20260312_dept_code_name
Revises: 20260312_desc_area_cname
Create Date: 2026-03-12

"""
from alembic import op
import sqlalchemy as sa

revision = "20260312_dept_code_name"
down_revision = "20260312_desc_area_cname"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("department_code", sa.String(), nullable=True),
    )
    op.add_column(
        "properties",
        sa.Column("department_name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("properties", "department_name")
    op.drop_column("properties", "department_code")
