
import os
from typing import Optional, Any, Dict, Tuple, List
from supabase import create_client, Client
import anyio
import hashlib, base64, re
from datetime import datetime, timezone

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
    return _client

async def run_db(fn, *args, **kwargs):
    return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))

# ---------- Referral Code ----------
def _make_referral_code(user_id: str) -> str:
    """
    Generate kode unik 8 chars uppercase [A-Z0-9] dari user_id deterministik.
    """
    h = hashlib.sha256(user_id.encode("utf-8")).digest()
    # Base32 lebih ringkas & uppercase
    code = base64.b32encode(h)[:8].decode("ascii")
    return re.sub(r"[^A-Z0-9]", "X", code)

# ---------- Upsert & Fetch ----------
async def upsert_user_on_start(user_id: str, username: str, referred_param: Optional[str]) -> Dict[str, Any]:
    """
    - Buat/update user.
    - Set referral_code jika belum ada.
    - Jika ada referred_param (kode referral) & valid → set referred_by jika belum di-set dan bukan diri sendiri.
    - Kembalikan snapshot termasuk derived premium status & referred_count.
    """
    sb = get_client()

    # 1) Ambil user jika ada
    try:
        res = await run_db(sb.table("users").select("*").eq("id", user_id).limit(1).execute)
        user = res.data[0] if res.data else None
    except Exception:
        user = None

    # 2) Siapkan referral_code user (persisten)
    my_code = user.get("referral_code") if user else None
    if not my_code:
        my_code = _make_referral_code(user_id)

    payload = {
        "id": user_id,
        "username": (username or ""),
        "referral_code": my_code,
    }

    # 3) Jika ada referred_param (kode) → resolve ke referrer
    referrer_id: Optional[str] = None
    if referred_param:
        # cari user dengan referral_code itu
        try:
            r = await run_db(sb.table("users").select("id").eq("referral_code", referred_param.upper()).limit(1).execute)
            ref_row = r.data[0] if r.data else None
            if ref_row and ref_row.get("id") and ref_row["id"] != user_id:
                referrer_id = ref_row["id"]
                # set referred_by hanya jika belum ada
                if not user or not user.get("referred_by"):
                    payload["referred_by"] = referrer_id
        except Exception:
            pass

    # 4) Upsert user
    try:
        await run_db(sb.table("users").upsert(payload, on_conflict="id").execute)
    except Exception as e:
        print(f"Error upserting user: {e}")

    # 5) Log referral event (opsional)
    if referrer_id:
        try:
            await run_db(sb.table("referral_events").insert({
                "referred_user_id": user_id,
                "referrer_user_id": referrer_id,
                "source": "start",
            }).execute)
        except Exception:
            pass

    # 6) Ambil snapshot final
    try:
        res2 = await run_db(sb.table("users").select("*").eq("id", user_id).limit(1).execute)
        u = res2.data[0] if res2.data else {}
    except Exception:
        u = payload

    # 7) Hitung derived premium
    now = datetime.now(timezone.utc)
    is_premium = bool(u.get("is_lifetime")) or (
        bool(u.get("premium_until")) and 
        datetime.fromisoformat(u["premium_until"].replace("Z","+00:00")) >= now
    )

    # 8) Hitung referred_count
    try:
        res3 = await run_db(sb.table("users").select("id", count="exact").eq("referred_by", user_id).execute)
        referred_count = getattr(res3, "count", 0) or 0
    except Exception:
        referred_count = 0

    return {
        "id": u.get("id", user_id),
        "username": u.get("username", ""),
        "is_admin": bool(u.get("is_admin")),
        "is_lifetime": bool(u.get("is_lifetime")),
        "premium_until": u.get("premium_until"),  # ISO string atau None
        "is_premium": is_premium,
        "credits": int(u.get("credits", 0)),
        "referral_code": u.get("referral_code", my_code),
        "referred_by": u.get("referred_by"),
        "referred_count": referred_count,
        "created_at": u.get("created_at"),
        "updated_at": u.get("updated_at"),
    }
