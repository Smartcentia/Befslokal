"""
Contract Analysis Tools

Specialized tools for analyzing and comparing contract data,
particularly financial aspects like monthly rent.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from app.db.session import SessionLocal


@asynccontextmanager
async def get_session():
    """Helper to get async database session."""
    async with SessionLocal() as session:
        yield session


async def compare_contracts_by_price() -> dict:
    """
    Compare the cheapest and most expensive lease contracts by monthly rent.
    Returns detailed information about both contracts including address, tenant, and price difference.
    
    Returns:
        dict: Contains cheapest_contract, most_expensive_contract, and price_difference
    """
    async with get_session() as db:
        query = text("""
            (SELECT 
                'cheapest' as comparison_type,
                c.contract_id::text,
                u.address,
                (c.amount->>'monthly_rent')::numeric as monthly_rent,
                COALESCE(c.amount->>'currency', 'NOK') as currency,
                p.name as tenant_name,
                c.status
             FROM contracts c
             LEFT JOIN units u ON c.unit_id = u.unit_id
             LEFT JOIN parties p ON c.party_id = p.party_id
             WHERE c.amount IS NOT NULL 
               AND c.amount->>'monthly_rent' IS NOT NULL
               AND c.amount->>'monthly_rent' ~ '^[0-9.]+$'
             ORDER BY (c.amount->>'monthly_rent')::numeric ASC
             LIMIT 1)
            
            UNION ALL
            
            (SELECT 
                'most_expensive' as comparison_type,
                c.contract_id::text,
                u.address,
                (c.amount->>'monthly_rent')::numeric as monthly_rent,
                COALESCE(c.amount->>'currency', 'NOK') as currency,
                p.name as tenant_name,
                c.status
             FROM contracts c
             LEFT JOIN units u ON c.unit_id = u.unit_id
             LEFT JOIN parties p ON c.party_id = p.party_id
             WHERE c.amount IS NOT NULL 
               AND c.amount->>'monthly_rent' IS NOT NULL
               AND c.amount->>'monthly_rent' ~ '^[0-9.]+$'
             ORDER BY (c.amount->>'monthly_rent')::numeric DESC
             LIMIT 1)
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        if len(rows) == 0:
            return {
                "error": "No contracts with price data found",
                "message": "Ingen kontrakter med prisdata funnet i databasen"
            }
        
        cheapest = None
        most_expensive = None
        
        for row in rows:
            data = {
                "contract_id": row[1],  # contract_id
                "address": row[2] or "Ukjent adresse",
                "monthly_rent": float(row[3]) if row[3] else None,
                "currency": row[4] or "NOK",
                "tenant": row[5] or "Ukjent leietaker",
                "status": row[6] or "unknown"
            }
            
            if row[0] == 'cheapest':  # comparison_type
                cheapest = data
            else:
                most_expensive = data
        
        # Calculate difference
        price_diff = None
        if cheapest and most_expensive:
            if cheapest["monthly_rent"] and most_expensive["monthly_rent"]:
                price_diff = most_expensive["monthly_rent"] - cheapest["monthly_rent"]
        
        return {
            "cheapest_contract": cheapest,
            "most_expensive_contract": most_expensive,
            "price_difference": price_diff,
            "currency": "NOK"
        }


async def get_contract_price_statistics() -> dict:
    """
    Calculate statistics about contract prices including average, median, min, max.
    
    Returns:
        dict: Statistical summary of contract prices
    """
    async with get_session() as db:
        query = text("""
            SELECT 
                COUNT(*) as total_contracts,
                COUNT(CASE WHEN amount->>'monthly_rent' IS NOT NULL THEN 1 END) as contracts_with_price,
                AVG((amount->>'monthly_rent')::numeric) as average_rent,
                MIN((amount->>'monthly_rent')::numeric) as min_rent,
                MAX((amount->>'monthly_rent')::numeric) as max_rent,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY (amount->>'monthly_rent')::numeric) as median_rent
            FROM contracts
            WHERE amount IS NOT NULL
              AND amount->>'monthly_rent' IS NOT NULL
              AND amount->>'monthly_rent' ~ '^[0-9.]+$'
        """)
        
        result = await db.execute(query)
        row = result.fetchone()
        
        if not row:
            return {"error": "Could not calculate statistics"}
        
        return {
            "total_contracts": row[0],
            "contracts_with_price_data": row[1],
            "average_monthly_rent": float(row[2]) if row[2] else None,
            "min_monthly_rent": float(row[3]) if row[3] else None,
            "max_monthly_rent": float(row[4]) if row[4] else None,
            "median_monthly_rent": float(row[5]) if row[5] else None,
            "currency": "NOK"
        }


async def find_contracts_by_price_range(min_price: float, max_price: float, limit: int = 10) -> list:
    """
    Find contracts within a specific price range.
    
    Args:
        min_price: Minimum monthly rent
        max_price: Maximum monthly rent
        limit: Maximum number of results to return
    
    Returns:
        list: Contracts within the price range
    """
    async with get_session() as db:
        query = text("""
            SELECT 
                c.contract_id::text,
                u.address,
                (c.amount->>'monthly_rent')::numeric as monthly_rent,
                COALESCE(c.amount->>'currency', 'NOK') as currency,
                p.name as tenant_name,
                c.status
            FROM contracts c
            LEFT JOIN units u ON c.unit_id = u.unit_id
            LEFT JOIN parties p ON c.party_id = p.party_id
            WHERE c.amount IS NOT NULL
              AND c.amount->>'monthly_rent' IS NOT NULL
              AND c.amount->>'monthly_rent' ~ '^[0-9.]+$'
              AND (c.amount->>'monthly_rent')::numeric BETWEEN :min_price AND :max_price
            ORDER BY (c.amount->>'monthly_rent')::numeric ASC
            LIMIT :limit
        """)
        
        result = await db.execute(query, {"min_price": min_price, "max_price": max_price, "limit": limit})
        rows = result.fetchall()
        
        contracts = []
        for row in rows:
            contracts.append({
                "contract_id": row[0],
                "address": row[1] or "Ukjent adresse",
                "monthly_rent": float(row[2]) if row[2] else None,
                "currency": row[3] or "NOK",
                "tenant": row[4] or "Ukjent leietaker",
                "status": row[5] or "unknown"
            })
        
        return contracts
