
import os
from typing import List, Tuple
import httpx

from .sb_client import available as sb_available, health as sb_health

TIMEOUT = 4.0

def _short(msg: str, n: int = 160) -> str:
    s = str(msg)
    return s if len(s) <= n else (s[: n - 3] + "...")

def check_supabase() -> Tuple[bool, str]:
    if not sb_available():
        return False, "client_not_initialized (cek SUPABASE_URL/KEY)"
    ok, detail = sb_health()
    return ok, _short(detail)

def check_coinapi() -> Tuple[bool, str]:
    base = os.getenv("COINAPI_BASE_URL", "https://rest.coinapi.io")
    # PRIORITAS BARU: COINAPI_API_KEY, fallback COINAPI_KEY
    key = os.getenv("COINAPI_API_KEY") or os.getenv("COINAPI_KEY")
    if not key:
        return False, "missing COINAPI_API_KEY"
    url = f"{base.rstrip('/')}/v1/assets?limit=1"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers={"X-CoinAPI-Key": key})
        if r.status_code == 200:
            return True, "200 OK"
        return False, f"{r.status_code} {_short(r.text, 80)}"
    except Exception as e:
        return False, f"request_error: {e}"

def check_cmc() -> Tuple[bool, str]:
    base = os.getenv("CMC_BASE_URL", "https://pro-api.coinmarketcap.com")
    key = os.getenv("CMC_API_KEY") or os.getenv("CMC_PRO_API_KEY")
    if not key:
        return False, "missing CMC_API_KEY"
    url = f"{base.rstrip('/')}/v1/cryptocurrency/map?limit=1"
    headers = {"X-CMC_PRO_API_KEY": key}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=headers)
        if r.status_code == 200:
            try:
                j = r.json()
                code = (j.get("status") or {}).get("error_code", 0)
                if code == 0:
                    return True, "200 OK"
                return False, f"status_error:{code}"
            except Exception:
                return True, "200 OK (no-json-parse)"
        return False, f"{r.status_code} {_short(r.text, 80)}"
    except Exception as e:
        return False, f"request_error: {e}"



# === NEW: OpenAI ===
def check_openai() -> Tuple[bool, str]:
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return False, "missing OPENAI_API_KEY"
    url = f"{base.rstrip('/')}/v1/models"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=headers)
        if r.status_code == 200:
            return True, "200 OK"
        # Banyak kasus 401/403 kalau key salah/expired
        return False, f"{r.status_code} {_short(r.text, 80)}"
    except Exception as e:
        return False, f"request_error: {e}"

def services_status_lines() -> List[str]:
    SERVICES = [
        ("Supabase", check_supabase),
        ("CoinAPI", check_coinapi),
        ("CoinMarketCap", check_cmc),
        ("OpenAI", check_openai),
    ]
    lines: List[str] = []
    for name, fn in SERVICES:
        ok, msg = fn()
        badge = "✅ Connected" if ok else f"❌ {_short(msg)}"
        lines.append(f"{name}: {badge}")
    return lines
