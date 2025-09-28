
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
    
    # Check for BTC, ETH pairs
    if any(s.endswith(x) for x in ("BTC", "ETH")):
        return s
    
    # For symbols like ASTER, BTC, ETH, SOL, XRP, BNB → default ke USDT
    if 2 <= len(s) <= 10:  # Extended range for longer symbols like ASTER
        return s + "USDT"
    return s

def normalize_symbol(symbol: str) -> str:
    """Terima 'btc', 'BTC/USDT', 'btc-usdt' → 'BTCUSDT' (default pair USDT)."""
    s = symbol.replace("/", "").replace("-", "").upper().strip()
    
    # Special mappings for coins with different symbols on Binance
    symbol_mappings = {
        'ASTER': 'ASTR',  # Astar Network uses ASTR on Binance, not ASTER
    }
    
    # Check if this is a base symbol that needs mapping
    for old_symbol, new_symbol in symbol_mappings.items():
        if s == old_symbol or s.startswith(old_symbol):
            s = s.replace(old_symbol, new_symbol)
            break
    
    return _append_usdt_if_base_only(s)

def get_price(symbol: str, futures: bool = False) -> float:
    sym = normalize_symbol(symbol)
    base = _base_url(futures)
    ep = "/fapi/v1/ticker/price" if futures else "/api/v3/ticker/price"
    
    try:
        r = _http.get(base + ep, params={"symbol": sym})
        data = r.json()
        
        # Better error detection
        if isinstance(data, dict):
            if "code" in data:
                error_code = data.get("code")
                error_msg = data.get("msg", "Unknown error")
                
                if error_code == -1121:
                    raise ValueError(f"Symbol {sym} not found on Binance: {error_msg}")
                elif error_code in [-1000, -1001, -1002]:
                    raise ValueError(f"Binance API error {error_code}: {error_msg}")
                else:
                    raise ValueError(f"Binance error {error_code}: {error_msg}")
            
            # Check if we have price data
            if "price" in data:
                price = float(data["price"])
                if price > 0:
                    return price
                else:
                    raise ValueError(f"Invalid price data for {sym}: {price}")
            else:
                raise ValueError(f"No price data returned for {sym}")
        else:
            raise ValueError(f"Unexpected response format for {sym}")
            
    except ValueError:
        # Re-raise ValueError as is
        raise
    except Exception as e:
        # Convert other exceptions to ValueError for consistency
        raise ValueError(f"Failed to get price for {sym}: {str(e)}")

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
