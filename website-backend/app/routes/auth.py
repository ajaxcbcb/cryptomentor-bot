import logging
import os
import time
from fastapi import APIRouter, HTTPException, Request
from app.auth.telegram import verify_telegram_auth_detailed
from app.auth.jwt import create_token
from app.auth.admin import augment_user_with_admin
from app.db.supabase import upsert_web_login
from app.models.user import TelegramAuthData

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

DEFAULT_MAX_AUTH_AGE_SECONDS = 86400  # 24 jam


def _resolve_max_auth_age_seconds() -> int:
    raw = str(os.getenv("TELEGRAM_AUTH_MAX_AGE_SECONDS") or "").strip()
    if not raw:
        return DEFAULT_MAX_AUTH_AGE_SECONDS
    try:
        parsed = int(raw)
    except ValueError:
        logger.warning("Invalid TELEGRAM_AUTH_MAX_AGE_SECONDS=%r, using default=%s", raw, DEFAULT_MAX_AUTH_AGE_SECONDS)
        return DEFAULT_MAX_AUTH_AGE_SECONDS
    if parsed <= 0:
        logger.warning("Non-positive TELEGRAM_AUTH_MAX_AGE_SECONDS=%s, using default=%s", parsed, DEFAULT_MAX_AUTH_AGE_SECONDS)
        return DEFAULT_MAX_AUTH_AGE_SECONDS
    return parsed


MAX_AUTH_AGE_SECONDS = _resolve_max_auth_age_seconds()


def _auth_error_detail(error_code: str, message: str, **extra):
    return {
        "error_code": error_code,
        "message": message,
        **extra,
    }


def _safe_auth_meta(payload: dict, request: Request, *, reason_code: str, auth_age_seconds: int | None = None) -> dict:
    headers = request.headers
    xff = (headers.get("x-forwarded-for") or "").split(",")[0].strip()
    ip = request.client.host if request.client else ""
    ua = headers.get("user-agent") or ""
    telegram_id = str(payload.get("id") or "")
    field_names = sorted(str(k) for k in payload.keys())
    return {
        "event": "telegram_auth_failed",
        "reason_code": reason_code,
        "client_ip": ip or xff or "unknown",
        "has_x_forwarded_for": bool(xff),
        "user_agent_prefix": ua[:96],
        "payload_fields": field_names,
        "has_hash": bool(payload.get("hash")),
        "telegram_id_suffix": telegram_id[-4:] if telegram_id else "",
        "auth_age_seconds": auth_age_seconds,
    }


@router.post("/telegram")
async def telegram_login(data: TelegramAuthData, request: Request):
    """
    Endpoint dipanggil frontend setelah user klik Telegram Login Widget.
    Frontend kirim semua field dari Telegram ke sini.
    """
    payload = data.model_dump()
    now_ts = int(time.time())

    # 1. Verifikasi hash dari Telegram
    auth_ok, reason_code = verify_telegram_auth_detailed(payload)
    if not auth_ok:
        logger.warning("telegram_auth_failure meta=%s", _safe_auth_meta(payload, request, reason_code=reason_code))
        raise HTTPException(
            status_code=401,
            detail=_auth_error_detail(
                error_code="telegram_auth_invalid",
                message="Invalid Telegram auth data. Please retry from Telegram widget.",
                reason_code=reason_code,
            ),
        )

    # 2. Cek auth_date tidak terlalu lama
    auth_age_seconds = now_ts - int(data.auth_date)
    if auth_age_seconds < -60:
        logger.warning(
            "telegram_auth_failure meta=%s",
            _safe_auth_meta(payload, request, reason_code="auth_date_in_future", auth_age_seconds=auth_age_seconds),
        )
        raise HTTPException(
            status_code=401,
            detail=_auth_error_detail(
                error_code="telegram_auth_invalid",
                message="Invalid Telegram auth date. Please retry from Telegram widget.",
                reason_code="auth_date_in_future",
            ),
        )
    if auth_age_seconds > MAX_AUTH_AGE_SECONDS:
        logger.warning(
            "telegram_auth_failure meta=%s",
            _safe_auth_meta(payload, request, reason_code="auth_data_expired", auth_age_seconds=auth_age_seconds),
        )
        raise HTTPException(
            status_code=401,
            detail=_auth_error_detail(
                error_code="telegram_auth_expired",
                message="Telegram auth data expired. Please login again from Telegram.",
                reason_code="auth_data_expired",
                max_age_seconds=MAX_AUTH_AGE_SECONDS,
            ),
        )

    # 3. Upsert user ke Supabase
    try:
        user = upsert_web_login(
            tg_id=data.id,
            username=data.username or "",
            first_name=data.first_name,
            last_name=data.last_name,
            referred_by=data.referred_by,
        )
        user = augment_user_with_admin(user)
    except Exception:
        logger.exception("Failed to upsert web login for tg_id=%s", data.id)
        raise HTTPException(status_code=503, detail="Login service temporarily unavailable")

    # 4. Buat JWT
    token = create_token(
        telegram_id=data.id,
        extra={"username": data.username, "first_name": data.first_name},
    )

    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/logout")
async def logout():
    # JWT stateless, logout cukup hapus token di frontend
    return {"message": "Logged out"}
