"""add_cost_forecast_tables

Revision ID: 20260122_forecast
Revises: e33b8f92c441
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '20260122_forecast'
down_revision = 'e33b8f92c441'
branch_labels = None
depends_on = None


def upgrade():
    """Create forecast_cache, scenarios, and action_recommendations tables."""
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Avhengig av properties – hopp over hvis den mangler (f.eks. ny/annen DB)
    if 'properties' not in existing_tables:
        return

    # Check if properties.property_id column exists
    has_property_id = False
    if 'properties' in existing_tables:
        property_columns = [c['name'] for c in inspector.get_columns('properties')]
        has_property_id = 'property_id' in property_columns

    # 1. forecast_cache - Caching layer for expensive cost forecasts
    if 'forecast_cache' not in existing_tables:
        if has_property_id:
            op.create_table(
                'forecast_cache',
                sa.Column('forecast_id', UUID(as_uuid=True), primary_key=True,
                          server_default=sa.text('gen_random_uuid()')),
                sa.Column('property_id', UUID(as_uuid=True),
                          sa.ForeignKey('properties.property_id', ondelete='CASCADE'),
                          nullable=True,
                          comment='Property ID (nullable for portfolio-wide forecasts)'),
            sa.Column('forecast_type', sa.String(50), nullable=False,
                      comment='Type: cash_flow, cost_forecast, monte_carlo'),
            sa.Column('parameters', JSONB, nullable=False,
                      comment='Forecast parameters (months_ahead, kpi_adjustment, etc)'),
            sa.Column('result', JSONB, nullable=False,
                      comment='Full forecast data with P10/P50/P90'),
                sa.Column('created_at', sa.DateTime(timezone=True),
                          server_default=sa.func.now()),
                sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False,
                          comment='Auto-delete after this timestamp (24h TTL)'),
            )
        else:
            # Create without FK if property_id column doesn't exist
            op.create_table(
                'forecast_cache',
                sa.Column('forecast_id', UUID(as_uuid=True), primary_key=True,
                          server_default=sa.text('gen_random_uuid()')),
                sa.Column('property_id', UUID(as_uuid=True),
                          nullable=True,
                          comment='Property ID (nullable for portfolio-wide forecasts)'),
                sa.Column('forecast_type', sa.String(50), nullable=False,
                          comment='Type: cash_flow, cost_forecast, monte_carlo'),
                sa.Column('parameters', JSONB, nullable=False,
                          comment='Forecast parameters (months_ahead, kpi_adjustment, etc)'),
                sa.Column('result', JSONB, nullable=False,
                          comment='Full forecast data with P10/P50/P90'),
                sa.Column('created_at', sa.DateTime(timezone=True),
                          server_default=sa.func.now()),
                sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False,
                          comment='Auto-delete after this timestamp (24h TTL)'),
            )

        # Indexes for forecast_cache
        op.create_index('idx_forecast_property', 'forecast_cache', ['property_id'])
        op.create_index('idx_forecast_expiry', 'forecast_cache', ['expires_at'])
        op.create_index('idx_forecast_type', 'forecast_cache', ['forecast_type'])
        op.create_index('idx_forecast_created', 'forecast_cache', ['created_at'])

    # 2. scenarios - User-created cost scenarios
    if 'scenarios' not in existing_tables:
        op.create_table(
            'scenarios',
            sa.Column('scenario_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.String(200), nullable=False,
                      comment='User-friendly scenario name'),
            sa.Column('description', sa.Text, nullable=True,
                      comment='Scenario description'),
            sa.Column('base_forecast_id', UUID(as_uuid=True),
                      sa.ForeignKey('forecast_cache.forecast_id', ondelete='SET NULL'),
                      nullable=True,
                      comment='Reference to baseline forecast'),
            sa.Column('modifications', JSONB, nullable=False,
                      comment='List of changes applied to baseline'),
            sa.Column('result_forecast', JSONB, nullable=False,
                      comment='Resulting forecast after modifications'),
            sa.Column('created_by', sa.String(100), nullable=True,
                      comment='User ID or email'),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now()),
        )

        # Indexes for scenarios
        op.create_index('idx_scenarios_created_by', 'scenarios', ['created_by'])
        op.create_index('idx_scenarios_created_at', 'scenarios', ['created_at'])
        op.create_index('idx_scenarios_base_forecast', 'scenarios', ['base_forecast_id'])

    # 3. action_recommendations - AI-generated cost reduction opportunities
    if 'action_recommendations' not in existing_tables:
        op.create_table(
            'action_recommendations',
            sa.Column('recommendation_id', UUID(as_uuid=True), primary_key=True,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('recommendation_type', sa.String(50), nullable=False,
                      comment='Type: kpi_adjustment, renegotiation, consolidation, etc'),
            sa.Column('target_entity_type', sa.String(50), nullable=False,
                      comment='Entity type: contract, property'),
            sa.Column('target_entity_id', UUID(as_uuid=True), nullable=False,
                      comment='ID of target contract/property'),
            sa.Column('priority', sa.Integer, nullable=False, default=3,
                      comment='Priority 1-5 (1=highest cost savings)'),
            sa.Column('estimated_impact_nok', sa.Numeric(15, 2), nullable=False,
                      comment='Estimated annual cost savings in NOK'),
            sa.Column('description', sa.Text, nullable=False,
                      comment='Human-readable action description'),
            sa.Column('ai_rationale', sa.Text, nullable=True,
                      comment='GPT-4 explanation of why this recommendation was made'),
            sa.Column('status', sa.String(20), nullable=False, default='pending',
                      comment='Status: pending, simulated, executed'),
            sa.Column('created_at', sa.DateTime(timezone=True),
                      server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True),
                      onupdate=sa.func.now()),
        )

        # Indexes for action_recommendations
        op.create_index('idx_recommendations_priority', 'action_recommendations', ['priority'])
        op.create_index('idx_recommendations_impact', 'action_recommendations', ['estimated_impact_nok'])
        op.create_index('idx_recommendations_status', 'action_recommendations', ['status'])
        op.create_index('idx_recommendations_entity', 'action_recommendations',
                        ['target_entity_type', 'target_entity_id'])
        op.create_index('idx_recommendations_created', 'action_recommendations', ['created_at'])

    # Performance indexes for gl_transactions – avhengig av faktisk tabellstruktur (period vs year/month)
    if 'gl_transactions' in existing_tables:
        cols = [c['name'] for c in inspector.get_columns('gl_transactions')]
        if 'period' in cols:
            op.execute("CREATE INDEX IF NOT EXISTS idx_gl_period_amount ON gl_transactions(period, amount)")
            op.execute("CREATE INDEX IF NOT EXISTS idx_gl_property_period ON gl_transactions(property_id, period)")
        elif 'year' in cols and 'month' in cols:
            op.execute("CREATE INDEX IF NOT EXISTS idx_gl_year_month_amount ON gl_transactions(year, month, amount)")
            op.execute("CREATE INDEX IF NOT EXISTS idx_gl_property_year_month ON gl_transactions(property_id, year, month)")

    if 'contracts' in existing_tables:
        op.execute("CREATE INDEX IF NOT EXISTS idx_contracts_end_date ON contracts((external_data->>'end_date'))")


def downgrade():
    """Drop forecast tables and indexes."""

    # Drop performance indexes (både period- og year/month-variant)
    op.execute("DROP INDEX IF EXISTS idx_contracts_end_date")
    op.execute("DROP INDEX IF EXISTS idx_gl_property_period")
    op.execute("DROP INDEX IF EXISTS idx_gl_period_amount")
    op.execute("DROP INDEX IF EXISTS idx_gl_property_year_month")
    op.execute("DROP INDEX IF EXISTS idx_gl_year_month_amount")

    # Drop action_recommendations
    op.drop_index('idx_recommendations_created', 'action_recommendations')
    op.drop_index('idx_recommendations_entity', 'action_recommendations')
    op.drop_index('idx_recommendations_status', 'action_recommendations')
    op.drop_index('idx_recommendations_impact', 'action_recommendations')
    op.drop_index('idx_recommendations_priority', 'action_recommendations')
    op.drop_table('action_recommendations')

    # Drop scenarios
    op.drop_index('idx_scenarios_base_forecast', 'scenarios')
    op.drop_index('idx_scenarios_created_at', 'scenarios')
    op.drop_index('idx_scenarios_created_by', 'scenarios')
    op.drop_table('scenarios')

    # Drop forecast_cache
    op.drop_index('idx_forecast_created', 'forecast_cache')
    op.drop_index('idx_forecast_type', 'forecast_cache')
    op.drop_index('idx_forecast_expiry', 'forecast_cache')
    op.drop_index('idx_forecast_property', 'forecast_cache')
    op.drop_table('forecast_cache')
