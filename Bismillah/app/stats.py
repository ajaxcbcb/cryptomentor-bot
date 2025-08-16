
import os, glob, json
from datetime import datetime, timezone
from typing import Tuple, Optional
from .sb_client import supabase, available as sb_available

UTC = timezone.utc

CANDIDATE_DIRS = ["data", "storage", "db", ".", "app/data", "app/storage", "Bismillah/data"]
CANDIDATE_FILES = ["users.json", "users_db.json", "database.json", "db.json", "data.json", "cmai_users.json", "users_local.json"]
GLOB_PATTERNS = ["**/users*.json", "**/*users*.json", "**/db*.json", "**/data*.json"]

def _find_legacy_json_path() -> Tuple[Optional[str], str]:
    reasons = []
    env_path = os.getenv("LEGACY_JSON_PATH")
    if env_path:
        if os.path.isfile(env_path):
            return env_path, f"env:{env_path}"
        reasons.append(f"LEGACY_JSON_PATH set but not found: {env_path}")

    for d in CANDIDATE_DIRS:
        for f in CANDIDATE_FILES:
            p = os.path.join(d, f)
            if os.path.isfile(p):
                return p, f"found:{p}"

    matches = []
    for pattern in GLOB_PATTERNS:
        matches += glob.glob(pattern, recursive=True)
        if len(matches) >= 3:
            break
    for p in matches:
        if os.path.isfile(p):
            return p, f"glob:{p}"

    return None, ("; ".join(reasons) if reasons else "no candidate JSON found")

def _load_json_payload(path: str) -> Tuple[Optional[object], str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip()
            # try standard JSON
            try:
                return json.loads(text), "json"
            except json.JSONDecodeError:
                # try JSON Lines
                items = []
                for i, line in enumerate(text.splitlines(), 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        return None, f"jsonl_error at line {i}: {e}"
                if items:
                    # normalisasi: jadikan {"users":[...]} agar parser bawah kompatibel
                    return {"users": items}, "jsonl"
                return None, "empty_file"
    except FileNotFoundError:
        return None, "not_found"
    except Exception as e:
        return None, f"read_error:{e}"

def _parse_users_from_json_payload(payload) -> list:
    if payload is None:
        return []
    if isinstance(payload, dict):
        users = payload.get("users", payload)
        if isinstance(users, dict):
            return list(users.values())
        if isinstance(users, list):
            return users
        return []
    if isinstance(payload, list):
        return payload
    return []

def _is_premium_active_local(u: dict) -> bool:
    try:
        if u.get("is_lifetime"):
            return True
        if u.get("is_premium") and u.get("premium_until"):
            val = u["premium_until"]
            if isinstance(val, (int, float)):
                dt = datetime.fromtimestamp(val, tz=UTC)
            else:
                dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            return dt > datetime.now(UTC)
    except Exception:
        pass
    return False

def legacy_json_totals_with_status(explicit_path: Optional[str]=None, data_obj: Optional[dict]=None) -> Tuple[int,int,str,str]:
    """
    return: total, premium, path_info, detail
    """
    if data_obj is not None:
        users = _parse_users_from_json_payload(data_obj)
        return len(users), sum(1 for u in users if _is_premium_active_local(u)), "memory", "ok:memory"

    path = explicit_path
    path_info = ""
    if not path:
        path, path_info = _find_legacy_json_path()
    else:
        path_info = f"explicit:{path}"

    if not path:
        return 0, 0, "-", f"not_found | {path_info}"

    payload, how = _load_json_payload(path)
    if payload is None:
        return 0, 0, path, f"load_failed:{how}"

    users = _parse_users_from_json_payload(payload)
    total = len(users)
    premium = sum(1 for u in users if _is_premium_active_local(u))
    return total, premium, path, f"ok:{how}"

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

def build_system_status(auto_signals_running: bool,
                        legacy_json_path: Optional[str]=None,
                        legacy_data: Optional[dict]=None) -> str:
    legacy_total, legacy_premium, legacy_path, legacy_detail = legacy_json_totals_with_status(
        explicit_path=legacy_json_path, data_obj=legacy_data
    )
    ok, db_detail = health()
    supa_total, supa_premium = (0, 0)
    if ok:
        supa_total, supa_premium = get_supabase_totals()

    db_text = "✅" if ok else "❌"
    auto_text = "🟢 RUNNING" if auto_signals_running else "🔴 STOPPED"
    now_utc = datetime.now(UTC).strftime("%H:%M:%S UTC")

    return (
        "📊 System Status\n\n"
        f"🗄️ Database: SUPABASE - {db_text}\n"
        f"🎯 Auto Signals: {auto_text}\n\n"
        "📊 User Statistics:\n"
        f"• Local JSON - Total Users: {legacy_total} | Premium: {legacy_premium} (path: {legacy_path})\n"
        f"• Supabase  - Total Users: {supa_total} | Premium: {supa_premium}\n\n"
        f"⏰ Last Update: {now_utc}\n"
        f"ℹ️ Local Detail: {legacy_detail[:220]}\n"
        f"ℹ️ DB Detail: {db_detail[:220]}"
    )
