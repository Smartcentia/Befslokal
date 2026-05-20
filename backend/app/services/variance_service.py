from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.financial_models import Budget, GLTransaction
from app.domains.core.models.property import Property
from app.services.analytics.cost_analysis_service import aggregate_consumption_by_year

class VarianceService:
    """Service for analyzing Budget vs Actual variance"""

    @staticmethod
    async def get_variance_report(
        db: AsyncSession, 
        property_id: str, 
        year: int, 
        period_type: str = "month",  # "month", "quarter", "ytd", "year"
        period_value: int = None     # 1-12 for month, 1-4 for quarter
    ) -> Dict[str, Any]:
        """
        Generates a variance report for a specific property and period.
        """
        
        # 1. Define Filters
        budget_filters = [Budget.property_id == property_id, Budget.year == year]
        actual_filters = [GLTransaction.property_id == property_id, GLTransaction.ar == year]
        
        if period_type == "month" and period_value:
            budget_filters.append(Budget.month == period_value)
            actual_filters.append(GLTransaction.maaned == period_value)
        elif period_type == "quarter" and period_value:
            start_month = (period_value - 1) * 3 + 1
            end_month = period_value * 3
            budget_filters.append(Budget.month.between(start_month, end_month))
            actual_filters.append(GLTransaction.maaned.between(start_month, end_month))
        elif period_type == "ytd" and period_value:
             budget_filters.append(Budget.month <= period_value)
             actual_filters.append(GLTransaction.maaned <= period_value)
             
        # 2. Query Budget Aggegrated by Category
        stmt_budget = (
            select(
                Budget.category,
                func.sum(Budget.amount).label("total_budget")
            )
            .where(and_(*budget_filters))
            .group_by(Budget.category)
        )
        result_budget = await db.execute(stmt_budget)
        budget_map = {row.category: row.total_budget for row in result_budget}
        
        # 3. Query Actuals Aggegrated by Category
        stmt_actual = (
            select(
                GLTransaction.category,
                func.sum(GLTransaction.belop).label("total_actual")
            )
            .where(and_(*actual_filters))
            .group_by(GLTransaction.category)
        )
        result_actual = await db.execute(stmt_actual)
        actual_map = {row.category: row.total_actual for row in result_actual}

        # 3b. Fallback: Hvis gl_transactions er tom, bruk manual_expenses fra property
        total_actual_from_gl = sum(actual_map.values())
        if total_actual_from_gl == 0:
            prop_stmt = select(Property).where(Property.property_id == property_id)
            prop_res = await db.execute(prop_stmt)
            prop = prop_res.scalar_one_or_none()
            if prop and prop.external_data:
                property_data = {
                    "property_id": str(prop.property_id),
                    "name": prop.name or "",
                    "external_data": prop.external_data or {},
                }
                by_year = aggregate_consumption_by_year(property_data, years=[year])
                year_data = by_year.get(year, {})
                if year_data and year_data.get("total", 0) > 0:
                    # Prorate for period
                    if period_type == "year":
                        factor = 1.0
                    elif period_type == "ytd" and period_value:
                        factor = period_value / 12.0
                    elif period_type == "month" and period_value:
                        factor = 1.0 / 12.0
                    elif period_type == "quarter" and period_value:
                        factor = 3.0 / 12.0
                    else:
                        factor = 1.0
                    for cat in ["property", "operations", "investment", "other"]:
                        amt = year_data.get(cat, 0.0) * factor
                        if amt > 0:
                            actual_map[cat] = actual_map.get(cat, 0.0) + amt

        # 4. Merge and Calculate Variance
        all_categories = set(budget_map.keys()) | set(actual_map.keys())
        line_items = []
        
        total_budget = 0
        total_actual = 0
        
        for cat in sorted(all_categories):
            b_amount = budget_map.get(cat, 0.0)
            a_amount = actual_map.get(cat, 0.0)
            
            variance = b_amount - a_amount # Positive if under budget (Good for costs)
            # Note: For Income, logic needs to be inverted. Assuming costs for now based on context.
            
            variance_pct = (variance / b_amount * 100) if b_amount != 0 else 0
            
            total_budget += b_amount
            total_actual += a_amount
            
            line_items.append({
                "category": cat,
                "budget": b_amount,
                "actual": a_amount,
                "variance": variance,
                "variance_pct": variance_pct
            })
            
        total_variance = total_budget - total_actual
        total_variance_pct = (total_variance / total_budget * 100) if total_budget != 0 else 0

        # Hvis ingen budsjettdata: gi tydelig feil slik at bruker vet hva som må gjøres
        if total_budget == 0 and total_actual == 0:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail="Eiendommen mangler budsjettdata. Kjør budsjettgenerering fra forbruk: "
                "Admin → Finans, eller backend: python3 scripts/fill_budget_from_consumption.py"
            )

        return {
            "property_id": property_id,
            "period": {
                "year": year,
                "type": period_type,
                "value": period_value
            },
            "summary": {
                "total_budget": total_budget,
                "total_actual": total_actual,
                "total_variance": total_variance,
                "total_variance_pct": total_variance_pct
            },
            "items": line_items
        }

    @staticmethod
    async def get_trend_analysis(
        db: AsyncSession,
        property_id: str,
        year: int
    ) -> Dict[str, Any]:
        """
        Returns monthly breakdown of Budget vs Actual for the entire year.
        """
        # Monthly Budget
        stmt_budget = (
            select(
                Budget.month,
                func.sum(Budget.amount).label("total_budget")
            )
            .where(and_(Budget.property_id == property_id, Budget.year == year))
            .group_by(Budget.month)
            .order_by(Budget.month)
        )
        
        # Monthly Actuals
        stmt_actual = (
            select(
                GLTransaction.maaned,
                func.sum(GLTransaction.belop).label("total_actual")
            )
            .where(and_(GLTransaction.property_id == property_id, GLTransaction.ar == year))
            .group_by(GLTransaction.maaned)
            .order_by(GLTransaction.maaned)
        )
        
        b_res = await db.execute(stmt_budget)
        a_res = await db.execute(stmt_actual)
        
        b_data = {row.month: row.total_budget for row in b_res}
        a_data = {row.month: row.total_actual for row in a_res}
        
        trend_data = []
        for m in range(1, 13):
            b_val = b_data.get(m, 0.0)
            a_val = a_data.get(m, 0.0)
            trend_data.append({
                "month": m,
                "budget": b_val,
                "actual": a_val,
                "variance": b_val - a_val
            })
            
        return {
            "property_id": property_id,
            "year": year,
            "trend": trend_data
        }
