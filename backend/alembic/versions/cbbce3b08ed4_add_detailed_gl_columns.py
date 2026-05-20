"""add_detailed_gl_columns_v2

Revision ID: cbbce3b08ed4
Revises: 6b2bea70fd4d
Create Date: 2026-02-10 22:40:17.315591

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbbce3b08ed4'
down_revision: Union[str, Sequence[str], None] = '6b2bea70fd4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - using raw SQL for memory efficiency."""
    # Use raw SQL to check and add columns - more memory efficient than Inspector
    conn = op.get_bind()
    
    # Add columns only if they don't exist
    columns_to_add = [
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS region_code VARCHAR(10)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS region_name VARCHAR(100)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS department_code VARCHAR(20)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS department_name VARCHAR(200)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS dim2_code VARCHAR(20)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS dim2_name VARCHAR(200)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS purpose_code VARCHAR(20)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS purpose_name VARCHAR(200)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS account_name VARCHAR(200)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS ba_code VARCHAR(10)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS ba_name VARCHAR(100)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS supplier_id VARCHAR(20)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS supplier_name VARCHAR(200)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(50)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS period VARCHAR(6)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS state_account VARCHAR(20)",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()",
        "ALTER TABLE gl_transactions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()",
    ]
    
    for sql in columns_to_add:
        conn.execute(sa.text(sql))
    
    # Add indexes only if they don't exist
    indexes_to_add = [
        "CREATE INDEX IF NOT EXISTS idx_gl_period_v2 ON gl_transactions(period)",
        "CREATE INDEX IF NOT EXISTS idx_gl_supplier_v2 ON gl_transactions(supplier_id)",
        "CREATE INDEX IF NOT EXISTS idx_gl_dept_code ON gl_transactions(department_code)",
    ]
    
    for sql in indexes_to_add:
        conn.execute(sa.text(sql))


def downgrade() -> None:
    """Downgrade schema."""
    # Simple column drops - they'll error if columns don't exist, which is fine for downgrade
    cols = [
        'updated_at', 'created_at', 'state_account', 'period', 'invoice_number',
        'supplier_name', 'supplier_id', 'ba_name', 'ba_code', 'account_name',
        'purpose_name', 'purpose_code', 'dim2_name', 'dim2_code',
        'department_name', 'department_code', 'region_name', 'region_code'
    ]
    
    for col in cols:
        op.drop_column('gl_transactions', col)
