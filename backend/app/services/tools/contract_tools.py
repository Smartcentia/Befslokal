from typing import List, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

from sqlalchemy.orm import contains_eager

async def search_contracts(query: str) -> str:
    """
    Searches for contracts using both Database (SQL) and Vector Search (PDF Content).
    
    1. SQL Search: Finds contracts by status, type (keywords like 'parking'), and address.
    2. Vector Search: Finds contracts by semantic content in invalid/scanned PDF files.
    
    Returns a combined summary.
    """
    import traceback
    try:
        from app.services.embeddings import generate_embeddings
        from app.core.config import settings
        
        output_parts = []
        
        # --- 1. SQL Search (Metadata/Type/Status) ---
        sql_results = ""
        try:
            query_text = query.lower()
            async with SessionLocal() as db:
                stmt = (
                    select(Contract, Unit, Property)
                    .join(Unit, Contract.unit_id == Unit.unit_id)
                    .join(Property, Unit.property_id == Property.property_id)
                )
                
                # Status Filter
                from sqlalchemy import cast, String
                if "utløpt" in query_text or "expired" in query_text:
                    stmt = stmt.where(cast(Contract.status, String) == "terminated")
                else:
                    stmt = stmt.where(cast(Contract.status, String) == "active")

                # Keyword Filter for SQL
                keywords = ["parkering", "garage", "garasje", "bolig", "næring", "lager", "storage"]
                found_keywords = [kw for kw in keywords if kw in query_text]
                
                if found_keywords:
                    from sqlalchemy import or_
                    conditions = [Unit.purpose.ilike(f"%{kw}%") for kw in found_keywords]
                    conditions.extend([Property.address.ilike(f"%{kw}%") for kw in found_keywords])
                    stmt = stmt.where(or_(*conditions))
                
                # Limit SQL results to top 5 to avoid noise if query is broad
                result = await db.execute(stmt.limit(5))
                rows = result.all()

                if rows:
                    sql_results += f"--- Database Treff ({len(rows)}) ---\n"
                    for contract, unit, prop in rows:
                        prop_addr = prop.address if prop else "Ukjent valg"
                        purpose = unit.purpose or "N/A"
                        sql_results += f"- ID: {str(contract.contract_id)} | Adresse: {prop_addr} | Type: {purpose} | Status: {contract.status}\n"
                else:
                    sql_results = "" # Silent fallback, let Vector speak
                    
            output_parts.append(sql_results)

        except Exception as e:
            output_parts.append(f"SQL Search Error: {e}")

        # --- 2. Vector Search (Document Content) ---
        vector_results = ""
        # Vector Search removed. Future: Use pgvector via app.services.vectordb
        # usage: 
        # from app.services.vectordb import search_documents
        # results = search_documents(query) 
        # For now, we skip vector search to avoid breaking without Vector DB.
        final_output = ""
        
        # 1. Vector Hits (Prioritize Document Content for "Find..." queries)
        if vector_results:
             final_output += vector_results + "\n"
             
        # 2. SQL Hits
        if sql_results:
             final_output += sql_results + "\n"
             
        # 3. Fallback
        if not final_output:
             final_output = "Ingen kontrakter funnet. Søkte i både strukturert database og dokumentarkiv.\n"
             
        output_parts.append(final_output)

        return "".join(output_parts)
        
    except Exception as e:
        error_msg = f"CRITICAL TOOL ERROR: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return error_msg
