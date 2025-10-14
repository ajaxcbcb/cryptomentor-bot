
# app/health.py
from __future__ import annotations
import os
import httpx
from typing import Tuple

TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "10.0"))

def _short(s: str, n: int = 50) -> str:
    return s[:n] + "..." if len(s) > n else s

def check_binance() -> Tuple[bool, str]:
    """Check Binance API connectivity"""
    url = "https://api.binance.com/api/v3/ping"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url)
        if r.status_code == 200:
            return True, "200 OK"
        return False, f"{r.status_code} {_short(r.text, 80)}"
    except Exception as e:
        return False, f"request_error: {e}"

def check_binance_futures() -> Tuple[bool, str]:
    """Check Binance Futures API connectivity"""
    url = "https://fapi.binance.com/fapi/v1/ping"
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url)
        if r.status_code == 200:
            return True, "200 OK"
        return False, f"{r.status_code} {_short(r.text, 80)}"
    except Exception as e:
        return False, f"request_error: {e}"

def check_openai() -> Tuple[bool, str]:
    """Check OpenAI API connectivity"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return False, "missing OPENAI_API_KEY"
    
    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(url, headers=headers)
        if r.status_code == 200:
            return True, "200 OK"
        return False, f"{r.status_code} {_short(r.text, 80)}"
    except Exception as e:
        return False, f"request_error: {e}"

def check_supabase() -> Tuple[bool, str]:
    """Check Supabase connectivity"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return False, "missing SUPABASE_URL or SUPABASE_KEY"
    
    health_url = f"{url.rstrip('/')}/rest/v1/rpc/hc"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.post(health_url, json={}, headers=headers)
        if r.status_code == 200:
            return True, "200 OK"
        return False, f"{r.status_code} {_short(r.text, 80)}"
    except Exception as e:
        return False, f"request_error: {e}"

# Main health check function
def run_health_checks() -> dict:
    """Run all health checks and return status"""
    checks = {}
    
    # Binance APIs
    checks["binance_spot"] = check_binance()
    checks["binance_futures"] = check_binance_futures()
    
    # Other services
    checks["openai"] = check_openai()
    checks["supabase"] = check_supabase()
    
    return checks
