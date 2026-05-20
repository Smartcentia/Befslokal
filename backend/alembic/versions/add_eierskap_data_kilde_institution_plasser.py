"""Add eierskap and data_kilde to institution_plasser

Revision ID: add_eierskap_data_kilde_inst
Revises:
Branch: None

Adds:
- eierskap VARCHAR(30): 'Statlig', 'Privat, ideell', 'Privat, kommersiell', 'Kommunal'
- data_kilde VARCHAR(50): 'bufetat_csv_2026', 'era_birk_2026'

Also backfills existing rows with eierskap='Statlig' and data_kilde='bufetat_csv_2026'.
"""
from alembic import op
from sqlalchemy import text, inspect

revision = 'add_eierskap_data_kilde_inst'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # Check table exists
    if 'institution_plasser' not in inspector.get_table_names():
        return

    existing_cols = {col['name'] for col in inspector.get_columns('institution_plasser')}

    if 'eierskap' not in existing_cols:
        conn.execute(text("ALTER TABLE institution_plasser ADD COLUMN eierskap VARCHAR(30)"))

    if 'data_kilde' not in existing_cols:
        conn.execute(text("ALTER TABLE institution_plasser ADD COLUMN data_kilde VARCHAR(50)"))

    # Backfill existing rows (Bufetat CSV import) with Statlig / bufetat_csv_2026
    conn.execute(text("""
        UPDATE institution_plasser
        SET eierskap = 'Statlig', data_kilde = 'bufetat_csv_2026'
        WHERE eierskap IS NULL AND data_kilde IS NULL
    """))


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_cols = {col['name'] for col in inspector.get_columns('institution_plasser')}
    if 'eierskap' in existing_cols:
        conn.execute(text("ALTER TABLE institution_plasser DROP COLUMN eierskap"))
    if 'data_kilde' in existing_cols:
        conn.execute(text("ALTER TABLE institution_plasser DROP COLUMN data_kilde"))
