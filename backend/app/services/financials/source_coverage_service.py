from sqlalchemy import func, select

from app.models.financial_models import GLTransaction, SalaryCost


def complete_source_coverage_property_ids_subquery(start_year: int = 2020, end_year: int = 2025):
    """
    Returns a subquery of property_id values that have records in BOTH:
    1) gl_transactions (ar)
    2) salary_costs (year)
    for every year in [start_year, end_year].

    This powers default filtering of "valid" properties across list/map/dashboard.
    """
    year_count = (end_year - start_year) + 1

    gl_complete_sq = (
        select(GLTransaction.property_id.label("property_id"))
        .where(
            GLTransaction.property_id.isnot(None),
            GLTransaction.ar >= start_year,
            GLTransaction.ar <= end_year,
        )
        .group_by(GLTransaction.property_id)
        .having(func.count(func.distinct(GLTransaction.ar)) == year_count)
        .subquery()
    )

    salary_complete_sq = (
        select(SalaryCost.property_id.label("property_id"))
        .where(
            SalaryCost.property_id.isnot(None),
            SalaryCost.year >= start_year,
            SalaryCost.year <= end_year,
        )
        .group_by(SalaryCost.property_id)
        .having(func.count(func.distinct(SalaryCost.year)) == year_count)
        .subquery()
    )

    return (
        select(gl_complete_sq.c.property_id)
        .join(
            salary_complete_sq,
            salary_complete_sq.c.property_id == gl_complete_sq.c.property_id,
        )
        .subquery()
    )
