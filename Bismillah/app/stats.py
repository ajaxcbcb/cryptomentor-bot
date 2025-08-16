
import json
from datetime import datetime, timezone
from typing import Tuple, Optional
import os
import sys

# Add the current directory to the Python path to import supabase_conn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.supabase_conn import get_supabase_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase connection not available for stats")

TZ = timezone.utc
ALLOWED_USER_FIELDS = {"telegram_id", "username", "first_name", "last_name", "is_premium", "is_lifetime", "premium_until", "credits"}

def _parse_users_from_json_payload(payload) -> list:
    """Parse users from various JSON payload formats"""
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
    """Check if user has active premium status locally"""
    if not isinstance(u, dict):
        return False
    if u.get("is_lifetime"):
        return True
    if u.get("is_premium") and u.get("premium_until"):
        try:
            val = u["premium_until"]
            if isinstance(val, (int, float)):
                dt = datetime.fromtimestamp(val, tz=TZ)
            else:
                dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
            return dt > datetime.now(TZ)
        except Exception:
            return False
    return False

def get_legacy_json_totals(path: Optional[str]=None, data_obj: Optional[dict]=None) -> Tuple[int, int]:
    """Get user totals from legacy JSON storage"""
    payload = None
    if data_obj is not None:
        payload = data_obj
    elif path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            payload = None
    
    users = _parse_users_from_json_payload(payload)
    total = len(users)
    premium = sum(1 for u in users if _is_premium_active_local(u))
    return total, premium

def get_supabase_totals() -> Tuple[int, int]:
    """Get user totals from Supabase using stats_totals() function"""
    if not SUPABASE_AVAILABLE:
        return 0, 0
    
    try:
        supabase = get_supabase_client()
        res = supabase.rpc("stats_totals").execute()
        
        row = (res.data[0] if isinstance(res.data, list) and res.data else
               res.data if isinstance(res.data, dict) else
               {"total_users": 0, "premium_users": 0})
        
        return int(row.get("total_users", 0)), int(row.get("premium_users", 0))
    except Exception as e:
        print(f"Error getting Supabase totals: {e}")
        return 0, 0

def ping_supabase_ok() -> bool:
    """Check if Supabase connection is working"""
    if not SUPABASE_AVAILABLE:
        return False
    
    try:
        supabase = get_supabase_client()
        supabase.table("users").select("id").limit(1).execute()
        return True
    except Exception:
        return False

def build_system_status(auto_signals_running: bool, legacy_json_path: Optional[str]=None, legacy_data: Optional[dict]=None) -> str:
    """Build comprehensive system status message"""
    legacy_total, legacy_premium = get_legacy_json_totals(legacy_json_path, legacy_data)
    supa_total, supa_premium = get_supabase_totals()
    db_text = "✅" if ping_supabase_ok() else "❌"
    auto_text = "🟢 RUNNING" if auto_signals_running else "🔴 STOPPED"

    return f"""📊 **System Status**

🗄️ **Database**: SUPABASE - {db_text}
🎯 **Auto Signals**: {auto_text}

📊 **User Statistics:**
• **Local JSON** - Total Users: {legacy_total} | Premium: {legacy_premium}
• **Supabase**  - Total Users: {supa_total} | Premium: {supa_premium}

⏰ **Last Update**: {datetime.now().strftime('%H:%M:%S WIB')}"""
