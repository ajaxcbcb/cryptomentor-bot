"""
Verification Guard Middleware

Blocks unverified users from accessing trading-related endpoints.
Only users with status 'approved' in user_verifications
can access protected routes. Returns 403 for unverified users.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.auth.jwt import decode_token
from app.db.supabase import _client
import logging

logger = logging.getLogger(__name__)
APPROVED_STATUS = "approved"

# Routes that do NOT require exchange verification
# (Always allowed even if user is not verified on Bitunix)
UNPROTECTED_PREFIXES = [
    "/auth/",
    "/user/me",
    "/user/dashboard",
    "/user/verification-status",
    "/user/submit-uid",
    "/dashboard/system",
    "/leaderboard",
    "/docs",
    "/openapi.json",
    # Legacy with /api/ prefix (direct access)
    "/api/auth/",
    "/api/user/me",
    "/api/user/dashboard",
    "/api/user/verification-status",
    "/api/user/submit-uid",
    "/api/leaderboard",
]

UNPROTECTED_EXACT = ["/", "/docs", "/openapi.json"]

# These route prefixes require verification status = 'approved'
PROTECTED_PREFIXES = [
    "/bitunix/",
    "/dashboard/engine/",
    "/dashboard/settings",
    "/dashboard/portfolio",
    "/dashboard/performance",
    "/dashboard/debug",
    "/signals/",
    "/performance/",
    "/engine/",
    # Legacy with /api/ prefix
    "/api/bitunix/",
    "/api/dashboard/",
    "/api/signals/",
    "/api/performance/",
    "/api/engine/",
]


class VerificationGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # If it's a root health check or docs, skip
        if path in UNPROTECTED_EXACT:
            return await call_next(request)

        # Skip check for unprotected routes
        if any(path.startswith(prefix) for prefix in UNPROTECTED_PREFIXES):
            return await call_next(request)

        # Only guard protected routes
        if not any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
            return await call_next(request)

        # Extract user from JWT
        auth_header = request.headers.get("authorization", "") or request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            # Fail closed for protected routes.
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "Missing Bearer token for protected route.",
                },
            )

        token = auth_header[7:]
        payload = decode_token(token)
        if not payload:
            # Fail closed for protected routes.
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_token",
                    "message": "Invalid or expired token.",
                },
            )

        try:
            tg_id = int(payload["sub"])
        except (KeyError, ValueError, TypeError):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "invalid_subject",
                    "message": "Invalid token subject.",
                },
            )

        # Check verification status from the central table.
        try:
            s = _client()
            res = (
                s.table("user_verifications")
                .select("status")
                .eq("telegram_id", tg_id)
                .limit(1)
                .execute()
            )
            row = (res.data or [None])[0]

            if not row or row.get("status") != APPROVED_STATUS:
                status = row.get("status") if row else "none"
                logger.info(f"[Guard:{tg_id}] Blocked access to {path} — status: {status}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "verification_required",
                        "status": status,
                        "message": "Your Bitunix UID is not approved yet. Submit UID and wait for Telegram admin approval." if status != "rejected" else "Your UID was rejected. Please resubmit a valid UID.",
                    },
                )
        except Exception as e:
            logger.error(f"[Guard:{tg_id}] Verification check failed: {e}")
            # Fail closed to prevent accidental bypass during transient DB failures.
            return JSONResponse(
                status_code=503,
                content={
                    "error": "verification_lookup_failed",
                    "message": "Unable to validate verification status right now. Please try again shortly.",
                },
            )

        return await call_next(request)
