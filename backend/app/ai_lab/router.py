from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.ai_lab.main_mvp import lab_service

router = APIRouter()

class LabRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class LabResponse(BaseModel):
    status: str
    message: Optional[str] = None
    tool_id: Optional[str] = None
    code: Optional[str] = None
    sandbox_stdout: Optional[str] = None
    error: Optional[str] = None
    logs: List[str] = []

@router.post("/chat", response_model=LabResponse)
async def lab_chat(request: LabRequest):
    """
    Interact with the Self-Evolving AI Lab.
    This endpoint allows creation and usage of generated tools.
    """
    try:
        # Process the request via the Singleton Lab Service
        result = await lab_service.process_request(request.query)
        
        return LabResponse(**result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def lab_status():
    return {"status": "online", "mode": "isolated_lab"}

# --- Tool Marketplace Endpoints ---

class ToolModelResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: str
    created_at: Any
    usage_count: int
    is_public: bool
    is_pinned: bool = False  # Add missing field
    qa_status: Optional[str] = None


@router.get("/tools", response_model=List[ToolModelResponse])
async def list_tools(status: Optional[str] = None):
    """List tools in the Shared Library."""
    tools = await lab_service.list_tools(status=status)
    return tools

@router.post("/tools/{tool_id}/publish")
async def publish_tool(tool_id: str, background_tasks: BackgroundTasks):
    """Promote a tool to VERIFIED status (triggers Auto-QA)."""
    # 1. Start Publication (sets to PENDING/EXPERIMENTAL)
    result = await lab_service.publish_tool(tool_id)
    
    if result["status"] == "error":
         raise HTTPException(status_code=400, detail=result["message"])
    
    # 2. Trigger Auto-QA
    from app.ai_lab.qa_service import qa_agent
    background_tasks.add_task(qa_agent.validate_tool, tool_id)
    
    return {"status": "success", "message": "Tool queued for Quality Assurance."}

@router.get("/tools/search", response_model=List[ToolModelResponse])
async def search_tools(query: str, limit: int = 5):
    """Semantic Search for tools."""
    tools = await lab_service.search_tools(query, limit=limit)
    return tools

class PinRequest(BaseModel):
    is_pinned: bool

@router.post("/tools/{tool_id}/pin")
async def toggle_pin(tool_id: str, request: PinRequest):
    """Pin or Unpin a tool for Dashboard Widgets."""
    result = await lab_service.toggle_pin_tool(tool_id, request.is_pinned)
    if result["status"] == "error":
         raise HTTPException(status_code=400, detail=result["message"])
    return result

class ExecuteRequest(BaseModel):
    input_text: str

@router.post("/tools/{tool_id}/execute")
async def execute_tool_endpoint(tool_id: str, request: ExecuteRequest):
    """Directly execute a verified tool."""
    result = await lab_service.execute_tool(tool_id, request.input_text)
    return result
