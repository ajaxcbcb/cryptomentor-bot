from __future__ import annotations
from datetime import datetime, timezone
from typing import Tuple
import os
import json

from app.supabase_conn import health as sb_health
from app.sb_repo import stats_totals

def get_local_stats() -> Tuple[int, int, str]:
    """Get local JSON statistics"""
    local_path = "data/users_local.json"
    try:
        if os.path.exists(local_path):
            with open(local_path, 'r', encoding='utf-8') as f:
                users = json.load(f)
                total = len(users)
                premium = sum(1 for u in users.values() if u.get('is_premium'))
                return total, premium, local_path
    except Exception:
        pass

    return 0, 0, f"{local_path} (not found)"

def get_supabase_stats() -> Tuple[int, int, bool, str]:
    """Get Supabase statistics and status"""
    try:
        ok, detail = sb_health()
        if ok:
            total, premium = stats_totals()
            return total, premium, True, detail
        else:
            return 0, 0, False, detail

    except Exception as e:
        return 0, 0, False, f"Error: {e}"

def build_admin_panel(autosignals_running: bool = False) -> str:
    """Build comprehensive admin status panel"""

    # Get local stats
    local_total, local_premium, local_path = get_local_stats()

    # Get Supabase stats
    s_total, s_premium, sb_status, sb_detail = get_supabase_stats()

    # Get system info
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    return f"""👑 **ADMIN CONTROL PANEL**

🗄️ **Database Status:**
• Local JSON - Total: {local_total} | Premium: {local_premium}
• Supabase - Total: {s_total} | Premium: {s_premium} {'✅' if sb_status else '❌'}

🎯 **System Status:**
• Auto Signals: {'🟢 RUNNING' if autosignals_running else '🔴 STOPPED'}
• Environment: {'🚀 Production' if os.getenv('REPLIT_DEPLOYMENT') else '🛠️ Development'}

🔎 **Database Details:**
• Local Path: `{local_path}`
• Supabase: {sb_detail}

⏰ **Last Update:** {now}

💡 **Commands:**
/admin diag - Detailed diagnostics
/restart - Restart bot
/refresh_credits - Weekly credit refresh"""

def build_supabase_diagnostics() -> str:
    """Build detailed Supabase diagnostics"""

    diagnostics = []

    # Environment check
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

    diagnostics.append("🔍 **SUPABASE DIAGNOSTICS**\n")
    diagnostics.append(f"• SUPABASE_URL: {'✅ SET' if url else '❌ NOT SET'}")
    diagnostics.append(f"• SUPABASE_SERVICE_KEY: {'✅ SET' if key else '❌ NOT SET'}")

    if url:
        diagnostics.append(f"• URL Check: {'✅ VALID' if 'supabase.co' in url else '❌ INVALID'}")

    # Connection test
    try:
        ok, reason = sb_health()
        diagnostics.append(f"\n🔗 **Connection Test:**")
        diagnostics.append(f"Status: {'✅ SUCCESS' if ok else '❌ FAILED'}")
        diagnostics.append(f"Detail: {reason}")
    except Exception as e:
        diagnostics.append(f"\n🔗 **Connection Test:**")
        diagnostics.append(f"Status: ❌ ERROR")
        diagnostics.append(f"Detail: {e}")

    # RPC tests
    if ok: # Only test RPC if connection is OK
        try:
            total, premium = stats_totals()
            diagnostics.append(f"\n📊 **User Statistics:**")
            diagnostics.append(f"• Supabase RPC (stats_totals): ✅ Total: {total} | Premium: {premium}")
        except Exception as e:
            diagnostics.append(f"\n📊 **User Statistics:**")
            diagnostics.append(f"• Supabase RPC (stats_totals): ❌ {e}")
    else:
        diagnostics.append("\n📊 **User Statistics:**")
        diagnostics.append("• Supabase RPC (stats_totals): Skipped (DB connection failed)")

    # Troubleshooting
    if not ok:
        diagnostics.append("\n💡 **Troubleshooting:**")
        if "not set" in reason.lower() or "missing" in reason.lower():
            diagnostics.append("• Ensure SUPABASE_URL and SUPABASE_SERVICE_KEY are correctly set in Secrets.")
        elif "unauthorized" in reason.lower() or "invalid" in reason.lower():
            diagnostics.append("• Verify the SUPABASE_SERVICE_KEY is a valid Service Role key, not an anon key.")
        elif "404" in reason.lower():
            diagnostics.append("• Check if the necessary RPC functions (e.g., `stats_totals`) exist in your Supabase database.")
        elif "timeout" in reason.lower() or "network" in reason.lower():
            diagnostics.append("• Confirm your server has internet access and check Supabase project status.")
        else:
            diagnostics.append("• Review the error detail and consult Supabase documentation or support.")

    return "\n".join(diagnostics)

def get_admin_status():
    """Get comprehensive admin status"""

    # Supabase health check
    ok, reason = sb_health()
    s_total, s_premium = (0, 0)

    if ok:
        try:
            s_total, s_premium = stats_totals()
        except Exception as e:
            reason = f"stats_totals error: {e}"

    # Environment check
    supabase_url = os.getenv("SUPABASE_URL", "")
    service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    env_ok = bool(supabase_url and service_key)

    # Admin users check
    admin_count = 0
    for i in range(1, 10):
        admin_key = f'ADMIN{i}'
        admin_id = os.getenv(admin_key, "").strip()
        if admin_id and admin_id.lower() != "none" and admin_id.isdigit():
            admin_count += 1

    status_text = f"""🔧 **Admin Status Panel**
📅 {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

🗄️ **Supabase:**
• Status: {'✅ Connected' if ok else '❌ Failed'}
• Response: {reason}
• Environment: {'✅ OK' if env_ok else '❌ Missing vars'}

📊 **Database Stats:**
• Total Users: {s_total:,}
• Premium Users: {s_premium:,}
• Free Users: {s_total - s_premium:,}

👥 **Admin Access:**
• Configured Admins: {admin_count}

💡 **Commands:**
• `/set_credit_all <amount> [--all]` - Set credits
• `/set_premium <user_id> <type> [value]` - Manage premium
• `/sb_status` - Detailed Supabase status

⚙️ **Environment Required:**
• SUPABASE_URL (supabase.co domain)
• SUPABASE_SERVICE_KEY (service role)
• ADMIN1, ADMIN2, etc. (telegram IDs)"""

    return status_text