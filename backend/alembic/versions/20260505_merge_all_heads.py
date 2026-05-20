"""merge all divergent heads before finance_budget

Revision ID: 20260505_merge_all_heads
Revises: 005_contract_filename, 20260122_forecast, 20260203_checklist,
         20260203_is_active, 20260207_knowledge_graph, 20260210_add_syn_fin,
         20260219_create_budget_table, 20260222_add_edon2_fields,
         20260303_gl_nullable, 20260406_risk_confidence, 20260408_innkjop_import,
         20260413_ompostering, 20260504_agresso_budgets, 9f8a7b6c5d4e,
         a1b2c3d4e5f6, add_email_verification_mfa, add_gl_transactions,
         add_infrastructure_costs, add_pgvector
Create Date: 2026-05-05

No-op merge that consolidates all divergent migration heads so that
the finance_budget migration (20260505_finance_budget) has a single
clean parent. The production DB is stamped at this revision directly.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260505_merge_all_heads"
down_revision = (
    "005_contract_filename",
    "20260122_forecast",
    "20260203_checklist",
    "20260203_is_active",
    "20260207_knowledge_graph",
    "20260210_add_syn_fin",
    "20260219_create_budget_table",
    "20260222_add_edon2_fields",
    "20260303_gl_nullable",
    "20260406_risk_confidence",
    "20260408_innkjop_import",
    "20260413_ompostering",
    "20260504_agresso_budgets",
    "9f8a7b6c5d4e",
    "a1b2c3d4e5f6",
    "add_email_verification_mfa",
    "add_gl_transactions",
    "add_infrastructure_costs",
    "add_pgvector",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
