
#!/usr/bin/env python3
"""
Premium Manager for CryptoMentor AI Bot
Handles premium user management directly with Supabase
"""

import os
from datetime import datetime, timedelta, timezone
from supabase import create_client, Client

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase_client():
    """Get Supabase client with service role key"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise Exception("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")
    
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def add_premium_user(user_id, duration_days=None, lifetime=False):
    """
    Add or update premium user in Supabase
    
    Args:
        user_id (str/int): Telegram user ID
        duration_days (int, optional): Number of days for premium access
        lifetime (bool): If True, grants lifetime premium access
    
    Returns:
        dict: Result with success status and message
    """
    try:
        supabase = get_supabase_client()
        
        # Convert user_id to int if it's a string
        telegram_id = int(user_id)
        
        # Calculate expiry date
        expires_at = None
        if lifetime:
            # Lifetime premium - set to None (null in database)
            expires_at = None
            premium_type = "lifetime"
        elif duration_days:
            # Premium with expiry date
            expires_at = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
            premium_type = f"{duration_days}_days"
        else:
            # Default 30 days if neither lifetime nor duration specified
            expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            premium_type = "30_days"
        
        print(f"🔄 Processing premium upgrade for user {telegram_id}")
        print(f"📝 Premium type: {premium_type}")
        print(f"📅 Expires at: {expires_at}")
        
        # Direct upsert without user existence validation
        print(f"🔄 Setting premium for user {telegram_id} (direct upsert)...")
        
        user_data = {
            'telegram_id': telegram_id,
            'username': f'premium_user_{telegram_id}',
            'is_premium': True,
            'premium_until': expires_at
        }
        
        # Use upsert to insert or update without validation
        result = supabase.table('users').upsert(user_data, on_conflict='telegram_id').execute()
        
        if result.data:
            print(f"✅ Premium status set successfully for user {telegram_id}")
            return {
                'success': True,
                'action': 'upserted',
                'user_id': telegram_id,
                'premium_type': premium_type,
                'expires_at': expires_at,
                'message': f"User {telegram_id} premium status set successfully"
            }
        else:
            error_msg = f"Failed to set premium status for user {telegram_id}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    except Exception as e:
        error_msg = f"Error processing premium user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }

def remove_premium_user(user_id):
    """
    Remove premium status from user
    
    Args:
        user_id (str/int): Telegram user ID
    
    Returns:
        dict: Result with success status and message
    """
    try:
        supabase = get_supabase_client()
        telegram_id = int(user_id)
        
        print(f"🔄 Removing premium status from user {telegram_id}")
        
        # Update user to remove premium status
        update_data = {
            'is_premium': False,
            'premium_until': None
        }
        
        result = supabase.table('users').update(update_data).eq('telegram_id', telegram_id).execute()
        
        if result.data:
            print(f"✅ Premium status removed from user {telegram_id}")
            return {
                'success': True,
                'user_id': telegram_id,
                'message': f"Premium status removed from user {telegram_id}"
            }
        else:
            error_msg = f"User {telegram_id} not found or already non-premium"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
    
    except Exception as e:
        error_msg = f"Error removing premium from user {user_id}: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg
        }

def check_premium_user(user_id):
    """
    Check if user has premium status and when it expires
    
    Args:
        user_id (str/int): Telegram user ID
    
    Returns:
        dict: Premium status information
    """
    try:
        supabase = get_supabase_client()
        telegram_id = int(user_id)
        
        result = supabase.table('users').select('*').eq('telegram_id', telegram_id).execute()
        
        if result.data:
            user = result.data[0]
            is_premium = user.get('is_premium', False)
            subscription_end = user.get('premium_until')
            
            if is_premium:
                if subscription_end is None:
                    premium_type = "lifetime"
                    is_active = True
                else:
                    # Check if subscription is still active
                    try:
                        end_date = datetime.fromisoformat(subscription_end.replace('Z', '+00:00'))
                        is_active = datetime.now(timezone.utc) < end_date
                        if is_active:
                            days_remaining = (end_date - datetime.now(timezone.utc)).days
                            premium_type = f"expires_in_{days_remaining}_days"
                        else:
                            premium_type = "expired"
                    except:
                        premium_type = "invalid_date"
                        is_active = False
                
                return {
                    'success': True,
                    'user_id': telegram_id,
                    'is_premium': is_premium,
                    'is_active': is_active,
                    'premium_type': premium_type,
                    'subscription_end': subscription_end
                }
            else:
                return {
                    'success': True,
                    'user_id': telegram_id,
                    'is_premium': False,
                    'is_active': False,
                    'premium_type': "none"
                }
        else:
            return {
                'success': False,
                'error': f"User {telegram_id} not found"
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Error checking premium status for user {user_id}: {str(e)}"
        }

def list_premium_users(limit=50):
    """
    Get list of all premium users
    
    Args:
        limit (int): Maximum number of users to return
    
    Returns:
        dict: List of premium users
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('users').select('telegram_id, username, is_premium, premium_until').eq('is_premium', True).limit(limit).execute()
        
        if result.data:
            premium_users = []
            for user in result.data:
                premium_until = user.get('premium_until')
                if premium_until is None:
                    status = "lifetime"
                else:
                    try:
                        end_date = datetime.fromisoformat(premium_until.replace('Z', '+00:00'))
                        if datetime.now(timezone.utc) < end_date:
                            days_remaining = (end_date - datetime.now(timezone.utc)).days
                            status = f"active ({days_remaining} days left)"
                        else:
                            status = "expired"
                    except:
                        status = "invalid_date"
                
                premium_users.append({
                    'telegram_id': user['telegram_id'],
                    'username': user.get('username', 'no_username'),
                    'status': status,
                    'premium_until': premium_until
                })
            
            return {
                'success': True,
                'count': len(premium_users),
                'users': premium_users
            }
        else:
            return {
                'success': True,
                'count': 0,
                'users': []
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Error listing premium users: {str(e)}"
        }

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Premium Manager...")
    print("=" * 50)
    
    # Test adding premium user with 30 days
    print("1️⃣ Testing add_premium_user with 30 days...")
    result = add_premium_user("123456789", duration_days=30)
    print(f"Result: {result}")
    
    print("\n2️⃣ Testing add_premium_user with lifetime...")
    result = add_premium_user("987654321", lifetime=True)
    print(f"Result: {result}")
    
    print("\n3️⃣ Testing check_premium_user...")
    result = check_premium_user("123456789")
    print(f"Result: {result}")
    
    print("\n4️⃣ Testing list_premium_users...")
    result = list_premium_users(10)
    print(f"Result: {result}")
    
    print("\n✅ Premium Manager testing completed!")
