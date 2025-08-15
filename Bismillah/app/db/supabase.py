
import os
from typing import Optional, Any, Dict
from supabase import create_client, Client
import anyio
import hashlib, base64, re
from datetime import datetime, timezone
import logging

L = logging.getLogger("supabase")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
USE_DB = os.getenv("USE_DB", "true").lower() in ("1","true","yes")

_client: Optional[Client] = None

def get_client() -> Client:
    if not USE_DB:
        raise RuntimeError("USE_DB=false — DB dimatikan")
    global _client
    if _client is None:
        if not SUPABASE_URL or not SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL/SUPABASE_SERVICE_KEY belum diset")
        _client = create_client(SUPABASE_URL, SERVICE_KEY)
        L.info("Supabase client initialized.")
    return _client

# ---------- eksekusi sinkron .execute() di thread ----------
async def exec_(req_callable):
    """
    Jalankan .execute() milik Postgrest request di thread terpisah.
    Pemakaian:
        await exec_(sb.table("users").upsert(payload, on_conflict="id"))
        await exec_(sb.table("users").select("*").eq("id", uid).single())
    """
    def _run():
        try:
            return req_callable.execute()
        except Exception as e:
            L.error("Supabase execute() error: %s", e)
            raise
    return await anyio.to_thread.run_sync(_run)

# ---------- Referral Code ----------
def _make_referral_code(user_id: str) -> str:
    h = hashlib.sha256(user_id.encode("utf-8")).digest()
    code = base64.b32encode(h)[:8].decode("ascii")
    return re.sub(r"[^A-Z0-9]", "X", code)

# ---------- Upsert & Fetch ----------
async def upsert_user_on_start(user_id: str, username: str, referred_param: str | None) -> Dict[str, Any]:
    sb = get_client()

    # 1) get existing
    try:
        res = await exec_(sb.table("users").select("*").eq("id", user_id).limit(1).single())
        user = getattr(res, "data", None)
    except Exception:
        user = None

    # 2) ensure referral_code
    my_code = user.get("referral_code") if user else None
    if not my_code:
        my_code = _make_referral_code(user_id)

    payload = {
        "id": user_id,
        "username": (username or ""),
        "referral_code": my_code,
    }

    # 3) resolve referred_by from referral code (if provided)
    referrer_id = None
    if referred_param:
        try:
            r = await exec_(sb.table("users").select("id").eq("referral_code", referred_param.upper()).limit(1).single())
            ref_row = getattr(r, "data", None)
            if ref_row and ref_row.get("id") and ref_row["id"] != user_id:
                referrer_id = ref_row["id"]
                if not user or not user.get("referred_by"):
                    payload["referred_by"] = referrer_id
        except Exception as e:
            L.warning("resolve referral code gagal: %s", e)

    # 4) UPSERT (PENTING: gunakan on_conflict='id' dan panggil .execute())
    _ = await exec_(sb.table("users").upsert(payload, on_conflict="id"))

    # 5) optional: log referral event
    if referrer_id:
        try:
            _ = await exec_(sb.table("referral_events").insert({
                "referred_user_id": user_id,
                "referrer_user_id": referrer_id,
                "source": "start",
            }))
        except Exception as e:
            L.warning("insert referral_events gagal: %s", e)

    # 6) snapshot final
    res2 = await exec_(sb.table("users").select("*").eq("id", user_id).limit(1).single())
    u = getattr(res2, "data", {}) or {}

    # 7) derived premium
    now = datetime.now(timezone.utc)
    prem_until_iso = u.get("premium_until")
    prem_until_ok = False
    if prem_until_iso:
        try:
            prem_until_ok = datetime.fromisoformat(prem_until_iso.replace("Z","+00:00")) >= now
        except Exception:
            prem_until_ok = False
    is_premium = bool(u.get("is_lifetime")) or prem_until_ok

    # 8) referred_count
    res3 = await exec_(sb.table("users").select("id", count="exact").eq("referred_by", user_id))
    referred_count = getattr(res3, "count", 0) or 0

    snap = {
        "id": u.get("id", user_id),
        "username": u.get("username", ""),
        "is_admin": bool(u.get("is_admin")),
        "is_lifetime": bool(u.get("is_lifetime")),
        "premium_until": u.get("premium_until"),  # ISO or None
        "is_premium": is_premium,
        "credits": int(u.get("credits", 0)),
        "referral_code": u.get("referral_code", my_code),
        "referred_by": u.get("referred_by"),
        "referred_count": referred_count,
        "created_at": u.get("created_at"),
        "updated_at": u.get("updated_at"),
    }
    L.info("upsert_user_on_start snapshot: %s", {k: snap[k] for k in ("id","username","is_premium","credits","referral_code","referred_count")})
    return snap
