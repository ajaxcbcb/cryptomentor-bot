
# app/sb_client.py
import os, httpx
from typing import Optional, Tuple
from supabase import create_client, Client

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = <REDACTED_SUPABASE_KEY>

_client: Optional[Client] = None

def supabase() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY (Service role secret)")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client

def health() -> Tuple[bool, str]:
    try:
        # coba RPC 'hc' (opsional)
        try:
            supabase().rpc("hc").execute()
            return True, "rpc(hc): OK"
        except Exception:
            # fallback ping REST
            r = httpx.get(f"{SUPABASE_URL}/rest/v1/", headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            }, timeout=6.0)
            if r.status_code in (200, 404):
                return True, f"rest ping {r.status_code}"
            if r.status_code in (401, 403):
                return False, f"{r.status_code} unauthorized (use Service role key)"
            return False, f"{r.status_code} {r.text[:100]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

# ====== WEEKLY CREDITS RPC WRAPPERS (dipakai bot) ======
WEEKLY_FREE_CREDITS = int(os.getenv("WEEKLY_FREE_CREDITS", "100"))

def upsert_user_with_weekly_reset_rpc(telegram_id: int, username: str=None, first_name: str=None, last_name: str=None):
    payload = {
        "p_telegram_id": int(telegram_id),
        "p_username": username,
        "p_first_name": first_name,
        "p_last_name": last_name,
        "p_weekly_quota": WEEKLY_FREE_CREDITS,
    }
    return supabase().rpc("upsert_user_with_weekly_reset", payload).execute().data

def enforce_weekly_reset_calendar_rpc(telegram_id: int):
    payload = { "p_telegram_id": int(telegram_id), "p_weekly_quota": WEEKLY_FREE_CREDITS }
    return supabase().rpc("enforce_weekly_reset_calendar", payload).execute().data
