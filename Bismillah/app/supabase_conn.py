from __future__ import annotations
import os
from functools import lru_cache
from typing import Tuple
from supabase import create_client, Client
import httpx

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def _assert_env():
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Set SUPABASE_URL & SUPABASE_SERVICE_KEY (Service role).")

def env_ok() -> Tuple[bool, str]:
    """Check if environment variables are properly set"""
    if not SUPABASE_URL:
        return False, "SUPABASE_URL belum diset"
    if "supabase.co" not in SUPABASE_URL:
        return False, f"SUPABASE_URL tidak valid: {SUPABASE_URL}"
    if not SUPABASE_SERVICE_KEY:
        return False, "SUPABASE_SERVICE_KEY belum diset"
    return True, "Environment OK"

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    _assert_env()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def health() -> Tuple[bool, str]:
    """Health check using RPC hc() function"""
    try:
        env_check, env_info = env_ok()
        if not env_check:
            return False, env_info

        cli = get_supabase_client()
        try:
            cli.rpc("hc").execute()  # fungsi hc() sudah dibuat di DB
            return True, "rpc(hc): OK"
        except Exception as rpc_error:
            # Fallback ke REST ping
            r = httpx.get(
                f"{SUPABASE_URL}/rest/v1/",
                headers={
                    "apikey": SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
                },
                timeout=6.0,
            )
            if r.status_code in (200, 404):
                return True, f"rest {r.status_code} (rpc unavailable)"
            if r.status_code in (401, 403):
                return False, f"{r.status_code} unauthorized (gunakan Service role key)"
            return False, f"{r.status_code} {r.text[:120]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"