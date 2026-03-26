"""
License API — FastAPI app untuk validasi lisensi Whitelabel.
Port: 8080 (via uvicorn)
Rate limiting: 60 req/menit per wl_id via slowapi
"""

import logging
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from license_server.license_manager import LicenseManager

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# UUID v4 regex
# ---------------------------------------------------------------------------
_UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_valid_uuid4(value: str) -> bool:
    return bool(_UUID_V4_RE.match(value))


# ---------------------------------------------------------------------------
# Rate limiter — key = wl_id from request body (fallback to IP)
# ---------------------------------------------------------------------------

def _wl_id_key(request: Request) -> str:
    """Extract wl_id from request body for rate limiting key."""
    # slowapi calls key_func synchronously; body is cached in request.state
    wl_id = getattr(request.state, "_wl_id_for_ratelimit", None)
    if wl_id:
        return wl_id
    return get_remote_address(request)


limiter = Limiter(key_func=_wl_id_key)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="License API", version="1.0.0")
app.state.limiter = limiter

license_manager = LicenseManager()


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded"},
    )


# ---------------------------------------------------------------------------
# POST /api/license/check
# ---------------------------------------------------------------------------

@app.post("/api/license/check")
@limiter.limit("60/minute")
async def check_license(request: Request):
    """
    Validate a WL license.

    Body: {"wl_id": str, "secret_key": str}

    Returns:
        200: {"valid": bool, "expires_in_days": int, "balance": float, "warning": bool, "status": str}
        400: {"error": "invalid_request"}   — secret_key bukan UUID v4
        401: {"error": "unauthorized"}      — secret_key tidak cocok
        404: {"error": "not_found"}         — wl_id tidak ditemukan
        503: {"error": "service_unavailable"} — Supabase failure
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # Parse body
    try:
        body = await request.json()
    except Exception:
        logger.warning("[%s] wl_id=unknown status=400 reason=malformed_json", timestamp)
        return JSONResponse(status_code=400, content={"error": "invalid_request"})

    wl_id: str = body.get("wl_id", "")
    secret_key: str = body.get("secret_key", "")

    # Store wl_id in request.state for rate limiter key func
    request.state._wl_id_for_ratelimit = wl_id or get_remote_address(request)

    # Validasi awal: secret_key harus UUID v4 sebelum query DB
    if not secret_key or not _is_valid_uuid4(secret_key):
        logger.warning("[%s] wl_id=%s status=400 reason=invalid_secret_key_format", timestamp, wl_id)
        return JSONResponse(status_code=400, content={"error": "invalid_request"})

    # Query DB
    try:
        license_row = await license_manager.get_license(wl_id)
    except Exception as exc:
        logger.error("[%s] wl_id=%s status=503 reason=supabase_error error=%s", timestamp, wl_id, exc)
        return JSONResponse(status_code=503, content={"error": "service_unavailable"})

    if license_row is None:
        logger.info("[%s] wl_id=%s status=404", timestamp, wl_id)
        return JSONResponse(status_code=404, content={"error": "not_found"})

    # Cek secret_key cocok
    if license_row.get("secret_key") != secret_key:
        logger.warning("[%s] wl_id=%s status=401", timestamp, wl_id)
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    # Hitung expires_in_days
    expires_at_raw = license_row.get("expires_at")
    if isinstance(expires_at_raw, str):
        expires_at = datetime.fromisoformat(expires_at_raw)
    else:
        expires_at = expires_at_raw  # already datetime

    # Ensure timezone-aware
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = expires_at - now
    expires_in_days = max(0, delta.days)

    balance_usdt: float = float(license_row.get("balance_usdt", 0))
    monthly_fee: float = float(license_row.get("monthly_fee", 0))
    status: str = license_row.get("status", "inactive")

    # valid = True jika status active atau grace_period dan belum expired
    valid: bool = status in ("active", "grace_period") and delta.total_seconds() > 0

    # warning jika hampir expired ATAU saldo kurang
    warning: bool = expires_in_days <= 5 or balance_usdt < monthly_fee

    response_body = {
        "valid": valid,
        "expires_in_days": expires_in_days,
        "balance": balance_usdt,
        "warning": warning,
        "status": status,
    }

    logger.info("[%s] wl_id=%s status=200 valid=%s expires_in_days=%d warning=%s",
                timestamp, wl_id, valid, expires_in_days, warning)

    return JSONResponse(status_code=200, content=response_body)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("LICENSE_API_PORT", 8080))
    uvicorn.run("license_server.license_api:app", host="0.0.0.0", port=port, reload=False)
