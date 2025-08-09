
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseUsers:
    def __init__(self):
        """Initialize Supabase connection for user management"""
        self.supabase = None
        self._init_supabase()
        
    def _init_supabase(self):
        """Initialize Supabase client with error handling"""
        try:
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_anon_key = <REDACTED_SUPABASE_KEY>
            
            if not supabase_url or not supabase_anon_key:
                logger.error("❌ SUPABASE_URL or SUPABASE_ANON_KEY not found in environment variables")
                return False
                
            self.supabase: Client = create_client(supabase_url, supabase_anon_key)
            logger.info("✅ Supabase connection established for user management")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            return False
    
    def add_user(self, user_id: int, username: str = "", first_name: str = "", last_name: str = "", status: str = "free") -> bool:
        """Add new user to Supabase users table"""
        try:
            if not self.supabase:
                logger.error("Supabase connection not available")
                return False
                
            # Check if user already exists
            existing_user = self.get_user(user_id)
            if existing_user:
                logger.info(f"User {user_id} already exists, updating info")
                return self.update_user_info(user_id, username, first_name, last_name)
            
            user_data = {
                'telegram_id': str(user_id),
                'username': username or 'no_username',
                'first_name': first_name or 'Unknown',
                'last_name': last_name or '',
                'status': status,
                'credits': 100,  # Default credits for new users
                'joined_at': datetime.now().isoformat(),
                'is_premium': status in ['premium', 'lifetime', 'admin'],
                'subscription_end': None if status in ['lifetime', 'admin'] else datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                logger.info(f"✅ User {user_id} added to Supabase")
                return True
            else:
                logger.error(f"❌ Failed to add user {user_id} to Supabase")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user data from Supabase by telegram_id"""
        try:
            if not self.supabase:
                return None
                
            result = self.supabase.table('users').select('*').eq('telegram_id', str(user_id)).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting user {user_id}: {e}")
            return None
    
    def update_user_status(self, user_id: int, new_status: str) -> bool:
        """Update user status in Supabase"""
        try:
            if not self.supabase:
                return False
                
            update_data = {
                'status': new_status,
                'is_premium': new_status in ['premium', 'lifetime', 'admin'],
                'last_active': datetime.now().isoformat()
            }
            
            # Set subscription_end based on status
            if new_status == 'lifetime' or new_status == 'admin':
                update_data['subscription_end'] = None
            elif new_status == 'premium':
                # Default 30 days for premium
                update_data['subscription_end'] = (datetime.now() + timedelta(days=30)).isoformat()
            else:
                update_data['subscription_end'] = datetime.now().isoformat()
            
            result = self.supabase.table('users').update(update_data).eq('telegram_id', str(user_id)).execute()
            
            if result.data:
                logger.info(f"✅ User {user_id} status updated to {new_status}")
                return True
            else:
                logger.error(f"❌ Failed to update user {user_id} status")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating user status {user_id}: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users from Supabase"""
        try:
            if not self.supabase:
                return []
                
            result = self.supabase.table('users').select('telegram_id, username, first_name, status, is_premium, last_active').execute()
            
            if result.data:
                # Convert telegram_id back to int for compatibility
                users = []
                for user in result.data:
                    user_copy = user.copy()
                    try:
                        user_copy['user_id'] = int(user_copy['telegram_id'])
                    except (ValueError, TypeError):
                        continue
                    users.append(user_copy)
                return users
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting all users: {e}")
            return []
    
    def get_users_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all users with specific status from Supabase"""
        try:
            if not self.supabase:
                return []
                
            result = self.supabase.table('users').select('telegram_id, username, first_name, status, is_premium').eq('status', status).execute()
            
            if result.data:
                # Convert telegram_id back to int for compatibility
                users = []
                for user in result.data:
                    user_copy = user.copy()
                    try:
                        user_copy['user_id'] = int(user_copy['telegram_id'])
                    except (ValueError, TypeError):
                        continue
                    users.append(user_copy)
                return users
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting users by status {status}: {e}")
            return []
    
    def get_premium_users(self) -> List[Dict[str, Any]]:
        """Get all premium users (premium, lifetime, admin)"""
        try:
            if not self.supabase:
                return []
                
            result = self.supabase.table('users').select('telegram_id, username, first_name, status, is_premium').eq('is_premium', True).execute()
            
            if result.data:
                users = []
                for user in result.data:
                    user_copy = user.copy()
                    try:
                        user_copy['user_id'] = int(user_copy['telegram_id'])
                    except (ValueError, TypeError):
                        continue
                    users.append(user_copy)
                return users
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting premium users: {e}")
            return []
    
    def get_eligible_auto_signal_users(self) -> List[Dict[str, Any]]:
        """Get users eligible for auto signals (admin + lifetime)"""
        try:
            if not self.supabase:
                return []
                
            result = self.supabase.table('users').select('telegram_id, username, first_name, status').in_('status', ['admin', 'lifetime']).execute()
            
            if result.data:
                users = []
                for user in result.data:
                    user_copy = user.copy()
                    try:
                        user_copy['user_id'] = int(user_copy['telegram_id'])
                    except (ValueError, TypeError):
                        continue
                    users.append(user_copy)
                return users
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting auto signal eligible users: {e}")
            return []
    
    def update_user_info(self, user_id: int, username: str = "", first_name: str = "", last_name: str = "") -> bool:
        """Update user basic information"""
        try:
            if not self.supabase:
                return False
                
            update_data = {
                'last_active': datetime.now().isoformat()
            }
            
            if username:
                update_data['username'] = username
            if first_name:
                update_data['first_name'] = first_name
            if last_name:
                update_data['last_name'] = last_name
                
            result = self.supabase.table('users').update(update_data).eq('telegram_id', str(user_id)).execute()
            
            if result.data:
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating user info {user_id}: {e}")
            return False
    
    def update_user_credits(self, user_id: int, credits: int) -> bool:
        """Update user credits in Supabase"""
        try:
            if not self.supabase:
                return False
                
            result = self.supabase.table('users').update({'credits': credits}).eq('telegram_id', str(user_id)).execute()
            
            if result.data:
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating user credits {user_id}: {e}")
            return False
    
    def add_user_credits(self, user_id: int, amount: int) -> bool:
        """Add credits to user account"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
                
            current_credits = user.get('credits', 0)
            new_credits = current_credits + amount
            
            return self.update_user_credits(user_id, new_credits)
            
        except Exception as e:
            logger.error(f"❌ Error adding credits to user {user_id}: {e}")
            return False
    
    def deduct_user_credits(self, user_id: int, amount: int) -> bool:
        """Deduct credits from user account"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
                
            current_credits = user.get('credits', 0)
            new_credits = max(0, current_credits - amount)
            
            return self.update_user_credits(user_id, new_credits)
            
        except Exception as e:
            logger.error(f"❌ Error deducting credits from user {user_id}: {e}")
            return False
    
    def get_user_credits(self, user_id: int) -> int:
        """Get user's current credits"""
        try:
            user = self.get_user(user_id)
            if user:
                return user.get('credits', 0)
            else:
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error getting user credits {user_id}: {e}")
            return 0
    
    def is_user_premium(self, user_id: int) -> bool:
        """Check if user has premium status"""
        try:
            user = self.get_user(user_id)
            if user:
                return user.get('is_premium', False) or user.get('status') in ['premium', 'lifetime', 'admin']
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking premium status {user_id}: {e}")
            return False
    
    def grant_premium(self, user_id: int, days: int) -> bool:
        """Grant premium status to user for specified days"""
        try:
            if not self.supabase:
                return False
                
            subscription_end = (datetime.now() + timedelta(days=days)).isoformat()
            
            update_data = {
                'status': 'premium',
                'is_premium': True,
                'subscription_end': subscription_end,
                'last_active': datetime.now().isoformat()
            }
            
            result = self.supabase.table('users').update(update_data).eq('telegram_id', str(user_id)).execute()
            
            if result.data:
                logger.info(f"✅ Granted {days} days premium to user {user_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error granting premium to user {user_id}: {e}")
            return False
    
    def grant_lifetime_premium(self, user_id: int) -> bool:
        """Grant lifetime premium to user"""
        try:
            if not self.supabase:
                return False
                
            update_data = {
                'status': 'lifetime',
                'is_premium': True,
                'subscription_end': None,
                'last_active': datetime.now().isoformat()
            }
            
            result = self.supabase.table('users').update(update_data).eq('telegram_id', str(user_id)).execute()
            
            if result.data:
                logger.info(f"✅ Granted lifetime premium to user {user_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error granting lifetime premium to user {user_id}: {e}")
            return False
    
    def revoke_premium(self, user_id: int) -> bool:
        """Revoke premium status from user"""
        try:
            if not self.supabase:
                return False
                
            update_data = {
                'status': 'free',
                'is_premium': False,
                'subscription_end': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            
            result = self.supabase.table('users').update(update_data).eq('telegram_id', str(user_id)).execute()
            
            if result.data:
                logger.info(f"✅ Revoked premium from user {user_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error revoking premium from user {user_id}: {e}")
            return False
    
    def get_bot_statistics(self) -> Dict[str, Any]:
        """Get bot statistics from Supabase"""
        try:
            if not self.supabase:
                return {
                    'total_users': 0,
                    'premium_users': 0,
                    'lifetime_users': 0,
                    'admin_users': 0,
                    'free_users': 0
                }
            
            # Get all users count
            total_result = self.supabase.table('users').select('telegram_id', count='exact').execute()
            total_users = total_result.count if total_result.count else 0
            
            # Get premium users count
            premium_result = self.supabase.table('users').select('telegram_id', count='exact').eq('is_premium', True).execute()
            premium_users = premium_result.count if premium_result.count else 0
            
            # Get lifetime users count
            lifetime_result = self.supabase.table('users').select('telegram_id', count='exact').eq('status', 'lifetime').execute()
            lifetime_users = lifetime_result.count if lifetime_result.count else 0
            
            # Get admin users count
            admin_result = self.supabase.table('users').select('telegram_id', count='exact').eq('status', 'admin').execute()
            admin_users = admin_result.count if admin_result.count else 0
            
            free_users = total_users - premium_users
            
            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'lifetime_users': lifetime_users,
                'admin_users': admin_users,
                'free_users': free_users
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting bot statistics: {e}")
            return {
                'total_users': 0,
                'premium_users': 0,
                'lifetime_users': 0,
                'admin_users': 0,
                'free_users': 0
            }
    
    def cleanup_expired_premium(self) -> int:
        """Clean up expired premium users"""
        try:
            if not self.supabase:
                return 0
                
            current_time = datetime.now().isoformat()
            
            # Get users with expired subscriptions
            result = self.supabase.table('users').select('telegram_id').lt('subscription_end', current_time).eq('is_premium', True).neq('status', 'lifetime').neq('status', 'admin').execute()
            
            if not result.data:
                return 0
            
            expired_users = [user['telegram_id'] for user in result.data]
            
            # Update their status to free
            update_result = self.supabase.table('users').update({
                'status': 'free',
                'is_premium': False
            }).in_('telegram_id', expired_users).execute()
            
            if update_result.data:
                logger.info(f"✅ Cleaned up {len(expired_users)} expired premium users")
                return len(expired_users)
            else:
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired premium users: {e}")
            return 0
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            if not self.supabase:
                return False
                
            # Simple test query
            result = self.supabase.table('users').select('telegram_id', count='exact').limit(1).execute()
            return True
            
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False
