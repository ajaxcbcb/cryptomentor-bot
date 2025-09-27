
# app/providers/binance_provider.py
from __future__ import annotations
import os, time
from typing import Any, Dict, List, Optional
import httpx

BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
BINANCE_FAPI_BASE_URL = os.getenv("BINANCE_FAPI_BASE_URL", "https://fapi.binance.com")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("HTTP_BACKOFF_BASE", "0.6"))  # seconds

class _RPS:
    def __init__(self, rps: float = 9.0):
        self.rate = max(rps, 1.0)
        self.tokens = self.rate
        self.last = time.monotonic()
    def acquire(self):
        now = time.monotonic()
        dt = now - self.last
        self.last = now
        self.tokens = min(self.rate, self.tokens + dt * self.rate)
        if self.tokens < 1.0:
            time.sleep((1.0 - self.tokens) / self.rate)
            self.tokens = 0.0
        else:
            self.tokens -= 1.0

_rps = _RPS()

class _HTTP:
    def __init__(self):
        self.client = httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                _rps.acquire()
                r = self.client.get(url, params=params, headers={"Accept": "application/json"})
                if r.status_code in (429,) or r.status_code >= 500:
                    time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))
                    continue
                r.raise_for_status()
                return r
            except httpx.HTTPError:
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))

_http = _HTTP()

# Interval map (gunakan huruf kecil 'h', dll.)
BINANCE_INTERVALS = {
    "1m":"1m","3m":"3m","5m":"5m","15m":"15m","30m":"30m",
    "1h":"1h","2h":"2h","4h":"4h","6h":"6h","8h":"8h","12h":"12h",
    "1d":"1d","3d":"3d","1w":"1w","1M":"1M",
}

def _base_url(futures: bool) -> str:
    return BINANCE_FAPI_BASE_URL if futures else BINANCE_BASE_URL

def _append_usdt_if_base_only(s: str) -> str:
    stables = ("USDT","FDUSD","USDC","BUSD","TUSD")
    if any(s.endswith(x) for x in stables):
        return s
    # BTC, ETH, SOL, XRP, BNB → default ke USDT
    if 3 <= len(s) <= 5:
        return s + "USDT"
    return s

def normalize_symbol(symbol: str) -> str:
    """Terima 'btc', 'BTC/USDT', 'btc-usdt' → 'BTCUSDT' (default pair USDT)."""
    try:
        s = symbol.replace("/", "").replace("-", "").upper().strip()
        normalized = _append_usdt_if_base_only(s)
        print(f"🔄 Symbol normalization: {symbol} -> {normalized}")
        return normalized
    except Exception as e:
        print(f"❌ Error normalizing symbol {symbol}: {e}")
        return f"{symbol.upper()}USDT"

def get_price(symbol: str, futures: bool = False) -> float:
    try:
        sym = normalize_symbol(symbol)
        base = _base_url(futures)
        ep = "/fapi/v1/ticker/price" if futures else "/api/v3/ticker/price"
        
        print(f"🌐 Fetching price from: {base + ep}?symbol={sym}")
        r = _http.get(base + ep, params={"symbol": sym})
        data = r.json()
        
        if "price" not in data:
            print(f"❌ No price in response: {data}")
            if "msg" in data:
                print(f"❌ Binance error: {data['msg']}")
            return 0.0
            
        price = float(data["price"])
        print(f"✅ Got price for {sym}: ${price}")
        return price
        
    except Exception as e:
        print(f"❌ Error getting price for {symbol}: {e}")
        return 0.0

def fetch_klines(symbol: str, interval: str, limit: int = 200, futures: bool = False) -> List[List[Any]]:
    sym = normalize_symbol(symbol)
    interval = BINANCE_INTERVALS.get(interval, interval)
    if interval not in BINANCE_INTERVALS.values():
        raise ValueError(f"Unsupported interval: {interval}")
    base = _base_url(futures)
    ep = "/fapi/v1/klines" if futures else "/api/v3/klines"
    r = _http.get(base + ep, params={"symbol": sym, "interval": interval, "limit": min(limit, 1500)})
    return r.json()

def exchange_info(symbol: Optional[str] = None, futures: bool = False) -> Dict[str, Any]:
    base = _base_url(futures)
    ep = "/fapi/v1/exchangeInfo" if futures else "/api/v3/exchangeInfo"
    params = {"symbol": normalize_symbol(symbol)} if symbol else None
    r = _http.get(base + ep, params=params)
    return r.json()
