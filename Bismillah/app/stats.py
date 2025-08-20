import os, glob, json
from datetime import datetime, timezone
from typing import Tuple, Optional, Any
from .sb_client import supabase, available as sb_available
from .health import services_status_lines

UTC = timezone.utc

def _coerce_json(obj: Any) -> Any:
    """
    Force anything to become JSON object (dict/list) if possible:
    - If string: try json.loads; if failed, try JSON Lines.
    - If already dict/list: return as is.
    - Otherwise: return None.
    """
    if isinstance(obj, (dict, list)) or obj is None:
        return obj
    if isinstance(obj, str):
        s = obj.strip()
        # try regular JSON
        try:
            return json.loads(s)
        except Exception:
            pass
        # try JSON Lines
        try:
            items = []
            for line in s.splitlines():
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))
            return {"users": items} if items else None
        except Exception:
            return None
    return None

def _normalize_users_structure(payload: Any) -> list:
    """
    Accept any format -> return list of user dicts.
    - dict with 'users' key: use that
    - dict-of-dict: take values()
    - list: directly
    - otherwise: []
    """
    payload = _coerce_json(payload)
    if isinstance(payload, dict):
        # Check for common keys that contain user data
        if "premium_users" in payload:
            users = payload["premium_users"]
        elif "users" in payload:
            users = payload["users"]
        else:
            users = payload

        if isinstance(users, dict):
            return [v for v in users.values() if isinstance(v, dict)]
        if isinstance(users, list):
            return [u for u in users if isinstance(u, dict)]
        return []
    if isinstance(payload, list):
        return [u for u in payload if isinstance(u, dict)]
    return []

def _is_premium_active_local(u: dict) -> bool:
    try:
        if u.get("is_lifetime"):
            return True
        # Check various premium indicators
        if u.get("is_premium"):
            # If subscription_end exists, check if it's valid
            if "subscription_end" in u and u["subscription_end"]:
                val = u["subscription_end"]
                if isinstance(val, (int, float)):
                    dt = datetime.fromtimestamp(val, tz=UTC)
                else:
                    dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
                return dt > datetime.now(UTC)
            # If no subscription_end but is_premium=1, consider active
            return True
        # Legacy check for premium_until
        if u.get("premium_until"):
            val = u["premium_until"]
            if isinstance(val, (int, float)):
                dt = datetime.fromtimestamp(val, tz=UTC)
            else:
                dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            return dt > datetime.now(UTC)
    except Exception:
        pass
    return bool(u.get("is_premium"))

def health() -> Tuple[bool, str]:
    """Health check for Supabase connection"""
    if not sb_available():
        return False, "Supabase client not available"

    try:
        # Use hc() RPC for health check
        result = supabase.rpc("hc").execute()
        if result.data:
            return True, "Connected via RPC hc()"
        return False, "RPC hc() returned empty"
    except Exception as e:
        return False, f"RPC error: {str(e)}"

def get_supabase_totals() -> Tuple[int, int]:
    if not sb_available():
        return 0, 0
    try:
        res = supabase.rpc("stats_totals").execute()
        row = (res.data[0] if isinstance(res.data, list) and res.data else
               res.data if isinstance(res.data, dict) else
               {"total_users": 0, "premium_users": 0})
        return int(row.get("total_users", 0)), int(row.get("premium_users", 0))
    except Exception as e:
        print(f"Error getting Supabase totals: {e}")
        return 0, 0

def get_legacy_json_totals(path: Optional[str]=None, data_obj: Optional[Any]=None) -> Tuple[int,int]:
    """
    Count Total & Premium from:
    - data_obj (in-memory) or
    - file path (JSON / string JSON / JSONL).
    Safe against string formats.
    """
    payload = None
    if data_obj is not None:
        payload = data_obj
    elif path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            payload = _coerce_json(text)
        except FileNotFoundError:
            payload = None
        except Exception:
            payload = None

    users = _normalize_users_structure(payload)
    total = len(users)
    premium = sum(1 for u in users if _is_premium_active_local(u))
    return total, premium

def build_system_status(auto_signals_running: bool,
                        legacy_json_path: Optional[str]=None,
                        legacy_data: Optional[Any]=None) -> str:
    """Build comprehensive system status"""

    # Protect against unexpected errors
    legacy_err = ""
    try:
        legacy_total, legacy_premium = get_legacy_json_totals(legacy_json_path, legacy_data)
    except Exception as e:
        legacy_total, legacy_premium = 0, 0
        legacy_err = f"(local-error: {e})"

    ok, db_detail = health()
    supa_total, supa_premium = (0, 0)
    if ok:
        supa_total, supa_premium = get_supabase_totals()

    db_text = "✅" if ok else "❌"
    auto_text = "🟢 RUNNING" if auto_signals_running else "🔴 STOPPED"
    now_utc = datetime.now(UTC).strftime("%H:%M:%S UTC")

    # Get integrations status
    svc_lines = services_status_lines()
    svc_block = "🔌 Integrations:\n" + "\n".join(f"• {line}" for line in svc_lines) + "\n\n" if svc_lines else ""

    # Build final status message
    json_path_display = legacy_json_path or "no path specified"
    return (
        "📊 System Status\n\n"
        f"🗄️ Database: SUPABASE - {db_text}\n"
        f"🎯 Auto Signals: {auto_text}\n\n"
        "📊 User Statistics:\n"
        f"• Local JSON - Total Users: {legacy_total} | Premium: {legacy_premium}"
        + (f" (path: {json_path_display})" if legacy_json_path else "")
        + (f" {legacy_err}" if legacy_err else "")
        + "\n"
        f"• Supabase  - Total Users: {supa_total} | Premium: {supa_premium}\n\n"
        f"{svc_block}"
        f"⏰ Last Update: {now_utc}\n"
        f"ℹ️ DB Detail: {db_detail[:220]}"
    )