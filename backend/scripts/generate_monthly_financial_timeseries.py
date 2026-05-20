#!/usr/bin/env python3
"""
Generate synthetic monthly financial time-series dataset for real estate.

This script generates monthly financial data covering the last 3 years,
with realistic seasonality for electricity and inflation-adjusted rent.

Can work with mock data OR fetch all properties from database.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from typing import Optional
import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Add backend to path for database imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env BEFORE importing app modules
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Import all models to ensure relationships are resolved
import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
# Import other models that might be needed
import app.domains.core.models.user
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control


def create_mock_assets(n: int = 10) -> pd.DataFrame:
    """
    Generate a mock DataFrame with building information.
    
    Args:
        n: Number of buildings to generate
        
    Returns:
        DataFrame with columns: id, sqm, current_base_rent, base_electricity_cost
    """
    np.random.seed(42)  # For reproducibility
    
    df = pd.DataFrame({
        'id': [f'PROP_{i:03d}' for i in range(1, n + 1)],
        'sqm': np.random.uniform(500, 5000, n).round(0),
        'current_base_rent': np.random.uniform(500000, 5000000, n).round(2),
        'base_electricity_cost': np.random.uniform(50000, 500000, n).round(2)
    })
    
    return df


def apply_seasonality_multiplier(month: int) -> float:
    """
    Get seasonality multiplier for electricity based on month.
    
    Winter months (Nov, Dec, Jan, Feb): 1.4-1.6
    Summer months (Jun, Jul, Aug): 0.6-0.8
    Shoulder months: ~1.0
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Seasonality multiplier
    """
    # Winter months (Nov=11, Dec=12, Jan=1, Feb=2)
    if month in [11, 12, 1, 2]:
        return np.random.uniform(1.4, 1.6)
    # Summer months (Jun=6, Jul=7, Aug=8)
    elif month in [6, 7, 8]:
        return np.random.uniform(0.6, 0.8)
    # Shoulder months
    else:
        return np.random.uniform(0.9, 1.1)


def generate_time_series(
    df_assets: pd.DataFrame,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    years_back: int = 3,
    inflation_rate: float = 0.035,  # 3.5% annual inflation
    rent_index_adj: float = 0.04,    # 4% KPI adjustment
    rent_noise: float = 0.01,        # +/- 1% monthly variation
    electricity_noise: float = 0.05  # +/- 5% monthly variation
) -> pd.DataFrame:
    """
    Generate monthly financial time-series data for assets.
    
    Args:
        df_assets: DataFrame with columns: id, sqm, current_base_rent, base_electricity_cost
        start_date: Start date (defaults to 3 years ago)
        end_date: End date (defaults to today)
        years_back: Number of years to go back (if start_date not provided)
        inflation_rate: Annual inflation rate for fixed costs
        rent_index_adj: Annual rent index adjustment (KPI)
        rent_noise: Monthly rent variation factor
        electricity_noise: Monthly electricity variation factor
        
    Returns:
        DataFrame with monthly financial data
    """
    # Set default dates
    if end_date is None:
        end_date = datetime.now().replace(day=1)  # First day of current month
    
    if start_date is None:
        start_date = end_date - relativedelta(years=years_back)
        start_date = start_date.replace(day=1)  # First day of start month
    
    # Generate date range (month start frequency)
    date_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    # Create cross-join: every asset × every month
    df_dates = pd.DataFrame({'date': date_range})
    df_assets_expanded = df_assets.copy()
    df_assets_expanded['key'] = 1
    df_dates['key'] = 1
    
    df_time_series = df_assets_expanded.merge(df_dates, on='key').drop('key', axis=1)
    
    # Calculate years and months from end date
    df_time_series['years_from_end'] = (
        (end_date - df_time_series['date']).dt.days / 365.25
    )
    df_time_series['month'] = df_time_series['date'].dt.month
    df_time_series['year'] = df_time_series['date'].dt.year
    
    # Initialize columns
    df_time_series['monthly_rent'] = 0.0
    df_time_series['monthly_electricity'] = 0.0
    df_time_series['monthly_parking'] = 0.0
    df_time_series['monthly_cleaning'] = 0.0
    
    # Calculate values for each row
    for idx, row in df_time_series.iterrows():
        years_back = row['years_from_end']
        month = row['month']
        
        # === RENT (Reverse Inflation Logic) ===
        # Start with current_base_rent, reduce backwards by rent_index_adj per year
        # Formula: historical_rent = current_rent / (1 + rent_index_adj) ^ years_back
        annual_rent = row['current_base_rent'] / ((1 + rent_index_adj) ** years_back)
        
        # Convert to monthly and add noise
        monthly_rent_base = annual_rent / 12
        noise_factor = np.random.uniform(1 - rent_noise, 1 + rent_noise)
        df_time_series.at[idx, 'monthly_rent'] = max(0, monthly_rent_base * noise_factor)
        
        # === ELECTRICITY (Seasonality) ===
        # Base monthly cost
        base_monthly_electricity = row['base_electricity_cost'] / 12
        
        # Apply reverse inflation (electricity prices have risen faster, ~5% annually)
        electricity_inflation = 0.05
        historical_monthly_base = base_monthly_electricity / ((1 + electricity_inflation) ** years_back)
        
        # Apply seasonality multiplier
        seasonality_mult = apply_seasonality_multiplier(month)
        
        # Add noise
        noise_factor = np.random.uniform(1 - electricity_noise, 1 + electricity_noise)
        
        df_time_series.at[idx, 'monthly_electricity'] = max(
            0, historical_monthly_base * seasonality_mult * noise_factor
        )
        
        # === FIXED COSTS (Parking & Cleaning) ===
        # Estimate parking cost as ~5% of rent, cleaning as ~3% of rent
        parking_annual = row['current_base_rent'] * 0.05
        cleaning_annual = row['current_base_rent'] * 0.03
        
        # Apply reverse inflation (smaller rate, ~2% annually)
        fixed_inflation = 0.02
        parking_monthly_base = (parking_annual / 12) / ((1 + fixed_inflation) ** years_back)
        cleaning_monthly_base = (cleaning_annual / 12) / ((1 + fixed_inflation) ** years_back)
        
        # Small variation
        df_time_series.at[idx, 'monthly_parking'] = max(
            0, parking_monthly_base * np.random.uniform(0.98, 1.02)
        )
        df_time_series.at[idx, 'monthly_cleaning'] = max(
            0, cleaning_monthly_base * np.random.uniform(0.98, 1.02)
        )
    
    # Round all financial columns to 2 decimals
    financial_cols = ['monthly_rent', 'monthly_electricity', 'monthly_parking', 'monthly_cleaning']
    df_time_series[financial_cols] = df_time_series[financial_cols].round(2)
    
    # Sort by id and date
    df_time_series = df_time_series.sort_values(['id', 'date']).reset_index(drop=True)
    
    return df_time_series


def format_for_gl_transactions(df_time_series: pd.DataFrame) -> pd.DataFrame:
    """
    Transform time-series data into General Ledger transaction format.
    
    Args:
        df_time_series: DataFrame with monthly financial data
        
    Returns:
        DataFrame with GL transaction structure:
        - Amount (negative for costs, positive for income)
        - AccountCode
        - AssetID
        - is_synthetic
        - data_source
    """
    # Account codes mapping
    ACCOUNT_CODES = {
        'rent': '3000',           # Income - Rent
        'electricity': '6000',     # Expense - Electricity
        'parking': '6100',         # Expense - Parking
        'cleaning': '6200'         # Expense - Cleaning
    }
    
    # Create separate rows for each transaction type
    gl_rows = []
    
    for _, row in df_time_series.iterrows():
        asset_id = row['id']
        transaction_date = row['date']
        
        # Rent (Income - Positive)
        gl_rows.append({
            'TransactionDate': transaction_date,
            'Description': f'Monthly Rent - {asset_id}',
            'Amount': row['monthly_rent'],
            'AccountCode': ACCOUNT_CODES['rent'],
            'AssetID': asset_id,
            'is_synthetic': True,
            'data_source': 'synthetic_timeseries'
        })
        
        # Electricity (Expense - Negative)
        gl_rows.append({
            'TransactionDate': transaction_date,
            'Description': f'Electricity Cost - {asset_id}',
            'Amount': -row['monthly_electricity'],  # Negative for expense
            'AccountCode': ACCOUNT_CODES['electricity'],
            'AssetID': asset_id,
            'is_synthetic': True,
            'data_source': 'synthetic_timeseries'
        })
        
        # Parking (Expense - Negative)
        gl_rows.append({
            'TransactionDate': transaction_date,
            'Description': f'Parking Cost - {asset_id}',
            'Amount': -row['monthly_parking'],  # Negative for expense
            'AccountCode': ACCOUNT_CODES['parking'],
            'AssetID': asset_id,
            'is_synthetic': True,
            'data_source': 'synthetic_timeseries'
        })
        
        # Cleaning (Expense - Negative)
        gl_rows.append({
            'TransactionDate': transaction_date,
            'Description': f'Cleaning Cost - {asset_id}',
            'Amount': -row['monthly_cleaning'],  # Negative for expense
            'AccountCode': ACCOUNT_CODES['cleaning'],
            'AssetID': asset_id,
            'is_synthetic': True,
            'data_source': 'synthetic_timeseries'
        })
    
    df_gl = pd.DataFrame(gl_rows)
    
    # Ensure TransactionDate is datetime
    df_gl['TransactionDate'] = pd.to_datetime(df_gl['TransactionDate'])
    
    # Sort by AssetID and TransactionDate
    df_gl = df_gl.sort_values(['AssetID', 'TransactionDate', 'AccountCode']).reset_index(drop=True)
    
    return df_gl


def visualize_electricity(df_time_series: pd.DataFrame, asset_id: Optional[str] = None):
    """
    Plot electricity cost over time to demonstrate seasonality.
    
    Args:
        df_time_series: DataFrame with monthly financial data
        asset_id: Specific asset to plot (if None, plots first asset)
    """
    if asset_id is None:
        asset_id = df_time_series['id'].iloc[0]
    
    df_asset = df_time_series[df_time_series['id'] == asset_id].copy()
    df_asset = df_asset.sort_values('date')
    
    plt.figure(figsize=(14, 6))
    plt.plot(df_asset['date'], df_asset['monthly_electricity'], 
             marker='o', linewidth=2, markersize=4)
    plt.title(f'Electricity Cost Over Time - {asset_id}\n(Demonstrating Seasonality)', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Monthly Electricity Cost (NOK)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    # Add vertical lines for year boundaries
    for year in df_asset['year'].unique():
        year_start = datetime(year, 1, 1)
        if year_start >= df_asset['date'].min() and year_start <= df_asset['date'].max():
            plt.axvline(x=year_start, color='gray', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.show()
    
    print(f"\n📊 Electricity Statistics for {asset_id}:")
    print(f"   Average: {df_asset['monthly_electricity'].mean():,.2f} NOK/month")
    print(f"   Min: {df_asset['monthly_electricity'].min():,.2f} NOK (month: {df_asset.loc[df_asset['monthly_electricity'].idxmin(), 'date'].strftime('%Y-%m')})")
    print(f"   Max: {df_asset['monthly_electricity'].max():,.2f} NOK (month: {df_asset.loc[df_asset['monthly_electricity'].idxmax(), 'date'].strftime('%Y-%m')})")
    print(f"   Winter avg (Nov-Feb): {df_asset[df_asset['month'].isin([11,12,1,2])]['monthly_electricity'].mean():,.2f} NOK/month")
    print(f"   Summer avg (Jun-Aug): {df_asset[df_asset['month'].isin([6,7,8])]['monthly_electricity'].mean():,.2f} NOK/month")


async def load_assets_from_database() -> pd.DataFrame:
    """
    Load all properties from database with their current rent and electricity costs.
    
    Returns:
        DataFrame with columns: id, sqm, current_base_rent, base_electricity_cost
    """
    print("📊 Loading properties from database...")
    
    async with SessionLocal() as db:
        # Get all properties
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        print(f"   Found {len(properties)} properties")
        
        # Get all active contracts with units and properties
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(
                joinedload(Contract.unit).joinedload(Unit.property)
            )
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        # Build property -> contracts mapping
        property_contracts = {}
        for contract in contracts:
            if contract.unit and contract.unit.property:
                prop_id = contract.unit.property.property_id
                if prop_id not in property_contracts:
                    property_contracts[prop_id] = []
                property_contracts[prop_id].append(contract)
        
        # Build assets DataFrame
        assets_data = []
        
        for prop in properties:
            prop_id = str(prop.property_id)
            
            # Get total area (sqm)
            sqm = prop.total_area if prop.total_area else 0
            
            # Get current rent from active contracts
            current_base_rent = 0.0
            if prop.property_id in property_contracts:
                for contract in property_contracts[prop.property_id]:
                    if contract.amount and isinstance(contract.amount, dict):
                        rent = contract.amount.get('amount_per_year', 0)
                        try:
                            current_base_rent += float(rent) if rent else 0
                        except (ValueError, TypeError):
                            pass
            
            # Get electricity cost from external_data
            base_electricity_cost = 0.0
            if prop.external_data and isinstance(prop.external_data, dict):
                financials = prop.external_data.get('financials', {})
                expenses = financials.get('manual_expenses', [])
                
                # Look for electricity/energy expenses
                for exp in expenses:
                    exp_type = str(exp.get('type', '')).lower()
                    if 'strøm' in exp_type or 'elektri' in exp_type or 'energi' in exp_type:
                        amount = exp.get('amount', 0) or exp.get('amount_parsed', 0)
                        try:
                            base_electricity_cost += float(amount) if amount else 0
                        except (ValueError, TypeError):
                            pass
                
                # Fallback: check for energy_cost field
                if base_electricity_cost == 0:
                    energy_cost = financials.get('energy_cost', 0) or financials.get('energi_kost', 0)
                    try:
                        base_electricity_cost = float(energy_cost) if energy_cost else 0
                    except (ValueError, TypeError):
                        pass
            
            # Estimate electricity if missing (based on area)
            if base_electricity_cost == 0 and sqm > 0:
                # Rough estimate: ~50-100 NOK per m² per år
                base_electricity_cost = sqm * np.random.uniform(50, 100)
            
            # Only include properties with at least some data
            if current_base_rent > 0 or sqm > 0:
                assets_data.append({
                    'id': prop_id,
                    'sqm': sqm,
                    'current_base_rent': current_base_rent,
                    'base_electricity_cost': base_electricity_cost
                })
        
        df_assets = pd.DataFrame(assets_data)
        
        print(f"   ✅ Loaded {len(df_assets)} properties with data")
        print(f"   Properties with rent: {len(df_assets[df_assets['current_base_rent'] > 0])}")
        print(f"   Properties with electricity cost: {len(df_assets[df_assets['base_electricity_cost'] > 0])}")
        
        return df_assets


async def main_async():
    """Main execution function (async version)."""
    print("=" * 70)
    print("Synthetic Monthly Financial Time-Series Generator")
    print("=" * 70)
    
    # Step 1: Load assets from database OR create mock
    use_database = True  # Set to False to use mock data instead
    
    if use_database:
        print("\n1️⃣ Loading assets from database...")
        try:
            df_assets = await load_assets_from_database()
            if len(df_assets) == 0:
                print("   ⚠️  No properties found in database, falling back to mock data...")
                df_assets = create_mock_assets(n=10)
        except Exception as e:
            print(f"   ⚠️  Error loading from database: {e}")
            print("   Falling back to mock data...")
            df_assets = create_mock_assets(n=10)
    else:
        print("\n1️⃣ Creating mock assets DataFrame...")
        df_assets = create_mock_assets(n=10)
    
    print(f"   ✅ Processing {len(df_assets)} assets")
    print(f"   Sample:\n{df_assets.head(3).to_string()}\n")
    
    # Step 2: Generate time series
    print("2️⃣ Generating monthly time-series data (3 years)...")
    df_time_series = generate_time_series(df_assets, years_back=3)
    print(f"   ✅ Generated {len(df_time_series):,} monthly records")
    print(f"   Date range: {df_time_series['date'].min().strftime('%Y-%m-%d')} to {df_time_series['date'].max().strftime('%Y-%m-%d')}")
    print(f"   Records per asset: {len(df_time_series) // len(df_assets)} months\n")
    
    # Step 3: Format for GL transactions
    print("3️⃣ Formatting for General Ledger transactions...")
    df_gl = format_for_gl_transactions(df_time_series)
    print(f"   ✅ Created {len(df_gl):,} GL transaction records")
    print(f"   (4 transactions per asset per month: Rent, Electricity, Parking, Cleaning)\n")
    
    # Step 4: Print first 10 rows
    print("4️⃣ First 10 rows of GL transactions:")
    print("=" * 70)
    print(df_gl.head(10).to_string(index=False))
    print("=" * 70)
    
    # Step 5: Summary statistics
    print("\n5️⃣ Summary Statistics:")
    print(f"   Total Income (Rent): {df_gl[df_gl['Amount'] > 0]['Amount'].sum():,.2f} NOK")
    print(f"   Total Expenses: {abs(df_gl[df_gl['Amount'] < 0]['Amount'].sum()):,.2f} NOK")
    print(f"   Net: {df_gl['Amount'].sum():,.2f} NOK")
    print(f"\n   By Account Code:")
    for code in df_gl['AccountCode'].unique():
        code_total = df_gl[df_gl['AccountCode'] == code]['Amount'].sum()
        code_name = {
            '3000': 'Rent (Income)',
            '6000': 'Electricity (Expense)',
            '6100': 'Parking (Expense)',
            '6200': 'Cleaning (Expense)'
        }.get(code, 'Unknown')
        print(f"      {code} - {code_name}: {code_total:,.2f} NOK")
    
    # Step 6: Visualize electricity seasonality
    print("\n6️⃣ Generating electricity seasonality visualization...")
    visualize_electricity(df_time_series)
    
    # Step 7: Export ready
    print("\n7️⃣ Data ready for export:")
    print(f"   - df_time_series: {len(df_time_series):,} rows (monthly aggregated)")
    print(f"   - df_gl: {len(df_gl):,} rows (GL transaction format)")
    print("\n   To export to CSV:")
    print("   df_gl.to_csv('gl_transactions.csv', index=False)")
    print("   df_time_series.to_csv('monthly_financials.csv', index=False)")
    
    return df_time_series, df_gl


def main():
    """Main execution function (wrapper for async)."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    df_time_series, df_gl = main()
