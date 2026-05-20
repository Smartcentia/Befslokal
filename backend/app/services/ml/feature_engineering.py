"""
Feature engineering for cross-sectional ML cost prediction.

Each training row = one (property_id, target_year, srs_category) tuple.
Features: property metadata + last year's GL costs + contract commitments.

Training data:  (property, 2024, category) → cost_2024
                (property, 2025, category) → cost_2025   [if available]
Prediction:     (property, 2026, category) → predicted cost
"""

import logging
from collections import defaultdict

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# SRS category mapping (same as prediction_service.py)
SRS_TO_CATEGORY = {
    "Drift": "operations",
    "Investering": "investment",
    "Gjennomstrømning": "property",
}
CATEGORIES = ["operations", "investment", "property", "other"]

# Region → integer (for ordinal encoding fallback)
REGION_ORDER = ["Nord", "Midt-Norge", "Vest", "Sør", "Øst", "Bufdir"]

# Energy label → ordinal
ENERGY_LABEL_MAP = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
ENERGY_LABEL_DEFAULT = 4  # D = middle

# Unit types
UNIT_TYPES = ["Barnevernsinstitusjon", "Institusjonsavdeling", "Omsorgssenter"]


async def fetch_property_features(db: AsyncSession) -> pd.DataFrame:
    """
    Returns one row per property with static metadata features.
    Missing values are imputed with sensible defaults.
    """
    try:
        rows = await db.execute(text("""
            SELECT
                property_id::text,
                COALESCE(region, 'Ukjent')             AS region,
                COALESCE(total_area, 0.0)              AS total_area,
                construction_year,
                COALESCE(energy_label, 'D')            AS energy_label,
                COALESCE(approved_places, 0)           AS approved_places,
                COALESCE(budgeted_places, 0)           AS budgeted_places,
                COALESCE(unit_type_derived, 'other')   AS unit_type_derived
            FROM properties
            WHERE property_id IS NOT NULL
        """))
        data = rows.mappings().all()
    except Exception as exc:
        logger.debug("fetch_property_features failed: %s", exc)
        return pd.DataFrame()

    df = pd.DataFrame([dict(r) for r in data])
    if df.empty:
        return df

    # Derived features
    current_year = 2026
    df["building_age"] = df["construction_year"].apply(
        lambda y: (current_year - int(y)) if pd.notna(y) and y else 25
    )
    df["energy_label_ord"] = df["energy_label"].map(
        lambda x: ENERGY_LABEL_MAP.get(str(x).upper()[:1], ENERGY_LABEL_DEFAULT)
    )

    # One-hot: region
    for reg in REGION_ORDER:
        df[f"region_{reg.lower().replace('-', '_')}"] = (df["region"] == reg).astype(int)

    # One-hot: unit type
    for ut in UNIT_TYPES:
        col = f"unit_{ut.lower().replace('ø', 'o').replace('å', 'a').replace('æ', 'ae')}"
        df[col] = (df["unit_type_derived"] == ut).astype(int)

    drop_cols = ["construction_year", "energy_label", "region", "unit_type_derived"]
    return df.drop(columns=[c for c in drop_cols if c in df.columns])


async def fetch_gl_annual_costs(
    db: AsyncSession, from_year: int, to_year: int
) -> pd.DataFrame:
    """
    Returns annual GL costs per (property_id, year, category).
    Only positive amounts (costs), property_id not null.
    """
    try:
        rows = await db.execute(text("""
            SELECT
                property_id::text,
                ar                                          AS year,
                COALESCE(srs_kategori, 'other')            AS srs_kategori,
                SUM(belop)::float                          AS cost
            FROM gl_transactions
            WHERE belop > 0
              AND property_id IS NOT NULL
              AND ar BETWEEN :from_year AND :to_year
            GROUP BY property_id, ar, srs_kategori
        """), {"from_year": from_year, "to_year": to_year})
        data = rows.mappings().all()
    except Exception as exc:
        logger.debug("fetch_gl_annual_costs failed: %s", exc)
        return pd.DataFrame(columns=["property_id", "year", "srs_kategori", "cost"])

    df = pd.DataFrame([dict(r) for r in data])
    if df.empty:
        return df

    df["category"] = df["srs_kategori"].map(
        lambda x: SRS_TO_CATEGORY.get(x, "other")
    )
    return df[["property_id", "year", "category", "cost"]]


async def fetch_contract_costs(db: AsyncSession) -> pd.DataFrame:
    """
    Returns annual committed contract costs per property (active contracts).
    """
    try:
        rows = await db.execute(text("""
            SELECT
                u.property_id::text,
                SUM(COALESCE(c.caretaker_cost, 0) + COALESCE(c.cleaning_cost, 0))
                    AS services_annual
            FROM contracts c
            JOIN units u ON u.unit_id = c.unit_id
            WHERE c.status = 'active'
              AND u.property_id IS NOT NULL
            GROUP BY u.property_id
        """))
        data = rows.mappings().all()
    except Exception as exc:
        logger.debug("fetch_contract_costs failed: %s", exc)
        return pd.DataFrame(columns=["property_id", "services_annual"])

    return pd.DataFrame([dict(r) for r in data])


async def fetch_salary_costs(db: AsyncSession, year: int) -> pd.DataFrame:
    """Returns total salary costs per property for a given year."""
    try:
        rows = await db.execute(text("""
            SELECT
                property_id::text,
                (COALESCE(faste_stillinger, 0)
                 + COALESCE(vikarer, 0)
                 + COALESCE(arbeidsgiveravgift, 0))::float AS salary_total
            FROM salary_costs
            WHERE year = :year
        """), {"year": year})
        data = rows.mappings().all()
    except Exception as exc:
        logger.debug("fetch_salary_costs failed: %s", exc)
        return pd.DataFrame(columns=["property_id", "salary_total"])

    return pd.DataFrame([dict(r) for r in data])


async def build_training_matrix(db: AsyncSession) -> pd.DataFrame:
    """
    Builds the full training matrix.

    Each row = (property_id, target_year, category) with:
      - All property features
      - last_year_cost (for same category, year-1)
      - contract costs
      - salary costs
      - target: cost for target_year

    Returns DataFrame ready for sklearn training.
    """
    prop_df = await fetch_property_features(db)
    if prop_df.empty:
        logger.warning("No property features found")
        return pd.DataFrame()

    gl_df = await fetch_gl_annual_costs(db, from_year=2023, to_year=2025)
    if gl_df.empty:
        logger.warning("No GL data found for training")
        return pd.DataFrame()

    contract_df = await fetch_contract_costs(db)
    salary_df = await fetch_salary_costs(db, year=2024)

    rows = []
    available_years = sorted(gl_df["year"].unique())

    # For each (property, target_year, category): use last_year as feature
    for target_year in available_years:
        last_year = target_year - 1
        target_costs = gl_df[gl_df["year"] == target_year]
        last_costs = gl_df[gl_df["year"] == last_year]

        # Pivot last year's costs: property_id → {category: cost}
        last_pivot: dict[str, dict[str, float]] = defaultdict(lambda: {c: 0.0 for c in CATEGORIES})
        for _, r in last_costs.iterrows():
            last_pivot[r["property_id"]][r["category"]] = r["cost"]

        for _, row in target_costs.iterrows():
            pid = row["property_id"]
            cat = row["category"]
            target_cost = row["cost"]

            # Get property metadata
            prop_row = prop_df[prop_df["property_id"] == pid]
            if prop_row.empty:
                continue

            feat = prop_row.iloc[0].to_dict()
            feat["target_year"] = target_year
            feat["category"] = cat
            feat["target_cost"] = target_cost

            # Last year costs (same category and total)
            feat["cost_last_year_same_cat"] = last_pivot[pid].get(cat, 0.0)
            feat["cost_last_year_total"] = sum(last_pivot[pid].values())

            # Contract commitments
            if not contract_df.empty:
                c_row = contract_df[contract_df["property_id"] == pid]
                feat["services_annual"] = float(c_row["services_annual"].iloc[0]) if not c_row.empty else 0.0
            else:
                feat["services_annual"] = 0.0

            # Salary costs
            if not salary_df.empty:
                s_row = salary_df[salary_df["property_id"] == pid]
                feat["salary_total"] = float(s_row["salary_total"].iloc[0]) if not s_row.empty else 0.0
            else:
                feat["salary_total"] = 0.0

            # Category as ordinal (separate models per category is also fine)
            feat["category_ord"] = CATEGORIES.index(cat) if cat in CATEGORIES else 3

            rows.append(feat)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df = df.fillna(0.0)
    return df


async def build_prediction_features(
    db: AsyncSession,
    target_year: int = 2026,
) -> pd.DataFrame:
    """
    Builds prediction feature matrix for all properties.
    Uses latest available GL data as 'last year' features.
    Returns one row per (property_id, category).
    """
    prop_df = await fetch_property_features(db)
    if prop_df.empty:
        return pd.DataFrame()

    last_year = target_year - 1
    gl_df = await fetch_gl_annual_costs(db, from_year=last_year, to_year=last_year)
    contract_df = await fetch_contract_costs(db)
    salary_df = await fetch_salary_costs(db, year=last_year)

    # Last year costs pivot
    last_pivot: dict[str, dict[str, float]] = defaultdict(lambda: {c: 0.0 for c in CATEGORIES})
    for _, r in gl_df.iterrows():
        last_pivot[r["property_id"]][r["category"]] = r["cost"]

    rows = []
    for _, prop_row in prop_df.iterrows():
        pid = prop_row["property_id"]
        if pid not in last_pivot and gl_df.empty:
            # No history at all – skip
            continue

        for cat in CATEGORIES:
            feat = prop_row.to_dict()
            feat["target_year"] = target_year
            feat["category"] = cat
            feat["target_cost"] = None  # unknown – what we're predicting

            feat["cost_last_year_same_cat"] = last_pivot[pid].get(cat, 0.0)
            feat["cost_last_year_total"] = sum(last_pivot[pid].values())

            if not contract_df.empty:
                c_row = contract_df[contract_df["property_id"] == pid]
                feat["services_annual"] = float(c_row["services_annual"].iloc[0]) if not c_row.empty else 0.0
            else:
                feat["services_annual"] = 0.0

            if not salary_df.empty:
                s_row = salary_df[salary_df["property_id"] == pid]
                feat["salary_total"] = float(s_row["salary_total"].iloc[0]) if not s_row.empty else 0.0
            else:
                feat["salary_total"] = 0.0

            feat["category_ord"] = CATEGORIES.index(cat) if cat in CATEGORIES else 3
            rows.append(feat)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df.fillna(0.0)


# Feature columns used in model (must match between train and predict)
FEATURE_COLS = [
    "total_area",
    "building_age",
    "energy_label_ord",
    "approved_places",
    "budgeted_places",
    "cost_last_year_same_cat",
    "cost_last_year_total",
    "services_annual",
    "salary_total",
    "category_ord",
    # region one-hots
    "region_nord",
    "region_midt_norge",
    "region_vest",
    "region_sor",
    "region_ost",
    "region_bufdir",
    # unit type one-hots
    "unit_barnevernsinstitusjon",
    "unit_institusjonsavdeling",
    "unit_omsorgssenter",
]


def extract_X_y(df: pd.DataFrame) -> tuple:
    """Extract feature matrix X and target vector y from the training DataFrame."""
    available = [c for c in FEATURE_COLS if c in df.columns]
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    for c in missing:
        df[c] = 0.0

    X = df[FEATURE_COLS].astype(float).values
    y = df["target_cost"].astype(float).values if "target_cost" in df.columns else None
    return X, y, FEATURE_COLS
