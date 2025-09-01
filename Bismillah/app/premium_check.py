

from datetime import datetime, timezone
from app.users_repo import get_user_by_telegram_id
from app.supabase_conn import get_supabase_client

def is_premium_active(tid: int) -> bool:
    """Check if user has active premium using direct Supabase query"""
    try:
        s = get_supabase_client()
        
        result = s.table("users").select("is_premium, is_lifetime, premium_until").eq("telegram_id", int(tid)).limit(1).execute()
        
        if not result.data:
            print(f"❌ User {tid} not found for premium check")
            return False

        user = result.data[0]
        print(f"🔍 Premium check for user {tid}: {user}")

        # Check lifetime premium first
        if user.get('is_lifetime'):
            print(f"✅ User {tid} has lifetime premium")
            return True

        # Check regular premium
        if not user.get('is_premium'):
            print(f"❌ User {tid} is_premium=False")
            return False

        # Check if premium hasn't expired
        premium_until = user.get('premium_until')
        if not premium_until:
            # If is_premium=True but no expiry date, treat as lifetime
            print(f"✅ User {tid} has premium without expiry (treating as active)")
            return True

        # Parse premium_until timestamp with better handling
        try:
            print(f"🔍 Raw premium_until: '{premium_until}' (type: {type(premium_until)})")
            
            if isinstance(premium_until, str):
                s = premium_until.strip()
                
                # Handle Supabase format: 2025-09-20 10:43:48.485047+00
                if "." in s and "+" in s:
                    parts = s.split(".")
                    if len(parts) == 2:
                        microsec_part = parts[1]
                        if "+" in microsec_part:
                            timezone_part = "+" + microsec_part.split("+")[1]
                            s = parts[0] + timezone_part
                
                # Normalize space to T for ISO format
                if " " in s and "T" not in s:
                    s = s.replace(" ", "T", 1)
                
                # Handle timezone formats
                if s.endswith('Z'):
                    s = s[:-1] + '+00:00'
                elif s.endswith('+00'):
                    s = s + ':00'
                elif '+' not in s and 'Z' not in s:
                    s = s + '+00:00'
                
                print(f"🔍 Normalized premium_until: '{s}'")
                premium_dt = datetime.fromisoformat(s)
            else:
                premium_dt = premium_until

            # Ensure timezone awareness
            if premium_dt.tzinfo is None:
                premium_dt = premium_dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            is_active = premium_dt > now
            
            print(f"⏰ User {tid} premium until: {premium_dt}, now: {now}, active: {is_active}")
            return is_active
            
        except Exception as e:
            print(f"❌ Error parsing premium_until for user {tid}: {e} - Raw: '{premium_until}'")
            # Try one more fallback approach
            try:
                from dateutil import parser
                premium_dt = parser.parse(str(premium_until))
                if premium_dt.tzinfo is None:
                    premium_dt = premium_dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                is_active = premium_dt > now
                print(f"⏰ User {tid} premium until (fallback): {premium_dt}, active: {is_active}")
                return is_active
            except Exception as e2:
                print(f"❌ Fallback parsing also failed for user {tid}: {e2}")
                return False

    except Exception as e:
        print(f"❌ Error checking premium status for user {tid}: {e}")
        return False

def is_premium(tid: int) -> bool:
    """Check if user has active premium using Supabase data only"""
    try:
        return is_premium_active(tid)
    except Exception as e:
        print(f"❌ Error checking premium for user {tid}: {e}")
        return False

def get_user_credits(tid: int) -> int:
    """Get user credits from Supabase"""
    try:
        u = get_user_by_telegram_id(tid)
        if not u:
            return 0
        return int(u.get("credits", 0))
    except Exception as e:
        print(f"❌ Error getting credits for user {tid}: {e}")
        return 0

def is_banned(tid: int) -> bool:
    """Check if user is banned"""
    try:
        u = get_user_by_telegram_id(tid)
        if not u:
            return False
        return bool(u.get("banned", False))
    except Exception as e:
        print(f"❌ Error checking banned status for user {tid}: {e}")
        return False

def get_user_info(tid: int) -> dict:
    """Get complete user info from Supabase"""
    try:
        user = get_user_by_telegram_id(tid)
        return user or {}
    except Exception as e:
        print(f"❌ Error getting user info for {tid}: {e}")
        return {}

