from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.mcp.handler import mcp_handler
from app.api.v1.mcp.document import router as document_router
from app.api.v1.mcp.fulltext import router as fulltext_router
from app.api.v1.mcp.fdv import router as fdv_router
from app.api.v1.mcp.iot import router as iot_router
from app.api.v1.mcp.bim import router as bim_router
from app.api.v1.mcp.risk import router as risk_router
from app.api.v1.mcp.gdpr import router as gdpr_router
from app.api.v1.mcp.action import router as action_router
from app.api.v1.mcp.memory import router as memory_router
from app.api.v1.mcp.finans import router as finans_router

router = APIRouter()

# Include specific MCP Server routers
router.include_router(document_router, prefix="/document", tags=["MCP Document"])
router.include_router(fulltext_router,prefix="/fulltext", tags=["MCP FullText"])
router.include_router(fdv_router, prefix="/fdv", tags=["MCP FDV"])
router.include_router(iot_router, prefix="/iot", tags=["MCP IoT"])
router.include_router(bim_router, prefix="/bim", tags=["MCP BIM"])
router.include_router(risk_router, prefix="/risk", tags=["MCP Risk"])
router.include_router(gdpr_router, prefix="/gdpr", tags=["MCP GDPR"])
router.include_router(action_router, prefix="/action", tags=["MCP Action"])
router.include_router(memory_router, prefix="/memory", tags=["MCP Memory"])
router.include_router(finans_router, prefix="/finans", tags=["MCP Finans"])

@router.get("/tools")
async def list_tools():
    """
    List all available tools registered with the MCP handler.
    """
    tools = mcp_handler.get_tools()
    return {"tools": [t.dict() for t in tools]}

@router.post("/tools/{tool_name}/call")
async def call_tool(tool_name: str, arguments: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """
    Execute a specific tool.
    """
    try:
        result = await mcp_handler.execute_tool(tool_name, arguments, db=db)
        return {"result": result}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
