import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get authenticated Supabase client"""
    try:
        from app.supabase_conn import get_supabase_client as get_client
        return get_client()
    except:
        # Fallback direct connection
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return create_client(url, key)

def get_vuser_by_telegram_id(tg_id: int) -> Optional[Dict[str, Any]]:
    s = get_supabase_client()
    res = s.table("v_users").select("*").eq("telegram_id", int(tg_id)).limit(1).execute()
    return res.data[0] if res.data else None

def is_premium_active(tg_id: int) -> bool:
    s = get_supabase_client()
    # 1) Pakai view v_users.premium_active (sumber kebenaran)
    try:
        res = s.table("v_users").select("premium_active").eq("telegram_id", int(tg_id)).limit(1).execute()
        if res.data:
            return bool(res.data[0].get("premium_active"))
    except Exception as e:
        print("[is_premium_active] v_users failed ->", e)

    # 2) Fallback langsung dari tabel 'users' + parser toleran
    try:
        r = s.table("users").select("is_premium,is_lifetime,premium_until")\
                .eq("telegram_id", int(tg_id)).limit(1).execute().data
        if not r:
            return False
        row = r[0]
        if row.get("is_lifetime"):
            return True
        if not row.get("is_premium"):
            return False
        return _ts_in_future(row.get("premium_until"))
    except Exception as e:
        print("[is_premium_active] users fallback failed ->", e)
        return False

def _ts_in_future(pu) -> bool:
    if not pu: return False
    s = str(pu).strip()
    
    # Handle various Supabase timestamp formats
    print(f"[DEBUG] Parsing premium_until: '{s}'")
    
    # Remove microseconds if present and normalize format
    if "." in s and "+" in s:
        # Format: 2025-09-20 10:43:48.485047+00
        parts = s.split(".")
        if len(parts) == 2:
            microsec_part = parts[1]
            if "+" in microsec_part:
                timezone_part = "+" + microsec_part.split("+")[1]
                s = parts[0] + timezone_part
            elif "Z" in microsec_part:
                s = parts[0] + "Z"
    
    # Normalize space to T
    if " " in s and "T" not in s:
        s = s.replace(" ", "T", 1)
    
    # Handle timezone formats
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    elif s.endswith("+00"):
        s = s + ":00"
    elif "+00:" in s and not s.endswith(":00"):
        s = s + "0" if s.endswith(":0") else s
    
    try:
        print(f"[DEBUG] Normalized timestamp: '{s}'")
        dt = datetime.fromisoformat(s)
    except Exception as e1:
        print(f"[DEBUG] fromisoformat failed: {e1}")
        try:
            from dateutil import parser
            dt = parser.parse(str(pu))
            print(f"[DEBUG] dateutil.parser succeeded")
        except Exception as e2:
            print(f"[DEBUG] dateutil.parser also failed: {e2}")
            return False
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    is_future = dt > now
    print(f"[DEBUG] premium_until: {dt}, now: {now}, is_future: {is_future}")
    return is_future


def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Get user by telegram ID from Supabase"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error getting user {telegram_id}: {e}")
        return None

def get_user_by_tid(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Alias for get_user_by_telegram_id"""
    return get_user_by_telegram_id(telegram_id)

def get_user_credits(telegram_id: int) -> int:
    """Get user credits from Supabase"""
    try:
        user_data = get_vuser_by_telegram_id(telegram_id)
        if user_data:
            return int(user_data.get('credits', 0))
        return 0
    except Exception as e:
        print(f"Error getting credits for user {telegram_id}: {e}")
        return 0


def create_user_if_not_exists(telegram_id: int, username: str = None, first_name: str = None) -> bool:
    """Create user in Supabase if not exists WITHOUT auto-assigning credits"""
    try:
        from app.supabase_repo import ensure_user_exists_no_credit
        
        # Use the new function that doesn't mess with credits
        user_data = ensure_user_exists_no_credit(telegram_id, username, first_name)
        return bool(user_data)

    except Exception as e:
        print(f"❌ Error creating/checking user {telegram_id}: {e}")
        
        # Fallback: manual creation without credits
        try:
            supabase = get_supabase_client()
            
            # Check if user exists
            existing = supabase.table("users").select("telegram_id").eq("telegram_id", telegram_id).execute()
            if existing.data:
                print(f"✅ User {telegram_id} already exists")
                return True

            # Create new user with 0 credits (welcome credits only from /start)
            user_data = {
                "telegram_id": telegram_id,
                "username": (username or "").strip().lstrip("@").lower() or None,
                "first_name": first_name or "New User",
                "credits": 0,  # No auto-credits, only from /start welcome
                "is_premium": False,
                "is_lifetime": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }

            result = supabase.table("users").insert(user_data).execute()
            print(f"✅ Created new user {telegram_id} with 0 credits in Supabase")
            return bool(result.data)

        except Exception as e2:
            print(f"❌ Fallback also failed for user {telegram_id}: {e2}")
            return False


def create_user(telegram_id: int, first_name: str = None, username: str = None,
                last_name: str = None, language_code: str = "id", credits: int = 100) -> bool:
    """Create a new user in Supabase"""
    try:
        supabase = get_supabase_client()

        user_data = {
            "telegram_id": telegram_id,
            "first_name": first_name or "User",
            "username": username,
            "last_name": last_name,
            "language_code": language_code,
            "credits": credits,
            "is_premium": False,
            "banned": False
        }

        result = supabase.table("users").insert(user_data).execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error creating user {telegram_id}: {e}")
        return False

def update_user_credits(telegram_id: int, credits: int) -> bool:
    """Update user credits in Supabase"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("users").update({"credits": credits}).eq("telegram_id", telegram_id).execute()
        return bool(result.data)
    except Exception as e:
        print(f"Error updating credits for user {telegram_id}: {e}")
        return False

def set_premium(telegram_id: int, lifetime: bool = False, days: int = None) -> bool:
    """Set premium status for user in Supabase (auto-creates user if not exists)"""
    try:
        supabase = get_supabase_client()

        # Check if user exists, if not create them first
        existing_user = get_user_by_telegram_id(telegram_id)
        if not existing_user:
            print(f"User {telegram_id} not found. Creating new user...")
            # Create user with minimal data since admin is adding premium
            user_data = {
                "telegram_id": telegram_id,
                "username": f"user_{telegram_id}",  # Placeholder username
                "first_name": "Premium User",  # Placeholder name
                "is_premium": False,  # Will be updated below
                "is_lifetime": False,
                "credits": 100,  # Default credits
                "premium_until": None
            }

            # Insert new user
            create_result = supabase.table("users").insert(user_data).execute()
            if not create_result.data:
                print(f"Failed to create user {telegram_id}")
                return False
            print(f"Successfully created user {telegram_id}")

        # Prepare premium update data
        update_data = {
            "is_premium": True,
            "is_lifetime": lifetime,
            "updated_at": datetime.utcnow().isoformat()
        }

        if lifetime:
            update_data["premium_until"] = None
        elif days:
            premium_until = datetime.utcnow() + timedelta(days=days)
            update_data["premium_until"] = premium_until.isoformat()
        else:
            # Default 30 days if no days specified
            premium_until = datetime.utcnow() + timedelta(days=30)
            update_data["premium_until"] = premium_until.isoformat()

        # Update user with premium status
        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()

        if result.data:
            premium_type = "LIFETIME" if lifetime else f"{days or 30} days"
            print(f"Set premium {premium_type} for user {telegram_id}")
            return True
        else:
            print(f"Failed to update premium for user {telegram_id}")
            return False

    except Exception as e:
        print(f"Error setting premium for user {telegram_id}: {e}")
        return False

def revoke_premium(telegram_id: int) -> bool:
    """Revoke premium status from user in Supabase with verification"""
    try:
        supabase = get_supabase_client()

        # First check if user exists
        existing = supabase.table("users").select("telegram_id, is_premium, is_lifetime").eq("telegram_id", telegram_id).execute()
        if not existing.data:
            print(f"User {telegram_id} not found for premium revocation")
            return False

        current_user = existing.data[0]
        was_premium = current_user.get('is_premium', False)
        was_lifetime = current_user.get('is_lifetime', False)

        # Reset premium status completely
        update_data = {
            "is_premium": False,
            "is_lifetime": False,
            "premium_until": None,
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()

        if result.data:
            premium_type = "lifetime" if was_lifetime else "timed"
            print(f"✅ Revoked {premium_type} premium for user {telegram_id}")
            
            # Double-check the revocation worked
            verification = supabase.table("users").select("is_premium, is_lifetime, premium_until").eq("telegram_id", telegram_id).execute()
            if verification.data:
                verified = verification.data[0]
                if not verified.get('is_premium') and not verified.get('is_lifetime') and not verified.get('premium_until'):
                    print(f"✅ Premium revocation verified for user {telegram_id}")
                    return True
                else:
                    print(f"⚠️ Premium revocation incomplete for user {telegram_id}: {verified}")
                    return False
            
            return True
        else:
            print(f"❌ Failed to revoke premium for user {telegram_id} - no data returned")
            return False

    except Exception as e:
        print(f"❌ Error revoking premium for user {telegram_id}: {e}")
        import traceback
        traceback.print_exc()
        return False

def touch_user_from_update(update):
    """Create/update user from Telegram update WITHOUT auto-assigning credits"""
    if not update or not update.effective_user:
        return

    user = update.effective_user
    from app.supabase_repo import ensure_user_exists_no_credit
    
    # Use function that doesn't touch credits
    ensure_user_exists_no_credit(
        tg_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

def get_credits(telegram_id: int) -> int:
    """Get user credits from Supabase"""
    try:
        user = get_user_by_telegram_id(telegram_id)
        return user.get("credits", 0) if user else 0
    except Exception as e:
        print(f"Error getting credits for user {telegram_id}: {e}")
        return 0

def is_premium_active(telegram_id: int) -> bool:
    """Check if user has active premium using improved logic"""
    try:
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            print(f"❌ User {telegram_id} not found for premium check")
            return False

        print(f"🔍 Premium check for user {telegram_id}: {user}")

        if not user.get("is_premium", False):
            print(f"❌ User {telegram_id} is_premium=False")
            return False

        if user.get("is_lifetime", False):
            print(f"✅ User {telegram_id} has lifetime premium")
            return True

        premium_until = user.get("premium_until")
        if not premium_until:
            # If is_premium=True but no expiry, treat as lifetime for backward compatibility
            print(f"✅ User {telegram_id} has premium without expiry (treating as active)")
            return True

        # Use the improved timestamp parsing from _ts_in_future
        is_active = _ts_in_future(premium_until)
        print(f"⏰ User {telegram_id} premium until: {premium_until}, active: {is_active}")
        return is_active

    except Exception as e:
        print(f"❌ Error checking premium for user {telegram_id}: {e}")
        return False

def debit_credits(telegram_id: int, amount: int) -> bool:
    """Deduct credits from user account"""
    try:
        supabase = get_supabase_client()

        # Get current credits
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            print(f"User {telegram_id} not found for credit debit")
            return False

        current_credits = user.get("credits", 0)
        if current_credits < amount:
            print(f"Insufficient credits for user {telegram_id}: {current_credits} < {amount}")
            return False

        # Deduct credits
        new_credits = current_credits - amount
        update_data = {
            "credits": new_credits,
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()

        if result.data:
            print(f"Debited {amount} credits from user {telegram_id}: {current_credits} → {new_credits}")
            return True
        else:
            print(f"Failed to debit credits for user {telegram_id}")
            return False

    except Exception as e:
        print(f"Error debiting credits for user {telegram_id}: {e}")
        return False

def add_credits(telegram_id: int, amount: int) -> bool:
    """Add credits to user account"""
    try:
        supabase = get_supabase_client()

        # Get current credits
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            print(f"User {telegram_id} not found for credit addition")
            return False

        current_credits = user.get("credits", 0)
        new_credits = current_credits + amount

        update_data = {
            "credits": new_credits,
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()

        if result.data:
            print(f"Added {amount} credits to user {telegram_id}: {current_credits} → {new_credits}")
            return True
        else:
            print(f"Failed to add credits for user {telegram_id}")
            return False

    except Exception as e:
        print(f"Error adding credits for user {telegram_id}: {e}")
        return False

def set_credits(telegram_id: int, amount: int) -> bool:
    """Set exact credit amount for user"""
    try:
        supabase = get_supabase_client()

        update_data = {
            "credits": amount,
            "updated_at": datetime.utcnow().isoformat()
        }

        result = supabase.table("users").update(update_data).eq("telegram_id", telegram_id).execute()

        if result.data:
            print(f"Set {amount} credits for user {telegram_id}")
            return True
        else:
            print(f"Failed to set credits for user {telegram_id}")
            return False

    except Exception as e:
        print(f"Error setting credits for user {telegram_id}: {e}")
        return False

def check_sufficient_credits(telegram_id: int, required_amount: int) -> bool:
    """Check if user has sufficient credits"""
    try:
        user = get_user_by_telegram_id(telegram_id)
        if not user:
            return False

        current_credits = user.get("credits", 0)
        return current_credits >= required_amount

    except Exception as e:
        print(f"Error checking credits for user {telegram_id}: {e}")
        return False