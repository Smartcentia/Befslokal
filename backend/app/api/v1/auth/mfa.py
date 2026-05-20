"""
MFA (Multi-Factor Authentication) endpoints.
"""
import secrets
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.core.models.mfa_token import MFAToken
from app.services.email_service import email_service
from app.core.config import settings
from app.core.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


class SendMFALinkRequest(BaseModel):
    email: EmailStr


class VerifyMFAResponse(BaseModel):
    success: bool
    message: str


@router.post("/send-mfa-link", status_code=status.HTTP_200_OK)
async def send_mfa_link(
    http_request: Request,
    request: SendMFALinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send MFA verification link to user's email.
    Requires authentication - user must be logged in.
    """
    email = request.email.lower().strip()
    client_ip = http_request.client.host if http_request.client else "unknown"

    # Audit log: MFA link requested
    logger.info(
        "MFA_LINK_REQUESTED | email=%s | ip=%s | user_id=%s",
        email, client_ip, current_user.id
    )

    # Verify that the authenticated user matches the email
    if current_user.email.lower() != email:
        logger.warning(
            "MFA_LINK_FORBIDDEN | email=%s | authenticated_as=%s | ip=%s",
            email, current_user.email, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot send MFA link for another user's email"
        )

    # Check if user has MFA enabled
    if not current_user.mfa_enabled:
        logger.warning(
            "MFA_LINK_DISABLED | email=%s | ip=%s",
            email, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this user"
        )
    
    # Generate cryptographically secure unique token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Invalidate old unused tokens for this user
    await db.execute(
        delete(MFAToken).where(
            MFAToken.user_email == email,
            MFAToken.used == False
        )
    )
    
    # Create new MFA token
    mfa_token = MFAToken(
        token=token,
        user_email=email,
        expires_at=expires_at,
        used=False
    )
    
    db.add(mfa_token)
    await db.commit()
    
    # Get frontend URL from settings
    frontend_url = settings.FRONTEND_URLS[0] if settings.FRONTEND_URLS else "https://knowme-frontend-amber.vercel.app"
    
    # Send email with verification link
    email_sent = await email_service.send_mfa_link(email, token, frontend_url)

    if not email_sent:
        logger.error(
            "MFA_EMAIL_FAILED | email=%s | ip=%s | token_id=%s",
            email, client_ip, token[:8]  # Log only first 8 chars of token for security
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send MFA email. Please try again later."
        )

    logger.info(
        "MFA_EMAIL_SENT | email=%s | ip=%s | token_id=%s | expires_at=%s",
        email, client_ip, token[:8], expires_at.isoformat()
    )

    return {
        "success": True,
        "message": "MFA verification link sent to your email"
    }


@router.get("/verify-mfa/{token}", response_model=VerifyMFAResponse, status_code=status.HTTP_200_OK)
async def verify_mfa(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify MFA token from email link.
    This endpoint is called when user clicks the MFA link in their email.
    Updates user's mfa_verified_at timestamp.
    Rate limited: 10 attempts per IP per minute.
    """
    # IP-based rate limit
    client_ip = request.client.host if request.client else "unknown"
    allowed, msg = check_rate_limit(f"verify_mfa:{client_ip}", max_attempts=10, window_seconds=60)
    if not allowed:
        logger.warning(
            "MFA_VERIFY_RATE_LIMITED | ip=%s | token_id=%s",
            client_ip, token[:8] if token else "empty"
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)

    # Audit log: MFA verification attempted
    logger.info(
        "MFA_VERIFY_ATTEMPTED | ip=%s | token_id=%s",
        client_ip, token[:8] if token else "empty"
    )

    # Find valid MFA token
    result = await db.execute(
        select(MFAToken).where(
            MFAToken.token == token,
            MFAToken.used == False
        )
    )
    mfa_token = result.scalar_one_or_none()

    if not mfa_token:
        logger.warning(
            "MFA_VERIFY_INVALID | ip=%s | token_id=%s | reason=token_not_found_or_used",
            client_ip, token[:8] if token else "empty"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired MFA token"
        )

    if mfa_token.is_expired():
        # Mark as used to prevent reuse
        mfa_token.used = True
        await db.commit()
        logger.warning(
            "MFA_VERIFY_EXPIRED | email=%s | ip=%s | token_id=%s | expired_at=%s",
            mfa_token.user_email, client_ip, token[:8], mfa_token.expires_at.isoformat()
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA token has expired. Please request a new one."
        )
    
    # Mark token as used
    mfa_token.used = True
    
    # Update user's MFA verification timestamp
    user_result = await db.execute(
        select(User).where(User.email == mfa_token.user_email)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.mfa_verified_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    logger.info(
        "MFA_VERIFY_SUCCESS | email=%s | ip=%s | token_id=%s | user_id=%s",
        mfa_token.user_email, client_ip, token[:8], user.id
    )

    return VerifyMFAResponse(
        success=True,
        message="MFA verified successfully"
    )
