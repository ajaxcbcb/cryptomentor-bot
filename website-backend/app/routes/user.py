import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
from app.auth.jwt import decode_token
from app.db.supabase import get_user_by_tid, _client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])
bearer = HTTPBearer()


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])

class SubmitUIDRequest(BaseModel):
    uid: str


VER_PENDING = "pending"
VER_APPROVED = "approved"
VER_REJECTED = "rejected"

_APPROVED_ALIASES = {VER_APPROVED, "uid_verified", "active", "verified"}
_PENDING_ALIASES = {VER_PENDING, "pending_verification", "awaiting_approval"}
_REJECTED_ALIASES = {VER_REJECTED, "uid_rejected", "denied"}


def _normalize_verification_status(raw_status: str) -> str:
    status = str(raw_status or "").strip().lower()
    if status in _APPROVED_ALIASES:
        return VER_APPROVED
    if status in _PENDING_ALIASES:
        return VER_PENDING
    if status in _REJECTED_ALIASES:
        return VER_REJECTED
    return status or "none"


def _load_admin_ids() -> list[int]:
    """Load admin IDs from multiple env keys for resilience."""
    ids = set()
    raw_values = [
        os.getenv("ADMIN_IDS", ""),
        os.getenv("ADMIN1", ""),
        os.getenv("ADMIN2", ""),
        os.getenv("ADMIN_USER_ID", ""),
        os.getenv("ADMIN2_USER_ID", ""),
    ]
    for raw in raw_values:
        for token in str(raw).split(","):
            token = token.strip()
            if token.isdigit():
                ids.add(int(token))
    return sorted(ids)

@router.get("/me")
async def get_me(tg_id: int = Depends(get_current_user)):
    user = get_user_by_tid(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/verification-status")
async def get_verification_status(tg_id: int = Depends(get_current_user)):
    """Single source of truth: user_verifications in Supabase."""
    admin_ids = _load_admin_ids()
    if tg_id in admin_ids:
        return {"status": VER_APPROVED, "exchange": "bitunix", "uid": None}

    s = _client()
    res = (
        s.table("user_verifications")
        .select("status, bitunix_uid, submitted_via, reviewed_at, reviewed_by_admin_id")
        .eq("telegram_id", tg_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    if not row:
        return {"status": "none", "exchange": None, "uid": None}
    normalized_status = _normalize_verification_status(row.get("status"))
    return {
        "status": normalized_status,
        "raw_status": row.get("status") or "none",
        "exchange": "bitunix",
        "uid": row.get("bitunix_uid"),
        "submitted_via": row.get("submitted_via"),
        "reviewed_at": row.get("reviewed_at"),
        "reviewed_by_admin_id": row.get("reviewed_by_admin_id"),
    }

@router.post("/submit-uid")
async def submit_uid(payload: SubmitUIDRequest, tg_id: int = Depends(get_current_user)):
    """Submit Bitunix UID for admin verification and notify admins."""
    uid = str(payload.uid or "").strip()
    if not uid.isdigit() or len(uid) < 5:
        raise HTTPException(status_code=400, detail="Invalid UID. Must be numeric and at least 5 digits.")

    s = _client()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Check current verification status (central source).
    res = (
        s.table("user_verifications")
        .select("status")
        .eq("telegram_id", tg_id)
        .limit(1)
        .execute()
    )
    row = (res.data or [None])[0]
    current_status = _normalize_verification_status(row.get("status") if row else "none")
    if current_status == VER_APPROVED:
        raise HTTPException(status_code=400, detail="Your UID is already verified.")

    s.table("user_verifications").upsert(
        {
            "telegram_id": tg_id,
            "bitunix_uid": uid,
            "status": VER_PENDING,
            "submitted_via": "web",
            "submitted_at": now_iso,
            "reviewed_at": None,
            "reviewed_by_admin_id": None,
            "rejection_reason": None,
            "updated_at": now_iso,
        },
        on_conflict="telegram_id",
    ).execute()

    # Backward compatibility for legacy flows still reading autotrade_sessions.
    try:
        s.table("autotrade_sessions").upsert(
            {
                "telegram_id": tg_id,
                "exchange": "bitunix",
                "bitunix_uid": uid,
                "status": "pending_verification",
                "updated_at": now_iso,
            },
            on_conflict="telegram_id",
        ).execute()
    except Exception:
        logger.warning("Failed to mirror pending status into autotrade_sessions for tg_id=%s", tg_id)

    # Get user info for richer admin notification
    user = get_user_by_tid(tg_id)
    username = user.get("username") or user.get("first_name") or str(tg_id) if user else str(tg_id)
    resubmit_note = " (resubmission after rejection)" if current_status == VER_REJECTED else ""

    # Admin notification
    admin_ids = _load_admin_ids()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    notification_failed = False

    if bot_token and admin_ids:
        async with httpx.AsyncClient(timeout=8.0) as client:
            for admin_id in admin_ids:
                try:
                    resp = await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={
                            "chat_id": admin_id,
                            "text": (
                                f"🔔 <b>New UID Verification{resubmit_note}</b>\n\n"
                                f"👤 User: @{username} (ID: <code>{tg_id}</code>)\n"
                                f"🔑 Bitunix UID: <code>{uid}</code>\n"
                                f"🔗 Referral: sq45"
                            ),
                            "parse_mode": "HTML",
                            "reply_markup": {"inline_keyboard": [[
                                {"text": "✅ Approve", "callback_data": f"uid_acc_{tg_id}"},
                                {"text": "❌ Reject", "callback_data": f"uid_reject_{tg_id}"}
                            ]]}
                        },
                    )
                    if resp.status_code >= 400:
                        notification_failed = True
                        logger.error("Telegram sendMessage failed: status=%s body=%s", resp.status_code, resp.text[:300])
                        continue

                    body = resp.json() if resp.text else {}
                    if not body.get("ok", False):
                        notification_failed = True
                        logger.error("Telegram sendMessage API returned ok=false: %s", str(body)[:300])
                except Exception as e:
                    notification_failed = True
                    logger.error("Telegram sendMessage exception for admin_id=%s: %s", admin_id, e)
    else:
        # Keep user pending but surface notification pipeline issue.
        notification_failed = True
        logger.error("Telegram notification skipped: bot_token_missing=%s admin_ids=%s", not bool(bot_token), admin_ids)

    if notification_failed:
        return {
            "status": VER_PENDING,
            "uid": uid,
            "warning": "UID submitted and pending, but admin notification failed. Please contact support/admin.",
        }

    return {"status": VER_PENDING, "uid": uid}

@router.get("/dashboard")
async def get_dashboard(tg_id: int = Depends(get_current_user)):
    """Data ringkasan untuk halaman dashboard website."""
    user = get_user_by_tid(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "telegram_id": user.get("telegram_id"),
        "username": user.get("username"),
        "first_name": user.get("first_name"),
        "credits": user.get("credits", 0),
        "is_premium": user.get("is_premium", False),
        "premium_until": user.get("premium_until"),
        "is_lifetime": user.get("is_lifetime", False),
    }
