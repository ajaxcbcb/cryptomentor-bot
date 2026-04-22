import logging
from typing import Any

from app.db.supabase import _client

logger = logging.getLogger(__name__)

VER_PENDING = "pending"
VER_APPROVED = "approved"
VER_REJECTED = "rejected"

_APPROVED_ALIASES = {VER_APPROVED, "uid_verified", "active", "verified"}
_PENDING_ALIASES = {VER_PENDING, "pending_verification", "awaiting_approval"}
_REJECTED_ALIASES = {VER_REJECTED, "uid_rejected", "denied"}
_LEGACY_SESSION_APPROVED_COMPAT = {"stopped", "inactive", "paused", "halted"}


def normalize_verification_status(raw_status: str | None) -> str:
    status = str(raw_status or "").strip().lower()
    if status in _APPROVED_ALIASES:
        return VER_APPROVED
    if status in _PENDING_ALIASES:
        return VER_PENDING
    if status in _REJECTED_ALIASES:
        return VER_REJECTED
    return status or "none"


def normalize_session_verification_status(raw_status: str | None, raw_uid: str | None) -> str:
    status = str(raw_status or "").strip().lower()
    has_uid = bool(str(raw_uid or "").strip())

    if has_uid and status in _LEGACY_SESSION_APPROVED_COMPAT:
        return VER_APPROVED

    normalized = normalize_verification_status(raw_status)
    if normalized != "none":
        return normalized
    return "none"


def uids_compatible(primary_uid: str | None, secondary_uid: str | None) -> bool:
    p_uid = str(primary_uid or "").strip()
    s_uid = str(secondary_uid or "").strip()
    if not p_uid or not s_uid:
        return True
    return p_uid == s_uid


def _safe_session_meta(session_row: dict[str, Any] | None) -> dict[str, Any]:
    if not session_row:
        return {
            "session_status": "none",
            "session_raw_status": "none",
            "session_uid_suffix": "",
            "session_present": False,
        }
    session_uid = str(session_row.get("bitunix_uid") or "")
    return {
        "session_status": normalize_session_verification_status(
            session_row.get("status"),
            session_uid,
        ),
        "session_raw_status": str(session_row.get("status") or "none"),
        "session_uid_suffix": session_uid[-4:] if session_uid else "",
        "session_present": True,
    }


def _build_snapshot(
    *,
    status: str,
    raw_status: str,
    uid: str | None,
    source: str,
    decision_reason: str,
    mismatch_detected: bool,
    uv_row: dict[str, Any] | None,
    sess_row: dict[str, Any] | None,
) -> dict[str, Any]:
    out = {
        "status": status or "none",
        "raw_status": raw_status or "none",
        "uid": uid or "",
        "source": source or "none",
        "decision_reason": decision_reason or "none",
        "mismatch_detected": bool(mismatch_detected),
    }
    if uv_row:
        out["submitted_via"] = uv_row.get("submitted_via")
        out["reviewed_at"] = uv_row.get("reviewed_at")
        out["reviewed_by_admin_id"] = uv_row.get("reviewed_by_admin_id")
        out["community_code"] = uv_row.get("community_code")
    else:
        out["submitted_via"] = None
        out["reviewed_at"] = None
        out["reviewed_by_admin_id"] = None
        out["community_code"] = None

    if mismatch_detected:
        uid = str(uid or "")
        mismatch_meta = {
            "event": "verification_status_mismatch",
            "decision_reason": out["decision_reason"],
            "decision_source": out["source"],
            "decision_status": out["status"],
            "uv_status": normalize_verification_status(uv_row.get("status") if uv_row else None),
            "uv_raw_status": str((uv_row or {}).get("status") or "none"),
            "uid_suffix": uid[-4:] if uid else "",
            **_safe_session_meta(sess_row),
        }
        out["mismatch_meta"] = mismatch_meta

    return out


def load_verification_snapshot(tg_id: int) -> dict[str, Any]:
    """
    Shared verification resolver for middleware and API status endpoints.
    Policy:
    - Canonical source: user_verifications.
    - Compat self-heal: if session indicates approved/rejected and UIDs are compatible,
      prefer that deterministic final state when user_verifications is pending.
    """
    s = _client()
    try:
        uv_res = (
            s.table("user_verifications")
            .select("status, bitunix_uid, submitted_via, reviewed_at, reviewed_by_admin_id, community_code")
            .eq("telegram_id", int(tg_id))
            .limit(1)
            .execute()
        )
    except Exception:
        uv_res = (
            s.table("user_verifications")
            .select("status, bitunix_uid, submitted_via, reviewed_at, reviewed_by_admin_id")
            .eq("telegram_id", int(tg_id))
            .limit(1)
            .execute()
        )

    sess_res = (
        s.table("autotrade_sessions")
        .select("status, bitunix_uid")
        .eq("telegram_id", int(tg_id))
        .limit(1)
        .execute()
    )

    uv_row = (uv_res.data or [None])[0]
    sess_row = (sess_res.data or [None])[0]

    uv_status = normalize_verification_status((uv_row or {}).get("status"))
    sess_status = normalize_session_verification_status(
        (sess_row or {}).get("status"),
        (sess_row or {}).get("bitunix_uid"),
    )
    uid_ok = uids_compatible((uv_row or {}).get("bitunix_uid"), (sess_row or {}).get("bitunix_uid"))

    mismatch_detected = (
        bool(uv_row and sess_row)
        and uv_status != "none"
        and sess_status != "none"
        and uv_status != sess_status
    )

    if uv_row:
        if uv_status == VER_PENDING and sess_row and sess_status in {VER_APPROVED, VER_REJECTED} and uid_ok:
            return _build_snapshot(
                status=sess_status,
                raw_status=str(uv_row.get("status") or "none"),
                uid=(sess_row.get("bitunix_uid") or uv_row.get("bitunix_uid") or ""),
                source="compat_session_override",
                decision_reason="uv_pending_session_final_uid_compatible",
                mismatch_detected=True,
                uv_row=uv_row,
                sess_row=sess_row,
            )
        if uv_status != "none":
            return _build_snapshot(
                status=uv_status,
                raw_status=str(uv_row.get("status") or "none"),
                uid=str(uv_row.get("bitunix_uid") or ""),
                source="user_verifications",
                decision_reason="uv_canonical",
                mismatch_detected=mismatch_detected,
                uv_row=uv_row,
                sess_row=sess_row,
            )

    if sess_row:
        return _build_snapshot(
            status=sess_status,
            raw_status=str(sess_row.get("status") or "none"),
            uid=str(sess_row.get("bitunix_uid") or ""),
            source="autotrade_sessions",
            decision_reason="session_fallback",
            mismatch_detected=False,
            uv_row=uv_row,
            sess_row=sess_row,
        )

    return _build_snapshot(
        status="none",
        raw_status="none",
        uid="",
        source="none",
        decision_reason="not_found",
        mismatch_detected=False,
        uv_row=uv_row,
        sess_row=sess_row,
    )
