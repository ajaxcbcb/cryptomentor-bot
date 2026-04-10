from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.jwt import decode_token
from app.db.supabase import get_user_by_tid, _client
from datetime import datetime, timezone
import os
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])
bearer = HTTPBearer()

# Admin Telegram IDs for UID verification notifications
_ADMIN_IDS: list[int] = []
for key in ['ADMIN_IDS', 'ADMIN1', 'ADMIN2', 'ADMIN_USER_ID', 'ADMIN2_USER_ID']:
    value = os.getenv(key)
    if value:
        for part in value.split(','):
            part = part.strip()
            if part.isdigit():
                _ADMIN_IDS.append(int(part))
_ADMIN_IDS = list(set(_ADMIN_IDS))

TELEGRAM_BOT_TOKEN = <REDACTED_TELEGRAM_BOT_TOKEN>
WEB_DASHBOARD_URL = os.getenv("FRONTEND_URL", "https://cryptomentor.id")


def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return int(payload["sub"])


@router.get("/me")
async def get_me(tg_id: int = Depends(get_current_user)):
    user = get_user_by_tid(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


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


@router.get("/verification-status")
async def get_verification_status(tg_id: int = Depends(get_current_user)):
    """
    Check user's exchange verification status.

    Returns:
        status: "none" | "pending_verification" | "uid_verified" | "active"
        exchange: exchange name if session exists
        uid: Bitunix UID if submitted
        community_code: community affiliation if present
    """
    s = _client()
    res = s.table("autotrade_sessions").select(
        "status, exchange, bitunix_uid, community_code"
    ).eq("telegram_id", tg_id).limit(1).execute()

    row = (res.data or [None])[0]
    if not row:
        return {
            "status": "none",
            "exchange": None,
            "uid": None,
            "community_code": None,
        }

    return {
        "status": row.get("status") or "none",
        "exchange": row.get("exchange") or "bitunix",
        "uid": row.get("bitunix_uid"),
        "community_code": row.get("community_code"),
    }


@router.post("/submit-uid")
async def submit_uid(payload: dict, tg_id: int = Depends(get_current_user)):
    """
    Submit Bitunix UID for admin verification (web registration flow).

    Saves UID to autotrade_sessions with status=pending_verification,
    then sends an approval request to admins via Telegram Bot API.
    """
    uid = str(payload.get("uid", "")).strip()

    # Validate UID
    if not uid or not uid.isdigit() or len(uid) < 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid UID. Must be numeric and at least 5 digits."
        )

    s = _client()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Upsert autotrade_sessions
    s.table("autotrade_sessions").upsert({
        "telegram_id": tg_id,
        "exchange": "bitunix",
        "bitunix_uid": uid,
        "status": "pending_verification",
        "updated_at": now_iso,
    }, on_conflict="telegram_id").execute()

    logger.info(f"[UID:{tg_id}] Submitted Bitunix UID {uid} for verification (via web)")

    # Send admin notification via Telegram Bot API
    if TELEGRAM_BOT_TOKEN and _ADMIN_IDS:
        user = get_user_by_tid(tg_id)
        full_name = user.get("first_name", "Unknown") if user else "Unknown"
        username = user.get("username", "") if user else ""
        username_display = f"@{username}" if username else "N/A"

        admin_text = (
            f"🔔 <b>AutoTrade UID Verification (Web)</b>\n\n"
            f"👤 User: <b>{full_name}</b> ({username_display})\n"
            f"🆔 Telegram ID: <code>{tg_id}</code>\n"
            f"🏦 Exchange: <b>Bitunix</b>\n"
            f"🔢 Bitunix UID: <code>{uid}</code>\n\n"
            f"Verify that this UID is registered under referral "
            f"<b>sq45</b> on Bitunix.\n\n"
            f"Approve or reject this user's registration:"
        )
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ APPROVE", "callback_data": f"uid_acc_{tg_id}"},
                {"text": "❌ REJECT", "callback_data": f"uid_reject_{tg_id}"},
            ]]
        }

        async with httpx.AsyncClient() as client:
            for admin_id in _ADMIN_IDS:
                try:
                    await client.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                        json={
                            "chat_id": admin_id,
                            "text": admin_text,
                            "parse_mode": "HTML",
                            "reply_markup": keyboard,
                        },
                        timeout=10,
                    )
                except Exception as e:
                    logger.warning(f"[UID:{tg_id}] Failed to notify admin {admin_id}: {e}")

    return {"status": "pending_verification", "uid": uid}
