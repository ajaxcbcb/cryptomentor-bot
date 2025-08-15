
from __future__ import annotations
import time
import asyncio
from typing import Dict, Tuple, Callable, Awaitable, Optional, Hashable

# Import config safely with fallback
try:
    from app.config import USE_RATE_LIMIT, RATE_LIMIT_QPS, BURST_TOKENS
except ImportError:
    # Fallback if config not available
    import os
    USE_RATE_LIMIT = os.getenv("USE_RATE_LIMIT", "true").lower() in ("1", "true", "yes")
    RATE_LIMIT_QPS = float(os.getenv("RATE_LIMIT_QPS", "1.5"))
    BURST_TOKENS = int(os.getenv("BURST_TOKENS", "3"))

class RateLimiter:
    """
    Token-bucket per key (mis. per-user atau per-command).
    - qps: token per detik (rata-rata)
    - burst: jumlah token maksimum (burst allowance)
    - key: (scope, user_id) tuple, atau string lain yang hashable
    """
    def __init__(self, qps: float = 1.0, burst: int = 3):
        self.qps = max(0.01, qps)
        self.burst = max(1, burst)
        self._store: Dict[Hashable, Tuple[float, float]] = {}  # key -> (tokens, last_ts)
        self._lock = asyncio.Lock()

    def _refill(self, tokens: float, last_ts: float) -> Tuple[float, float]:
        now = time.monotonic()
        tokens = min(self.burst, tokens + (now - last_ts) * self.qps)
        return tokens, now

    async def allow(self, key: Hashable, cost: float = 1.0) -> bool:
        if not USE_RATE_LIMIT:
            return True
        async with self._lock:
            tokens, last_ts = self._store.get(key, (self.burst, time.monotonic()))
            tokens, now = self._refill(tokens, last_ts)
            if tokens >= cost:
                tokens -= cost
                self._store[key] = (tokens, now)
                return True
            # belum cukup token
            self._store[key] = (tokens, now)
            return False

    async def wait(self, key: Hashable, cost: float = 1.0) -> None:
        """Block until allowed (gunakan untuk internal jobs)."""
        if not USE_RATE_LIMIT:
            return
        while True:
            if await self.allow(key, cost):
                return
            # hitung waktu tunggu kira2
            await asyncio.sleep(max(0.05, cost / self.qps))

# ---- Instance global yang diharapkan ada oleh kode lain ----
rate_limiter = RateLimiter(qps=RATE_LIMIT_QPS, burst=BURST_TOKENS)

# ---- Decorator helper untuk handlers ----
def limit_command(scope: str, cost: float = 1.0):
    """
    Pakai di handler Telegram:
    @limit_command("analyze", cost=1)
    async def cmd_analyze(update, context): ...
    """
    def wrap(fn: Callable[..., Awaitable]):
        async def inner(*args, **kwargs):
            # cari update untuk ambil user.id
            update = None
            if args:
                for a in args:
                    # PTB: update arg pertama/ kedua
                    if getattr(a, "effective_user", None):
                        update = a
                        break
            if update and getattr(update, "effective_user", None):
                uid = str(update.effective_user.id)
                key = (scope, uid)
            else:
                key = (scope, "anonymous")

            if await rate_limiter.allow(key, cost=cost):
                return await fn(*args, **kwargs)
            else:
                # throttle message minimalis; jangan raise agar tidak crash
                try:
                    msg = getattr(update, "effective_message", None)
                    if msg:
                        await msg.reply_text("⏳ Terlalu banyak permintaan. Coba lagi sebentar...")
                except Exception:
                    pass
                return None
        return inner
    return wrap

# Legacy compatibility - keep existing classes for backward compatibility
class AsyncRateLimiter:
    """Async rate limiter with delay functionality"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        self.limiter = RateLimiter(max_calls, time_window)
    
    async def acquire(self, key: str) -> None:
        """Acquire rate limit permission, waiting if necessary"""
        await self.limiter.wait(key, 1.0)

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
