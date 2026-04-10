"""
Verification Guard Middleware

Blocks unverified users from accessing trading-related endpoints.
Users must have autotrade_sessions.status in ('uid_verified', 'active')
to access protected routes.

Unprotected routes (always allowed):
- /auth/*         — login/logout
- /user/me        — profile
- /user/verification-status — check status
- /user/submit-uid — submit UID
- /dashboard/system — health check
- /              — root health check
"""

import logging
from fastapi import Request, HTTPException
from app.auth.jwt import decode_token
from app.db.supabase import _client

logger = logging.getLogger(__name__)

UNPROTECTED_ROUTES = [
    "/auth/",
    "/user/me",
    "/user/verification-status",
    "/user/submit-uid",
    "/dashboard/system",
    "/",
    "/docs",
    "/openapi.json",
]

PROTECTED_PREFIXES = [
    "/bitunix/",
    "/dashboard/engine/",
    "/dashboard/signals/",
]


def is_unprotected(path: str) -> bool:
    """Returns True if the route is whitelisted (no verification needed)."""
    for route in UNPROTECTED_ROUTES:
        if path == route or path.startswith(route):
            return True
    return False


def is_protected(path: str) -> bool:
    """Returns True if the route requires verification."""
    for prefix in PROTECTED_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


async def verification_guard_middleware(request: Request, call_next):
    """
    FastAPI middleware that enforces UID verification on protected routes.
    Returns 403 with verification_required error for unverified users.
    """
    path = request.url.path

    # Skip check for unprotected routes
    if is_unprotected(path):
        return await call_next(request)

    # Only enforce on explicitly protected prefixes
    if not is_protected(path):
        return await call_next(request)

    # Extract JWT from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    tg_id = int(payload["sub"])

    # Check verification status in autotrade_sessions
    try:
        s = _client()
        res = s.table("autotrade_sessions").select("status").eq(
            "telegram_id", tg_id
        ).limit(1).execute()
        row = (res.data or [None])[0]
        status = row.get("status") if row else None
    except Exception as e:
        logger.error(f"[VerificationGuard] DB error for user {tg_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check verification status")

    if status not in ("uid_verified", "active"):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "verification_required",
                "status": status or "none",
                "message": "Complete exchange registration before accessing trading features.",
            }
        )

    return await call_next(request)
