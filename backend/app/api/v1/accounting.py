from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, text as sa_text
from uuid import UUID

from app.api.deps import get_db
from app.api.deps import get_current_user
from app.domains.core.models.user import User
from app.models.financial_models import GLTransaction
from app.schemas.accounting import TransactionListResponse, GLTransactionResponse

router = APIRouter()

@router.get("/transactions", response_model=TransactionListResponse)
async def get_transactions(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size"),
    property_id: Optional[UUID] = Query(None, description="Filter by property"),
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, description="Filter by month"),
    search: Optional[str] = Query(None, description="Search text (supplier, description, invoice)"),
    account_code: Optional[str] = Query(None, description="Filter by account code")
) -> Any:
    """
    Get detailed General Ledger transactions.
    """
    # Build query
    query = select(GLTransaction)
    
    if property_id:
        query = query.where(GLTransaction.property_id == property_id)
    
    if year:
        query = query.where(GLTransaction.ar == year)
        
    if month:
        query = query.where(GLTransaction.maaned == month)
        
    if account_code:
        query = query.where(GLTransaction.konto == account_code)
        
    if search:
        search_filter = f"%{search}%"
        query = query.where(or_(
            GLTransaction.leverandor_navn.ilike(search_filter),
            GLTransaction.tekst.ilike(search_filter),
            GLTransaction.bilagsnr.ilike(search_filter),
            GLTransaction.konto.ilike(search_filter),
            GLTransaction.dim1_navn.ilike(search_filter)
        ))
        
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Pagination and sorting
    query = query.order_by(desc(GLTransaction.bilagsdato), desc(GLTransaction.created_at))
    query = query.offset((page - 1) * size).limit(size)
    
    # Execute
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": (total + size - 1) // size
    }


@router.get("/konto-summary")
async def get_konto_summary(
    db: AsyncSession = Depends(get_db),
    year: int = Query(2025, description="Regnskapsår"),
    property_id: Optional[str] = Query(None, description="Filtrer per eiendom (UUID)"),
    region: Optional[str] = Query(None, description="Filtrer per region"),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    GL-kostnader gruppert per konto + srs_kategori for et gitt år.
    Returnerer netto per kontogruppe (GROUP BY HAVING SUM > 0).
    Sortert på total beløp (høyest først).
    """
    filters = ["gt.ar = :year", "gt.belop > 0"]
    params: dict = {"year": year}

    if property_id:
        filters.append("gt.property_id::text = :property_id")
        params["property_id"] = property_id

    if region:
        filters.append("p.region = :region")

    join_clause = ""
    if region or not property_id:
        join_clause = "LEFT JOIN properties p ON gt.property_id::text = p.property_id::text"
        if region:
            params["region"] = region

    where_sql = " AND ".join(filters)

    sql = sa_text(f"""
        SELECT
            gt.konto,
            gt.konto_navn,
            gt.srs_kategori,
            COUNT(DISTINCT gt.property_id) AS antall_eiendommer,
            SUM(gt.belop)                  AS total_belop,
            COUNT(*)                       AS antall_transaksjoner
        FROM gl_transactions gt
        {join_clause}
        WHERE {where_sql}
        GROUP BY gt.konto, gt.konto_navn, gt.srs_kategori
        ORDER BY total_belop DESC
    """)

    try:
        result = await db.execute(sql, params)
        rows = result.all()
    except Exception:
        await db.rollback()
        return {"year": year, "rows": [], "total": 0.0}

    data = [
        {
            "konto": r.konto or "",
            "konto_navn": r.konto_navn or "",
            "srs_kategori": r.srs_kategori or "Ukjent",
            "antall_eiendommer": int(r.antall_eiendommer or 0),
            "total_belop": float(r.total_belop or 0),
            "antall_transaksjoner": int(r.antall_transaksjoner or 0),
        }
        for r in rows
    ]

    total = sum(r["total_belop"] for r in data)
    return {"year": year, "rows": data, "total": total}
