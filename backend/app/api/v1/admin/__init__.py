from fastapi import APIRouter
from .financial_analysis import router as financial_router
from .system import router as system_router
from .api_usage import router as api_usage_router
from .economic_import import router as economic_import_router
from .contracts import router as contracts_router
from .evolution import router as evolution_router
from .agresso_import import router as agresso_router

router = APIRouter()

# Include sub-routers
router.include_router(financial_router)
router.include_router(system_router)
router.include_router(api_usage_router)
router.include_router(economic_import_router)
router.include_router(contracts_router)
router.include_router(evolution_router, prefix="/evolution")
router.include_router(agresso_router)

