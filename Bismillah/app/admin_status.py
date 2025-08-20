
# app/admin_status.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Tuple
from .supabase_conn import health as sb_health
from .sb_repo import stats_totals
import os
import json

def get_local_stats() -> Tuple[int, int, str]:
    """Get local JSON stats for comparison"""
    try:
        local_path = "data/users_local.json"
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                data = json.load(f)
                users = data.get("users", [])
                total = len(users)
                premium = sum(1 for u in users if u.get("is_premium", False))
                return total, premium, local_path
        return 0, 0, "data/users_local.json (not found)"
    except Exception as e:
        return 0, 0, f"local error: {e}"

def build_admin_panel(autosignals_running: bool = False) -> str:
    """Build comprehensive admin status panel"""
    # Supabase health check
    ok, reason = sb_health()
    s_total, s_premium = (0, 0)
    
    if ok:
        try:
            s_total, s_premium = stats_totals()
        except Exception as e:
            reason = f"stats_totals error: {e}"
            ok = False
    
    # Local stats for comparison
    local_total, local_premium, local_path = get_local_stats()
    
    # Environment info
    supabase_url = os.getenv("SUPABASE_URL", "NOT SET")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "NOT SET")
    
    # Mask sensitive info for display
    url_display = "✅ SET" if supabase_url != "NOT SET" else "❌ NOT SET"
    if supabase_url != "NOT SET" and "supabase.co" not in supabase_url:
        url_display = "❌ INVALID"
    
    key_display = "✅ SET" if supabase_key != "NOT SET" else "❌ NOT SET"
    
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    
    return (
        "👑 **ADMIN CONTROL PANEL**\n\n"
        
        "🔐 **Environment Variables:**\n"
        f"• SUPABASE_URL: {url_display}\n"
        f"• SUPABASE_SERVICE_KEY: {key_display}\n\n"
        
        "🗄️ **Database Status:**\n"
        f"• Supabase: {'✅ ONLINE' if ok else '❌ OFFLINE'}\n"
        f"• Connection: {('OK' if ok else reason)}\n\n"
        
        "📊 **User Statistics:**\n"
        f"• **Supabase** - Total: {s_total} | Premium: {s_premium}\n"
        f"• **Local JSON** - Total: {local_total} | Premium: {local_premium}\n"
        f"• Local Path: `{local_path}`\n\n"
        
        "🎯 **System Status:**\n"
        f"• Auto Signals: {'🟢 RUNNING' if autosignals_running else '🔴 STOPPED'}\n"
        f"• Environment: {'🚀 Production' if os.getenv('REPLIT_DEPLOYMENT') else '🛠️ Development'}\n\n"
        
        f"⏰ **Last Update:** {now}"
    )

def build_supabase_diagnostics() -> str:
    """Build detailed Supabase diagnostics"""
    ok, reason = sb_health()
    
    # Environment check
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    diagnostics = "🔍 **SUPABASE DIAGNOSTICS**\n\n"
    
    # URL validation
    if not supabase_url:
        diagnostics += "❌ SUPABASE_URL not set\n"
    elif "supabase.co" not in supabase_url:
        diagnostics += f"❌ SUPABASE_URL invalid: {supabase_url[:50]}...\n"
    else:
        diagnostics += f"✅ SUPABASE_URL valid: {supabase_url[:30]}...\n"
    
    # Key validation
    if not supabase_key:
        diagnostics += "❌ SUPABASE_SERVICE_KEY not set\n"
    else:
        diagnostics += "✅ SUPABASE_SERVICE_KEY set\n"
    
    # Connection test
    diagnostics += f"\n🔗 **Connection Test:**\n"
    diagnostics += f"Status: {'✅ SUCCESS' if ok else '❌ FAILED'}\n"
    diagnostics += f"Detail: {reason}\n\n"
    
    # Troubleshooting
    if not ok:
        diagnostics += "💡 **Troubleshooting:**\n"
        if "not set" in reason:
            diagnostics += "• Add missing environment variables in Secrets\n"
        elif "unauthorized" in reason:
            diagnostics += "• Use Service Role key, not anon key\n"
        elif "404" in reason:
            diagnostics += "• Check if required RPC functions exist in DB\n"
        else:
            diagnostics += "• Check network connectivity and Supabase project status\n"
    
    return diagnostics
