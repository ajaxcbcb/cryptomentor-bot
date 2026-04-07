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

from license_manager import LicenseManager

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
# POST /api/license/info  — get deposit address for a WL
# ---------------------------------------------------------------------------

@app.post("/api/license/info")
@limiter.limit("30/minute")
async def license_info(request: Request):
    """
    Get deposit address and full license info for a WL.
    Body: {"wl_id": str, "secret_key": str}
    Returns: deposit_address, balance, status, monthly_fee, expires_in_days
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid_request"})

    wl_id: str = body.get("wl_id", "")
    secret_key: str = body.get("secret_key", "")
    request.state._wl_id_for_ratelimit = wl_id or get_remote_address(request)

    if not secret_key or not _is_valid_uuid4(secret_key):
        return JSONResponse(status_code=400, content={"error": "invalid_request"})

    try:
        license_row = await license_manager.get_license(wl_id)
    except Exception as exc:
        logger.error("[%s] info wl_id=%s error=%s", timestamp, wl_id, exc)
        return JSONResponse(status_code=503, content={"error": "service_unavailable"})

    if license_row is None:
        return JSONResponse(status_code=404, content={"error": "not_found"})

    if license_row.get("secret_key") != secret_key:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    expires_at_raw = license_row.get("expires_at")
    expires_in_days = 0
    if expires_at_raw:
        try:
            exp = datetime.fromisoformat(str(expires_at_raw))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            expires_in_days = max(0, (exp - datetime.now(timezone.utc)).days)
        except Exception:
            pass

    return JSONResponse(status_code=200, content={
        "deposit_address": license_row.get("deposit_address", ""),
        "balance": float(license_row.get("balance_usdt", 0)),
        "monthly_fee": float(license_row.get("monthly_fee", 10)),
        "status": license_row.get("status", "inactive"),
        "expires_in_days": expires_in_days,
        "network": "BSC (BEP20)",
        "token": "USDT",
    })


# ---------------------------------------------------------------------------
# POST /api/license/deposit  — manual balance top-up by WL admin
# ---------------------------------------------------------------------------

@app.post("/api/license/deposit")
@limiter.limit("20/minute")
async def deposit_balance(request: Request):
    """
    Manually credit balance to a WL license (called from WL bot /admin).

    Body: {"wl_id": str, "secret_key": str, "amount": float}

    Returns:
        200: {"success": true, "balance": float, "expires_in_days": int}
        400: invalid request
        401: unauthorized
        404: not found
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "invalid_request"})

    wl_id: str = body.get("wl_id", "")
    secret_key: str = body.get("secret_key", "")
    amount = body.get("amount", 0)

    request.state._wl_id_for_ratelimit = wl_id or get_remote_address(request)

    if not secret_key or not _is_valid_uuid4(secret_key):
        return JSONResponse(status_code=400, content={"error": "invalid_request"})

    try:
        amount = float(amount)
        if amount < 1:
            return JSONResponse(status_code=400, content={"error": "amount_too_small"})
    except (TypeError, ValueError):
        return JSONResponse(status_code=400, content={"error": "invalid_amount"})

    try:
        license_row = await license_manager.get_license(wl_id)
    except Exception as exc:
        logger.error("[%s] deposit wl_id=%s error=%s", timestamp, wl_id, exc)
        return JSONResponse(status_code=503, content={"error": "service_unavailable"})

    if license_row is None:
        return JSONResponse(status_code=404, content={"error": "not_found"})

    if license_row.get("secret_key") != secret_key:
        return JSONResponse(status_code=401, content={"error": "unauthorized"})

    # Credit balance using a unique tx_hash based on timestamp
    import uuid as _uuid
    tx_hash = f"manual_{wl_id}_{_uuid.uuid4().hex}"

    try:
        await license_manager.credit_balance(
            wl_id=wl_id,
            amount=amount,
            tx_hash=tx_hash,
            block_number=0,
        )
    except Exception as exc:
        logger.error("[%s] deposit credit_balance error: %s", timestamp, exc)
        return JSONResponse(status_code=503, content={"error": "service_unavailable"})

    # If license was suspended/inactive, reactivate it via billing
    current_status = license_row.get("status", "inactive")
    if current_status in ("suspended", "inactive", "grace_period"):
        try:
            await license_manager.debit_billing(wl_id)
        except Exception:
            pass  # non-fatal — balance is already credited

    # Fetch updated license
    updated = await license_manager.get_license(wl_id)
    new_balance = float(updated.get("balance_usdt", 0)) if updated else 0

    expires_at_raw = updated.get("expires_at") if updated else None
    expires_in_days = 0
    if expires_at_raw:
        try:
            exp = datetime.fromisoformat(str(expires_at_raw))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            expires_in_days = max(0, (exp - datetime.now(timezone.utc)).days)
        except Exception:
            pass

    logger.info("[%s] deposit wl_id=%s amount=%.2f new_balance=%.2f", timestamp, wl_id, amount, new_balance)

    return JSONResponse(status_code=200, content={
        "success": True,
        "balance": new_balance,
        "expires_in_days": expires_in_days,
        "status": updated.get("status", "active") if updated else "active",
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("LICENSE_API_PORT", 8080))
    uvicorn.run("license_api:app", host="0.0.0.0", port=port, reload=False)
