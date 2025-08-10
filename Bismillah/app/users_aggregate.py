
import os
from typing import List
from app.supabase_conn import sb_list_users
from app.chat_store import get_private_chat_id

def get_eligible_recipients_for_autosignal() -> List[int]:
    """
    Get eligible users for AutoSignal - only admin + Supabase lifetime users
    Removed all local backup and JSON sources
    """
    try:
        # Get admin IDs from environment
        admin_ids = set()
        for key in ("ADMIN_USER_ID", "ADMIN2_USER_ID", "ADMIN1", "ADMIN2"):
            val = os.getenv(key)
            if val and val.isdigit():
                admin_ids.add(int(val))
        
        eligible_users = list(admin_ids)
        
        # Get lifetime premium from Supabase only  
        try:
            rows = sb_list_users({
                "is_premium": "eq.true",
                "banned": "eq.false",
                "premium_until": "is.null"  # lifetime only
            }, columns="telegram_id")
            
            # Add users who have private chat consent
            for row in rows:
                tid = row.get("telegram_id")
                if tid and get_private_chat_id(int(tid)) is not None:
                    eligible_users.append(int(tid))
                    
        except Exception as e:
            print(f"Error getting Supabase lifetime users: {e}")
        
        return list(set(eligible_users))  # Remove duplicates
        
    except Exception as e:
        print(f"Error in get_eligible_recipients_for_autosignal: {e}")
        return []

def get_premium_user_count() -> int:
    """Get count of premium users from Supabase"""
    try:
        rows = sb_list_users({
            "is_premium": "eq.true",
            "banned": "eq.false"
        }, columns="telegram_id")
        return len(rows)
    except Exception as e:
        print(f"Error getting premium user count: {e}")
        return 0

def get_lifetime_user_count() -> int:
    """Get count of lifetime premium users from Supabase"""
    try:
        rows = sb_list_users({
            "is_premium": "eq.true", 
            "banned": "eq.false",
            "premium_until": "is.null"
        }, columns="telegram_id")
        return len(rows)
    except Exception as e:
        print(f"Error getting lifetime user count: {e}")
        return 0
