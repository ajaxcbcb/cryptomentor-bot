
import logging
from typing import Dict, Any, Optional
from .sb_client import supabase_client

logger = logging.getLogger(__name__)

def fetch_bot_stats() -> Optional[Dict[str, Any]]:
    """
    Fetch bot statistics from Supabase view v_bot_stats
    Returns: Dict with keys: total_users, premium_users, banned_users, active_today, total_credits
    """
    try:
        logger.info("🔍 Fetching bot statistics from Supabase...")
        
        # Query the v_bot_stats view
        stats = supabase_client.query_view(
            "v_bot_stats",
            select="total_users,premium_users,banned_users,active_today,total_credits"
        )
        
        if stats is None:
            logger.error("❌ Failed to fetch bot statistics from Supabase")
            return None
        
        logger.info("✅ Successfully fetched bot statistics from Supabase")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error fetching bot statistics: {e}")
        return None

def log_stats_on_startup():
    """
    Log bot statistics to console during startup
    """
    print("\n" + "="*50)
    print("🤖 CryptoMentor AI Bot Statistics")
    print("="*50)
    
    # Test Supabase connection first
    is_connected, conn_msg = supabase_client.test_connection()
    if is_connected:
        print(f"✅ Supabase: {conn_msg}")
    else:
        print(f"❌ Supabase: {conn_msg}")
        print("⚠️  Statistics unavailable - Check Supabase configuration")
        print("="*50)
        return
    
    # Fetch statistics
    stats = fetch_bot_stats()
    
    if stats:
        print(f"📊 Total Users: {stats.get('total_users', 0):,}")
        print(f"💎 Premium Users: {stats.get('premium_users', 0):,}")
        print(f"🚫 Banned Users: {stats.get('banned_users', 0):,}")
        print(f"🔥 Active Today: {stats.get('active_today', 0):,}")
        print(f"💰 Total Credits: {stats.get('total_credits', 0):,}")
    else:
        print("❌ Failed to load statistics from Supabase")
        print("💡 Check view 'v_bot_stats' exists in Supabase")
    
    print("="*50)

def format_stats_message() -> str:
    """
    Format bot statistics for Telegram message
    Returns formatted markdown string
    """
    stats = fetch_bot_stats()
    
    if not stats:
        return """❌ **Bot Statistics Error**

Failed to fetch statistics from Supabase.
Please check database connection and ensure view `v_bot_stats` exists.

💡 **Troubleshooting:**
• Verify SUPABASE_URL and SUPABASE_SERVICE_KEY
• Check if view `public.v_bot_stats` exists
• Ensure service key has read permissions"""
    
    # Format the statistics message
    message = f"""📊 **CryptoMentor AI Statistics**

👥 **Total Users:** `{stats.get('total_users', 0):,}`
💎 **Premium Users:** `{stats.get('premium_users', 0):,}`
🚫 **Banned Users:** `{stats.get('banned_users', 0):,}`
🔥 **Active Today:** `{stats.get('active_today', 0):,}`
💰 **Total Credits:** `{stats.get('total_credits', 0):,}`

📈 **Premium Rate:** `{(stats.get('premium_users', 0) / max(stats.get('total_users', 1), 1) * 100):.1f}%`
🎯 **Active Rate:** `{(stats.get('active_today', 0) / max(stats.get('total_users', 1), 1) * 100):.1f}%`

🗄️ **Data Source:** Supabase `v_bot_stats`
⏰ **Updated:** Just now"""
    
    return message

def get_stats_summary() -> Dict[str, int]:
    """
    Get a simple dictionary of key statistics
    Returns: Dict with basic stats or zeros if failed
    """
    stats = fetch_bot_stats()
    
    if not stats:
        return {
            'total_users': 0,
            'premium_users': 0,
            'banned_users': 0,
            'active_today': 0,
            'total_credits': 0
        }
    
    return {
        'total_users': stats.get('total_users', 0),
        'premium_users': stats.get('premium_users', 0),
        'banned_users': stats.get('banned_users', 0),
        'active_today': stats.get('active_today', 0),
        'total_credits': stats.get('total_credits', 0)
    }
