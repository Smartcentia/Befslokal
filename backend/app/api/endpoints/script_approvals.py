"""
Script Approval API Endpoints
Admin can view, approve, or reject pending script executions.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.api.deps import get_db
from app.models.pending_script_execution import PendingScriptExecution
from app.services.mcp.script_executor import execute_analysis_script

router = APIRouter(prefix="/api/v1/script-approvals", tags=["Script Approvals"])

class ScriptExecutionRequest(BaseModel):
    script_key: str
    params: dict = None
    reason: str = None

class ApprovalResponse(BaseModel):
    execution_id: str
    approved: bool
    reason: str = None

@router.get("/pending")
async def get_pending_scripts(db: AsyncSession = Depends(get_db)):
    """Get all pending script execution requests."""
    result = await db.execute(
        select(PendingScriptExecution).where(
            PendingScriptExecution.status == "pending"
        ).order_by(PendingScriptExecution.requested_at.desc())
    )
    pending = result.scalars().all()
    
    return [{
        "execution_id": p.execution_id,
        "script_key": p.script_key,
        "params": p.params,
        "requested_by": p.requested_by,
        "requested_at": p.requested_at.isoformat(),
        "reason": p.reason
    } for p in pending]

@router.post("/request")
async def request_script_execution(
    request: ScriptExecutionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Request a script execution (creates pending approval)."""
    execution_id = str(uuid.uuid4())
    
    pending = PendingScriptExecution(
        execution_id=execution_id,
        script_key=request.script_key,
        params=request.params,
        requested_by="ki_kollega",  # TODO: Get from auth context
        reason=request.reason
    )
    
    db.add(pending)
    await db.commit()
    
    return {
        "execution_id": execution_id,
        "status": "pending",
        "message": f"Script '{request.script_key}' awaits admin approval."
    }

@router.post("/approve/{execution_id}")
async def approve_script_execution(
    execution_id: str,
    response: ApprovalResponse,
    db: AsyncSession = Depends(get_db)
):
    """Approve and execute a pending script."""
    # Get pending execution
    result = await db.execute(
        select(PendingScriptExecution).where(
            PendingScriptExecution.execution_id == execution_id
        )
    )
    pending = result.scalar_one_or_none()
    
    if not pending:
        raise HTTPException(status_code=404, detail="Execution request not found")
    
    if pending.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request already {pending.status}")
    
    if response.approved:
        # Execute the script
        try:
            output = await execute_analysis_script(
                pending.script_key,
                pending.params
            )
            
            # Update record
            await db.execute(
                update(PendingScriptExecution)
                .where(PendingScriptExecution.execution_id == execution_id)
                .values(
                    status="executed",
                    approved_by="admin",  # TODO: Get from auth
                    approved_at=datetime.utcnow(),
                    executed_at=datetime.utcnow(),
                    execution_result=output
                )
            )
            await db.commit()
            
            return {
                "execution_id": execution_id,
                "status": "executed",
                "output": output
            }
            
        except Exception as e:
            # Mark as failed
            await db.execute(
                update(PendingScriptExecution)
                .where(PendingScriptExecution.execution_id == execution_id)
                .values(
                    status="failed",
                    execution_result=str(e)
                )
            )
            await db.commit()
            raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
    
    else:
        # Reject
        await db.execute(
            update(PendingScriptExecution)
            .where(PendingScriptExecution.execution_id == execution_id)
            .values(
                status="rejected",
                approved_by="admin",
                approved_at=datetime.utcnow(),
                reason=response.reason
            )
        )
        await db.commit()
        
        return {
            "execution_id": execution_id,
            "status": "rejected",
            "reason": response.reason
        }

@router.get("/history")
async def get_execution_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get script execution history."""
    result = await db.execute(
        select(PendingScriptExecution)
        .order_by(PendingScriptExecution.requested_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    
    return [{
        "execution_id": h.execution_id,
        "script_key": h.script_key,
        "params": h.params,
        "requested_by": h.requested_by,
        "requested_at": h.requested_at.isoformat(),
        "status": h.status,
        "approved_by": h.approved_by,
        "approved_at": h.approved_at.isoformat() if h.approved_at else None,
        "executed_at": h.executed_at.isoformat() if h.executed_at else None,
        "result_preview": h.execution_result[:200] if h.execution_result else None
    } for h in history]
