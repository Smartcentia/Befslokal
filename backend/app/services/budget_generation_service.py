"""
Budget Generation Service - Generate synthetic budgets based on actual costs.

Since no budget data exists in the system, this service creates realistic budgets by:
1. Analyzing last 12 months of actual costs
2. Applying inflation adjustment (KPI)
3. Adding realistic variance per cost category
4. Storing in budget table for comparison

Author: KI Kollega (AI Assistant)
Date: 2026-01-22
"""

import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.dialects.postgresql import insert

from app.models.financial_models import Budget, GLTransaction
from app.services.analytics.cost_analysis_service import (
    CostCategory,
    analyze_property_costs,
    categorize_expense,
)
from app.domains.core.utils.region_mapping import COUNTY_TO_REGION

logger = logging.getLogger(__name__)


class BudgetGenerationService:
    """
    Generates synthetic budgets based on historical cost data.

    For public sector organizations without existing budget data,
    this service creates baseline budgets from actual costs.
    """

    # Default inflation rate for Norway 2026 (SSB estimate)
    DEFAULT_INFLATION_RATE = 0.035  # 3.5%

    # Realistic budget variance by category (budget planning uncertainty)
    CATEGORY_VARIANCE = {
        CostCategory.PROPERTY.value: 0.05,      # 5% - rent is predictable
        CostCategory.OPERATIONS.value: 0.15,    # 15% - utilities vary
        CostCategory.INVESTMENT.value: 0.30,    # 30% - capital projects uncertain
        CostCategory.OTHER.value: 0.20,         # 20% - miscellaneous
        "property": 0.05,
        "operations": 0.15,
        "investment": 0.30,
        "other": 0.20
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def generate_property_budget(
        self,
        db: AsyncSession,
        property_id: str,
        year: int,
        inflation_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate budget for a single property based on historical costs.

        Args:
            db: Database session
            property_id: Property UUID
            year: Budget year
            inflation_rate: KPI adjustment (default: 3.5%)

        Returns:
            Dict with budget data by category and month
        """
        if inflation_rate is None:
            inflation_rate = self.DEFAULT_INFLATION_RATE

        self.logger.info(f"Generating budget for property {property_id}, year {year}")

        # Get historical costs from last 12 months
        result = await db.execute(text("""
            SELECT
                category,
                AVG(amount) as avg_monthly_amount,
                STDDEV(amount) as stddev_amount,
                COUNT(*) as num_transactions
            FROM gl_transactions
            WHERE property_id = :property_id
              AND transaction_date >= NOW() - INTERVAL '12 months'
              AND transaction_date < NOW()
            GROUP BY category
        """), {"property_id": property_id})

        historical_data = result.fetchall()

        if not historical_data:
            self.logger.warning(f"No historical cost data for property {property_id}")
            return self._generate_fallback_budget(db, property_id, year, inflation_rate)

        # Generate budget per category
        budget_entries = []
        total_budget = 0.0

        for row in historical_data:
            category = row[0]
            avg_monthly = float(row[1] or 0)
            stddev = float(row[2] or 0)

            # Apply inflation adjustment
            base_amount = avg_monthly * (1 + inflation_rate)

            # Add variance based on category
            variance_factor = self.CATEGORY_VARIANCE.get(category, 0.10)
            variance = base_amount * variance_factor * random.uniform(-1, 1)

            budgeted_amount = base_amount + variance

            # Generate monthly budgets (all 12 months)
            for month in range(1, 13):
                # Add some monthly seasonality (e.g., higher costs in winter)
                seasonal_factor = self._get_seasonal_factor(category, month)
                monthly_budget = budgeted_amount * seasonal_factor

                budget_entries.append({
                    "property_id": property_id,
                    "year": year,
                    "month": month,
                    "category": category,
                    "category": category,
                    "amount": round(monthly_budget, 2),
                    "is_synthetic": True,
                    "data_source": "budget_generator"
                })

                total_budget += monthly_budget

        return {
            "property_id": property_id,
            "year": year,
            "inflation_rate": inflation_rate,
            "total_annual_budget": round(total_budget, 2),
            "budget_entries": budget_entries,
            "num_categories": len(historical_data)
        }

    async def _generate_fallback_budget(
        self,
        db: AsyncSession,
        property_id: str,
        year: int,
        inflation_rate: float,
        quiet: bool = False,
    ) -> Dict[str, Any]:
        """
        Fallback: Generate budget from contract data if no GL transactions exist.
        """
        if not quiet:
            self.logger.info(f"Using fallback budget generation from contracts for {property_id}")

        # Get annual rent from contracts
        result = await db.execute(text("""
            SELECT
                COALESCE(SUM(
                    COALESCE(
                        (c.amount->>'total_per_year')::float,
                        (c.amount->>'amount_per_year')::float,
                        (c.amount->>'monthly_rent')::float * 12,
                        0
                    )
                ), 0) as annual_rent
            FROM contracts c
            JOIN units u ON c.unit_id = u.unit_id
            WHERE u.property_id = :property_id
              AND c.status = 'active'
        """), {"property_id": property_id})

        annual_rent = float(result.scalar() or 0)

        if annual_rent == 0:
            if not quiet:
                self.logger.warning(f"No contract data for property {property_id}, skipping fallback budget")
            return {
                "property_id": property_id,
                "year": year,
                "inflation_rate": inflation_rate,
                "total_annual_budget": 0.0,
                "budget_entries": [],
                "num_categories": 0,
                "fallback": True,
            }

        # Estimate costs based on typical ratios (from cost_analysis_service.py)
        # Property costs: ~100% of rent (leie)
        # Operations: ~15% of rent (drift)
        monthly_rent = annual_rent / 12

        budget_entries = []

        # Property costs (lease)
        for month in range(1, 13):
            budget_entries.append({
                "property_id": property_id,
                "year": year,
                "month": month,
                "month": month,
                "category": "property",
                "amount": round(monthly_rent * (1 + inflation_rate), 2),
                "is_synthetic": True,
                "data_source": "budget_generator_fallback"
            })

        # Operations costs
        monthly_ops = (annual_rent * 0.15) / 12
        for month in range(1, 13):
            seasonal_factor = self._get_seasonal_factor("operations", month)
            budget_entries.append({
                "property_id": property_id,
                "year": year,
                "month": month,
                "category": "operations",
                "amount": round(monthly_ops * (1 + inflation_rate) * seasonal_factor, 2),
                "is_synthetic": True,
                "data_source": "budget_generator_fallback"
            })

        total_budget = sum(e["amount"] for e in budget_entries)

        return {
            "property_id": property_id,
            "year": year,
            "inflation_rate": inflation_rate,
            "total_annual_budget": round(total_budget, 2),
            "budget_entries": budget_entries,
            "num_categories": 2,
            "fallback": True
        }

    def _get_seasonal_factor(self, category: str, month: int) -> float:
        """
        Get seasonal adjustment factor for budget estimates.

        Winter months (Nov-Feb) have higher operations costs (heating).
        Summer months (Jun-Aug) have lower costs.
        """
        if category in ["operations", CostCategory.OPERATIONS.value]:
            # Higher costs in winter
            if month in [11, 12, 1, 2]:
                return 1.2
            # Lower costs in summer
            elif month in [6, 7, 8]:
                return 0.8

        return 1.0  # No seasonality for other categories

    async def generate_property_budget_from_consumption(
        self,
        db: AsyncSession,
        property_data: Dict[str, Any],
        year: int,
        variance_pct: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate budget for a single property from actual consumption (manual_expenses).

        Uses cost_analysis_service.analyze_property_costs to categorize expenses,
        then applies ±variance_pct per category and distributes over 12 months.

        Args:
            db: Database session (for annual_rent and fallback)
            property_data: Dict with property_id, name, external_data
            year: Budget year
            variance_pct: Variance per category (default 0.2 = ±20%)

        Returns:
            Same structure as generate_property_budget: budget_entries, total_annual_budget, etc.
        """
        property_id = str(property_data.get("property_id", ""))
        self.logger.info(f"Generating budget from consumption for property {property_id}, year {year}")

        # Hent årlig husleie fra kontrakter (kun for analyse, ikke for budsjettbeløp)
        result = await db.execute(text("""
            SELECT
                COALESCE(SUM(
                    COALESCE(
                        (c.amount->>'total_per_year')::float,
                        (c.amount->>'amount_per_year')::float,
                        (c.amount->>'monthly_rent')::float * 12,
                        0
                    )
                ), 0) as annual_rent
            FROM contracts c
            JOIN units u ON c.unit_id = u.unit_id
            WHERE u.property_id = :property_id
              AND c.status = 'active'
        """), {"property_id": property_id})
        annual_rent = float(result.scalar() or 0)

        analysis = analyze_property_costs(property_data, annual_rent)

        if analysis.total_costs == 0:
            self.logger.warning(f"No consumption data for property {property_id}, using fallback budget")
            return await self._generate_fallback_budget(
                db, property_id, year, self.DEFAULT_INFLATION_RATE
            )

        # Kategorier med årlig budsjett = faktisk * random(1 - variance_pct, 1 + variance_pct)
        categories = [
            (CostCategory.PROPERTY.value, analysis.property_costs),
            (CostCategory.OPERATIONS.value, analysis.operations_costs),
            (CostCategory.INVESTMENT.value, analysis.investment_costs),
            (CostCategory.OTHER.value, analysis.other_costs),
        ]

        budget_entries = []
        total_budget = 0.0

        for category_name, category_total in categories:
            if category_total <= 0:
                continue
            budget_annual = category_total * random.uniform(1 - variance_pct, 1 + variance_pct)
            # Fordel på 12 måneder (med sesong for operations)
            for month in range(1, 13):
                seasonal = self._get_seasonal_factor(category_name, month)
                monthly_amount = (budget_annual / 12) * seasonal
                budget_entries.append({
                    "property_id": property_id,
                    "year": year,
                    "month": month,
                    "category": category_name,
                    "category": category_name,
                    "amount": round(monthly_amount, 2),
                    "is_synthetic": True,
                    "data_source": "budget_generator_consumption"
                })
                total_budget += monthly_amount

        return {
            "property_id": property_id,
            "year": year,
            "total_annual_budget": round(total_budget, 2),
            "budget_entries": budget_entries,
            "num_categories": len([c for c in categories if c[1] > 0]),
            "source": "consumption"
        }

    async def populate_budget_from_consumption(
        self,
        db: AsyncSession,
        year: int,
        variance_pct: float = 0.2,
        property_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Batch populate budget table from consumption (manual_expenses) for all or selected properties.

        Args:
            db: Database session
            year: Budget year
            variance_pct: Variance per category (default 0.2 = ±20%)
            property_ids: Optional list of property UUIDs (default: all)

        Returns:
            Summary: properties_processed, generated, failed, total_budget_nok, entries_created
        """
        self.logger.info(f"Populating budget from consumption for year {year}, variance_pct={variance_pct}")

        if property_ids:
            property_query = text("""
                SELECT property_id, name, external_data FROM properties
                WHERE property_id = ANY(:property_ids)
            """)
            result = await db.execute(property_query, {"property_ids": property_ids})
        else:
            result = await db.execute(text("""
                SELECT property_id, name, external_data FROM properties
            """))

        rows = result.fetchall()
        # Normaliser external_data (kan være dict eller JSON-streng)
        properties = []
        for row in rows:
            prop_id, name, ext = row[0], row[1], row[2]
            if ext is None:
                ext = {}
            elif isinstance(ext, str):
                try:
                    ext = json.loads(ext) if ext else {}
                except Exception:
                    ext = {}
            else:
                ext = dict(ext) if ext else {}
            properties.append((str(prop_id), name, ext))

        self.logger.info(f"Generating budgets from consumption for {len(properties)} properties")

        total_budget_nok = 0.0
        generated_count = 0
        failed_count = 0
        all_budget_entries = []

        for prop_id, prop_name, external_data in properties:
            property_data = {"property_id": prop_id, "name": prop_name, "external_data": external_data}
            try:
                budget_data = await self.generate_property_budget_from_consumption(
                    db, property_data, year, variance_pct
                )
                all_budget_entries.extend(budget_data["budget_entries"])
                total_budget_nok += budget_data["total_annual_budget"]
                generated_count += 1
                self.logger.debug(f"Generated from consumption for {prop_name}: {budget_data['total_annual_budget']} NOK")
            except Exception as e:
                self.logger.error(f"Failed to generate budget from consumption for property {prop_id}: {e}")
                failed_count += 1

        if all_budget_entries:
            if property_ids:
                await db.execute(text("""
                    DELETE FROM budget WHERE year = :year AND property_id = ANY(:property_ids)
                """), {"year": year, "property_ids": property_ids})
            else:
                await db.execute(text("""
                    DELETE FROM budget WHERE year = :year
                """), {"year": year})
            stmt = insert(Budget).values(all_budget_entries)
            await db.execute(stmt)
            await db.commit()
            self.logger.info(f"Inserted {len(all_budget_entries)} budget entries from consumption")

        return {
            "year": year,
            "variance_pct": variance_pct,
            "properties_processed": len(properties),
            "generated": generated_count,
            "failed": failed_count,
            "total_budget_nok": round(total_budget_nok, 2),
            "entries_created": len(all_budget_entries)
        }

    async def populate_budget_table(
        self,
        db: AsyncSession,
        year: int,
        inflation_rate: Optional[float] = None,
        property_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Batch populate budget table for all properties (or specified properties).

        Args:
            db: Database session
            year: Budget year
            inflation_rate: KPI adjustment
            property_ids: Optional list of property UUIDs (default: all)

        Returns:
            Summary of generated budgets
        """
        self.logger.info(f"Populating budget table for year {year}")

        # Get list of properties
        if property_ids:
            property_query = text("""
                SELECT property_id, name FROM properties
                WHERE property_id = ANY(:property_ids)
            """)
            result = await db.execute(property_query, {"property_ids": property_ids})
        else:
            result = await db.execute(text("SELECT property_id, name FROM properties"))

        properties = result.fetchall()

        self.logger.info(f"Generating budgets for {len(properties)} properties")

        total_budget_nok = 0.0
        generated_count = 0
        failed_count = 0
        all_budget_entries = []

        for prop_id, prop_name in properties:
            try:
                budget_data = await self.generate_property_budget(
                    db, str(prop_id), year, inflation_rate
                )

                all_budget_entries.extend(budget_data["budget_entries"])
                total_budget_nok += budget_data["total_annual_budget"]
                generated_count += 1

                self.logger.debug(f"Generated budget for {prop_name}: {budget_data['total_annual_budget']} NOK")

            except Exception as e:
                self.logger.error(f"Failed to generate budget for property {prop_id}: {e}")
                failed_count += 1

        # Batch insert budgets
        if all_budget_entries:
            # Delete existing budgets for this year first
            await db.execute(text("""
                DELETE FROM budget WHERE year = :year
            """), {"year": year})

            # Insert new budgets
            stmt = insert(Budget).values(all_budget_entries)
            await db.execute(stmt)
            await db.commit()

            self.logger.info(f"Inserted {len(all_budget_entries)} budget entries")

        return {
            "year": year,
            "inflation_rate": inflation_rate or self.DEFAULT_INFLATION_RATE,
            "properties_processed": len(properties),
            "generated": generated_count,
            "failed": failed_count,
            "total_budget_nok": round(total_budget_nok, 2),
            "entries_created": len(all_budget_entries)
        }

    async def estimate_budget_from_historical_years(
        self,
        db: AsyncSession,
        source_years: List[int],
        target_year: int,
        inflation_rate: Optional[float] = None,
        property_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Estimate budget for target_year based on gl_transactions from source_years.

        Aggregates costs per (property_id, category), averages across years,
        applies inflation, and distributes over 12 months.

        Args:
            db: Database session
            source_years: Years to aggregate (e.g. [2024, 2025])
            target_year: Year to create budget for (e.g. 2026)
            inflation_rate: KPI adjustment (default 3.5%)
            property_ids: Optional list of property UUIDs (default: all with GL data)

        Returns:
            Dict with budget_entries, total_budget_nok, report (total, by_region, by_property),
            properties_with_gl, properties_fallback, entries_created
        """
        if inflation_rate is None:
            inflation_rate = self.DEFAULT_INFLATION_RATE

        def _norm_id(v):
            if v is None:
                return None
            s = str(v).strip()
            if not s:
                return None
            if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
                return s[:-2]
            return s

        # Mapping department_code → property_id (unit_id_erp)
        dept_rows = (await db.execute(text("""
            SELECT unit_id_erp, property_id FROM properties WHERE unit_id_erp IS NOT NULL
        """))).fetchall()
        dept_to_prop: Dict[str, str] = {}
        for r in dept_rows:
            if r[0]:
                k = _norm_id(r[0])
                if k:
                    dept_to_prop[k] = str(r[1])

        # Fetch GL transactions for source years (property_id IS NOT NULL)
        property_filter = ""
        params: Dict[str, Any] = {"source_years": source_years}
        if property_ids:
            property_filter = "AND property_id = ANY(:property_ids)"
            params["property_ids"] = property_ids

        result = await db.execute(text(f"""
            SELECT
                property_id,
                year,
                COALESCE(NULLIF(TRIM(category), ''), 'other') as cat,
                COALESCE(account_name, '') as account_name,
                SUM(amount) as year_total
            FROM gl_transactions
            WHERE year = ANY(:source_years)
              AND property_id IS NOT NULL
              AND amount > 0
              {property_filter}
            GROUP BY property_id, year, category, account_name
        """), params)

        rows = result.fetchall()

        # Also fetch transactions with department_code (property_id IS NULL) – match via unit_id_erp in Python
        dept_result = await db.execute(text("""
            SELECT
                department_code,
                year,
                COALESCE(NULLIF(TRIM(category), ''), 'other') as cat,
                COALESCE(account_name, '') as account_name,
                SUM(amount) as year_total
            FROM gl_transactions
            WHERE year = ANY(:source_years)
              AND property_id IS NULL
              AND department_code IS NOT NULL
              AND amount > 0
            GROUP BY department_code, year, category, account_name
        """), {"source_years": source_years})
        dept_rows_gl = dept_result.fetchall()

        # Map account_name to category when category is 'other'
        # Build (property_id, category) -> {year: total}
        by_property_category: Dict[str, Dict[str, Dict[int, float]]] = {}
        for row in rows:
            prop_id = str(row[0])
            year_val = int(row[1])
            cat = str(row[2]) if row[2] else "other"
            account_name = str(row[3]) if row[3] else ""
            year_total = float(row[4] or 0)

            if cat == "other" and account_name:
                resolved = categorize_expense(account_name, account_name)
                cat = resolved.value

            if prop_id not in by_property_category:
                by_property_category[prop_id] = {}
            if cat not in by_property_category[prop_id]:
                by_property_category[prop_id][cat] = {}
            by_property_category[prop_id][cat][year_val] = (
                by_property_category[prop_id][cat].get(year_val, 0) + year_total
            )

        # Merge department_code-matched transactions (property_id IS NULL, department_code = unit_id_erp)
        for drow in dept_rows_gl:
            dept_code = _norm_id(drow[0]) if drow[0] else None
            prop_id = dept_to_prop.get(dept_code) if dept_code else None
            if not prop_id or (property_ids and prop_id not in {str(p) for p in property_ids}):
                continue
            year_val = int(drow[1])
            cat = str(drow[2]) if drow[2] else "other"
            account_name = str(drow[3]) if drow[3] else ""
            year_total = float(drow[4] or 0)
            if cat == "other" and account_name:
                resolved = categorize_expense(account_name, account_name)
                cat = resolved.value
            if prop_id not in by_property_category:
                by_property_category[prop_id] = {}
            if cat not in by_property_category[prop_id]:
                by_property_category[prop_id][cat] = {}
            by_property_category[prop_id][cat][year_val] = (
                by_property_category[prop_id][cat].get(year_val, 0) + year_total
            )

        # Fetch property names and regions for report
        props_result = await db.execute(text("""
            SELECT property_id, name, region FROM properties
        """))
        prop_info = {str(r[0]): {"name": r[1], "region": r[2] or "Ukjent"} for r in props_result.fetchall()}

        # Normalize region for report
        def normalize_region(r: Optional[str]) -> str:
            if not r:
                return "Ukjent"
            return COUNTY_TO_REGION.get(str(r).strip(), str(r).strip())

        budget_entries = []
        properties_with_gl = set()
        properties_fallback = set()

        for prop_id, categories in by_property_category.items():
            for cat, year_totals in categories.items():
                if not year_totals:
                    continue
                avg_annual = sum(year_totals.values()) / len(year_totals)
                budget_annual = avg_annual * (1 + inflation_rate)
                properties_with_gl.add(prop_id)

                for month in range(1, 13):
                    seasonal = self._get_seasonal_factor(cat, month)
                    monthly_amount = (budget_annual / 12) * seasonal
                    budget_entries.append({
                        "property_id": prop_id,
                        "year": target_year,
                        "month": month,
                        "category": cat,
                        "amount": round(monthly_amount, 2),
                        "is_synthetic": True,
                        "data_source": "estimate_2026_from_regions",
                    })

        # Fallback: properties without GL data
        if property_ids:
            all_prop_ids = {str(p) for p in property_ids}
        else:
            all_props_result = await db.execute(text("SELECT property_id FROM properties"))
            all_prop_ids = {str(r[0]) for r in all_props_result.fetchall()}
        missing = all_prop_ids - properties_with_gl

        if missing:
            self.logger.info(f"Fallback: genererer budsjett for {len(missing)} eiendommer uten GL-data")

        for prop_id in missing:
            try:
                budget_data = await self._generate_fallback_budget(
                    db, prop_id, target_year, inflation_rate, quiet=True
                )
                entries = budget_data.get("budget_entries", [])
                if entries:
                    budget_entries.extend([
                        {**e, "data_source": "estimate_2026_from_regions_fallback"}
                        for e in entries
                    ])
                    properties_fallback.add(prop_id)
            except Exception as e:
                self.logger.warning(f"Fallback budget failed for {prop_id}: {e}")

        # Build report
        by_property: Dict[str, float] = {}
        for e in budget_entries:
            pid = str(e["property_id"])
            by_property[pid] = by_property.get(pid, 0) + e["amount"]

        by_region: Dict[str, float] = {}
        for pid, total in by_property.items():
            info = prop_info.get(pid, {})
            region = normalize_region(info.get("region"))
            by_region[region] = by_region.get(region, 0) + total

        total_budget = sum(by_property.values())

        report = {
            "total": round(total_budget, 2),
            "by_region": {k: round(v, 2) for k, v in sorted(by_region.items(), key=lambda x: -x[1])},
            "by_property": [
                {
                    "property_id": pid,
                    "name": prop_info.get(pid, {}).get("name", "?"),
                    "region": normalize_region(prop_info.get(pid, {}).get("region")),
                    "total": round(total, 2),
                }
                for pid, total in sorted(by_property.items(), key=lambda x: -x[1])
            ],
        }

        return {
            "target_year": target_year,
            "source_years": source_years,
            "inflation_rate": inflation_rate,
            "budget_entries": budget_entries,
            "total_budget_nok": round(total_budget, 2),
            "entries_created": len(budget_entries),
            "properties_with_gl": len(properties_with_gl),
            "properties_fallback": len(properties_fallback),
            "report": report,
        }

    INNKJØPSANALYSE_SOURCE = "innkjøpsanalyse_2025"

    def _load_total_kost_per_region(self, source_year: int) -> Optional[Dict[str, float]]:
        """Les total_kost_per_region_{year}.json, returner by_region totals (sum over kategorier)."""
        data_dir = Path(__file__).resolve().parents[2] / "data"
        json_path = data_dir / f"total_kost_per_region_{source_year}.json"
        if not json_path.exists():
            return None
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            by_region: Dict[str, float] = {}
            for cat_data in (data.get("by_category") or {}).values():
                totals = cat_data.get("by_region_totals") or {}
                for reg, amt in totals.items():
                    by_region[reg] = by_region.get(reg, 0) + float(amt or 0)
            return by_region
        except Exception as e:
            self.logger.warning("Kunne ikke lese total_kost_per_region: %s", e)
            return None

    async def estimate_budget_from_innkjøpsanalyse(
        self,
        db: AsyncSession,
        source_year: int = 2025,
        target_year: int = 2026,
        inflation_rate: Optional[float] = None,
        property_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Estimate budget for target_year based on Innkjøpsanalyse.

        Bruker total_kost_per_region (504 MNOK) som baseline. Eiendommer med
        property_husleie_csv får eksakte beløp; resten fordeles proporsjonalt
        fra regionale restbeløp (etter kontraktsandel).
        """
        if inflation_rate is None:
            inflation_rate = self.DEFAULT_INFLATION_RATE

        # 1. Last regionale totaler fra JSON (504 MNOK)
        total_by_region_json = self._load_total_kost_per_region(source_year)
        if total_by_region_json:
            total_json = sum(total_by_region_json.values())
            self.logger.info("Total kost fra JSON: %s MNOK", round(total_json / 1e6, 1))
        else:
            total_by_region_json = {}
            total_json = 0.0

        # 2. Hent aggregert per eiendom fra property_husleie_csv
        params: Dict[str, Any] = {
            "source_year": source_year,
            "source": self.INNKJØPSANALYSE_SOURCE,
        }
        prop_filter = ""
        if property_ids:
            prop_filter = "AND property_id = ANY(:property_ids)"
            params["property_ids"] = property_ids
        result = await db.execute(text(f"""
            SELECT property_id, SUM(amount) as total
            FROM property_husleie_csv
            WHERE year = :source_year AND source = :source {prop_filter}
            GROUP BY property_id
        """), params)
        rows = result.fetchall()

        by_property: Dict[str, float] = {}
        for row in rows:
            pid_str = str(row[0])
            total_amt = float(row[1] or 0)
            by_property[pid_str] = by_property.get(pid_str, 0.0) + total_amt

        # 3. Hent property info + kontraktsbeløp for fordeling
        props_result = await db.execute(text("""
            SELECT p.property_id, p.name, p.region,
                COALESCE(SUM(
                    COALESCE((c.amount->>'total_per_year')::float, (c.amount->>'amount_per_year')::float,
                    (c.amount->>'monthly_rent')::float * 12, 0)
                ), 0) as contract_rent
            FROM properties p
            LEFT JOIN units u ON u.property_id = p.property_id
            LEFT JOIN contracts c ON c.unit_id = u.unit_id AND c.status = 'active'
            GROUP BY p.property_id, p.name, p.region
        """))
        prop_info = {}
        for r in props_result.fetchall():
            pid = str(r[0])
            prop_info[pid] = {
                "name": r[1],
                "region": r[2] or "Ukjent",
                "contract_rent": float(r[3] or 0),
            }

        def normalize_region(r: Optional[str]) -> str:
            if not r:
                return "Ukjent"
            reg = COUNTY_TO_REGION.get(str(r).strip(), str(r).strip())
            return "Midt-Norge" if reg == "Midt" else reg

        def region_for_json(reg: str) -> str:
            return "Midt-Norge" if reg == "Midt" else reg

        # 4. Beregn restbeløp per region (JSON total - allerede allokert fra property_husleie_csv)
        allocated_by_region: Dict[str, float] = {}
        for pid, amt in by_property.items():
            if amt <= 0:
                continue
            info = prop_info.get(pid, {})
            reg = normalize_region(info.get("region"))
            reg_key = region_for_json(reg)
            allocated_by_region[reg_key] = allocated_by_region.get(reg_key, 0) + amt

        remainder_by_region: Dict[str, float] = {}
        for reg, json_total in total_by_region_json.items():
            allocated = allocated_by_region.get(reg, 0)
            remainder = (json_total * (1 + inflation_rate)) - (allocated * (1 + inflation_rate))
            remainder_by_region[reg] = max(0, remainder)

        # 5. Eiendommer uten Innkjøpsanalyse: fordeles restbeløp proporsjonalt (etter kontrakt)
        if property_ids:
            all_prop_ids = {str(p) for p in property_ids}
        else:
            all_props_result = await db.execute(text("SELECT property_id FROM properties"))
            all_prop_ids = {str(r[0]) for r in all_props_result.fetchall()}
        missing = all_prop_ids - set(by_property.keys())

        # Per region: sum contract_rent for missing properties
        contract_sum_by_region: Dict[str, float] = {}
        missing_by_region: Dict[str, List[str]] = {}
        for pid in missing:
            info = prop_info.get(pid, {})
            reg = region_for_json(normalize_region(info.get("region")))
            if reg not in missing_by_region:
                missing_by_region[reg] = []
            missing_by_region[reg].append(pid)
            contract_sum_by_region[reg] = contract_sum_by_region.get(reg, 0) + info.get("contract_rent", 0)

        budget_entries = []
        properties_innkjøpsanalyse = set()
        properties_fallback = set()

        PROPERTY_PCT = 0.85
        OPERATIONS_PCT = 0.15

        # 6. Eiendommer med Innkjøpsanalyse: eksakte beløp
        for prop_id, base_2025 in by_property.items():
            if base_2025 <= 0:
                continue
            budget_annual = base_2025 * (1 + inflation_rate)
            prop_budget = budget_annual * PROPERTY_PCT
            ops_budget = budget_annual * OPERATIONS_PCT
            properties_innkjøpsanalyse.add(prop_id)

            for month in range(1, 13):
                monthly_prop = prop_budget / 12
                seasonal = self._get_seasonal_factor("operations", month)
                monthly_ops = (ops_budget / 12) * seasonal
                budget_entries.append({
                    "property_id": prop_id,
                    "year": target_year,
                    "month": month,
                    "category": "property",
                    "amount": round(monthly_prop, 2),
                    "is_synthetic": True,
                    "data_source": "estimate_2026_from_innkjøpsanalyse",
                })
                budget_entries.append({
                    "property_id": prop_id,
                    "year": target_year,
                    "month": month,
                    "category": "operations",
                    "amount": round(monthly_ops, 2),
                    "is_synthetic": True,
                    "data_source": "estimate_2026_from_innkjøpsanalyse",
                })

        # 7. Eiendommer uten Innkjøpsanalyse: fordeles restbeløp
        for reg, remainder in remainder_by_region.items():
            if remainder <= 0:
                continue
            pids = missing_by_region.get(reg, [])
            contract_sum = contract_sum_by_region.get(reg, 0)
            if not pids:
                continue
            if contract_sum > 0:
                for pid in pids:
                    share = (prop_info.get(pid, {}).get("contract_rent", 0) or 0) / contract_sum
                    budget_annual = remainder * share
                    prop_budget = budget_annual * PROPERTY_PCT
                    ops_budget = budget_annual * OPERATIONS_PCT
                    properties_fallback.add(pid)
                    for month in range(1, 13):
                        monthly_prop = prop_budget / 12
                        seasonal = self._get_seasonal_factor("operations", month)
                        monthly_ops = (ops_budget / 12) * seasonal
                        budget_entries.append({
                            "property_id": pid,
                            "year": target_year,
                            "month": month,
                            "category": "property",
                            "amount": round(monthly_prop, 2),
                            "is_synthetic": True,
                            "data_source": "estimate_2026_from_innkjøpsanalyse_fallback",
                        })
                        budget_entries.append({
                            "property_id": pid,
                            "year": target_year,
                            "month": month,
                            "category": "operations",
                            "amount": round(monthly_ops, 2),
                            "is_synthetic": True,
                            "data_source": "estimate_2026_from_innkjøpsanalyse_fallback",
                        })
            else:
                # Ingen kontrakter: fordeles likt
                per_prop = remainder / len(pids)
                for pid in pids:
                    budget_annual = per_prop
                    prop_budget = budget_annual * PROPERTY_PCT
                    ops_budget = budget_annual * OPERATIONS_PCT
                    properties_fallback.add(pid)
                    for month in range(1, 13):
                        monthly_prop = prop_budget / 12
                        seasonal = self._get_seasonal_factor("operations", month)
                        monthly_ops = (ops_budget / 12) * seasonal
                        budget_entries.append({
                            "property_id": pid,
                            "year": target_year,
                            "month": month,
                            "category": "property",
                            "amount": round(monthly_prop, 2),
                            "is_synthetic": True,
                            "data_source": "estimate_2026_from_innkjøpsanalyse_fallback",
                        })
                        budget_entries.append({
                            "property_id": pid,
                            "year": target_year,
                            "month": month,
                            "category": "operations",
                            "amount": round(monthly_ops, 2),
                            "is_synthetic": True,
                            "data_source": "estimate_2026_from_innkjøpsanalyse_fallback",
                        })

        # 8. Eiendommer i regioner uten restbeløp (JSON mangler region): bruk kontrakt-fallback
        for pid in missing - properties_fallback:
            try:
                budget_data = await self._generate_fallback_budget(
                    db, pid, target_year, inflation_rate, quiet=True
                )
                entries = budget_data.get("budget_entries", [])
                if entries:
                    budget_entries.extend([
                        {**e, "data_source": "estimate_2026_from_innkjøpsanalyse_fallback"}
                        for e in entries
                    ])
                    properties_fallback.add(pid)
            except Exception as e:
                self.logger.warning("Fallback budget failed for %s: %s", pid, e)

        # Build report
        by_prop_total: Dict[str, float] = {}
        for e in budget_entries:
            pid = str(e["property_id"])
            by_prop_total[pid] = by_prop_total.get(pid, 0) + e["amount"]

        by_region: Dict[str, float] = {}
        for pid, total in by_prop_total.items():
            info = prop_info.get(pid, {})
            region = normalize_region(info.get("region"))
            by_region[region] = by_region.get(region, 0) + total

        total_budget = sum(by_prop_total.values())

        report = {
            "total": round(total_budget, 2),
            "by_region": {k: round(v, 2) for k, v in sorted(by_region.items(), key=lambda x: -x[1])},
            "by_property": [
                {
                    "property_id": pid,
                    "name": prop_info.get(pid, {}).get("name", "?"),
                    "region": normalize_region(prop_info.get(pid, {}).get("region")),
                    "total": round(total, 2),
                }
                for pid, total in sorted(by_prop_total.items(), key=lambda x: -x[1])
            ],
        }

        return {
            "target_year": target_year,
            "source_year": source_year,
            "inflation_rate": inflation_rate,
            "budget_entries": budget_entries,
            "total_budget_nok": round(total_budget, 2),
            "entries_created": len(budget_entries),
            "properties_innkjøpsanalyse": len(properties_innkjøpsanalyse),
            "properties_fallback": len(properties_fallback),
            "report": report,
        }


# Singleton instance
budget_generation_service = BudgetGenerationService()
