import os
import re
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

@router.get("/me")
async def get_me(tg_id: int = Depends(get_current_user)):
    user = get_user_by_tid(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/verification-status")
async def get_verification_status(tg_id: int = Depends(get_current_user)):
    """Check user's exchange verification status and admin bypass."""
    admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
    if tg_id in admin_ids:
        return {"status": "active", "exchange": "bitunix", "uid": None}

    s = _client()
    res = s.table("autotrade_sessions").select("status, exchange, bitunix_uid, community_code").eq("telegram_id", tg_id).limit(1).execute()
    row = (res.data or [None])[0]
    if not row:
        return {"status": "none", "exchange": None, "uid": None}
    return {
        "status": row.get("status") or "none",
        "exchange": row.get("exchange") or "bitunix",
        "uid": row.get("bitunix_uid"),
        "community_code": row.get("community_code"),
    }

@router.post("/submit-uid")
async def submit_uid(payload: dict, tg_id: int = Depends(get_current_user)):
    """Submit Bitunix UID for admin verification and notify admins."""
    uid = str(payload.get("uid", "")).strip()
    if not uid.isdigit() or len(uid) < 5:
        raise HTTPException(status_code=400, detail="Invalid UID. Must be numeric and at least 5 digits.")

    s = _client()
    now_iso = datetime.now(timezone.utc).isoformat()
    s.table("autotrade_sessions").upsert({
        "telegram_id": tg_id,
        "exchange": "bitunix",
        "bitunix_uid": uid,
        "status": "pending_verification",
        "updated_at": now_iso,
    }, on_conflict="telegram_id").execute()

    # Admin notification
    admin_ids = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if bot_token and admin_ids:
        async with httpx.AsyncClient() as client:
            for admin_id in admin_ids:
                try:
                    await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={
                            "chat_id": admin_id,
                            "text": f"🔔 <b>New UID Verification</b>\n\nUser ID: {tg_id}\nUID: {uid}\nReferral: sq45",
                            "parse_mode": "HTML",
                            "reply_markup": {"inline_keyboard": [[
                                {"text": "✅ Approve", "callback_data": f"uid_acc_{tg_id}"},
                                {"text": "❌ Reject", "callback_data": f"uid_reject_{tg_id}"}
                            ]]}
                        }
                    )
                except: pass
    return {"status": "pending_verification", "uid": uid}

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
