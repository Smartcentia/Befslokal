from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, EmailStr
import uuid

from app.api.deps import get_db, get_current_user
from app.domains.core.models.session import Session
from app.domains.core.models.user import User

router = APIRouter()

# Request/Response Models
class SessionCreate(BaseModel):
    user_email: EmailStr
    access_token: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: datetime

class SessionResponse(BaseModel):
    session_id: str
    user_email: str
    expires_at: datetime
    created_at: datetime

class SessionWithTokens(SessionResponse):
    access_token: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None

# Endpoints

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new session for NextAuth.
    Users can only create sessions for themselves.
    """
    # Security: Users can only create sessions for themselves
    if session_data.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot create session for another user")
    
    new_session = Session(
        user_email=session_data.user_email,
        access_token=session_data.access_token,
        id_token=session_data.id_token,
        refresh_token=session_data.refresh_token,
        expires_at=session_data.expires_at,
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return SessionResponse(
        session_id=str(new_session.session_id),
        user_email=new_session.user_email,
        expires_at=new_session.expires_at,
        created_at=new_session.created_at,
    )

@router.get("/sessions/{session_id}", response_model=SessionWithTokens)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get session by ID with tokens.
    Users can only access their own sessions.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    result = await db.execute(
        select(Session).where(Session.session_id == session_uuid)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Security: Users can only access their own sessions
    if session.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot access other user's session")
    
    # Check if expired
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if expires_at < datetime.now(timezone.utc):
        # Delete expired session
        await db.delete(session)
        await db.commit()
        raise HTTPException(status_code=404, detail="Session expired")
    
    return SessionWithTokens(
        session_id=str(session.session_id),
        user_email=session.user_email,
        access_token=session.access_token,
        id_token=session.id_token,
        refresh_token=session.refresh_token,
        expires_at=session.expires_at,
        created_at=session.created_at,
    )

@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update session tokens (e.g., after token refresh).
    Users can only update their own sessions.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    result = await db.execute(
        select(Session).where(Session.session_id == session_uuid)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Security: Users can only update their own sessions
    if session.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot update other user's session")
    
    # Update fields
    session.access_token = session_data.access_token
    session.id_token = session_data.id_token
    session.refresh_token = session_data.refresh_token
    session.expires_at = session_data.expires_at
    
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        session_id=str(session.session_id),
        user_email=session.user_email,
        expires_at=session.expires_at,
        created_at=session.created_at,
    )

@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete session (logout).
    Users can only delete their own sessions.
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    # First check if session exists and belongs to user
    result = await db.execute(
        select(Session).where(Session.session_id == session_uuid)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Security: Users can only delete their own sessions
    if session.user_email != current_user.email:
        raise HTTPException(status_code=403, detail="Forbidden: Cannot delete other user's session")
    
    # Delete the session
    await db.delete(session)
    await db.commit()
    
    return None

@router.delete("/sessions-cleanup", status_code=status.HTTP_200_OK)
async def cleanup_expired_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin endpoint to clean up expired sessions.
    Can be called periodically via cron job.
    """
    result = await db.execute(
        delete(Session).where(Session.expires_at < datetime.now(timezone.utc))
    )
    
    await db.commit()
    
    return {"deleted_count": result.rowcount}
