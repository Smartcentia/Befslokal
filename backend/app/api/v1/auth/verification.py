"""
Email verification endpoints for new user registration.
"""
import secrets
import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User
from app.domains.core.models.email_verification import EmailVerificationCode
from app.services.email_service import email_service
from app.core.config import settings
from app.core.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()


class SendVerificationCodeRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class VerifyEmailResponse(BaseModel):
    success: bool
    message: str


def hash_code(code: str) -> str:
    """Hash verification code for storage."""
    return hashlib.sha256(code.encode()).hexdigest()


def generate_verification_code() -> str:
    """Generate a random 6-digit verification code."""
    return f"{secrets.randbelow(1000000):06d}"


@router.post("/send-verification-code", status_code=status.HTTP_200_OK)
async def send_verification_code(
    request: SendVerificationCodeRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a 6-digit verification code to the user's email.
    Rate limited: Max 3 codes per email per hour, 10 requests per IP per minute.
    """
    # IP-based rate limit (10/min)
    client_ip = http_request.client.host if http_request.client else "unknown"
    allowed, msg = check_rate_limit(f"send_code:{client_ip}", max_attempts=10, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)

    email = request.email.lower().strip()
    
    # Check if user already exists and is verified
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user and existing_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Rate limiting: Check for recent codes (max 3 per hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_codes_result = await db.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.created_at > one_hour_ago
        )
    )
    recent_codes = recent_codes_result.scalars().all()
    
    if len(recent_codes) >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification codes sent. Please wait before requesting a new one."
        )
    
    # Generate new code
    code = generate_verification_code()
    code_hash = hash_code(code)
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    # Invalidate old unused codes for this email
    await db.execute(
        delete(EmailVerificationCode).where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.used == False
        )
    )
    
    # Create new verification code record
    verification_code = EmailVerificationCode(
        id=str(uuid.uuid4()),
        email=email,
        code_hash=code_hash,
        expires_at=expires_at,
        used=False
    )
    
    db.add(verification_code)
    await db.commit()
    
    # Send email
    email_sent = await email_service.send_verification_code(email, code)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )
    
    return {
        "success": True,
        "message": "Verification code sent to your email"
    }


@router.post("/verify-email", response_model=VerifyEmailResponse, status_code=status.HTTP_200_OK)
async def verify_email(
    request: VerifyEmailRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email address with the provided code.
    Marks user as email_verified=True if successful.
    Rate limited: 10 attempts per IP per minute to prevent brute force.
    """
    # IP-based rate limit (10/min) to prevent brute force of 6-digit code
    client_ip = http_request.client.host if http_request.client else "unknown"
    allowed, msg = check_rate_limit(f"verify_email:{client_ip}", max_attempts=10, window_seconds=60)
    if not allowed:
        logger.warning(
            "EMAIL_VERIFY_RATE_LIMITED | ip=%s",
            client_ip
        )
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=msg)

    email = request.email.lower().strip()
    code = request.code.strip()

    logger.info(
        "EMAIL_VERIFY_ATTEMPTED | email=%s | ip=%s",
        email, client_ip
    )

    if len(code) != 6 or not code.isdigit():
        logger.warning(
            "EMAIL_VERIFY_INVALID_FORMAT | email=%s | ip=%s | code_length=%s",
            email, client_ip, len(code)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code format. Code must be 6 digits."
        )
    
    # Find valid verification code
    # Fetch all unused codes for this email to enable constant-time comparison (timing attack protection)
    result = await db.execute(
        select(EmailVerificationCode).where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.used == False
        )
    )
    all_codes = result.scalars().all()

    # Use constant-time comparison to prevent timing attacks
    code_hash = hash_code(code)
    verification_code = None
    for candidate in all_codes:
        if secrets.compare_digest(candidate.code_hash, code_hash):
            verification_code = candidate
            break

    if not verification_code:
        logger.warning(
            "EMAIL_VERIFY_FAILED | email=%s | ip=%s | reason=code_not_found_or_used",
            email, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )

    if verification_code.is_expired():
        # Mark as used to prevent reuse
        verification_code.used = True
        await db.commit()
        logger.warning(
            "EMAIL_VERIFY_EXPIRED | email=%s | ip=%s | expired_at=%s",
            email, client_ip, verification_code.created_at.isoformat()
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new one."
        )
    
    # Mark code as used
    verification_code.used = True
    await db.commit()

    # Update or create user
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()

    if user:
        # Update existing user
        user.email_verified = True
        await db.commit()
        await db.refresh(user)
        logger.info(
            "EMAIL_VERIFY_SUCCESS | email=%s | ip=%s | user_id=%s",
            email, client_ip, user.id
        )
    else:
        # This shouldn't happen in normal flow, but handle it gracefully
        # User should be created during login attempt
        logger.error(
            "EMAIL_VERIFY_NO_USER | email=%s | ip=%s",
            email, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please try logging in first."
        )

    return VerifyEmailResponse(
        success=True,
        message="Email verified successfully"
    )
