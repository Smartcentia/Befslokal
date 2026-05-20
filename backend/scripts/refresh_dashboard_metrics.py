#!/usr/bin/env python3
"""
Refresh DashboardMetrics table.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.db.session import engine, SessionLocal
from app.db.session import engine, SessionLocal
from app.core.config import settings
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = settings.DATABASE_URL

async def refresh_metrics():
    """Refresh dashboard metrics in database."""
    
    # Use imported shared SessionLocal
    async with SessionLocal() as db:
        # Calculate properties count and maintenance
        print("📊 Calculating property metrics...")
        result = await db.execute(text("""
            SELECT
                COUNT(*) as count,
                COALESCE(SUM(
                    COALESCE((external_data->'financials'->>'total_maintenance')::float, 0) +
                    COALESCE((external_data->'financials'->>'total_manual_expenses')::float, 0) +
                    COALESCE((external_data->'financials'->>'total_spend_csv')::float, 0)
                ), 0) as maintenance
            FROM properties
        """))
        prop_stats = result.one()
        print(f"   Properties: {prop_stats.count}")
        print(f"   Total Maintenance: {prop_stats.maintenance:,.0f} NOK")

        # Calculate contracts count and rent
        print("\n📊 Calculating contract metrics...")
        result = await db.execute(text("""
            SELECT
                COUNT(*) as count,
                COALESCE(SUM((amount->>'amount_per_year')::float), 0) as rent
            FROM contracts
            WHERE status = 'active'
        """))
        contract_stats = result.one()
        print(f"   Active Contracts: {contract_stats.count}")
        print(f"   Total Annual Rent: {contract_stats.rent:,.0f} NOK")

        # Calculate risks
        result = await db.execute(text("SELECT COUNT(*) FROM risk_assessments"))
        risks_count = result.scalar() or 0
        print(f"   Risks: {risks_count}")

        # Ensure dashboard_metrics table exists (use metric_id as primary key to match model)
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS dashboard_metrics (
                metric_id SERIAL PRIMARY KEY,
                properties_count INTEGER DEFAULT 0,
                contracts_count INTEGER DEFAULT 0,
                risks_count INTEGER DEFAULT 0,
                total_annual_rent FLOAT DEFAULT 0,
                total_maintenance_cost FLOAT DEFAULT 0,
                last_updated TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Check if row exists
        result = await db.execute(text("SELECT metric_id FROM dashboard_metrics LIMIT 1"))
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing
            await db.execute(text("""
                UPDATE dashboard_metrics SET
                    properties_count = :props,
                    contracts_count = :contracts,
                    risks_count = :risks,
                    total_annual_rent = :rent,
                    total_maintenance_cost = :maintenance,
                    last_updated = NOW()
            """), {
                "props": prop_stats.count,
                "contracts": contract_stats.count,
                "risks": risks_count,
                "rent": contract_stats.rent,
                "maintenance": prop_stats.maintenance
            })
            print("\n✅ Updated existing dashboard_metrics row")
        else:
            # Insert new
            await db.execute(text("""
                INSERT INTO dashboard_metrics (properties_count, contracts_count, risks_count, total_annual_rent, total_maintenance_cost)
                VALUES (:props, :contracts, :risks, :rent, :maintenance)
            """), {
                "props": prop_stats.count,
                "contracts": contract_stats.count,
                "risks": risks_count,
                "rent": contract_stats.rent,
                "maintenance": prop_stats.maintenance
            })
            print("\n✅ Inserted new dashboard_metrics row")

        await db.commit()

        # Verify
        result = await db.execute(text("SELECT * FROM dashboard_metrics LIMIT 1"))
        row = result.one()
        print(f"\n📊 Final DashboardMetrics:")
        print(f"   Properties: {row.properties_count}")
        print(f"   Contracts: {row.contracts_count}")
        print(f"   Risks: {row.risks_count}")
        print(f"   Total Annual Rent: {row.total_annual_rent:,.0f} NOK")
        print(f"   Total Maintenance: {row.total_maintenance_cost:,.0f} NOK")
        print(f"   Last Updated: {row.last_updated}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(refresh_metrics())
