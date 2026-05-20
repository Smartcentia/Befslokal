from starlette.types import ASGIApp, Receive, Send, Scope
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.security import security_validator
from app.core.config import settings
from app.services.audit_service import audit_service
import re
import json
import logging

logger = logging.getLogger(__name__)

# CORS: single source from config (Fix 5 - CODE_REVIEW_30-01)
ALLOWED_ORIGIN_REGEX = re.compile(r"https://.*\.vercel\.app")
LOCAL_ORIGIN_REGEX = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$")


def get_cors_headers(origin: str) -> dict:
    """Get CORS headers based on request origin (uses settings.get_cors_origins_list())."""
    allowed = settings.get_cors_origins_list()
    local_ok = settings.ENVIRONMENT in ("local", "development") and LOCAL_ORIGIN_REGEX.match(origin or "")
    if origin in allowed or ALLOWED_ORIGIN_REGEX.match(origin or "") or local_ok:
        return {
            "access-control-allow-origin": origin,
            "access-control-allow-credentials": "true",
            "access-control-allow-methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "access-control-allow-headers": "*",
        }
    return {}


async def send_json_response(send: Send, status_code: int, content: dict, cors_headers: dict):
    """Send a JSON response with CORS headers."""
    body = json.dumps(content).encode("utf-8")
    
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ]
    
    # Add CORS headers
    for key, value in cors_headers.items():
        headers.append((key.encode(), value.encode()))
    
    await send({
        "type": "http.response.start",
        "status": status_code,
        "headers": headers,
    })
    await send({
        "type": "http.response.body",
        "body": body,
    })


class AuthMiddleware:
    """
    Pure ASGI middleware for authentication.
    
    NOTE: This uses pure ASGI instead of BaseHTTPMiddleware to avoid
    "generator didn't stop after athrow()" errors with async dependencies.
    """
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive, send)
        
        # Get origin for CORS headers
        origin = request.headers.get("origin", "")
        cors_headers = get_cors_headers(origin)
        
        # Allow ONLY health checks and auth endpoints (for new user registration) AND OPTIONS requests (CORS preflight)
        # All other endpoints require authentication
        open_paths = [
            "/health",
            "/api/v1/health",
            "/api/v1/auth/validate-credentials",  # Allow login
            "/api/v1/auth/send-verification-code",  # Allow sending verification codes
            "/api/v1/auth/verify-email",  # Allow verifying email
            "/api/v1/auth/verify-mfa",  # Allow MFA verification via link
            # /api/v1/ai/debug removed: requires auth; returns 404 in production
        ]
        
        # Check if path starts with any open path
        is_open = any(request.url.path == path or request.url.path.startswith(path + "/") for path in open_paths)
        
        if request.method == "OPTIONS" or is_open:
            await self.app(scope, receive, send)
            return
        
        # Get authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header:
            await send_json_response(
                send,
                status_code=401,
                content={"detail": "Not authenticated"},
                cors_headers=cors_headers
            )
            return

        # ---------------------------------------------------------
        # SHARED SECRET BYPASS (kun når ALLOW_SHARED_SECRET_BYPASS er True)
        # ---------------------------------------------------------
        # Når SUPABASE_JWT_SECRET er satt, skal nettleseren bruke Supabase access_token – ikke statisk hemmelighet.
        token = auth_header.replace("Bearer ", "").strip()
        SHARED_SECRET_FALLBACK = "befs-super-secret-key-12345"

        if settings.ALLOW_SHARED_SECRET_BYPASS and (
            (settings.SECRET_KEY and token == settings.SECRET_KEY)
            or (token == SHARED_SECRET_FALLBACK)
        ):
            # Inject a "system" user for audit logs
            scope["state"] = scope.get("state", {})
            user = {
                "user_id": "system", 
                "email": "system@befs.no", 
                "role": "ADMIN",
                "mfa_verified": True # System/Frontend is trusted
            }
            scope["state"]["user"] = user
            
            # ALLOW IMPERSONATION with shared secret too
            impersonate_email = request.headers.get("X-Impersonate-Email")
            # Also allow a "soft" identity via X-User-Email for personalization without full impersonation
            user_email = impersonate_email or request.headers.get("X-User-Email") or "system@befs.no"
            
            if user_email != "system@befs.no":
                if impersonate_email:
                    logger.warning("Shared Secret Auth: Impersonating %s", impersonate_email)
                
                # Fetch target user role if possible for realistic context/permissions
                target_role = "PROPERTY_MANAGER"
                if user_email in settings.ADMIN_EMAILS:
                    target_role = "ADMIN"
                else:
                    try:
                        from app.db.session import SessionLocal
                        from app.domains.core.models.user import User
                        from sqlalchemy import select
                        
                        db = SessionLocal()
                        try:
                            stmt = select(User).where(User.email == user_email)
                            result = await db.execute(stmt)
                            db_user = result.scalar_one_or_none()
                            if db_user:
                                target_role = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
                            else:
                                # Auto-create if not exists? No, keep it simple for now, 
                                # but set a reasonable role if they are not in DB yet.
                                pass
                        except Exception as inner_e:
                            logger.warning("DB query for user role failed: %s", inner_e)
                        finally:
                            await db.close()
                    except Exception as e:
                        logger.warning("Could not fetch user role: %s", e)
                
                scope["state"]["user"] = {
                    **user, 
                    "email": user_email, 
                    "role": target_role,
                    "is_impersonating": bool(impersonate_email)
                }
                
            await self.app(scope, receive, send)
            return
        # ---------------------------------------------------------

        try:
            # Token validation logic

            user = await security_validator.verify_token(auth_header)
            scope["state"] = scope.get("state", {})
            scope["state"]["user"] = user

            # MFA Enforcement
            # MFA DISABLED FOR VERCEL AUTH STRATEGY
            # 1. Check if token says MFA is verified (fast path)
            # if not user.get("mfa_verified", False):
            #     # 2. If not verified in token, we must check DB state
            #     # This handles the case where user enabled MFA but hasn't verified yet this session
            #     # or if the token was issued before MFA was enabled (though rare with short lived tokens)
            #     try:
            #         from app.db.session import SessionLocal
            #         from app.domains.core.models.user import User
            #         from sqlalchemy import select
            #         from datetime import datetime, timedelta
            # 
            #         db = SessionLocal()
            #         try:
            #             # Fetch fresh user data including MFA status
            #             stmt = select(User).where(User.email == user.get("email"))
            #             result = await db.execute(stmt)
            #             db_user = result.scalar_one_or_none()
            # 
            #             if db_user and db_user.mfa_enabled:
            #                 # MFA is enabled for this user. Check if they have verified recently.
            #                 # We allow a grace period or session-based verification from DB
            #                 # For now, strict check: must have verified_at timestamp within last 24h
            #                 
            #                 is_verified_recently = False
            #                 if db_user.mfa_verified_at:
            #                     # Check if verification is fresh (e.g. 24 hours)
            #                     if datetime.utcnow() - db_user.mfa_verified_at < timedelta(hours=24):
            #                         is_verified_recently = True
            #                 
            #                 if not is_verified_recently:
            #                     # Return special 403 for frontend to trigger MFA flow
            #                     await send_json_response(
            #                         send,
            #                         status_code=403,
            #                         content={
            #                             "detail": "MFA verification required",
            #                             "code": "MFA_REQUIRED",
            #                             "mfa_required": True
            #                         },
            #                         cors_headers=cors_headers
            #                     )
            #                     return
            #         finally:
            #             await db.close()
            #     except Exception as e:
            #         logger.error(f"MFA check failed: {e}")
            #         # If DB check fails, fail safe? Or allow?
            #         # Fail safe: Block access if we can't verify MFA status
            #         await send_json_response(
            #             send,
            #             status_code=500,
            #             content={"detail": "Internal Server Error during MFA check"},
            #             cors_headers=cors_headers
            #         )
            #         return

            # Impersonation Logic (Admin Only)
            impersonate_email = request.headers.get("X-Impersonate-Email")
            if impersonate_email:
                user_email = user.get("email")
                # Check if current user is an admin
                if user_email not in settings.ADMIN_EMAILS:
                    await send_json_response(
                        send,
                        status_code=403,
                        content={"detail": "Forbidden", "error": "Only admins can impersonate users"},
                        cors_headers=cors_headers
                    )
                    return

                # Audit log impersonation
                try:
                    # Get DB session for audit logging
                    from app.db.session import SessionLocal
                    db = SessionLocal()
                    try:
                        await audit_service.log_event(
                            db=db,
                            action="IMPERSONATION",
                            actor=user_email,
                            entity_type="user",
                            entity_id=impersonate_email,
                            details={
                                "admin_email": user_email,
                                "target_email": impersonate_email,
                                "endpoint": str(request.url.path),
                                "method": request.method,
                                "ip_address": request.client.host if request.client else "unknown"
                            },
                            severity="WARNING"
                        )
                    finally:
                        await db.close()
                except Exception as e:
                    # Don't block request if audit logging fails
                    logger.warning("Failed to log impersonation: %s", e)

                logger.warning("Admin %s impersonating %s", user_email, impersonate_email)
                
                # Fetch target user role if possible for realistic impersonation
                target_role = "PROPERTY_MANAGER"
                if impersonate_email in settings.ADMIN_EMAILS:
                    target_role = "ADMIN"
                else:
                    try:
                        from app.db.session import SessionLocal
                        from app.domains.core.models.user import User
                        from sqlalchemy import select
                        
                        db = SessionLocal()
                        try:
                            stmt = select(User).where(User.email == impersonate_email)
                            result = await db.execute(stmt)
                            db_user = result.scalar_one_or_none()
                            if db_user:
                                target_role = db_user.role.value if hasattr(db_user.role, "value") else str(db_user.role)
                        except Exception as inner_e:
                            logger.warning("DB query for impersonation role failed: %s", inner_e)
                        finally:
                            await db.close()
                    except Exception as e:
                        logger.warning("Could not fetch impersonated user role: %s", e)
                
                # Switch identity for the request
                scope["state"]["user"] = {
                    **user, 
                    "email": impersonate_email, 
                    "role": target_role,
                    "is_impersonating": True
                }

            # Role Simulation Logic (Admin Only)
            simulate_role = request.headers.get("X-Simulate-Role")
            if simulate_role:
                user_email = user.get("email")
                # Check if current user is an admin
                if user_email in settings.ADMIN_EMAILS:
                    logger.info("Admin %s simulating role %s", user_email, simulate_role)
                    # Inject simulated role into user state
                    scope["state"]["user"]["simulated_role"] = simulate_role

        except Exception as e:
            # Return 401 instead of crashing with 500
            # Do not leak JWT/signature details to client (Fix 3 - CODE_REVIEW_30-01)
            content = {"detail": "Invalid authentication credentials"}
            if settings.ENVIRONMENT != "production":
                content["error_type"] = type(e).__name__
            await send_json_response(
                send,
                status_code=401,
                content=content,
                cors_headers=cors_headers
            )
            return

        await self.app(scope, receive, send)
