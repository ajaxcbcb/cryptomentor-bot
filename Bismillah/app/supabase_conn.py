import os
import httpx
from functools import lru_cache
from typing import Tuple

# Pastikan pydantic v2 OK sebelum import supabase
try:
    from app.fix_pydantic import ensure as _ensure_pyd
    _ensure_pyd()
except Exception as e:
    print("[pydantic-fix] warn:", e)

from supabase import create_client, Client

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def _assert_env():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Set SUPABASE_URL & SUPABASE_SERVICE_KEY (Service role).")

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    _assert_env()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def health() -> Tuple[bool, str]:
    try:
        s = get_supabase_client()
        try:
            s.rpc("hc").execute()
            return True, "rpc(hc): OK"
        except Exception:
            pass

        r = httpx.get(
            f"{SUPABASE_URL}/rest/v1/",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
            },
            timeout=6.0
        )

        if r.status_code in (200, 404):
            return True, f"rest {r.status_code}"
        if r.status_code in (401, 403):
            return False, f"{r.status_code} unauthorized (Service role?)"
        return False, f"{r.status_code} {r.text[:100]}"

    except Exception as e:
        return False, f"{type(e).__name__}: {e}"