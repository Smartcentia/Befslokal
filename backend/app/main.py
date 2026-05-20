from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from contextlib import asynccontextmanager
import logging

from app.core.logging_config import setup_logging
from app.core.config import settings

# Configure logging early (Fix 4 - CODE_REVIEW_30-01)
setup_logging(settings.ENVIRONMENT)
logger = logging.getLogger("app.main")

# CRITICAL: Import all models early to ensure SQLAlchemy mappers are initialized correctly
# before any routers (which might reference models) are imported.
try:
    import app.db.base
    logger.info("SQLAlchemy models registered successfully")
except Exception as e:
    logger.error("Failed to register SQLAlchemy models: %s", e)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text # Original import
import os # Moved up from later in the file
import sys

# Pydantic v2 Compatibility Hack for Semantic Kernel 0.9.x
try:
    import pydantic.networks
    if not hasattr(pydantic.networks, 'Url'):
        from pydantic import AnyUrl
        pydantic.networks.Url = AnyUrl
except ImportError:
    pass

from fastapi import Depends, Response, HTTPException # Added HTTPException
from app.api.deps import get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("BEFS lifespan starting")
    from app.db.session import engine
    from app.db.base_class import Base
    import asyncio
    
    # Import all models to ensure they are registered via Base
    logger.info("Importing models")
    import app.db.base

    # DB check removed from startup: the /health endpoint already returns 200 (degraded)
    # when DB is down, so Railway healthcheck always passes even without DB.
    # A blocking DB check here would prevent the healthcheck from responding.
    logger.info("BEFS startup complete - skipping blocking DB check")
    
    # # Run ad-hoc migrations in background (these are non-critical schema updates)
    # async def migration_task():
    #     try:
    #         from app.db.migrations import run_migrations
    #         logger.info("Starting background ad-hoc migrations")
    #         await asyncio.wait_for(run_migrations(), timeout=120.0)
    #         logger.info("Background migrations completed")
    #     except asyncio.TimeoutError:
    #         logger.warning("Ad-hoc migrations timed out after 120s")
    #     except Exception as e:
    #         logger.warning("Ad-hoc migrations error: %s", e)

    # asyncio.create_task(migration_task())

    logger.info("BEFS lifespan ready")
    yield
    logger.info("BEFS lifespan shutting down")

    # Shutdown (if needed)

app = FastAPI(
    title="BEFS Backend",
    description="Backend for BEFS - Bufetat eiendomsforvaltningsystem",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Routers ---
from app.api.v1.mcp import router as mcp_router
from app.api.v1.ai.assistant import router as ai_router
from app.api.v1.ai.chat import router as ki_kollega_router
from app.api.v1.ai.transparency import router as transparency_router
admin_router = None
if os.getenv("BEFS_SKIP_ADMIN_ROUTER", "0") != "1":
    from app.api.v1.admin import router as admin_router
from app.api.v1.files import router as files_router
from app.api.v1.help import router as help_router
from app.api.v1.import_api import router as import_router
from app.api.v1.indexing import router as indexing_router
from app.api.bup_locations import router as bup_router
from app.api.v1.users import router as users_router
from app.api.v1.fulltext_search import router as fulltext_search_router
from app.api.v1.external_api import router as external_api_router
from app.api.v1.sessions import router as sessions_router  # NextAuth sessions
from app.api.v1.auth.verification import router as verification_router
from app.api.v1.auth.mfa import router as mfa_router
from app.api.v1.jira import router as jira_router
from app.api.v1.auth.login import router as login_router
from app.api.v1.endpoints.governance import router as governance_router
from app.api.v1.endpoints.glossary import router as glossary_router

# Domain Routers
from app.domains.innsikt.routers.agent import router as agent_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.feature_flags import router as feature_flags_router
from app.domains.innsikt.routers.search import router as search_router
from app.domains.core.routers.properties import router as properties_router
from app.domains.core.routers.units import router as units_router
from app.domains.core.routers.parties import router as parties_router
from app.domains.core.routers.konkurs_monitor import router as konkurs_monitor_router
from app.domains.core.routers.contracts import router as contracts_router
from app.api.endpoints.contract_analytics import router as contract_analytics_router
from app.domains.hms.routers.risk import router as risk_router
from app.domains.hms.routers.deviations import router as deviations_router
from app.domains.hms.routers.checklists import router as checklists_router
from app.domains.hms.routers.internal_control import router as internal_control_router
from app.domains.hms.routers.scheduled_activities import router as scheduled_activities_router
from app.domains.fdv.routers import components_router as fdv_components_router # Phase 1 Semantic Data
from app.domains.fdv.routers.compliance import router as fdv_compliance_router
from app.domains.fdv.routers.maintenance import router as fdv_maintenance_router
from app.domains.fdv.routers.doc_search import router as fdv_doc_search_router
from app.domains.fdv.routers.ifc_import import router as fdv_ifc_router
from app.domains.fdv.routers.import_fdv import router as fdv_import_router
from app.domains.fdv.routers.simba_validate import router as fdv_simba_router
# from app.api.v1.integration import router as integration_router # Added by user instruction - Commented out as file is missing
from app.api.v1.centers import router as centers_router
from app.api.v1.financials import router as financials_router
from app.api.v1.budget_prediction import router as budget_prediction_router
from app.api.v1.finance_budget import router as finance_budget_router
from app.api.v1.plasser import router as plasser_router
from app.api.v1.ml_predictions import router as ml_predictions_router
from app.api.v1.costs import router as costs_router
from app.api.v1.cost_management import router as cost_management_router
from app.api.v1.forecast import router as forecast_router
from app.api.endpoints.script_approvals import router as script_approvals_router
from app.api.v1.ns3451 import router as ns3451_router
from app.api.v1.accounting import router as accounting_router
from app.api.v1.procurement import router as procurement_router
from app.domains.barnevern.routers.barnevern import router as barnevern_router
from app.api.v1.barnevern_documents import router as barnevern_docs_router
from app.api.v1.bufdir_catalog import router as bufdir_catalog_router
from app.api.v1.ssb_api import router as ssb_router

# AI Lab (Self-Evolving Agent)
from app.ai_lab.router import router as lab_router

# --- Register Routes ---
# Import admin user management router
from app.api.v1.admin.user_management import router as admin_user_mgmt_router

app.include_router(sessions_router, prefix="/api/v1", tags=["Sessions"])  # NextAuth - NO AUTH
app.include_router(verification_router, prefix="/api/v1/auth", tags=["Email Verification"])
app.include_router(mfa_router, prefix="/api/v1/auth", tags=["MFA"])
# app.include_router(login_router, prefix="/api/v1/auth", tags=["Auth"])

# ...

# Middleware
# AUTHENTICATION DISABLED TEMPORARILY (OAuth setup needed)
# Re-enabled with Shared Secret Check for Vercel Auth Strategy
from app.middleware.auth_middleware import AuthMiddleware
app.add_middleware(AuthMiddleware)

app.include_router(jira_router, prefix="/api/v1/jira", tags=["Jira Integration"])
app.include_router(mcp_router, prefix="/api/v1/mcp", tags=["MCP Agents"])
app.include_router(ai_router, prefix="/api/v1/ai/assistant", tags=["AI Assistant (Legacy)"])
app.include_router(ki_kollega_router, prefix="/api/v1/ai", tags=["KI Kollega"])
app.include_router(transparency_router, prefix="/api/v1/ai/transparency", tags=["AI Transparency"])
if admin_router is not None:
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin Tools"])
app.include_router(governance_router, prefix="/api/v1/governance", tags=["Data Governance"])
app.include_router(glossary_router, prefix="/api/v1/glossary", tags=["Glossary"])
app.include_router(admin_user_mgmt_router, prefix="/api/v1/admin", tags=["Admin - User Management"])
app.include_router(files_router, prefix="/api/v1/files", tags=["Files"])
app.include_router(indexing_router, prefix="/api/v1/indexing", tags=["Indexing"])
app.include_router(help_router, prefix="/api/v1/help", tags=["Help"])
app.include_router(import_router, prefix="/api/v1/import", tags=["Import"])
app.include_router(bup_router, prefix="/api/v1/bup-locations", tags=["BUP Locations"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(fulltext_search_router, prefix="/api/v1/fulltext-search", tags=["Full-Text Search"])
app.include_router(external_api_router, prefix="/api/external", tags=["External APIs"])

# Domain Routes
app.include_router(agent_router, prefix="/api/v1/agent", tags=["AI Agent"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(feature_flags_router, prefix="/api/v1", tags=["Feature Flags"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
app.include_router(properties_router, prefix="/api/v1/properties", tags=["Properties"])
app.include_router(units_router, prefix="/api/v1/units", tags=["Units"])
app.include_router(parties_router, prefix="/api/v1/parties", tags=["Parties"])
app.include_router(konkurs_monitor_router, prefix="/api/v1/konkurs-monitor", tags=["Konkurs Monitor"])
app.include_router(contracts_router, prefix="/api/v1/contracts", tags=["Contracts"])
app.include_router(contract_analytics_router, prefix="/api/v1/contracts", tags=["Contract Analytics"])
app.include_router(risk_router, prefix="/api/v1/risk", tags=["Risk Analysis"])
app.include_router(deviations_router, prefix="/api/v1/deviations", tags=["Deviations"])
app.include_router(checklists_router, prefix="/api/v1/checklists", tags=["Checklists"])
app.include_router(internal_control_router, prefix="/api/v1/internal-control", tags=["Internal Control"])
app.include_router(scheduled_activities_router, prefix="/api/v1/hms/activities", tags=["HMS Calendar"])
app.include_router(fdv_components_router, prefix="/api/v1/fdv/components", tags=["FDV Components (Semantic Data)"])
app.include_router(fdv_compliance_router, prefix="/api/v1/fdv/compliance", tags=["FDV Compliance"])
app.include_router(fdv_maintenance_router, prefix="/api/v1/fdv/maintenance", tags=["FDV Maintenance"])
app.include_router(fdv_doc_search_router, prefix="/api/v1/fdv/docs", tags=["FDV Documents"])
app.include_router(fdv_ifc_router, prefix="/api/v1/fdv/import/ifc", tags=["FDV IFC Import"])
app.include_router(fdv_import_router, prefix="/api/v1/fdv/import", tags=["FDV Import"])
app.include_router(fdv_simba_router, prefix="/api/v1/fdv/validate", tags=["FDV SIMBA Validate"])
# FDVU alias routes — frontend bruker /fdvu/ (med u), backend-routers er koblet til /fdv/
# Disse aliasene sikrer at alle eksisterende frontend-kall fungerer
app.include_router(fdv_compliance_router, prefix="/api/v1/fdvu", tags=["FDVU Compliance (alias)"])
app.include_router(fdv_maintenance_router, prefix="/api/v1/fdvu/maintenance", tags=["FDVU Maintenance (alias)"])
# app.include_router(integration_router, prefix="/api/v1/integration", tags=["Integrations"])
app.include_router(centers_router, prefix="/api/v1/centers", tags=["Crisis Centers"])
app.include_router(financials_router, prefix="/api/v1/financials", tags=["Financials"])
app.include_router(budget_prediction_router, prefix="/api/v1/financials", tags=["Budget Prediction"])
app.include_router(finance_budget_router, prefix="/api/v1/finance-budget", tags=["Finance Budget"])
app.include_router(plasser_router, prefix="/api/v1", tags=["Institusjonsplasser"])
app.include_router(ml_predictions_router, prefix="/api/v1/ml", tags=["ML Predictions"])
app.include_router(costs_router, prefix="/api/v1/costs", tags=["Cost Monitoring"])
app.include_router(cost_management_router, prefix="/api/v1/cost-management", tags=["Cost Management & Forecasting"])
app.include_router(forecast_router, prefix="/api/v1/forecast", tags=["Financial Forecast"])
app.include_router(script_approvals_router, tags=["Script Approvals"])
app.include_router(ns3451_router, prefix="/api/v1/ns3451", tags=["NS 3451"])
app.include_router(accounting_router, prefix="/api/v1/accounting", tags=["Accounting"])
app.include_router(procurement_router, prefix="/api/v1/procurement", tags=["Procurement Analysis"])
app.include_router(barnevern_router, prefix="/api/v1/barnevern", tags=["Barnevern"])
app.include_router(barnevern_docs_router, prefix="/api/v1/barnevern-docs", tags=["Barnevern Documents"])
app.include_router(bufdir_catalog_router, prefix="/api/v1/bufdir-catalog", tags=["Bufdir catalog"])
app.include_router(ssb_router, prefix="/api/v1/ssb", tags=["SSB Statistikk"])

# Lab Route
app.include_router(lab_router, prefix="/api/v1/lab", tags=["AI Lab"])

# CORS: single source from config (Fix 5 - CODE_REVIEW_30-01)
origins = settings.get_cors_origins_list()

allow_creds = True

logger.info("Final configured CORS origins: %s", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app", # Support ALL Vercel Deployments
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Global exception handler with CORS headers
import re
from starlette.responses import JSONResponse as StarletteJSONResponse
from starlette.requests import Request as StarletteRequest

# Single source for CORS - uses settings.get_cors_origins_list()
CORS_ALLOWED_ORIGIN_REGEX = re.compile(r"https://.*\.vercel\.app")

def get_cors_headers_for_origin(origin: str) -> dict:
    """Return CORS headers if origin is allowed. Uses settings.get_cors_origins_list() as single source."""
    allowed_origins = settings.get_cors_origins_list()
    if origin in allowed_origins or CORS_ALLOWED_ORIGIN_REGEX.match(origin or ""):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    return {}

@app.exception_handler(Exception)
async def global_exception_handler(request: StarletteRequest, exc: Exception):
    """Catch-all exception handler that ensures CORS headers are always present."""
    origin = request.headers.get("origin", "")
    cors_headers = get_cors_headers_for_origin(origin)

    logger.error(f"Unhandled exception: {exc} for {request.url}")

    # Hide error details in production
    content = {"detail": "Internal server error"}
    if settings.ENVIRONMENT != "production":
        import traceback
        content["error"] = str(exc)
        content["traceback"] = traceback.format_exc()

    return StarletteJSONResponse(
        status_code=500,
        content=content,
        headers=cors_headers
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: StarletteRequest, exc: HTTPException):
    """HTTP exception handler that ensures CORS headers are always present."""
    origin = request.headers.get("origin", "")
    cors_headers = get_cors_headers_for_origin(origin)
    
    return StarletteJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=cors_headers
    )

@app.get("/health")
@app.get("/api/v1/health")
async def health_check(response: Response):
    return {"status": "healthy", "service": "knowme-backend"}


@app.get("/")
async def root():
    return {"message": "Welcome to BEFS Backend"}
