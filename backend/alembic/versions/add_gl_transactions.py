"""Add gl_transactions table for General Ledger data

Revision ID: add_gl_transactions
Revises: 
Create Date: 2026-01-10 08:35:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = 'add_gl_transactions'
down_revision = '001_initial'  # Depends on initial migration
branch_labels = None
depends_on = None


def upgrade():
    """Create gl_transactions table for importing accounting data."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'gl_transactions' not in existing_tables:
        # Check if properties.property_id exists before creating FK
        has_property_id = conn.execute(sa.text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'properties'
                    AND column_name = 'property_id'
            )
        """)).scalar()

        if has_property_id:
            # Create table with FK
            op.create_table(
                'gl_transactions',
                sa.Column('transaction_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
                sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column('region_code', sa.String(10)),
                sa.Column('region_name', sa.String(100)),
                sa.Column('department_code', sa.String(20)),
                sa.Column('department_name', sa.String(200)),
                sa.Column('dim2_code', sa.String(20)),
                sa.Column('dim2_name', sa.String(200)),
                sa.Column('purpose_code', sa.String(20)),
                sa.Column('purpose_name', sa.String(200)),
                sa.Column('account_code', sa.String(20)),
                sa.Column('account_name', sa.String(200)),
                sa.Column('ba_code', sa.String(10)),
                sa.Column('ba_name', sa.String(100)),
                sa.Column('supplier_id', sa.String(20)),
                sa.Column('supplier_name', sa.String(200)),
                sa.Column('invoice_number', sa.String(50)),
                sa.Column('amount', sa.Numeric(15, 2)),
                sa.Column('period', sa.String(6)),  # YYYYMM
                sa.Column('state_account', sa.String(20)),
                sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
                sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
                sa.ForeignKeyConstraint(['property_id'], ['properties.property_id'], ondelete='SET NULL'),
            )
        else:
            # Create table without FK
            op.create_table(
                'gl_transactions',
                sa.Column('transaction_id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
                sa.Column('property_id', postgresql.UUID(as_uuid=True), nullable=True),
                sa.Column('region_code', sa.String(10)),
                sa.Column('region_name', sa.String(100)),
                sa.Column('department_code', sa.String(20)),
                sa.Column('department_name', sa.String(200)),
                sa.Column('dim2_code', sa.String(20)),
                sa.Column('dim2_name', sa.String(200)),
                sa.Column('purpose_code', sa.String(20)),
                sa.Column('purpose_name', sa.String(200)),
                sa.Column('account_code', sa.String(20)),
                sa.Column('account_name', sa.String(200)),
                sa.Column('ba_code', sa.String(10)),
                sa.Column('ba_name', sa.String(100)),
                sa.Column('supplier_id', sa.String(20)),
                sa.Column('supplier_name', sa.String(200)),
                sa.Column('invoice_number', sa.String(50)),
                sa.Column('amount', sa.Numeric(15, 2)),
                sa.Column('period', sa.String(6)),  # YYYYMM
                sa.Column('state_account', sa.String(20)),
                sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()')),
                sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()')),
            )

        # Create indexes for common queries (idempotent)
        op.execute("CREATE INDEX IF NOT EXISTS idx_gl_period ON gl_transactions(period)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_gl_property ON gl_transactions(property_id)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_gl_supplier ON gl_transactions(supplier_id)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_gl_account ON gl_transactions(account_code)")
        op.execute("CREATE INDEX IF NOT EXISTS idx_gl_amount ON gl_transactions(amount)")


def downgrade():
    """Drop gl_transactions table."""
    op.drop_index('idx_gl_amount', 'gl_transactions')
    op.drop_index('idx_gl_account', 'gl_transactions')
    op.drop_index('idx_gl_supplier', 'gl_transactions')
    op.drop_index('idx_gl_property', 'gl_transactions')
    op.drop_index('idx_gl_period', 'gl_transactions')
    op.drop_table('gl_transactions')
