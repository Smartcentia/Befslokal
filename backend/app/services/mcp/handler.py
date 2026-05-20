from typing import Callable, Dict, Any, List
from pydantic import BaseModel
import json
import uuid
from sqlalchemy import select, text
from uuid import UUID
from fastapi import HTTPException
from app.services.infrastructure.logger import get_logger

logger = get_logger(__name__)

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.hms.models.risk import RiskAssessment
from app.domains.core.utils.region_mapping import get_operational_region

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class MCPHandler:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any] = None):
        """Decorator to register a function as an MCP tool."""
        if parameters is None:
            parameters = {"type": "object", "properties": {}}

        def decorator(func: Callable):
            self._tools[name] = func
            self._definitions[name] = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters
            )
            return func
        return decorator

    async def execute_tool(self, name: str, arguments: Dict[str, Any], db: Any = None) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found")
        
        func = self._tools[name]
        
        import inspect
        
        # Check if function accepts 'db' parameter
        call_kwargs = arguments.copy()
        sig = inspect.signature(func)
        if 'db' in sig.parameters and db is not None:
             call_kwargs['db'] = db

        if inspect.iscoroutinefunction(func):
            return await func(**call_kwargs)
        
        # Run synchronous tools in a separate thread to avoid blocking the event loop
        # We use run_in_threadpool from starlette (FastAPI's core) as it handles contextvars correctly.
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(func, **call_kwargs)

    def get_tools(self) -> List[ToolDefinition]:
        return list(self._definitions.values())


# Valid Tools Implementation
from app.services.search.search_service import search_fulltext
from app.domains.hms.services.risk_service import risk_service
from app.domains.fdv.services.action_service import action_service
from app.services.tool_registry import tool_registry
from app.services.external.api_clients.lovdata_client import LovdataClient

mcp_handler = MCPHandler()

# --- Helper for DB Session ---

# Tools need to manage their own sessions since they are called outside of FastAPI dependency injection
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session():
    async with SessionLocal() as session:
        yield session

@asynccontextmanager
async def get_or_use_session(db=None):
    if db:
        yield db
    else:
        async with get_session() as session:
            yield session

@mcp_handler.register_tool(
    name="search_documents",
    description="Search for relevant information in documentation.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
)
async def search_documents_tool(query: str, db: Any = None):
    async with get_or_use_session(db) as db:
        try:
            results = await search_fulltext(session=db, query=query, limit=5)
            if not results:
                raise HTTPException(status_code=404, detail="No documents found")
            
            formatted = []
            for doc in results:
                formatted.append(f"File: {doc.get('source_file')}\nHeadline: {doc.get('headline')}\nScore: {doc.get('rank')}\n")
            return "\n".join(formatted)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Document search failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Search service unavailable")

@mcp_handler.register_tool(
    name="classify_risk",
    description="Analyser tekst for risikonivå, eller beregn total risiko for en spesifikk eiendom (Emerald, Amber, Orange, Rose).",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Tekst som skal analyseres for risikoindikasjoner"},
            "property_id": {"type": "string", "description": "UUID til eiendommen for beregning av aggregert risiko"}
        },
        "required": ["text"]
    }
)
async def classify_risk_tool(text: str, property_id: str = None, db: Any = None):
    async with get_or_use_session(db) as db:
        if property_id:
            try:
                uuid_obj = UUID(property_id)
                result = await risk_service.calculate_risk_for_property(str(uuid_obj), db)
                return result
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid property_id format: {property_id}")
            except Exception as e:
                logger.error(f"Risk calculation failed: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail="Risk calculation service unavailable")

        # If no property_id, we would typically use an LLM or pattern matcher
        raise HTTPException(status_code=400, detail="Text-only risk analysis requires property_id parameter")

@mcp_handler.register_tool(
    name="create_work_order",
    description="Create a maintenance work order.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string"},
            "description": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
        },
        "required": ["property_id", "description"]
    }
)
async def create_work_order_tool(property_id: str, description: str, priority: str = "medium", db: Any = None):
    """Create a maintenance work order for a property."""
    from datetime import datetime

    # Validate priority
    valid_priorities = ["low", "medium", "high", "critical"]
    if priority not in valid_priorities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority '{priority}'. Must be one of: {', '.join(valid_priorities)}"
        )

    async with get_or_use_session(db) as db:
        try:
            # Verify property exists
            try:
                uuid_obj = UUID(property_id)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid UUID format: {property_id}")

            result = await db.execute(select(Property).where(Property.property_id == uuid_obj))
            prop = result.scalar_one_or_none()

            if not prop:
                raise HTTPException(status_code=404, detail=f"Property {property_id} not found")

            # Generate work order ID
            order_id = f"WO-{str(uuid.uuid4())[:8]}"

            # Log the work order creation
            logger.info(f"Work order {order_id} created for property {prop.address} with priority {priority}")

            # Return successful work order creation
            # In a full implementation, this would create a record in a work_orders table
            return {
                "order_id": order_id,
                "status": "created",
                "property_id": str(uuid_obj),
                "property_name": prop.name or prop.address,
                "description": description,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "message": f"Work order created for {prop.address}"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Work order creation failed: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Work order service unavailable")

@mcp_handler.register_tool(
    name="check_anomalies",
    description="Check for risk anomalies or high-severity deviations for a property.",
    parameters={
        "type": "object", 
        "properties": {"property_id": {"type": "string"}},
        "required": ["property_id"]
    }
)
async def check_anomalies_tool(property_id: str):
    # Integration with Risk Service to find 'Red' or 'High' risks
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            stmt = select(RiskAssessment).where(
                RiskAssessment.property_id == uuid_obj,
                RiskAssessment.risk_level.in_(["High", "Critical", "Red"]) # Assuming string enum
            ).order_by(RiskAssessment.assessment_date.desc()).limit(5)
            
            result = await db.execute(stmt)
            risks = result.scalars().all()
            
            if not risks:
                return "No high-severity anomalies detected."
                
            return [
                {
                    "date": str(r.assessment_date),
                    "category": r.risk_category,
                    "level": r.risk_level,
                    "notes": r.notes
                }
                for r in risks
            ]
        except ValueError:
            return "Invalid Property ID"
        except Exception as e:
            return f"Error checking anomalies: {str(e)}"

# --- Geo & Proximity Tools ---

@mcp_handler.register_tool(
    name="get_nearby_services",
    description="Get nearby services (schools, transport, health, poi) for a property using Mapbox.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string"},
            "type": {"type": "string", "description": "Type of service or search query (e.g., school, hospital, poi)", "default": "point_of_interest"}
        },
        "required": ["property_id"]
    }
)
async def get_nearby_services_tool(property_id: str, type: str = "point_of_interest"):
    """Hent nærliggende tjenester for eiendom via Mapbox."""
    from app.services.proximity.service import ProximityService
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            prop_res = await db.execute(select(Property).where(Property.property_id == uuid_obj))
            prop = prop_res.scalar_one_or_none()
            if not prop:
                return {"error": f"Property {property_id} not found", "services": []}
            if not prop.latitude or not prop.longitude:
                return {"error": "Property has no coordinates", "services": []}
            service = ProximityService(db)
            results = await service.fetch_proximity_services(
                prop.property_id, prop.latitude, prop.longitude,
                service_types=[type] if type != "point_of_interest" else None
            )
            return {
                "property_id": property_id,
                "services": [
                    {"name": s.service_name, "type": s.service_type, "distance_meters": s.distance_meters}
                    for s in results
                ]
            }
        except ValueError:
            return {"error": "Invalid property_id format", "services": []}
        except Exception as e:
            return {"error": str(e), "services": []}

# --- New Tools for Full Data Access (User Request) ---

import uuid

@mcp_handler.register_tool(
    name="get_property_info",
    description="Get detailed information about a property.",
    parameters={
        "type": "object",
        "properties": {"property_id": {"type": "string"}},
        "required": ["property_id"]
    }
)
async def get_property_info_tool(property_id: str):
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            
            # Fetch Property
            prop_res = await db.execute(select(Property).where(Property.property_id == uuid_obj))
            prop = prop_res.scalar_one_or_none()
            
            if not prop:
                return f"Property with ID {property_id} not found."
            
            # Fetch Units
            unit_res = await db.execute(select(Unit).where(Unit.property_id == uuid_obj))
            units = unit_res.scalars().all()
            
            # Fetch Contracts via Units
            contracts = []
            if units:
                unit_ids = [u.unit_id for u in units]
                contract_res = await db.execute(select(Contract).where(Contract.unit_id.in_(unit_ids)))
                contracts = contract_res.scalars().all()
                
            # Fetch Latest Risk
            risk_res = await db.execute(
                select(RiskAssessment)
                .where(RiskAssessment.property_id == uuid_obj)
                .order_by(RiskAssessment.assessment_date.desc())
                .limit(1)
            )
            latest_risk = risk_res.scalar_one_or_none()
            
            return {
                "property_id": str(prop.property_id),
                "address": prop.address,
                "city": prop.city,
                "total_area": prop.total_area,
                "unit_count": len(units),
                "contract_count": len(contracts),
                "risk_status": latest_risk.overall_score if latest_risk else "Not Assessed",
                "manager": "Ola Nordmann (Default)" # Placeholder until Manager rel is added
            }
            
        except ValueError:
            return "Invalid Property ID format."
        except Exception as e:
            return f"Error fetching property info: {str(e)}"

@mcp_handler.register_tool(
    name="list_properties",
    description="List properties with optional filtering.",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": []
    }
)
async def list_properties_tool(city: str = None):
    async with get_session() as db:
        try:
            query = select(Property)
            if city:
                query = query.where(Property.city.ilike(f"%{city}%"))
            
            # Limit to 10 to avoid token overflow
            query = query.limit(10)
            
            result = await db.execute(query)
            props = result.scalars().all()
            
            return [
                {"id": str(p.property_id), "address": p.address, "city": p.city, "usage": p.usage} 
                for p in props
            ]
        except Exception as e:
            return f"Error listing properties: {str(e)}"

@mcp_handler.register_tool(
    name="check_internal_control",
    description="Check internal control (HMS/Quality) process status for a property.",
    parameters={
        "type": "object",
        "properties": {"property_id": {"type": "string"}},
        "required": ["property_id"]
    }
)
async def check_internal_control_tool(property_id: str):
    from app.domains.hms.models.internal_control import InternalControlCase
    from app.domains.core.models.property import Property
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.party import Party
    from app.domains.core.models.user import User
    
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            # Find active cases for this property
            stmt = select(InternalControlCase).where(
                InternalControlCase.property_id == uuid_obj,
                InternalControlCase.status == "open"
            ).limit(5)
            
            result = await db.execute(stmt)
            cases = result.scalars().all()
            
            if not cases:
                return {
                    "property_id": property_id,
                    "status": "compliant",
                    "message": "No open internal control cases found."
                }
                
            return [
                {
                    "case_id": str(c.case_id),
                    "title": c.title,
                    "state": c.process_state,
                    "updated": str(c.updated_at)
                }
                for c in cases
            ]
        except Exception as e:
            return f"Error checking internal control: {str(e)}"

from app.services.help_service import help_service

@mcp_handler.register_tool(
    name="list_help_articles",
    description="List all available technical and process documentation articles.",
    parameters={"type": "object", "properties": {}}
)
async def list_help_articles_tool():
    articles = help_service.list_articles()
    return "\n".join([f"- {a['id']}: {a['title']}" for a in articles])

@mcp_handler.register_tool(
    name="read_help_article",
    description="Read the full content of a specific documentation article.",
    parameters={
        "type": "object",
        "properties": {"article_id": {"type": "string"}},
        "required": ["article_id"]
    }
)
async def read_help_article_tool(article_id: str):
    content = help_service.get_article(article_id)
    return content if content else f"Article {article_id} not found."

# Lazy import: CodeInterpreter pulls in matplotlib which can fail/slow startup on Render.
# Only load when execute_code is actually called.
def _get_code_interpreter():
    from app.services.intelligence.ai.code_interpreter import CodeInterpreter
    return CodeInterpreter()

@mcp_handler.register_tool(
    name="execute_code",
    description="Execute Python code to perform calculation, data analysis or visualization.",
    parameters={
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"]
    }
)
async def execute_code_tool(code: str):
    return await _get_code_interpreter().execute_code(code)

@mcp_handler.register_tool(
    name="list_contracts",
    description="List all active contracts with financial details.",
    parameters={
        "type": "object",
        "properties": {"limit": {"type": "integer"}},
        "required": []
    }
)
async def list_contracts_tool(limit: int = 50):
    async with get_session() as db:
        try:
            # Join with Unit to get Area
            stmt = select(Contract, Unit).join(Unit, Contract.unit_id == Unit.unit_id).limit(limit)
            result = await db.execute(stmt)
            rows = result.all()
            
            data = []
            for contract, unit in rows:
                # Extract rent from JSON amount field (assuming simple structure for MVP)
                # Amount format might be complex, we'll try to get 'total' or 'monthly_rent'
                rent_amount = 0
                if isinstance(contract.amount, dict):
                    rent_amount = contract.amount.get("total", 0) or contract.amount.get("monthly", 0)
                
                data.append({
                    "contract_id": str(contract.contract_id),
                    "party_id": str(contract.party_id),
                    "rent_amount": rent_amount,
                    "start_date": str(contract.periods.get("start")) if contract.periods else None,
                    "area_m2": unit.total_area,
                    "property_id": str(unit.property_id)
                })
            return data
        except Exception as e:
            return f"Error fetching contracts: {str(e)}"

@mcp_handler.register_tool(
    name="fetch_ssb_market_data",
    description="Fetch market rent prices (NOK/m2) for benchmarking.",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
    }
)
async def fetch_ssb_market_data_tool(city: str):
    # Data fetch via ssb_client.py
    return {}

# --- Math & Logic Tools ---

@mcp_handler.register_tool(
    name="check_leap_year",
    description="Checks if a year is a leap year.",
    parameters={
        "type": "object",
        "properties": {"year": {"type": "integer"}},
        "required": ["year"]
    }
)
def check_leap_year_tool(year: int):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

@mcp_handler.register_tool(
    name="calculate_days_between",
    description="Calculate days between two dates (YYYY-MM-DD).",
    parameters={
        "type": "object",
        "properties": {
            "start_date": {"type": "string"},
            "end_date": {"type": "string"}
        },
        "required": ["start_date", "end_date"]
    }
)
def calculate_days_between_tool(start_date: str, end_date: str):
    from datetime import datetime
    try:
        d1 = datetime.strptime(start_date, "%Y-%m-%d")
        d2 = datetime.strptime(end_date, "%Y-%m-%d")
        return abs((d2 - d1).days)
    except Exception as e:
        return f"Error: {str(e)}"

# --- Contract Search Tool ---

@mcp_handler.register_tool(
    name="search_contracts",
    description="Search for contracts by keyword, attributes, or type (e.g., parking, garage, lease, rent). Use this to find specific agreements.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
)
async def search_contracts_tool(query: str):
    from app.services.tools.contract_tools import search_contracts
    return await search_contracts(query)

@mcp_handler.register_tool(
    name="search_fulltext",
    description="Search through 481 contract documents using PostgreSQL full-text search with Norwegian language support. Returns relevant excerpts with highlighting and ranking.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query in Norwegian"},
            "limit": {"type": "integer", "description": "Number of results (default 5)", "default": 5}
        },
        "required": ["query"]
    }
)
async def search_fulltext_tool(query: str, limit: int = 5):
    """Search using PostgreSQL full-text search."""
    from app.services.search.search_service import search_fulltext
    async with get_session() as db:
        try:
            # Call search_fulltext with session as first parameter
            results = await search_fulltext(
                session=db,
                query=query,
                limit=limit
            )
            
            # Format for LLM consumption
            if not results:
                return f"Ingen dokumenter funnet for '{query}'."
            
            formatted = []
            for idx, doc in enumerate(results, 1):
                # Extract useful info
                source_file = doc.get("source_file", "Ukjent kilde")
                headline = doc.get("headline", doc.get("content", "")[:200])
                rank = doc.get("rank", 0)
                
                formatted.append(f"**Resultat {idx}** (relevans: {rank:.2f}):\n{source_file}\n{headline}\n")
            
            summary = f"Fant {len(results)} dokumenter for '{query}':\n\n" + "\n".join(formatted)
            return summary
            
        except Exception as e:
            return f"Feil ved fulltekstsøk: {str(e)}"


@mcp_handler.register_tool(
    name="read_audit_logs",
    description="Read system audit logs to investigate activity, errors, or tool executions.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
            "severity": {"type": "string"}
        }
    }
)
async def read_audit_logs_tool(property_id: str = None, limit: int = 20, severity: str = None):
    from app.domains.core.models.audit import AuditLog
    async with get_session() as db:
        try:
            query = select(AuditLog)
            if property_id:
                query = query.where(AuditLog.entity_id == property_id)
            if severity:
                query = query.where(AuditLog.severity == severity)
            
            query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
            result = await db.execute(query)
            logs = result.scalars().all()
            
            if not logs:
                return "No audit logs found."
                
            return [
                {
                    "timestamp": str(l.timestamp),
                    "action": l.action,
                    "actor": l.actor,
                    "entity": f"{l.entity_type} {l.entity_id}" if l.entity_id else "system",
                    "details": l.details,
                    "severity": l.severity
                }
                for l in logs
            ]
        except Exception as e:
            return f"Error reading logs: {str(e)}"

import sqlparse
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        # Clean up old calls
        self.calls[user_id] = [t for t in self.calls[user_id] if now - t < self.period]
        
        if len(self.calls[user_id]) >= self.max_calls:
            return False
            
        self.calls[user_id].append(now)
        return True

# Initialize rate limiter: 10 queries per 60 seconds
sql_rate_limiter = RateLimiter(max_calls=10, period=60)

def validate_readonly_query(query: str) -> str:
    """
    Validates that the query is a strict READ-ONLY SQL SELECT statement using sqlparse.
    Returns None if valid, or an error message string if invalid.
    """
    try:
        parsed = sqlparse.parse(query)
    except Exception as e:
        return f"SQL Parsing Error: {str(e)}"

    if not parsed:
        return "Empty query."

    for statement in parsed:
        # Get the statement type (keys are usually 'SELECT', 'INSERT', etc.)
        stmt_type = statement.get_type().upper()
        
        if stmt_type != 'SELECT':
            return f"Error: Only SELECT queries are allowed. Found: {stmt_type}"
            
    return None

# --- Universal SQL Tool ---

@mcp_handler.register_tool(
    name="execute_sql_query",
    description="""Utfør en READ-ONLY SQL-spørring mot Postgres-databasen. Bruk denne for komplekse analyser, statistikk og data som ikke dekkes av spesialiserte verktøy.
    
    TABELLER: 
    - properties: Navn, adresse, region, external_data (JSONB)
    - units: Enheter, areal, formål
    - contracts: Kontrakter, status, amount (JSONB med leieinfo)
    - parties: Utleiere/Parter
    - risk_assessments: Risikovurderinger
    - socioeconomic_data: crime_rate_per_1000, unemployment_rate, median_income, population_density
    
    JSONB OPERASJONER (PostgreSQL):
    - Hent felt som tekst: external_data->'master_data'->>'area'
    - Hent finansiell transaksjon: external_data->'financials'->'transactions_2024'
    - Konverter til tall: (amount->>'amount_per_year')::numeric
    
    EKSEMPLER:
    1. Finn eiendommer med høyest kriminalitetsrate:
       SELECT p.name, s.crime_rate_per_1000 FROM properties p 
       JOIN socioeconomic_data s ON p.property_id = s.property_id 
       ORDER BY s.crime_rate_per_1000 DESC LIMIT 5;
    
    2. Finn totalt beløp brukt på vedlikehold (konto 6600) i 2024 per region:
       SELECT p.region, SUM((t->>'amount')::numeric) as total_spend 
       FROM properties p, jsonb_array_elements(external_data->'financials'->'transactions_2024') t 
       WHERE t->>'account' = '6600' GROUP BY p.region;
    
    3. Finn leiekontrakter som utløper snart:
       SELECT contract_id, end_date FROM contracts WHERE end_date > CURRENT_DATE AND end_date < CURRENT_DATE + INTERVAL '6 months';
    """,
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
)
async def execute_sql_query_tool(query: str, db: Any = None):
    # 1. Rate Limiting (using a default 'mcp_user' since we don't have user context here easily)
    # Ideally, we'd pass the user ID from the request context, but for MVP remediation:
    if not sql_rate_limiter.is_allowed("default_user"):
        return "Error: Rate limit exceeded (10 queries/minute). Please try again later."

    # 2. SQL Injection & Read-Only Validation
    error = validate_readonly_query(query)
    if error:
        return error

    async with get_or_use_session(db) as db:
        try:
            # Execute
            result = await db.execute(text(query))
            
            # Convert to list of dicts
            try:
                rows = result.mappings().all()
            except Exception:
                # Handle cases where result returns no rows (shouldn't happen with SELECT but safe to handle)
                return "Query executed but returned no result set."
            
            if not rows:
                return "No results found."
                
            # Limit rows to 20 to avoid context overflow
            limited_rows = rows[:20]
            data = [dict(row) for row in limited_rows]
            
            res_str = json.dumps(data, default=str)
            if len(rows) > 20:
                res_str += f"\n(and {len(rows) - 20} more rows...)"
            return res_str
            
        except Exception as e:
            return f"SQL Error: {str(e)}"

# --- Contract Price Analysis Tools ---

@mcp_handler.register_tool(
    name="compare_contracts_by_price",
    description="Compare the cheapest and most expensive lease contracts by monthly rent. Returns full details including address, tenant, price difference, and currency.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def compare_contracts_by_price_tool():
    from app.services.tools.contract_analysis_tools import compare_contracts_by_price
    return await compare_contracts_by_price()

@mcp_handler.register_tool(
    name="get_contract_price_statistics",
    description="Get statistical summary of contract prices including average, median, min, max, and total counts.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_contract_price_statistics_tool():
    from app.services.tools.contract_analysis_tools import get_contract_price_statistics
    return await get_contract_price_statistics()

@mcp_handler.register_tool(
    name="find_contracts_by_price_range",
    description="Find contracts within a specific monthly rent price range (in NOK).",
    parameters={
        "type": "object",
        "properties": {
            "min_price": {"type": "number", "description": "Minimum monthly rent in NOK"},
            "max_price": {"type": "number", "description": "Maximum monthly rent in NOK"},
            "limit": {"type": "integer", "description": "Maximum number of results", "default": 10}
        },
        "required": ["min_price", "max_price"]
    }
)
async def find_contracts_by_price_range_tool(min_price: float, max_price: float, limit: int = 10):
    from app.services.tools.contract_analysis_tools import find_contracts_by_price_range
    return await find_contracts_by_price_range(min_price, max_price, limit)

@mcp_handler.register_tool(
    name="search_lovdata",
    description="Search through laws, regulations, and legal documents in Lovdata. Returns relevant results with summaries and external links.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query in Norwegian"},
            "limit": {"type": "integer", "description": "Number of results (default 5)", "default": 5}
        },
        "required": ["query"]
    }
)
async def search_lovdata_tool(query: str, limit: int = 5):
    """Search using Lovdata API."""
    client = LovdataClient()
    try:
        results = await client.search(query, limit=limit)
        
        # Format for LLM consumption
        # Note: we need to handle different possible return structures from Lovdata
        items = results.get("results") or results.get("items") or []
        
        if not items:
            return f"Ingen lovdata-treff funnet for '{query}'."
        
        formatted = []
        for idx, item in enumerate(items[:limit], 1):
            title = item.get("title") or item.get("name") or "Uten tittel"
            summary = item.get("summary") or item.get("snippet") or "Ingen beskrivelse."
            doc_id = item.get("id", "ukjent")
            url = item.get("url") or f"https://lovdata.no/dokument/{doc_id}"
            
            formatted.append(f"**[{idx}] {title}**\n{summary}\nLenke: {url}\n")
        
        header = f"Fant {len(items)} treff i Lovdata for '{query}':\n\n"
        return header + "\n".join(formatted)
        
    except Exception as e:
        return f"Feil ved søk i Lovdata: {str(e)}"


# ============================================================================
# FINANS MCP TOOLS - Financial Analytics, Cost Management, CRUD Operations
# ============================================================================

@mcp_handler.register_tool(
    name="finans_get_property_costs",
    description="Hent detaljert kostnadsanalyse for en eiendom. Returnerer totale kostnader, fordelt på kategori og leverandør.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string", "description": "UUID til eiendommen"},
            "year": {"type": "string", "description": "År (f.eks. '2024') eller 'all' for alle år", "default": "all"}
        },
        "required": ["property_id"]
    }
)
async def finans_get_property_costs_tool(property_id: str, year: str = "all"):
    """Get detailed cost breakdown for a property."""
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            stmt = select(Property).where(Property.property_id == uuid_obj)
            result = await db.execute(stmt)
            prop = result.scalar_one_or_none()

            if not prop:
                return {"error": f"Eiendom {property_id} ikke funnet"}

            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])

            # Filter by year if specified
            if year != "all":
                expenses = [e for e in expenses if year in str(e.get('date', ''))]

            # Aggregate by category and provider
            by_category = {}
            by_provider = {}
            total = 0.0

            for exp in expenses:
                amount = float(exp.get('amount', 0) or exp.get('amount_parsed', 0) or 0)
                total += amount

                cat = exp.get('type', 'Ukjent')
                by_category[cat] = by_category.get(cat, 0) + amount

                prov = exp.get('provider', 'Ukjent')
                by_provider[prov] = by_provider.get(prov, 0) + amount

            # Add CSV spend if available
            csv_spend = financials.get('total_spend_csv', 0) or 0

            return {
                "property_id": property_id,
                "property_name": prop.name,
                "address": prop.address,
                "year": year,
                "total_manual_expenses": total,
                "total_csv_spend": csv_spend,
                "total_costs": total + csv_spend,
                "cost_by_category": by_category,
                "cost_by_provider": by_provider,
                "expense_count": len(expenses),
                "currency": "NOK"
            }
        except ValueError:
            return {"error": "Ugyldig property_id format"}
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_get_regional_costs",
    description="Hent aggregerte kostnader per region. Returnerer totaler, gjennomsnitt og antall eiendommer.",
    parameters={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "Filtrer til spesifikk region (valgfritt)"}
        },
        "required": []
    }
)
async def finans_get_regional_costs_tool(region: str = None):
    """Get aggregated costs by region."""
    async with get_session() as db:
        try:
            query = select(Property)
            if region:
                query = query.where(Property.region.ilike(f"%{region}%"))

            result = await db.execute(query)
            properties = result.scalars().all()

            regional_data = {}

            for prop in properties:
                reg = get_operational_region(prop.region or "Sør")
                if reg not in regional_data:
                    regional_data[reg] = {
                        "total_costs": 0,
                        "property_count": 0,
                        "properties": []
                    }

                ext = prop.external_data or {}
                financials = ext.get('financials', {})
                manual = financials.get('total_manual_expenses', 0) or 0
                csv = financials.get('total_spend_csv', 0) or 0
                total = manual + csv

                regional_data[reg]["total_costs"] += total
                regional_data[reg]["property_count"] += 1
                if total > 0:
                    regional_data[reg]["properties"].append({
                        "name": prop.name,
                        "address": prop.address,
                        "costs": total
                    })

            # Calculate averages
            for reg in regional_data:
                count = regional_data[reg]["property_count"]
                if count > 0:
                    regional_data[reg]["average_cost"] = regional_data[reg]["total_costs"] / count
                # Keep only top 5 properties by cost
                regional_data[reg]["properties"] = sorted(
                    regional_data[reg]["properties"],
                    key=lambda x: x["costs"],
                    reverse=True
                )[:5]

            return {
                "regions": regional_data,
                "total_properties": len(properties),
                "currency": "NOK"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_get_rent_income",
    description="Hent leieinntekter for en eiendom. Inkluderer alle aktive kontrakter og tilleggskostnader.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string", "description": "UUID til eiendommen"}
        },
        "required": ["property_id"]
    }
)
async def finans_get_rent_income_tool(property_id: str):
    """Get rent income for a property including all active contracts."""
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)

            # Get property
            prop_res = await db.execute(select(Property).where(Property.property_id == uuid_obj))
            prop = prop_res.scalar_one_or_none()
            if not prop:
                return {"error": f"Eiendom {property_id} ikke funnet"}

            # Get units for this property
            unit_res = await db.execute(select(Unit).where(Unit.property_id == uuid_obj))
            units = unit_res.scalars().all()

            if not units:
                return {
                    "property_id": property_id,
                    "property_name": prop.name,
                    "total_rent_income": 0,
                    "contracts": [],
                    "message": "Ingen enheter funnet for denne eiendommen"
                }

            # Get contracts for these units
            unit_ids = [u.unit_id for u in units]
            contract_res = await db.execute(
                select(Contract).where(
                    Contract.unit_id.in_(unit_ids),
                    Contract.status == "active"
                )
            )
            contracts = contract_res.scalars().all()

            total_rent = 0.0
            total_ancillary = 0.0
            contract_list = []

            for c in contracts:
                # Extract rent from amount JSONB
                amount_data = c.amount or {}
                monthly = amount_data.get('monthly_rent', 0) or amount_data.get('monthly', 0) or 0
                yearly = amount_data.get('amount_per_year', 0) or amount_data.get('total_per_year', 0) or 0

                if yearly > 0:
                    total_rent += yearly
                elif monthly > 0:
                    total_rent += monthly * 12

                # Add ancillary costs
                ancillary = (c.caretaker_cost or 0) + (c.cleaning_cost or 0) + (c.parking_cost or 0) + (c.card_reader_cost or 0)
                total_ancillary += ancillary

                contract_list.append({
                    "contract_id": str(c.contract_id),
                    "monthly_rent": monthly,
                    "yearly_rent": yearly if yearly > 0 else monthly * 12,
                    "caretaker_cost": c.caretaker_cost,
                    "cleaning_cost": c.cleaning_cost,
                    "parking_cost": c.parking_cost,
                    "status": c.status
                })

            return {
                "property_id": property_id,
                "property_name": prop.name,
                "address": prop.address,
                "total_rent_income": total_rent,
                "total_ancillary_income": total_ancillary,
                "total_income": total_rent + total_ancillary,
                "contract_count": len(contracts),
                "contracts": contract_list,
                "currency": "NOK"
            }
        except ValueError:
            return {"error": "Ugyldig property_id format"}
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_get_rent_cost_ratio",
    description="Beregn driftsresultat (NOI) og leie/kostnad-forhold for eiendom eller region.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string", "description": "UUID til eiendommen (valgfritt)"},
            "region": {"type": "string", "description": "Filtrer til region (valgfritt)"}
        },
        "required": []
    }
)
async def finans_get_rent_cost_ratio_tool(property_id: str = None, region: str = None):
    """Calculate NOI and rent/cost ratio for property or region."""
    async with get_session() as db:
        try:
            query = select(Property)
            if property_id:
                query = query.where(Property.property_id == UUID(property_id))
            elif region:
                query = query.where(Property.region.ilike(f"%{region}%"))

            result = await db.execute(query)
            properties = result.scalars().all()

            if not properties:
                return {"error": "Ingen eiendommer funnet"}

            total_income = 0.0
            total_costs = 0.0
            property_results = []

            for prop in properties:
                # Get costs
                ext = prop.external_data or {}
                financials = ext.get('financials', {})
                costs = (financials.get('total_manual_expenses', 0) or 0) + (financials.get('total_spend_csv', 0) or 0)

                # Get income (simplified - sum from contracts)
                unit_res = await db.execute(select(Unit).where(Unit.property_id == prop.property_id))
                units = unit_res.scalars().all()

                income = 0.0
                if units:
                    unit_ids = [u.unit_id for u in units]
                    contract_res = await db.execute(
                        select(Contract).where(Contract.unit_id.in_(unit_ids), Contract.status == "active")
                    )
                    for c in contract_res.scalars().all():
                        amount_data = c.amount or {}
                        yearly = amount_data.get('amount_per_year', 0) or 0
                        monthly = amount_data.get('monthly_rent', 0) or 0
                        income += yearly if yearly > 0 else monthly * 12

                noi = income - costs
                ratio = (income / costs * 100) if costs > 0 else 0

                total_income += income
                total_costs += costs

                if property_id or len(properties) <= 10:
                    property_results.append({
                        "property_id": str(prop.property_id),
                        "name": prop.name,
                        "income": income,
                        "costs": costs,
                        "noi": noi,
                        "rent_cost_ratio_percent": round(ratio, 1)
                    })

            total_noi = total_income - total_costs
            total_ratio = (total_income / total_costs * 100) if total_costs > 0 else 0

            return {
                "summary": {
                    "total_income": total_income,
                    "total_costs": total_costs,
                    "total_noi": total_noi,
                    "overall_rent_cost_ratio_percent": round(total_ratio, 1),
                    "property_count": len(properties)
                },
                "properties": property_results if property_results else "Bruk property_id for detaljert visning",
                "currency": "NOK"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_get_portfolio_summary",
    description="Hent finansiell oversikt for hele porteføljen. Totale inntekter, kostnader og netto.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def finans_get_portfolio_summary_tool():
    """Get portfolio-level financial summary."""
    async with get_session() as db:
        try:
            # Get all properties
            result = await db.execute(select(Property))
            properties = result.scalars().all()

            total_costs = 0.0
            total_income = 0.0
            by_region = {}
            top_cost_properties = []
            top_income_properties = []

            for prop in properties:
                # Costs
                ext = prop.external_data or {}
                financials = ext.get('financials', {})
                costs = (financials.get('total_manual_expenses', 0) or 0) + (financials.get('total_spend_csv', 0) or 0)
                total_costs += costs

                # Income from contracts
                unit_res = await db.execute(select(Unit).where(Unit.property_id == prop.property_id))
                units = unit_res.scalars().all()

                income = 0.0
                if units:
                    unit_ids = [u.unit_id for u in units]
                    contract_res = await db.execute(
                        select(Contract).where(Contract.unit_id.in_(unit_ids), Contract.status == "active")
                    )
                    for c in contract_res.scalars().all():
                        amount_data = c.amount or {}
                        yearly = amount_data.get('amount_per_year', 0) or 0
                        monthly = amount_data.get('monthly_rent', 0) or 0
                        income += yearly if yearly > 0 else monthly * 12

                total_income += income

                # Track by region
                reg = get_operational_region(prop.region or "Sør")
                if reg not in by_region:
                    by_region[reg] = {"income": 0, "costs": 0, "count": 0}
                by_region[reg]["income"] += income
                by_region[reg]["costs"] += costs
                by_region[reg]["count"] += 1

                # Track top properties
                if costs > 0:
                    top_cost_properties.append({"name": prop.name, "costs": costs})
                if income > 0:
                    top_income_properties.append({"name": prop.name, "income": income})

            # Sort and limit top lists
            top_cost_properties = sorted(top_cost_properties, key=lambda x: x["costs"], reverse=True)[:5]
            top_income_properties = sorted(top_income_properties, key=lambda x: x["income"], reverse=True)[:5]

            return {
                "portfolio_totals": {
                    "total_income": total_income,
                    "total_costs": total_costs,
                    "net_operating_income": total_income - total_costs,
                    "property_count": len(properties)
                },
                "by_region": by_region,
                "top_5_by_costs": top_cost_properties,
                "top_5_by_income": top_income_properties,
                "currency": "NOK"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_get_expiring_contracts",
    description="Finn kontrakter som utløper snart. Viser finansiell påvirkning.",
    parameters={
        "type": "object",
        "properties": {
            "days_ahead": {"type": "integer", "description": "Antall dager frem i tid (standard: 90)", "default": 90}
        },
        "required": []
    }
)
async def finans_get_expiring_contracts_tool(days_ahead: int = 90):
    """Find contracts expiring soon with financial impact."""
    from datetime import datetime, timedelta

    async with get_session() as db:
        try:
            cutoff_date = datetime.now() + timedelta(days=days_ahead)

            # Query contracts with end_date within range
            stmt = select(Contract, Unit).join(Unit, Contract.unit_id == Unit.unit_id).where(
                Contract.end_date != None,
                Contract.end_date <= cutoff_date,
                Contract.end_date >= datetime.now(),
                Contract.status == "active"
            ).order_by(Contract.end_date)

            result = await db.execute(stmt)
            rows = result.all()

            if not rows:
                return {
                    "message": f"Ingen kontrakter utløper de neste {days_ahead} dagene",
                    "contracts": []
                }

            total_at_risk = 0.0
            contracts = []

            for contract, unit in rows:
                amount_data = contract.amount or {}
                yearly = amount_data.get('amount_per_year', 0) or 0
                monthly = amount_data.get('monthly_rent', 0) or 0
                rent = yearly if yearly > 0 else monthly * 12
                total_at_risk += rent

                # Get property info
                prop_res = await db.execute(select(Property).where(Property.property_id == unit.property_id))
                prop = prop_res.scalar_one_or_none()

                contracts.append({
                    "contract_id": str(contract.contract_id),
                    "property": prop.name if prop else "Ukjent",
                    "address": prop.address if prop else "Ukjent",
                    "end_date": str(contract.end_date),
                    "days_until_expiry": (contract.end_date - datetime.now().date()).days if hasattr(contract.end_date, 'days') else (contract.end_date.date() - datetime.now().date()).days,
                    "yearly_rent": rent
                })

            return {
                "days_ahead": days_ahead,
                "expiring_count": len(contracts),
                "total_income_at_risk": total_at_risk,
                "contracts": contracts,
                "currency": "NOK"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_compare_costs",
    description="Sammenlign kostnader på tvers av eiendommer. Velg spesifikke eiendommer for sammenligning.",
    parameters={
        "type": "object",
        "properties": {
            "property_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Liste med property_id-er å sammenligne"
            }
        },
        "required": ["property_ids"]
    }
)
async def finans_compare_costs_tool(property_ids: list):
    """Compare costs across specific properties."""
    async with get_session() as db:
        try:
            if not property_ids or len(property_ids) < 2:
                return {"error": "Oppgi minst 2 property_id-er for sammenligning"}

            comparisons = []

            for pid in property_ids:
                try:
                    uuid_obj = UUID(pid)
                    stmt = select(Property).where(Property.property_id == uuid_obj)
                    result = await db.execute(stmt)
                    prop = result.scalar_one_or_none()

                    if not prop:
                        comparisons.append({"property_id": pid, "error": "Ikke funnet"})
                        continue

                    ext = prop.external_data or {}
                    financials = ext.get('financials', {})
                    manual = financials.get('total_manual_expenses', 0) or 0
                    csv = financials.get('total_spend_csv', 0) or 0
                    total = manual + csv

                    # Get area for per-m2 calculation
                    area = prop.total_area or 0

                    comparisons.append({
                        "property_id": pid,
                        "name": prop.name,
                        "address": prop.address,
                        "region": prop.region,
                        "total_costs": total,
                        "area_m2": area,
                        "cost_per_m2": round(total / area, 2) if area > 0 else 0
                    })
                except ValueError:
                    comparisons.append({"property_id": pid, "error": "Ugyldig UUID"})

            # Sort by total costs
            valid = [c for c in comparisons if "error" not in c]
            valid_sorted = sorted(valid, key=lambda x: x["total_costs"], reverse=True)

            # Calculate stats
            costs = [c["total_costs"] for c in valid]
            avg_cost = sum(costs) / len(costs) if costs else 0
            min_cost = min(costs) if costs else 0
            max_cost = max(costs) if costs else 0

            return {
                "comparison": valid_sorted,
                "errors": [c for c in comparisons if "error" in c],
                "statistics": {
                    "average_cost": round(avg_cost, 2),
                    "min_cost": min_cost,
                    "max_cost": max_cost,
                    "spread": max_cost - min_cost
                },
                "currency": "NOK"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_find_cost_anomalies",
    description="Finn eiendommer med uvanlig høye kostnader sammenlignet med regionalt gjennomsnitt.",
    parameters={
        "type": "object",
        "properties": {
            "threshold_percent": {
                "type": "number",
                "description": "Prosentvis terskel over gjennomsnitt (standard: 50)",
                "default": 50
            }
        },
        "required": []
    }
)
async def finans_find_cost_anomalies_tool(threshold_percent: float = 50):
    """Find properties with unusually high costs compared to regional average."""
    async with get_session() as db:
        try:
            # Get all properties
            result = await db.execute(select(Property))
            properties = result.scalars().all()

            # Group by region and calculate averages
            regional_stats = {}
            property_costs = []

            for prop in properties:
                ext = prop.external_data or {}
                financials = ext.get('financials', {})
                costs = (financials.get('total_manual_expenses', 0) or 0) + (financials.get('total_spend_csv', 0) or 0)

                reg = get_operational_region(prop.region or "Sør")
                if reg not in regional_stats:
                    regional_stats[reg] = {"total": 0, "count": 0}
                regional_stats[reg]["total"] += costs
                regional_stats[reg]["count"] += 1

                property_costs.append({
                    "property_id": str(prop.property_id),
                    "name": prop.name,
                    "address": prop.address,
                    "region": reg,
                    "costs": costs
                })

            # Calculate regional averages
            for reg in regional_stats:
                count = regional_stats[reg]["count"]
                regional_stats[reg]["average"] = regional_stats[reg]["total"] / count if count > 0 else 0

            # Find anomalies
            anomalies = []
            for pc in property_costs:
                reg_avg = regional_stats[pc["region"]]["average"]
                if reg_avg > 0:
                    deviation_percent = ((pc["costs"] - reg_avg) / reg_avg) * 100
                    if deviation_percent >= threshold_percent:
                        anomalies.append({
                            **pc,
                            "regional_average": round(reg_avg, 2),
                            "deviation_percent": round(deviation_percent, 1)
                        })

            # Sort by deviation
            anomalies = sorted(anomalies, key=lambda x: x["deviation_percent"], reverse=True)

            return {
                "threshold_percent": threshold_percent,
                "anomaly_count": len(anomalies),
                "anomalies": anomalies[:20],  # Limit to top 20
                "regional_averages": {k: round(v["average"], 2) for k, v in regional_stats.items()},
                "currency": "NOK"
            }
        except Exception as e:
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_get_kpis",
    description="Hent finansielle nøkkeltall (KPI-er) for porteføljen.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def finans_get_kpis_tool():
    """Get key financial performance indicators."""
    async with get_session() as db:
        try:
            # Get all properties
            prop_result = await db.execute(select(Property))
            properties = prop_result.scalars().all()

            # Get all active contracts
            contract_result = await db.execute(
                select(Contract).where(Contract.status == "active")
            )
            contracts = contract_result.scalars().all()

            # Calculate metrics
            total_properties = len(properties)
            total_contracts = len(contracts)

            total_area = sum(p.total_area or 0 for p in properties)
            total_costs = 0.0
            total_income = 0.0

            properties_with_costs = 0

            for prop in properties:
                ext = prop.external_data or {}
                financials = ext.get('financials', {})
                costs = (financials.get('total_manual_expenses', 0) or 0) + (financials.get('total_spend_csv', 0) or 0)
                total_costs += costs
                if costs > 0:
                    properties_with_costs += 1

            for c in contracts:
                amount_data = c.amount or {}
                yearly = amount_data.get('amount_per_year', 0) or 0
                monthly = amount_data.get('monthly_rent', 0) or 0
                income = yearly if yearly > 0 else monthly * 12
                total_income += income

            # Calculate KPIs
            noi = total_income - total_costs
            noi_margin = (noi / total_income * 100) if total_income > 0 else 0
            cost_per_m2 = total_costs / total_area if total_area > 0 else 0
            income_per_m2 = total_income / total_area if total_area > 0 else 0
            occupancy_rate = (total_contracts / total_properties * 100) if total_properties > 0 else 0

            return {
                "kpis": {
                    "net_operating_income": round(noi, 2),
                    "noi_margin_percent": round(noi_margin, 1),
                    "cost_per_m2": round(cost_per_m2, 2),
                    "income_per_m2": round(income_per_m2, 2),
                    "occupancy_rate_percent": round(occupancy_rate, 1)
                },
                "portfolio_stats": {
                    "total_properties": total_properties,
                    "total_contracts": total_contracts,
                    "total_area_m2": total_area,
                    "total_income": total_income,
                    "total_costs": total_costs,
                    "properties_with_costs": properties_with_costs
                },
                "currency": "NOK"
            }
        except Exception as e:
            return {"error": str(e)}


# ============================================================================
# FINANS CRUD TOOLS - Add, Update, Delete Expenses
# ============================================================================

@mcp_handler.register_tool(
    name="finans_add_expense",
    description="Legg til en manuell kostnad/utgift på en eiendom.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string", "description": "UUID til eiendommen"},
            "type": {"type": "string", "description": "Kostnadskategori (f.eks. Vedlikehold, Renhold, Drift)"},
            "amount": {"type": "number", "description": "Beløp i NOK"},
            "provider": {"type": "string", "description": "Leverandørnavn (valgfritt)"},
            "date": {"type": "string", "description": "Dato (f.eks. '2024-Q1' eller '2024-01-15')"},
            "description": {"type": "string", "description": "Beskrivelse (valgfritt)"}
        },
        "required": ["property_id", "type", "amount"]
    }
)
async def finans_add_expense_tool(
    property_id: str,
    type: str,
    amount: float,
    provider: str = None,
    date: str = None,
    description: str = None
):
    """Add a manual expense to a property."""
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            stmt = select(Property).where(Property.property_id == uuid_obj)
            result = await db.execute(stmt)
            prop = result.scalar_one_or_none()

            if not prop:
                return {"error": f"Eiendom {property_id} ikke funnet"}

            # Get or initialize external_data
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])

            # Create new expense entry
            from datetime import datetime as dt
            new_expense = {
                "type": type,
                "amount": amount,
                "amount_parsed": amount,
                "provider": provider or "Ukjent",
                "date": date or dt.now().strftime("%Y-%m-%d"),
                "description": description or "",
                "source": "mcp_tool",
                "created_at": dt.now().isoformat()
            }

            expenses.append(new_expense)

            # Update totals
            total = sum(float(e.get('amount', 0) or 0) for e in expenses)
            financials['manual_expenses'] = expenses
            financials['total_manual_expenses'] = total

            ext['financials'] = financials
            prop.external_data = ext

            await db.commit()

            return {
                "status": "success",
                "message": f"Kostnad på {amount} NOK lagt til for {prop.name}",
                "expense_index": len(expenses) - 1,
                "new_total": total,
                "currency": "NOK"
            }
        except ValueError:
            return {"error": "Ugyldig property_id format"}
        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_update_expense",
    description="Oppdater en eksisterende kostnad/utgift.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string", "description": "UUID til eiendommen"},
            "expense_index": {"type": "integer", "description": "Indeks til kostnaden i listen (0-basert)"},
            "type": {"type": "string", "description": "Ny kategori (valgfritt)"},
            "amount": {"type": "number", "description": "Nytt beløp (valgfritt)"},
            "provider": {"type": "string", "description": "Ny leverandør (valgfritt)"},
            "date": {"type": "string", "description": "Ny dato (valgfritt)"},
            "description": {"type": "string", "description": "Ny beskrivelse (valgfritt)"}
        },
        "required": ["property_id", "expense_index"]
    }
)
async def finans_update_expense_tool(
    property_id: str,
    expense_index: int,
    type: str = None,
    amount: float = None,
    provider: str = None,
    date: str = None,
    description: str = None
):
    """Update an existing expense."""
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            stmt = select(Property).where(Property.property_id == uuid_obj)
            result = await db.execute(stmt)
            prop = result.scalar_one_or_none()

            if not prop:
                return {"error": f"Eiendom {property_id} ikke funnet"}

            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])

            if expense_index < 0 or expense_index >= len(expenses):
                return {"error": f"Ugyldig expense_index: {expense_index}. Gyldige verdier: 0-{len(expenses)-1}"}

            # Update fields if provided
            expense = expenses[expense_index]
            if type is not None:
                expense['type'] = type
            if amount is not None:
                expense['amount'] = amount
                expense['amount_parsed'] = amount
            if provider is not None:
                expense['provider'] = provider
            if date is not None:
                expense['date'] = date
            if description is not None:
                expense['description'] = description

            from datetime import datetime as dt
            expense['updated_at'] = dt.now().isoformat()

            expenses[expense_index] = expense

            # Recalculate total
            total = sum(float(e.get('amount', 0) or 0) for e in expenses)
            financials['manual_expenses'] = expenses
            financials['total_manual_expenses'] = total

            ext['financials'] = financials
            prop.external_data = ext

            await db.commit()

            return {
                "status": "success",
                "message": f"Kostnad oppdatert for {prop.name}",
                "updated_expense": expense,
                "new_total": total,
                "currency": "NOK"
            }
        except ValueError:
            return {"error": "Ugyldig property_id format"}
        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


@mcp_handler.register_tool(
    name="finans_delete_expense",
    description="Slett en kostnad/utgift fra en eiendom.",
    parameters={
        "type": "object",
        "properties": {
            "property_id": {"type": "string", "description": "UUID til eiendommen"},
            "expense_index": {"type": "integer", "description": "Indeks til kostnaden som skal slettes (0-basert)"}
        },
        "required": ["property_id", "expense_index"]
    }
)
async def finans_delete_expense_tool(property_id: str, expense_index: int):
    """Delete an expense from a property."""
    async with get_session() as db:
        try:
            uuid_obj = UUID(property_id)
            stmt = select(Property).where(Property.property_id == uuid_obj)
            result = await db.execute(stmt)
            prop = result.scalar_one_or_none()

            if not prop:
                return {"error": f"Eiendom {property_id} ikke funnet"}

            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])

            if expense_index < 0 or expense_index >= len(expenses):
                return {"error": f"Ugyldig expense_index: {expense_index}. Gyldige verdier: 0-{len(expenses)-1}"}

            # Remove the expense
            deleted = expenses.pop(expense_index)

            # Recalculate total
            total = sum(float(e.get('amount', 0) or 0) for e in expenses)
            financials['manual_expenses'] = expenses
            financials['total_manual_expenses'] = total

            ext['financials'] = financials
            prop.external_data = ext

            await db.commit()

            return {
                "status": "success",
                "message": f"Kostnad slettet fra {prop.name}",
                "deleted_expense": deleted,
                "new_total": total,
                "remaining_expenses": len(expenses),
                "currency": "NOK"
            }
        except ValueError:
            return {"error": "Ugyldig property_id format"}
        except Exception as e:
            await db.rollback()
            return {"error": str(e)}

# ============================================================================
# WEB TOOLS - Search and Content Fetching
# ============================================================================

# User-Agent som ligner nettleser – DuckDuckGo blokkerer ofte forespørsler fra cloud (f.eks. Render) uten dette
_DDGS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def _search_web_sync(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Sync DuckDuckGo text search (no API key). Returns list of {title, href, body}."""
    import time
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        raise ImportError("duckduckgo-search is not installed. Run: pip install duckduckgo-search==8.1.1")

    n = min(max(1, max_results), 10)
    regions_to_try = ["no-no", "wt-wt", "us-en"]  # Norge først, deretter nøytral, deretter USA
    backends_to_try = ["auto", "bing"]  # Bing som fallback hvis DuckDuckGo blokkerer

    for attempt in range(2):  # Maks 2 forsøk
        for region in regions_to_try:
            for backend in backends_to_try:
                try:
                    with DDGS(headers=_DDGS_HEADERS, timeout=15) as ddgs:
                        results = list(
                            ddgs.text(
                                query,
                                region=region,
                                safesearch="moderate",
                                max_results=n,
                                backend=backend,
                            )
                        )
                    out = []
                    for r in results:
                        out.append({
                            "title": r.get("title") or "",
                            "href": r.get("href") or r.get("url") or "",
                            "body": r.get("body") or "",
                        })
                    if out:
                        return out
                except Exception as e:
                    logger.warning(
                        f"search_web (DuckDuckGo) region={region} backend={backend} attempt={attempt + 1}: {e}"
                    )
        if attempt == 0:
            time.sleep(1.5)  # Kort pause før retry
    return []


@mcp_handler.register_tool(
    name="search_web",
    description="Search the web for information. Use this to find real-time info, news, company details, or market data. Uses DuckDuckGo (no API key).",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "max_results": {"type": "integer", "default": 5, "description": "Number of results to return (max 10)"}
        },
        "required": ["query"]
    }
)
async def search_web_tool(query: str, max_results: int = 5):
    import asyncio
    if not (query and str(query).strip()):
        return []
    n = min(max(1, max_results), 10) if max_results else 5
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _search_web_sync, str(query).strip(), n)
    return results

@mcp_handler.register_tool(
    name="fetch_web_content",
    description="Fetch a URL, extract text, and ingest it into the Knowledge Base (RAG) for future retrieval.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The URL to fetch"},
            "ingest": {"type": "boolean", "default": True, "description": "Whether to save to vector DB"}
        },
        "required": ["url"]
    }
)
async def fetch_web_content_tool(url: str, ingest: bool = True):
    import httpx
    # Lazy imports for RAG dependencies
    from app.services.embeddings import generate_embeddings
    from app.models.text_content import TextContent
    from sqlalchemy.sql import func
    import uuid

    try:
        # 1. Fetch HTML
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; BEFS-Updates/1.0)"}
            resp = await client.get(url, headers=headers)
            
            if resp.status_code != 200:
                return f"Error: Failed to fetch URL (Status: {resp.status_code})"
            
            html = resp.text
            
        # 2. Parse and Clean Content
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.string.strip() if soup.title else url
            
            # Remove junk
            for script in soup(["script", "style", "nav", "footer", "iframe", "noscript", "svg"]):
                script.decompose()
            
            # Get structured text
            text_content = soup.get_text(separator="\n\n")
            
            # Simple cleaning
            lines = (line.strip() for line in text_content.splitlines())
            chunks_text = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks_text if chunk)
            
        except ImportError:
            return "Error: beautifulsoup4 not installed."
        except Exception as e:
            return f"Error parsing content: {str(e)}"

        if not ingest:
            # Just return preview if not ingesting
            return f"**{title}**\nSource: {url}\n\n{clean_text[:2000]}..."

        # 3. RAG Ingestion
        try:
            # Basic Chunking (approx 1000 chars overlap)
            # OpenAI limit is 8191 tokens ~ 30k chars, but smaller chunks are better for retrieval
            chunk_size = 2000
            overlap = 200
            
            text_chunks = []
            for i in range(0, len(clean_text), chunk_size - overlap):
                text_chunks.append(clean_text[i:i + chunk_size])
            
            if not text_chunks:
                return "No text found to ingest."

            # Generate Embeddings
            embeddings = generate_embeddings(text_chunks)
            
            async with get_session() as db:
                # Optional: Clear old content from this URL to avoid duplicates
                await db.execute(
                    text("DELETE FROM text_content WHERE source_file = :url"),
                    {"url": url}
                )
                
                # Insert new chunks
                count = 0
                for i, chunk_text in enumerate(text_chunks):
                    # Safety check for embedding failure
                    if i < len(embeddings):
                        emb = embeddings[i]
                        
                        entry = TextContent(
                            text_id=uuid.uuid4(),
                            source_type="web_rag",
                            source_file=url,
                            content=chunk_text,
                            embedding=emb,
                            search_vector=func.to_tsvector('norwegian', chunk_text),
                            category="web_search",
                            chunk_index=i,
                            additional_metadata={
                                "title": title,
                                "url": url,
                                "ingested_at": str(func.now())
                            }
                        )
                        db.add(entry)
                        count += 1
                
                await db.commit()
                
            return f"Successfully ingested {count} chunks from '{title}' ({url}) into Knowledge Base. You can now query this data."
            
        except Exception as e:
            return f"Error during RAG ingestion: {str(e)}"
            
    except Exception as e:
        return f"Error fetching content: {str(e)}"



@mcp_handler.register_tool(
    name="run_analysis_script",
    description="Kjør et forhåndsgodkjent analyseskript for dybdeanalyse av eiendomsdata.",
    parameters={
        "type": "object",
        "properties": {
            "script_key": {"type": "string", "enum": ["audit_contracts", "cost_analyzer_search", "cost_analyzer_anomalies"]},
            "params": {"type": "object"}
        },
        "required": ["script_key"]
    }
)
async def run_analysis_script_tool(script_key: str, params: dict = None):
    from app.services.mcp.script_executor import execute_analysis_script
    return await execute_analysis_script(script_key, params)


# --- Financial Analysis Tools (ML) ---

@mcp_handler.register_tool(
    name="analyze_property_financials",
    description="Analyze property financials using ML. Provides forecasts (3 years) and detects spending anomalies.",
    parameters={
        "type": "object",
        "properties": {"property_name": {"type": "string"}},
        "required": ["property_name"]
    }
)
async def analyze_property_financials_tool(property_name: str):
    from app.services.analytics.financial_analytics import financial_analytics_service
    
    async with get_session() as db:
        try:
            # 1. Find Property
            stmt = select(Property).where(Property.name.ilike(f"%{property_name}%"))
            result = await db.execute(stmt)
            prop = result.scalar_one_or_none()
            
            if not prop:
                return f"Could not find property matching '{property_name}'."
            
            prop_id = str(prop.property_id)
            
            # 2. Run Analysis
            forecast = await financial_analytics_service.forecast_future_costs(db, prop_id)
            anomalies = await financial_analytics_service.detect_spending_anomalies(db, prop_id)
            
            # 3. Format Output
            summary = [f"📊 **Financial Analysis for {prop.name}**"]
            summary.append("")
            
            # Forecast Section
            if not forecast or "error" in forecast:
                err = forecast.get('error', 'Unknown error') if forecast else 'No data'
                summary.append(f"⚠️ Forecast: {err}")
            else:
                summary.append(f"🔮 **Cost Forecast (Next 3 Years):**")
                summary.append(f"Trend: **{forecast['trend']}** (Annual Change: {forecast['annual_change_estimate']} NOK)")
                summary.append("")
                for f in forecast['forecast']:
                    summary.append(f"- {f['year']}: {f['predicted_cost']:,.0f} NOK")
            
            summary.append("")
            
            # Anomaly Section
            if not anomalies or "error" in anomalies:
                err = anomalies.get('error', 'Unknown error') if anomalies else 'No data'
                summary.append(f"⚠️ Anomalies: {err}")
            else:
                summary.append(f"🚨 **Anomaly Detection:**")
                if anomalies['anomalies']:
                    summary.append(f"Found {len(anomalies['anomalies'])} unusual spending years:")
                    for a in anomalies['anomalies']:
                        summary.append(f"- {a['year']}: {a['amount']:,.0f} NOK ({a['reason']})")
                else:
                    summary.append("✅ No spending anomalies detected.")
            
            return "\n".join(summary)
            
        except ImportError:
            return "ML dependencies (scikit-learn) not installed. Please contact admin."
        except Exception as e:
            # Log error properly in real app
            return f"Error running financial analysis: {str(e)}"

# --- Playwright MCP Server ---
try:
    from app.services.mcp import playwright_server
except ImportError:
    pass # Optional dependency
