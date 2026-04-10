"""
Verification Guard Middleware

Blocks unverified users from accessing trading-related endpoints.
Only users with status 'uid_verified' or 'active' in autotrade_sessions
can access protected routes. Returns 403 for unverified users.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.auth.jwt import decode_token
from app.db.supabase import _client
import logging

logger = logging.getLogger(__name__)

# Routes that do NOT require exchange verification
# (Always allowed even if user is not verified on Bitunix)
UNPROTECTED_PREFIXES = [
    "/api/auth/",
    "/api/user/me",
    "/api/user/dashboard",
    "/api/user/verification-status",
    "/api/user/submit-uid",
    "/api/dashboard/system",
    "/api/leaderboard",
    "/api/docs",
    "/api/openapi.json",
    "/docs",
    "/openapi.json",
    "/",
]

# These route prefixes require verification status in ('uid_verified', 'active')
PROTECTED_PREFIXES = [
    "/api/bitunix/",
    "/api/dashboard/engine/",
    "/api/dashboard/settings",
    "/api/dashboard/portfolio",
    "/api/dashboard/performance",
    "/api/dashboard/debug",
    "/api/signals/",
    "/api/performance/",
    "/api/engine/",
]


class VerificationGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # If it's a root health check or docs, skip
        if path in ["/", "/docs", "/openapi.json"]:
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
            # Let the route handler deal with missing auth (return 401)
            return await call_next(request)

        token = auth_header[7:]
        payload = decode_token(token)
        if not payload:
            # Let route handler reject invalid token
            return await call_next(request)

        try:
            tg_id = int(payload["sub"])
        except (KeyError, ValueError, TypeError):
            return await call_next(request)

        # Check verification status
        try:
            s = _client()
            res = s.table("autotrade_sessions").select("status").eq(
                "telegram_id", tg_id
            ).limit(1).execute()
            row = (res.data or [None])[0]

            if not row or row.get("status") not in ("uid_verified", "active"):
                status = row.get("status") if row else "none"
                logger.info(f"[Guard:{tg_id}] Blocked access to {path} — status: {status}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "verification_required",
                        "status": status,
                        "message": "Complete exchange registration before accessing trading features.",
                    },
                )
        except Exception as e:
            logger.error(f"[Guard:{tg_id}] Verification check failed: {e}")
            # Fail open — don't block users if DB is down
            pass

        return await call_next(request)
