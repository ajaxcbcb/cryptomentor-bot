
# app/admin_status.py
import os
from typing import Dict, Any
from app.supabase_conn import get_supabase_client, health
from app.sb_repo import stats_totals

def _load_admin_ids():
    """Load admin IDs from various environment variables"""
    admin_ids = set()
    
    # Try ADMIN_IDS (comma-separated)
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        for admin_id in admin_ids_str.split(","):
            try:
                admin_ids.add(int(admin_id.strip()))
            except ValueError:
                pass
    
    # Try ADMIN1, ADMIN2, ADMIN3, etc.
    for key in ['ADMIN1', 'ADMIN2', 'ADMIN3', 'ADMIN_USER_ID', 'ADMIN2_USER_ID']:
        value = os.getenv(key)
        if value:
            try:
                admin_ids.add(int(value.strip()))
            except ValueError:
                pass
    
    return admin_ids

ADMIN_IDS = _load_admin_ids()

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


def get_database_broadcast_stats() -> Dict[str, Any]:
    """Get detailed database statistics for broadcast"""
    try:
        from services import get_database
        db = get_database()
        
        # Get broadcast data
        broadcast_data = db.get_all_broadcast_users()
        stats = broadcast_data['stats']
        
        # Get additional stats
        local_users = broadcast_data['local_users']
        supabase_users = broadcast_data['supabase_users']
        
        # Count premium users
        local_premium = sum(1 for u in local_users if u.get('is_premium'))
        supabase_premium = sum(1 for u in supabase_users if u.get('is_premium'))
        
        return {
            'success': True,
            'local': {
                'total': stats['local_count'],
                'premium': local_premium,
                'free': stats['local_count'] - local_premium
            },
            'supabase': {
                'total': stats['supabase_count'],
                'unique': stats['supabase_unique'],
                'premium': supabase_premium,
                'free': stats['supabase_count'] - supabase_premium
            },
            'combined': {
                'total_unique': stats['total_unique'],
                'duplicates': stats['duplicates'],
                'coverage': f"{(stats['total_unique'] / max(stats['local_count'] + stats['supabase_count'], 1) * 100):.1f}%"
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def format_database_stats() -> str:
    """Format database statistics for display"""
    stats = get_database_broadcast_stats()
    
    if not stats.get('success'):
        return f"❌ **Database Stats Error**: {stats.get('error', 'Unknown error')}"
    
    local = stats['local']
    supabase = stats['supabase']
    combined = stats['combined']
    
    msg = f"""📊 **DATABASE BROADCAST STATISTICS**

🗄️ **Local Database (SQLite)**:
• Total Users: {local['total']:,}
• Premium: {local['premium']:,}
• Free: {local['free']:,}

☁️ **Supabase Database**:
• Total Users: {supabase['total']:,}
• Unique to Supabase: {supabase['unique']:,}
• Premium: {supabase['premium']:,}
• Free: {supabase['free']:,}

🎯 **Combined Statistics**:
• Total Unique Users: {combined['total_unique']:,}
• Duplicate Entries: {combined['duplicates']:,}
• Data Coverage: {combined['coverage']}

💡 **Broadcast Reach**:
When you broadcast, the message will be sent to {combined['total_unique']:,} unique users.

⚠️ **Note**: 
- Duplicates are automatically removed
- Banned users are excluded
- Users who blocked the bot won't receive messages
"""
    
    return msg
