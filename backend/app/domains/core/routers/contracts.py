"""API endpoints for contracts."""
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, cast, String
from typing import List, Optional
from uuid import UUID

from app.api.deps import get_db, get_current_user, get_current_admin_user
from app.domains.core.models.user import User
from app.core.property_access import check_property_access
from app.domains.core.models.contract import Contract as ContractModel
from app.domains.core.models.unit import Unit as UnitModel
from app.domains.core.models.party import Party as PartyModel
from app.domains.core.services.contract_cost_overview import build_contract_cost_overview
from app.schemas.contract import Contract, ContractCreate

# Import our migrated search service
from app.domains.innsikt.routers.search import vector_search_contracts

router = APIRouter()

@router.get("", response_model=List[Contract])
async def get_contracts(
    status: Optional[str] = Query(None, description="Filtrer på status (active/terminated)"),
    unit_id: Optional[str] = Query(None, description="Filtrer på enhet"),
    category: Optional[str] = Query(None, description="Filtrer på kategori"),
    vector_search: Optional[bool] = Query(False, description="Bruk vektorsøk i dokumenter"),
    query: Optional[str] = Query(None, description="Søketekst for vektorsøk"),
    skip: int = Query(0, description="Antall å hoppe over (pagination)"),
    limit: int = Query(50, description="Antall å hente (pagination)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hent liste over kontrakter (filtrert basert på property access).
    Støtter filtrering og hybrid søk (via vector_search=True).
    """
    # 1. Start with base query
    stmt = select(ContractModel)
    
    # 2. Apply Standard Filters
    if status:
        stmt = stmt.where(ContractModel.status == status)
    
    if unit_id:
        # Check property access via unit
        unit_stmt = select(UnitModel).where(UnitModel.unit_id == unit_id)
        unit_result = await db.execute(unit_stmt)
        unit = unit_result.scalar_one_or_none()
        
        if unit and unit.property_id:
            # Check access to property
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(unit.property_id),
                require_write=False
            )
        
        stmt = stmt.where(ContractModel.unit_id == unit_id)

    if category:
        stmt = stmt.where(ContractModel.category == category)
        
    # 3. Handle Vector Search / Hybrid Logic
    if vector_search and query:
        # Perform vector search first to get relevant contract IDs
        vector_results = await vector_search_contracts(
            db, 
            query_text=query, 
            n_results=10
        )
        # Extract contract IDs from metadata
        relevant_contract_ids = set()
        for res in vector_results:
            if res.get("metadata") and res["metadata"].get("contract_id"):
                relevant_contract_ids.add(res["metadata"]["contract_id"])
        
        # If we found relevant contracts, filter by them
        if relevant_contract_ids:
            stmt = stmt.where(ContractModel.contract_id.in_(relevant_contract_ids))
        else:
            # No semantic matches found, return empty or fallback to text search?
            # For now, return empty if vector search was explicitly requested but yield no results
            return []

    # 4. Execute Query with Eager Loading
    from sqlalchemy.orm import selectinload
    # Enforce max limit for performance
    safe_limit = min(limit, 10000)
    
    stmt = stmt.options(
        selectinload(ContractModel.party),
        selectinload(ContractModel.unit).selectinload(UnitModel.property),
        selectinload(ContractModel.files)
    ).offset(skip).limit(safe_limit)
    
    result = await db.execute(stmt)
    contracts_db = result.scalars().all()
    
    # 5. Filter contracts based on property access
    from app.domains.core.models.user import UserRole

    # ADMIN sees all contracts - skip per-contract DB lookups entirely
    if current_user.role == UserRole.ADMIN:
        return list(contracts_db)

    # For other roles: filter by accessible property IDs (one DB query, not N)
    from app.core.property_access import get_user_accessible_property_ids
    accessible_ids = await get_user_accessible_property_ids(db, current_user)
    if accessible_ids is None:
        return list(contracts_db)  # fallback: admin-equivalent

    filtered_contracts = []
    for contract in contracts_db:
        if contract.unit and contract.unit.property_id:
            if contract.unit.property_id in accessible_ids:
                filtered_contracts.append(contract)
        # Contracts without unit: skip for non-admin users

    return filtered_contracts


@router.get("/costs")
async def get_contract_cost_overview_alias(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """
    Samme svar som GET /api/v1/admin/contracts/costs.
    Må ligge før /{contract_id}, ellers matches «costs» som kontrakt-ID (404).
    """
    return await build_contract_cost_overview(db)


@router.get("/{contract_id}", response_model=Contract)
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Hent kontrakt ved ID (med property access check)."""
    # Eager load related data
    from sqlalchemy.orm import selectinload
    stmt = select(ContractModel).where(ContractModel.contract_id == contract_id).options(
        selectinload(ContractModel.party),
        selectinload(ContractModel.unit).selectinload(UnitModel.property),
        selectinload(ContractModel.files)
    )
    
    result = await db.execute(stmt)
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Kontrakt ikke funnet")
    
    # Check access to property via unit
    if contract.unit and contract.unit.property_id:
        await check_property_access(
            db=db,
            user=current_user,
            property_id=str(contract.unit.property_id),
            require_write=False
        )
    
    return contract

@router.post("", response_model=Contract, status_code=201)
async def create_contract(
    contract_data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Opprett ny kontrakt (med property access check)."""
    # Verify Unit
    unit_res = await db.execute(select(UnitModel).where(UnitModel.unit_id == str(contract_data.unit_id)))
    unit = unit_res.scalar_one_or_none()
    if not unit:
         raise HTTPException(status_code=404, detail="Enhet ikke funnet")
    
    # Check property access (write access required to create contract)
    if unit.property_id:
        await check_property_access(
            db=db,
            user=current_user,
            property_id=str(unit.property_id),
            require_write=True
        )
         
    # Verify Party
    party_res = await db.execute(select(PartyModel).where(PartyModel.party_id == str(contract_data.party_id)))
    if not party_res.scalar_one_or_none():
         raise HTTPException(status_code=404, detail="Part ikke funnet")

    # Serialize complex fields
    # Use mode='python' to get datetime objects for SQLAlchemy DateTime columns
    data = contract_data.model_dump(exclude={'periods', 'amount'})
    
    # Convert IDs to string for SQLite compatibility
    data['unit_id'] = str(data['unit_id'])
    data['party_id'] = str(data['party_id'])
    
    # Manually serialize JSON columns to be JSON-safe (e.g. strings for dates)
    # SQLAlchemy's JSON type with SQLite might imply simple json.dumps which fails on datetimes.
    # We verify if we need to dump these specific fields as JSON-ready (dicts of strings)
    # Using mode='json' for these specific nested models/fields ensures date serialization.
    periods_data = [p.model_dump(mode='json') for p in contract_data.periods]
    amount_data = contract_data.amount.model_dump(mode='json')
    
    # Merge
    data['periods'] = periods_data
    data['amount'] = amount_data

    db_contract = ContractModel(**data)
    db.add(db_contract)
    await db.commit()
    await db.refresh(db_contract)
    
    # Reload with relationships for response model verification
    from sqlalchemy.orm import selectinload
    stmt = select(ContractModel).where(ContractModel.contract_id == db_contract.contract_id).options(
        selectinload(ContractModel.party),
        selectinload(ContractModel.unit).selectinload(UnitModel.property),
        selectinload(ContractModel.files)
    )
    result = await db.execute(stmt)
    db_contract_loaded = result.scalar_one()
    
    return db_contract_loaded

@router.patch("/{contract_id}", response_model=Contract)
async def patch_contract(
    contract_id: str,
    contract_in: dict, # Support flexible patching for now or add schema
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Oppdater deler av en kontrakt (med property access check)."""
    try:
        uuid_obj = str(contract_id)
        from sqlalchemy.orm import selectinload
        stmt = select(ContractModel).where(ContractModel.contract_id == uuid_obj).options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property)
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            raise HTTPException(status_code=404, detail="Kontrakt ikke funnet")
        
        # Check property access (write access required to update contract)
        if db_obj.unit and db_obj.unit.property_id:
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(db_obj.unit.property_id),
                require_write=True
            )
            
        for field, value in contract_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")

@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Slett en kontrakt (med property access check)."""
    try:
        uuid_obj = str(contract_id)
        from sqlalchemy.orm import selectinload
        stmt = select(ContractModel).where(ContractModel.contract_id == uuid_obj).options(
            selectinload(ContractModel.unit).selectinload(UnitModel.property)
        )
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        if not db_obj:
            raise HTTPException(status_code=404, detail="Kontrakt ikke funnet")
        
        # Check property access (write access required to delete contract)
        if db_obj.unit and db_obj.unit.property_id:
            await check_property_access(
                db=db,
                user=current_user,
                property_id=str(db_obj.unit.property_id),
                require_write=True
            )
        
        await db.delete(db_obj)
        await db.commit()
        return Response(status_code=204)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ugyldig UUID-format")
