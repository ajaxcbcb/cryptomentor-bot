# Rate Limiter - Prevent Spam and Abuse
# Implements rate limiting for spawn operations, withdrawals, and API calls

import os
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import time


class RateLimiter:
    """
    Manages rate limiting for various operations
    
    Features:
    - Limit spawn operations to 1 per user per hour
    - Limit withdrawal requests to 3 per user per day
    - Limit API calls with exponential backoff
    - Store rate limit state in-memory (Redis optional)
    
    Security:
    - Prevents spam attacks
    - Prevents abuse of expensive operations
    - Protects external APIs from rate limit errors
    """
    
    def __init__(self, db=None):
        """
        Initialize Rate Limiter
        
        Args:
            db: Database instance (optional)
        """
        self.db = db
        
        # In-memory storage for rate limits
        # Format: {user_id: {operation: [timestamp1, timestamp2, ...]}}
        self._rate_limits: Dict[int, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
        
        # API call tracking for exponential backoff
        # Format: {api_name: {'failures': count, 'last_failure': timestamp, 'backoff_until': timestamp}}
        self._api_backoff: Dict[str, Dict] = {}
        
        # Rate limit configurations
        self.limits = {
            'spawn': {
                'max_requests': 1,
                'window_seconds': 3600,  # 1 hour
                'description': 'Agent spawn operations'
            },
            'withdrawal': {
                'max_requests': 3,
                'window_seconds': 86400,  # 24 hours (1 day)
                'description': 'Withdrawal requests'
            },
            'ai_signal': {
                'max_requests': 10,
                'window_seconds': 3600,  # 1 hour
                'description': 'AI signal requests'
            },
            'api_call': {
                'max_failures': 3,
                'base_backoff': 1,  # 1 second
                'max_backoff': 300,  # 5 minutes
                'description': 'External API calls'
            }
        }
        
        print("✅ Rate Limiter initialized")
    
    def check_spawn_limit(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user can spawn an agent
        
        Limit: 1 spawn per hour per user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        try:
            operation = 'spawn'
            config = self.limits[operation]
            
            # Get user's spawn history
            spawn_history = self._rate_limits[user_id][operation]
            
            # Clean up old entries outside the time window
            cutoff_time = datetime.now() - timedelta(seconds=config['window_seconds'])
            spawn_history = [ts for ts in spawn_history if ts > cutoff_time]
            self._rate_limits[user_id][operation] = spawn_history
            
            # Check if limit exceeded
            if len(spawn_history) >= config['max_requests']:
                # Calculate time until next allowed spawn
                oldest_spawn = min(spawn_history)
                next_allowed = oldest_spawn + timedelta(seconds=config['window_seconds'])
                time_remaining = next_allowed - datetime.now()
                
                minutes_remaining = int(time_remaining.total_seconds() / 60)
                
                error_msg = (
                    f"⏱️ Rate limit exceeded!\n\n"
                    f"You can only spawn {config['max_requests']} agent per hour.\n"
                    f"Please wait {minutes_remaining} minutes before spawning again."
                )
                
                print(f"🚫 Spawn rate limit exceeded for user {user_id} - {minutes_remaining} minutes remaining")
                return False, error_msg
            
            # Limit not exceeded, record this attempt
            spawn_history.append(datetime.now())
            self._rate_limits[user_id][operation] = spawn_history
            
            print(f"✅ Spawn rate limit check passed for user {user_id} ({len(spawn_history)}/{config['max_requests']})")
            return True, None
        
        except Exception as e:
            print(f"❌ Error checking spawn rate limit: {e}")
            # On error, allow the operation (fail open for better UX)
            return True, None
    
    def check_withdrawal_limit(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user can request a withdrawal
        
        Limit: 3 withdrawals per day per user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        try:
            operation = 'withdrawal'
            config = self.limits[operation]
            
            # Get user's withdrawal history
            withdrawal_history = self._rate_limits[user_id][operation]
            
            # Clean up old entries outside the time window (24 hours)
            cutoff_time = datetime.now() - timedelta(seconds=config['window_seconds'])
            withdrawal_history = [ts for ts in withdrawal_history if ts > cutoff_time]
            self._rate_limits[user_id][operation] = withdrawal_history
            
            # Check if limit exceeded
            if len(withdrawal_history) >= config['max_requests']:
                # Calculate time until next allowed withdrawal
                oldest_withdrawal = min(withdrawal_history)
                next_allowed = oldest_withdrawal + timedelta(seconds=config['window_seconds'])
                time_remaining = next_allowed - datetime.now()
                
                hours_remaining = int(time_remaining.total_seconds() / 3600)
                
                error_msg = (
                    f"⏱️ Withdrawal limit exceeded!\n\n"
                    f"You can only request {config['max_requests']} withdrawals per day.\n"
                    f"Please wait {hours_remaining} hours before requesting another withdrawal."
                )
                
                print(f"🚫 Withdrawal rate limit exceeded for user {user_id} - {hours_remaining} hours remaining")
                return False, error_msg
            
            # Limit not exceeded, record this attempt
            withdrawal_history.append(datetime.now())
            self._rate_limits[user_id][operation] = withdrawal_history
            
            print(f"✅ Withdrawal rate limit check passed for user {user_id} ({len(withdrawal_history)}/{config['max_requests']})")
            return True, None
        
        except Exception as e:
            print(f"❌ Error checking withdrawal rate limit: {e}")
            # On error, allow the operation (fail open for better UX)
            return True, None
    
    def check_api_backoff(self, api_name: str) -> Tuple[bool, Optional[float]]:
        """
        Check if API call should be delayed due to exponential backoff
        
        Args:
            api_name: Name of the API (e.g., 'conway', 'polygon_rpc')
            
        Returns:
            Tuple of (allowed: bool, wait_seconds: Optional[float])
        """
        try:
            if api_name not in self._api_backoff:
                # No backoff for this API
                return True, None
            
            backoff_info = self._api_backoff[api_name]
            backoff_until = backoff_info.get('backoff_until')
            
            if backoff_until and datetime.now() < backoff_until:
                # Still in backoff period
                wait_seconds = (backoff_until - datetime.now()).total_seconds()
                print(f"⏳ API {api_name} in backoff - wait {wait_seconds:.1f}s")
                return False, wait_seconds
            
            # Backoff period expired or not set
            return True, None
        
        except Exception as e:
            print(f"❌ Error checking API backoff: {e}")
            return True, None
    
    def record_api_failure(self, api_name: str) -> float:
        """
        Record an API failure and calculate exponential backoff
        
        Args:
            api_name: Name of the API
            
        Returns:
            Backoff duration in seconds
        """
        try:
            config = self.limits['api_call']
            
            if api_name not in self._api_backoff:
                self._api_backoff[api_name] = {
                    'failures': 0,
                    'last_failure': None,
                    'backoff_until': None
                }
            
            backoff_info = self._api_backoff[api_name]
            backoff_info['failures'] += 1
            backoff_info['last_failure'] = datetime.now()
            
            # Calculate exponential backoff: base * 2^(failures-1)
            # Example: 1s, 2s, 4s, 8s, 16s, ... up to max_backoff
            backoff_seconds = min(
                config['base_backoff'] * (2 ** (backoff_info['failures'] - 1)),
                config['max_backoff']
            )
            
            backoff_info['backoff_until'] = datetime.now() + timedelta(seconds=backoff_seconds)
            
            print(f"⚠️ API {api_name} failure #{backoff_info['failures']} - backoff {backoff_seconds}s")
            
            return backoff_seconds
        
        except Exception as e:
            print(f"❌ Error recording API failure: {e}")
            return 0
    
    def record_api_success(self, api_name: str):
        """
        Record an API success and reset backoff
        
        Args:
            api_name: Name of the API
        """
        try:
            if api_name in self._api_backoff:
                # Reset backoff on success
                del self._api_backoff[api_name]
                print(f"✅ API {api_name} success - backoff reset")
        
        except Exception as e:
            print(f"❌ Error recording API success: {e}")
    
    def get_rate_limit_status(self, user_id: int) -> Dict[str, any]:
        """
        Get current rate limit status for a user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict with rate limit status for each operation
        """
        try:
            status = {}
            
            for operation in ['spawn', 'withdrawal']:
                config = self.limits[operation]
                history = self._rate_limits[user_id][operation]
                
                # Clean up old entries
                cutoff_time = datetime.now() - timedelta(seconds=config['window_seconds'])
                history = [ts for ts in history if ts > cutoff_time]
                
                remaining = config['max_requests'] - len(history)
                
                # Calculate reset time
                if history:
                    oldest = min(history)
                    reset_time = oldest + timedelta(seconds=config['window_seconds'])
                else:
                    reset_time = None
                
                status[operation] = {
                    'used': len(history),
                    'limit': config['max_requests'],
                    'remaining': max(0, remaining),
                    'reset_time': reset_time.isoformat() if reset_time else None,
                    'window_hours': config['window_seconds'] / 3600
                }
            
            return status
        
        except Exception as e:
            print(f"❌ Error getting rate limit status: {e}")
            return {}
    
    def reset_user_limits(self, user_id: int, operation: Optional[str] = None):
        """
        Reset rate limits for a user (admin function)
        
        Args:
            user_id: Telegram user ID
            operation: Specific operation to reset, or None for all
        """
        try:
            if operation:
                if user_id in self._rate_limits and operation in self._rate_limits[user_id]:
                    self._rate_limits[user_id][operation] = []
                    print(f"🔄 Reset {operation} rate limit for user {user_id}")
            else:
                if user_id in self._rate_limits:
                    self._rate_limits[user_id] = defaultdict(list)
                    print(f"🔄 Reset all rate limits for user {user_id}")
        
        except Exception as e:
            print(f"❌ Error resetting rate limits: {e}")
    
    def cleanup_old_entries(self):
        """
        Clean up old rate limit entries to prevent memory bloat
        Should be called periodically (e.g., hourly)
        """
        try:
            cleaned_users = 0
            cleaned_entries = 0
            
            for user_id in list(self._rate_limits.keys()):
                for operation in list(self._rate_limits[user_id].keys()):
                    config = self.limits.get(operation)
                    if not config:
                        continue
                    
                    # Remove entries older than the time window
                    cutoff_time = datetime.now() - timedelta(seconds=config['window_seconds'])
                    old_count = len(self._rate_limits[user_id][operation])
                    self._rate_limits[user_id][operation] = [
                        ts for ts in self._rate_limits[user_id][operation] 
                        if ts > cutoff_time
                    ]
                    new_count = len(self._rate_limits[user_id][operation])
                    cleaned_entries += (old_count - new_count)
                    
                    # Remove empty operation lists
                    if not self._rate_limits[user_id][operation]:
                        del self._rate_limits[user_id][operation]
                
                # Remove empty user entries
                if not self._rate_limits[user_id]:
                    del self._rate_limits[user_id]
                    cleaned_users += 1
            
            if cleaned_entries > 0 or cleaned_users > 0:
                print(f"🧹 Cleaned up {cleaned_entries} old rate limit entries for {cleaned_users} users")
        
        except Exception as e:
            print(f"❌ Error cleaning up rate limits: {e}")


# Singleton instance
_rate_limiter = None


def get_rate_limiter(db=None):
    """
    Get singleton Rate Limiter instance
    
    Args:
        db: Database instance (optional)
        
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(db)
    return _rate_limiter

    def check_ai_signal_limit(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user can request an AI signal
        
        Limit: 10 AI signals per hour per user
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        try:
            operation = 'ai_signal'
            config = self.limits[operation]
            
            # Get user's AI signal history
            signal_history = self._rate_limits[user_id][operation]
            
            # Clean up old entries outside the time window
            cutoff_time = datetime.now() - timedelta(seconds=config['window_seconds'])
            signal_history = [ts for ts in signal_history if ts > cutoff_time]
            self._rate_limits[user_id][operation] = signal_history
            
            # Check if limit exceeded
            if len(signal_history) >= config['max_requests']:
                # Calculate time until next allowed signal
                oldest_signal = min(signal_history)
                next_allowed = oldest_signal + timedelta(seconds=config['window_seconds'])
                time_remaining = next_allowed - datetime.now()
                
                minutes_remaining = int(time_remaining.total_seconds() / 60)
                
                error_msg = (
                    f"⏱️ Rate limit exceeded!\n\n"
                    f"You can only request {config['max_requests']} AI signals per hour.\n"
                    f"Please wait {minutes_remaining} minutes before requesting another signal."
                )
                
                print(f"🚫 AI signal rate limit exceeded for user {user_id} - {minutes_remaining} minutes remaining")
                return False, error_msg
            
            # Limit not exceeded, record this attempt
            signal_history.append(datetime.now())
            self._rate_limits[user_id][operation] = signal_history
            
            print(f"✅ AI signal rate limit check passed for user {user_id} ({len(signal_history)}/{config['max_requests']})")
            return True, None
        
        except Exception as e:
            print(f"❌ Error checking AI signal rate limit: {e}")
            # On error, allow the operation (fail open for better UX)
            return True, None
