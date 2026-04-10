import os
import re
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.auth.jwt import decode_token
from app.db.supabase import get_user_by_tid, _client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])
bearer = HTTPBearer()

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WEB_DASHBOARD_URL = os.getenv("WEB_DASHBOARD_URL", "https://app.cryptomentor.ai")


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


class SubmitUIDRequest(BaseModel):
    uid: str


@router.get("/me")
async def get_me(tg_id: int = Depends(get_current_user)):
    user = get_user_by_tid(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/verification-status")
async def get_verification_status(tg_id: int = Depends(get_current_user)):
    """
    Returns the user's autotrade verification status.
    Admins always get status 'active' to bypass the verification gate.
    """
    # Admin bypass — admins always have full access
    if tg_id in ADMIN_IDS:
        return {"status": "active", "exchange": "bitunix", "uid": None, "community_code": None}

    s = _client()
    res = s.table("autotrade_sessions").select(
        "status, exchange, bitunix_uid, community_code"
    ).eq("telegram_id", tg_id).limit(1).execute()

    row = (res.data or [None])[0]
    if not row:
        return {"status": "none", "exchange": None, "uid": None, "community_code": None}

    return {
        "status": row.get("status") or "none",
        "exchange": row.get("exchange"),
        "uid": row.get("bitunix_uid"),
        "community_code": row.get("community_code"),
    }


@router.post("/submit-uid")
async def submit_uid(body: SubmitUIDRequest, tg_id: int = Depends(get_current_user)):
    """
    Submit Bitunix UID for admin verification.
    Validates UID, upserts to autotrade_sessions, and notifies admins via Telegram.
    """
    uid = body.uid.strip()

    # Validate: numeric, min 5 digits
    if not re.match(r"^\d{5,}$", uid):
        raise HTTPException(
            status_code=400,
            detail="UID must be numeric and at least 5 digits"
        )

    s = _client()
    now_iso = datetime.utcnow().isoformat()

    # Upsert autotrade_sessions
    s.table("autotrade_sessions").upsert({
        "telegram_id": tg_id,
        "exchange": "bitunix",
        "bitunix_uid": uid,
        "status": "pending_verification",
        "updated_at": now_iso,
    }, on_conflict="telegram_id").execute()

    # Get user info for admin notification
    user = get_user_by_tid(tg_id)
    first_name = (user or {}).get("first_name", "User")
    username = (user or {}).get("username", "")
    username_str = f"@{username}" if username else f"ID:{tg_id}"

    # Send admin Telegram notification with approve/reject buttons
    if TELEGRAM_BOT_TOKEN and ADMIN_IDS:
        import httpx
        text = (
            f"🔔 <b>New UID Verification Request</b>\n\n"
            f"👤 User: {first_name} ({username_str})\n"
            f"🆔 Telegram ID: <code>{tg_id}</code>\n"
            f"🏦 Exchange: Bitunix\n"
            f"🔢 UID: <code>{uid}</code>\n\n"
            f"Please verify this UID in the Bitunix system."
        )
        inline_keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Approve", "callback_data": f"uid_acc_{tg_id}"},
                {"text": "❌ Reject", "callback_data": f"uid_reject_{tg_id}"}
            ]]
        }
        async with httpx.AsyncClient(timeout=10) as client:
            for admin_id in ADMIN_IDS:
                try:
                    await client.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": admin_id,
                            "text": text,
                            "parse_mode": "HTML",
                            "reply_markup": inline_keyboard,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify admin {admin_id}: {e}")

    return {"status": "pending_verification"}


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
