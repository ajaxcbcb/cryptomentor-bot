import os
import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import httpx
from app.auth.jwt import decode_token
from app.auth.admin import augment_user_with_admin, is_admin_telegram_id, load_admin_ids
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
    community_code: Optional[str] = None


VER_PENDING = "pending"
VER_APPROVED = "approved"
VER_REJECTED = "rejected"

_APPROVED_ALIASES = {VER_APPROVED, "uid_verified", "active", "verified"}
_PENDING_ALIASES = {VER_PENDING, "pending_verification", "awaiting_approval"}
_REJECTED_ALIASES = {VER_REJECTED, "uid_rejected", "denied"}
_LEGACY_SESSION_APPROVED_COMPAT = {"stopped", "inactive", "paused", "halted"}


def _normalize_verification_status(raw_status: str) -> str:
    status = str(raw_status or "").strip().lower()
    if status in _APPROVED_ALIASES:
        return VER_APPROVED
    if status in _PENDING_ALIASES:
        return VER_PENDING
    if status in _REJECTED_ALIASES:
        return VER_REJECTED
    return status or "none"


def _normalize_session_verification_status(raw_status: str, raw_uid: str) -> str:
    normalized = _normalize_verification_status(raw_status)
    if normalized != "none":
        return normalized

    status = str(raw_status or "").strip().lower()
    has_uid = bool(str(raw_uid or "").strip())
    if has_uid and status in _LEGACY_SESSION_APPROVED_COMPAT:
        return VER_APPROVED
    return "none"


def _uids_compatible(uv_uid: str | None, session_uid: str | None) -> bool:
    uv = str(uv_uid or "").strip()
    sess = str(session_uid or "").strip()
    if not uv or not sess:
        return True
    return uv == sess


def _load_verification_snapshot(tg_id: int) -> dict:
    """
    Compatibility lookup:
    1) user_verifications (canonical)
    2) autotrade_sessions (legacy fallback)
    """
    s = _client()
    try:
        uv_res = (
            s.table("user_verifications")
            .select("status, bitunix_uid, submitted_via, reviewed_at, reviewed_by_admin_id, community_code")
            .eq("telegram_id", tg_id)
            .limit(1)
            .execute()
        )
    except Exception:
        uv_res = (
            s.table("user_verifications")
            .select("status, bitunix_uid, submitted_via, reviewed_at, reviewed_by_admin_id")
            .eq("telegram_id", tg_id)
            .limit(1)
            .execute()
        )

    sess_res = (
        s.table("autotrade_sessions")
        .select("status, bitunix_uid")
        .eq("telegram_id", tg_id)
        .limit(1)
        .execute()
    )
    sess_row = (sess_res.data or [None])[0]

    uv_row = (uv_res.data or [None])[0]
    if uv_row:
        raw_status = uv_row.get("status")
        normalized = _normalize_verification_status(raw_status)
        if normalized == VER_PENDING and sess_row:
            sess_raw_status = sess_row.get("status")
            sess_uid = sess_row.get("bitunix_uid")
            sess_normalized = _normalize_session_verification_status(sess_raw_status, sess_uid)
            if sess_normalized in {VER_APPROVED, VER_REJECTED} and _uids_compatible(uv_row.get("bitunix_uid"), sess_uid):
                logger.warning(
                    "[Verification] Using compat override for tg_id=%s uv_status=%s session_status=%s",
                    tg_id,
                    raw_status,
                    sess_raw_status,
                )
                return {
                    "status": sess_normalized,
                    "raw_status": raw_status or "none",
                    "uid": sess_uid or uv_row.get("bitunix_uid"),
                    "submitted_via": uv_row.get("submitted_via"),
                    "reviewed_at": uv_row.get("reviewed_at"),
                    "reviewed_by_admin_id": uv_row.get("reviewed_by_admin_id"),
                    "community_code": uv_row.get("community_code"),
                    "source": "compat_session_override",
                }
        if normalized != "none":
            return {
                "status": normalized,
                "raw_status": raw_status or "none",
                "uid": uv_row.get("bitunix_uid"),
                "submitted_via": uv_row.get("submitted_via"),
                "reviewed_at": uv_row.get("reviewed_at"),
                "reviewed_by_admin_id": uv_row.get("reviewed_by_admin_id"),
                "community_code": uv_row.get("community_code"),
                "source": "user_verifications",
            }

    if sess_row:
        raw_status = sess_row.get("status")
        raw_uid = sess_row.get("bitunix_uid")
        return {
            "status": _normalize_session_verification_status(raw_status, raw_uid),
            "raw_status": raw_status or "none",
            "uid": raw_uid,
            "submitted_via": None,
            "reviewed_at": None,
            "reviewed_by_admin_id": None,
            "community_code": None,
            "source": "autotrade_sessions",
        }

    return {
        "status": "none",
        "raw_status": "none",
        "uid": None,
        "submitted_via": None,
        "reviewed_at": None,
        "reviewed_by_admin_id": None,
        "community_code": None,
        "source": "none",
    }


def _sanitize_community_code(raw: str | None) -> str | None:
    code = str(raw or "").strip().lower()
    if not code:
        return None
    code = "".join(ch for ch in code if ch.isalnum())
    return code[:32] or None


def _fallback_referral_url() -> str:
    return os.getenv(
        "FALLBACK_REFERRAL_URL",
        "https://www.bitunix.com/register?vipCode=sq45",
    )


def _telegram_safe_text(value: str) -> str:
    """Normalize escaped newlines/tabs so Telegram renders readable message blocks."""
    text = str(value or "")
    # Handle double-escaped payloads first, then regular escaped sequences.
    return (
        text
        .replace("\\\\r\\\\n", "\n")
        .replace("\\\\n", "\n")
        .replace("\\\\t", "\t")
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
    )


def _resolve_referral_context(community_code: str | None) -> dict:
    normalized = _sanitize_community_code(community_code)
    if not normalized:
        fallback = _fallback_referral_url()
        logger.info("[Referral] ref_source=fallback community_code=none url=%s", fallback)
        return {
            "community_code": None,
            "partner_telegram_id": None,
            "partner_name": None,
            "bitunix_referral_url": fallback,
            "ref_source": "fallback",
        }

    s = _client()
    try:
        res = (
            s.table("community_partners")
            .select("telegram_id, community_name, community_code, bitunix_referral_url, status")
            .eq("community_code", normalized)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        row = (res.data or [None])[0]
        if row and row.get("bitunix_referral_url"):
            resolved_url = row.get("bitunix_referral_url")
            logger.info(
                "[Referral] ref_source=dynamic community_code=%s partner_id=%s url=%s",
                row.get("community_code") or normalized,
                row.get("telegram_id"),
                resolved_url,
            )
            return {
                "community_code": row.get("community_code") or normalized,
                "partner_telegram_id": row.get("telegram_id"),
                "partner_name": row.get("community_name"),
                "bitunix_referral_url": resolved_url,
                "ref_source": "dynamic",
            }
    except Exception as exc:
        logger.error("[Referral] Failed to resolve community_code=%s: %s", normalized, exc)

    fallback = _fallback_referral_url()
    logger.warning(
        "[Referral] ref_source=fallback community_code=%s reason=no_active_partner url=%s",
        normalized,
        fallback,
    )
    return {
        "community_code": normalized,
        "partner_telegram_id": None,
        "partner_name": None,
        "bitunix_referral_url": fallback,
        "ref_source": "fallback",
    }

@router.get("/me")
async def get_me(tg_id: int = Depends(get_current_user)):
    user = get_user_by_tid(tg_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return augment_user_with_admin(user)

@router.get("/verification-status")
async def get_verification_status(tg_id: int = Depends(get_current_user)):
    """Single source of truth: user_verifications in Supabase."""
    admin_ids = load_admin_ids()
    if tg_id in admin_ids:
        return {
            "status": VER_APPROVED,
            "raw_status": VER_APPROVED,
            "exchange": "bitunix",
            "uid": None,
            "source": "admin_bypass",
        }

    snap = _load_verification_snapshot(tg_id)
    if snap.get("status") == "none":
        return {
            "status": "none",
            "raw_status": "none",
            "exchange": None,
            "uid": None,
            "community_code": None,
            "bitunix_referral_url": _fallback_referral_url(),
            "ref_source": "fallback",
            "source": "none",
        }
    referral = _resolve_referral_context(snap.get("community_code"))
    return {
        "status": snap.get("status"),
        "raw_status": snap.get("raw_status") or "none",
        "exchange": "bitunix",
        "uid": snap.get("uid"),
        "submitted_via": snap.get("submitted_via"),
        "reviewed_at": snap.get("reviewed_at"),
        "reviewed_by_admin_id": snap.get("reviewed_by_admin_id"),
        "community_code": referral.get("community_code"),
        "bitunix_referral_url": referral.get("bitunix_referral_url"),
        "ref_source": referral.get("ref_source"),
        "source": snap.get("source") or "none",
    }


@router.get("/referral-context")
async def get_referral_context(
    community_code: str | None = None,
):
    return _resolve_referral_context(community_code)

@router.post("/submit-uid")
async def submit_uid(payload: SubmitUIDRequest, tg_id: int = Depends(get_current_user)):
    """Submit Bitunix UID for admin verification and notify admins."""
    uid = str(payload.uid or "").strip()
    if not uid.isdigit() or len(uid) < 5:
        raise HTTPException(status_code=400, detail="Invalid UID. Must be numeric and at least 5 digits.")

    community_code = _sanitize_community_code(payload.community_code)
    referral = _resolve_referral_context(community_code)

    s = _client()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Check current verification status with legacy fallback compatibility.
    current_status = _load_verification_snapshot(tg_id).get("status", "none")
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
            "community_code": community_code,
            "updated_at": now_iso,
        },
        on_conflict="telegram_id",
    ).execute()
    # Best-effort enrichment for newer schemas that store resolved referral context.
    # Keep compatibility with older DBs by swallowing unknown-column errors.
    try:
        s.table("user_verifications").update(
            {
                "resolved_partner_telegram_id": referral.get("partner_telegram_id"),
                "resolved_partner_name": referral.get("partner_name"),
                "resolved_referral_url": referral.get("bitunix_referral_url"),
                "ref_source": referral.get("ref_source"),
            }
        ).eq("telegram_id", tg_id).execute()
    except Exception:
        logger.info("user_verifications referral enrichment columns unavailable; continuing.")

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

    # Admin/Partner notification
    admin_ids = _load_admin_ids()
    target_ids = admin_ids.copy()
    referral_display = referral.get("community_code") or "StackMentor (Direct)"

    # Check if this comes from a community partner
    partner_id = referral.get("partner_telegram_id")
    partner_name = referral.get("partner_name")
    if partner_id:
        if partner_id not in target_ids:
            target_ids.append(partner_id)
        if partner_name and referral.get("community_code"):
            referral_display = f"{partner_name} ({referral.get('community_code')})"

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    notification_failed = False

    if bot_token and target_ids:
        async with httpx.AsyncClient(timeout=8.0) as client:
            for target_id in target_ids:
                try:
                    message_text = _telegram_safe_text(
                        (
                            f"🔔 <b>New UID Verification{resubmit_note}</b>\n\n"
                            "<b>User Details</b>\n"
                            f"• User: @{username}\n"
                            f"• Telegram ID: <code>{tg_id}</code>\n"
                            f"• Bitunix UID: <code>{uid}</code>\n\n"
                            "<b>Referral Context</b>\n"
                            f"• Community: <code>{referral_display}</code>\n"
                            f"• Source: <code>{referral.get('ref_source') or 'fallback'}</code>\n"
                            f"• URL: <code>{referral.get('bitunix_referral_url') or _fallback_referral_url()}</code>\n\n"
                            f"<b>Submitted At</b>\n"
                            f"• <code>{now_iso}</code>"
                        )
                    )
                    resp = await client.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={
                            "chat_id": target_id,
                            "text": message_text,
                            "parse_mode": "HTML",
                            "disable_web_page_preview": True,
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
                    logger.error("Telegram sendMessage exception for target_id=%s: %s", target_id, e)
    else:
        # Keep user pending but surface notification pipeline issue.
        notification_failed = True
        logger.error("Telegram notification skipped: bot_token_missing=%s admin_ids=%s", not bool(bot_token), admin_ids)

    if notification_failed:
        return {
            "status": VER_PENDING,
            "uid": uid,
            "community_code": referral.get("community_code"),
            "bitunix_referral_url": referral.get("bitunix_referral_url"),
            "ref_source": referral.get("ref_source"),
            "warning": "UID submitted and pending, but admin notification failed. Please contact support/admin.",
        }

    return {
        "status": VER_PENDING,
        "uid": uid,
        "community_code": referral.get("community_code"),
        "bitunix_referral_url": referral.get("bitunix_referral_url"),
        "ref_source": referral.get("ref_source"),
    }

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
        "is_admin": is_admin_telegram_id(user.get("telegram_id")),
    }

