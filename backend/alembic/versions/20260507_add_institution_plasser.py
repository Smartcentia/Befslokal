"""add_institution_plasser

Revision ID: 20260507_institution_plasser
Revises: 20260505_merge_all_heads
Create Date: 2026-05-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '20260507_institution_plasser'
down_revision = '20260505_finance_budget'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Bruk IF NOT EXISTS for idempotent migrering (tabellen kan allerede eksistere)
    op.execute("""
        CREATE TABLE IF NOT EXISTS institution_plasser (
            id UUID NOT NULL,
            koststed_kode VARCHAR(20) NOT NULL,
            property_id UUID,
            region VARCHAR(50),
            malgruppe VARCHAR(100),
            enhetsnr INTEGER,
            institusjons_navn VARCHAR(200),
            avdelings_navn VARCHAR(200),
            antall_kvalitetssikrede INTEGER,
            antall_budsjetterte INTEGER,
            rapport_dato DATE NOT NULL,
            import_batch_id UUID,
            imported_at TIMESTAMPTZ DEFAULT now(),
            imported_by VARCHAR(100),
            PRIMARY KEY (id),
            FOREIGN KEY (property_id) REFERENCES properties(property_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_ip_property ON institution_plasser (property_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ip_dato ON institution_plasser (rapport_dato)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_ip_koststed ON institution_plasser (koststed_kode)")


def downgrade() -> None:
    op.drop_index('idx_ip_koststed', table_name='institution_plasser')
    op.drop_index('idx_ip_dato', table_name='institution_plasser')
    op.drop_index('idx_ip_property', table_name='institution_plasser')
    op.drop_table('institution_plasser')
