
import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str) -> bool:
        """Check if a call is allowed for the given key"""
        now = time.time()
        call_times = self.calls[key]
        
        # Remove old calls outside the time window
        while call_times and call_times[0] <= now - self.time_window:
            call_times.popleft()
        
        # Check if we're under the limit
        if len(call_times) < self.max_calls:
            call_times.append(now)
            return True
        
        return False
    
    def get_reset_time(self, key: str) -> Optional[float]:
        """Get the time when the rate limit will reset"""
        call_times = self.calls[key]
        if not call_times:
            return None
        
        return call_times[0] + self.time_window

class AsyncRateLimiter:
    """Async rate limiter with delay functionality"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        self.limiter = RateLimiter(max_calls, time_window)
    
    async def acquire(self, key: str) -> None:
        """Acquire rate limit permission, waiting if necessary"""
        while not self.limiter.is_allowed(key):
            reset_time = self.limiter.get_reset_time(key)
            if reset_time:
                wait_time = max(0, reset_time - time.time())
                if wait_time > 0:
                    await asyncio.sleep(min(wait_time, 1))  # Wait max 1 second at a time
            else:
                await asyncio.sleep(0.1)  # Small delay if no reset time

# Global rate limiters for different APIs
api_rate_limiters = {
    'coinapi': AsyncRateLimiter(max_calls=100, time_window=3600),  # 100 calls per hour
    'binance': AsyncRateLimiter(max_calls=1200, time_window=60),   # 1200 calls per minute
    'coinglass': AsyncRateLimiter(max_calls=300, time_window=60),  # 300 calls per minute
    'cmc': AsyncRateLimiter(max_calls=333, time_window=86400),     # 333 calls per day (basic plan)
}

async def rate_limit_api_call(api_name: str, key: str = "default"):
    """Apply rate limiting for API calls"""
    if api_name in api_rate_limiters:
        await api_rate_limiters[api_name].acquire(key)
