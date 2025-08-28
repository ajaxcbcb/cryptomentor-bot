import os
from .stats import build_system_status
from datetime import datetime

# Default to correct backup file; can be overridden via Secrets: LEGACY_JSON_PATH
DEFAULT_LEGACY_PATH = "premium_users_backup_20250802_130229.json"
LEGACY_JSON_PATH = os.getenv("LEGACY_JSON_PATH", DEFAULT_LEGACY_PATH)

# Try to import autosignal function, fallback to True if not available
try:
    from .autosignal import is_auto_signal_running
    _auto = is_auto_signal_running()
except Exception:
    _auto = True

def get_admin_panel_text() -> str:
    """Get comprehensive admin panel status text with combined user counts"""
    try:
        # Database status check
        from app.db_router import db_status
        status = db_status()

        # Get system health
        from app.health import get_health_status
        health = get_health_status()

        # Get combined user counts from both sources
        total_users_combined = 0
        total_premium_combined = 0
        supabase_users = 0
        supabase_premium = 0
        local_users = 0
        local_premium = 0

        # Get Supabase totals
        try:
            from app.stats import get_supabase_totals
            supabase_users, supabase_premium = get_supabase_totals()
        except Exception as e:
            print(f"Error getting Supabase totals: {e}")

        # Get Local SQLite totals
        try:
            from database import Database
            db = Database()

            # Count total local users
            db.cursor.execute("SELECT COUNT(*) FROM users")
            local_users = db.cursor.fetchone()[0] or 0

            # Count premium local users
            db.cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1")
            local_premium = db.cursor.fetchone()[0] or 0

            db.close()
        except Exception as e:
            print(f"Error getting Local SQLite totals: {e}")

        # Calculate combined totals (avoiding duplicates by assuming Supabase is primary)
        # We'll show both sources separately and combined estimate
        total_users_combined = max(supabase_users, local_users) + min(supabase_users, local_users) // 2
        total_premium_combined = max(supabase_premium, local_premium) + min(supabase_premium, local_premium) // 2

        # Format status message
        mode_icon = "🗄️" if status['mode'] == 'supabase' else "📁"
        db_status_text = f"{mode_icon} {status['mode'].title()}: {status['note']}"

        # API status
        api_status = []
        for api, ok in health.items():
            icon = "✅" if ok else "❌"
            api_status.append(f"{icon} {api.upper()}")

        api_status_text = " | ".join(api_status)

        message = f"""🤖 **CryptoMentor AI System Status**

📊 **Database:**
{db_status_text}

👥 **User Statistics (Combined):**
• 📊 **Total Combined**: ~{total_users_combined} users
• 💎 **Premium Combined**: ~{total_premium_combined} users

📈 **Breakdown by Source:**
• 🗄️ **Supabase**: {supabase_users} users ({supabase_premium} premium)
• 📁 **Local SQLite**: {local_users} users ({local_premium} premium)

🌐 **APIs:** {api_status_text}

⏰ **Last Check:** {datetime.now().strftime('%H:%M:%S WIB')}

💡 **Note:** Combined total estimates unique users across both databases"""

        return message

    except Exception as e:
        return f"""🤖 **CryptoMentor AI System Status**

❌ **Error loading status:** {str(e)}

⏰ **Time:** {datetime.now().strftime('%H:%M:%S WIB')}"""