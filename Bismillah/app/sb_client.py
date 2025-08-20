
# app/sb_client.py
from __future__ import annotations
import os, re, time
from typing import Tuple, Optional
from supabase import create_client, Client
import httpx

# ====== ENV RESOLUTION ======
def _env(name: str) -> Optional[str]:
    v = os.getenv(name)
    return v.strip() if v and v.strip() else None

def _resolve_url() -> str:
    url = _env("SUPABASE_URL") or ""
    if not url:
        raise RuntimeError("Missing SUPABASE_URL")
    return url.rstrip("/")

def _resolve_service_key() -> str:
    # Prioritas: SERVICE (baru) → fallback ke nama lama
    key = (
        _env("SUPABASE_SERVICE_KEY")
        or _env("SERVICE_ROLE_KEY")
        or _env("SUPABASE_SECRET_KEY")
        or _env("SUPABASE_KEY")
        or ""
    )
    if not key:
        raise RuntimeError("Missing SUPABASE_SERVICE_KEY (service role)")
    return key

def _mask(s: str, head: int = 6, tail: int = 6) -> str:
    if not s: return ""
    if len(s) <= head + tail + 3:
        return s[0] + "***" + s[-1]
    return f"{s[:head]}…{s[-tail:]}"

# ====== CLIENT ======
_supabase: Optional[Client] = None
_diagnostics: str = ""

def init() -> Client:
    global _supabase, _diagnostics
    url = _resolve_url()
    key = _resolve_service_key()

    # Validasi URL
    if not re.search(r"\.supabase\.co$", url):
        # tetap izinkan self-host, tapi beri catatan
        _note = "URL tidak standar (.supabase.co). Pastikan benar."
    else:
        _note = "ok"

    _supabase = create_client(url, key)
    _diagnostics = f"url={url} key(service_role)={_mask(key)} note={_note}"
    return _supabase

def supabase() -> Client:
    global _supabase
    if _supabase is None:
        init()
    return _supabase  # type: ignore

def available() -> bool:
    try:
        return supabase() is not None
    except Exception:
        return False

def diagnostics() -> str:
    return _diagnostics

# ====== HEALTH CHECK ======
def health() -> Tuple[bool, str]:
    """
    Coba RPC 'hc' jika ada; bila 401/403, kemungkinan key salah (anon).
    """
    try:
        cli = supabase()
        try:
            res = cli.rpc("hc").execute()
            # res.data bisa apa saja; yang penting 200 OK
            return True, "hc rpc OK"
        except Exception as e:
            # fallback: GET /rest/v1 root (harus 404/200; 401 → key salah)
            url = _resolve_url().rstrip("/") + "/rest/v1/"
            hdr = {"apikey": _resolve_service_key(), "Authorization": f"Bearer {_resolve_service_key()}"}
            try:
                r = httpx.get(url, headers=hdr, timeout=6.0)
                if r.status_code in (200, 404):
                    return True, f"rest ping {r.status_code}"
                elif r.status_code in (401, 403):
                    return False, f"{r.status_code} unauthorized (pakai Service Role?)"
                else:
                    return False, f"{r.status_code} {r.text[:80]}"
            except Exception as ex:
                return False, f"health error: {ex}"
    except Exception as ex:
        return False, f"init error: {ex}"

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
    return supabase().rpc("upsert_user_with_weekly_reset", payload).execute().data  # type: ignore

def enforce_weekly_reset_calendar_rpc(telegram_id: int):
    payload = { "p_telegram_id": int(telegram_id), "p_weekly_quota": WEEKLY_FREE_CREDITS }
    return supabase().rpc("enforce_weekly_reset_calendar", payload).execute().data  # type: ignore
