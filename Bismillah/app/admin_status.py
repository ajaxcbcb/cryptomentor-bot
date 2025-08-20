
# app/admin_status.py
import os
from typing import Dict, Any
from app.supabase_conn import get_supabase_client, health
from app.sb_repo import stats_totals

ADMIN_IDS = {int(x.strip()) for x in (os.getenv("ADMIN_IDS", "").split(",") if os.getenv("ADMIN_IDS") else [])}

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

def get_admin_status() -> Dict[str, Any]:
    """Get comprehensive admin status"""
    try:
        # Supabase health check
        sb_ok, sb_detail = health()
        
        # Get user stats
        total_users = premium_users = 0
        if sb_ok:
            try:
                total_users, premium_users = stats_totals()
            except Exception as e:
                sb_detail = f"stats error: {e}"
        
        # Environment checks
        env_status = {
            'SUPABASE_URL': bool(os.getenv('SUPABASE_URL')),
            'SUPABASE_SERVICE_KEY': bool(os.getenv('SUPABASE_SERVICE_KEY')),
            'ADMIN_IDS': bool(os.getenv('ADMIN_IDS')),
            'REFERRAL_REQUIRED': os.getenv('REFERRAL_REQUIRED', 'false'),
            'WELCOME_CREDITS': os.getenv('WELCOME_CREDITS', '100'),
        }
        
        return {
            'supabase_healthy': sb_ok,
            'supabase_detail': sb_detail,
            'total_users': total_users,
            'premium_users': premium_users,
            'free_users': total_users - premium_users,
            'admin_count': len(ADMIN_IDS),
            'environment': env_status
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'supabase_healthy': False,
            'total_users': 0,
            'premium_users': 0
        }

def format_admin_status() -> str:
    """Format admin status for display"""
    status = get_admin_status()
    
    if 'error' in status:
        return f"❌ **Admin Status Error**: {status['error']}"
    
    sb_icon = "✅" if status['supabase_healthy'] else "❌"
    
    msg = f"""👑 **Admin Control Panel**

🔧 **System Status**:
• Supabase: {sb_icon} {status['supabase_detail']}

📊 **User Statistics**:
• Total Users: {status['total_users']:,}
• Premium Users: {status['premium_users']:,}
• Free Users: {status['free_users']:,}

🛡️ **Admin Configuration**:
• Admin Count: {status['admin_count']}
• Referral Required: {status['environment']['REFERRAL_REQUIRED']}
• Welcome Credits: {status['environment']['WELCOME_CREDITS']}

🔐 **Environment**:"""

    for key, value in status['environment'].items():
        icon = "✅" if value else "❌"
        if key in ['REFERRAL_REQUIRED', 'WELCOME_CREDITS']:
            msg += f"\n• {key}: {value}"
        else:
            msg += f"\n• {key}: {icon}"
    
    return msg
