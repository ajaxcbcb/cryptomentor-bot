
# app/providers/binance_provider.py
from __future__ import annotations
import os, time, logging, random
from typing import Any, Dict, List, Optional, Set
import httpx

BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")
BINANCE_FAPI_BASE_URL = os.getenv("BINANCE_FAPI_BASE_URL", "https://fapi.binance.com")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))
BACKOFF_BASE = float(os.getenv("HTTP_BACKOFF_BASE", "0.6"))  # seconds

logger = logging.getLogger(__name__)

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
        # Primary HTTP/2 client with header rotation for Binance
        http2_config = {
            "timeout": HTTP_TIMEOUT,
            "follow_redirects": True,
            "http2": True,  # HTTP/2 primary
            "limits": httpx.Limits(max_connections=10, max_keepalive_connections=5),
            "headers": {
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
        
        # Fallback HTTP/1.1 client (HTTP/3 not always stable)
        http11_config = {
            "timeout": HTTP_TIMEOUT,
            "follow_redirects": True,
            "http2": False,  # HTTP/1.1 fallback
            "limits": httpx.Limits(max_connections=10, max_keepalive_connections=5),
            "headers": {
                "Accept-Encoding": "gzip, deflate",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }
        
        self.client_http2 = httpx.Client(**http2_config)
        self.client_http11 = httpx.Client(**http11_config)
        self.current_client = self.client_http2
        self.invalid_symbols: Set[str] = set()
        self.request_count = 0
        self.rotation_interval = random.randint(3, 5)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
        ]
        
        logger.info("✅ HTTP/2 + HTTP/1.1 ENABLED with User-Agent rotation (every 3-5 requests)")
        
    def _rotate_headers(self):
        """Rotate User-Agent every 3-5 requests to avoid Binance 400 errors"""
        self.request_count += 1
        
        if self.request_count >= self.rotation_interval:
            new_agent = random.choice(self.user_agents)
            self.client_http2.headers.update({"User-Agent": new_agent})
            self.client_http11.headers.update({"User-Agent": new_agent})
            self.request_count = 0
            self.rotation_interval = random.randint(3, 5)
            logger.debug(f"🔄 Rotated User-Agent (HTTP/2 active), next rotation in {self.rotation_interval} requests")
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        # Check if symbol is known to be invalid (circuit breaker)
        if params and "symbol" in params:
            symbol = params["symbol"]
            if symbol in self.invalid_symbols:
                logger.debug(f"Skipping known invalid symbol: {symbol}")
                return None
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                _rps.acquire()
                self._rotate_headers()
                
                # Try HTTP/2 first, fallback to HTTP/1.1 on errors
                try:
                    r = self.client_http2.get(url, params=params, headers={"Accept": "application/json"})
                except (httpx.ConnectError, httpx.TimeoutException):
                    logger.debug(f"HTTP/2 failed, switching to HTTP/1.1 (attempt {attempt}/{MAX_RETRIES})")
                    r = self.client_http11.get(url, params=params, headers={"Accept": "application/json"})
                
                # 400 = Bad Request (invalid symbol - don't retry)
                if r.status_code == 400:
                    if params and "symbol" in params:
                        self.invalid_symbols.add(params["symbol"])
                        logger.debug(f"Symbol {params['symbol']} is invalid (400), caching")
                    return r
                
                # 429 = Rate Limited, 5xx = Server Error (retry with fallback)
                if r.status_code in (429,) or r.status_code >= 500:
                    logger.debug(f"Retrying (HTTP/2→HTTP/1.1) due to status {r.status_code} (attempt {attempt}/{MAX_RETRIES})")
                    time.sleep(BACKOFF_BASE * (2 ** (attempt - 1)))
                    continue
                
                r.raise_for_status()
                return r
            except httpx.HTTPError as e:
                if attempt == MAX_RETRIES:
                    logger.error(f"HTTP error after {MAX_RETRIES} retries: {e}")
                    raise
                logger.debug(f"HTTP error, retrying (attempt {attempt}/{MAX_RETRIES})")
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
    
    # Check for BTC, ETH pairs (e.g., SOLBTC, ETHBTC) - but NOT if the symbol IS BTC/ETH
    quote_assets = ("BTC", "ETH")
    for quote in quote_assets:
        if s.endswith(quote) and len(s) > len(quote):
            return s  # It's a pair like SOLBTC
    
    # For base symbols like BTC, ETH, SOL, XRP, BNB → add USDT
    if 2 <= len(s) <= 10:  # Extended range for longer symbols
        return s + "USDT"
    return s

def normalize_symbol(symbol: str) -> str:
    """Terima 'btc', 'BTC/USDT', 'btc-usdt' → 'BTCUSDT' (default pair USDT)."""
    s = symbol.replace("/", "").replace("-", "").upper().strip()
    
    # Special mappings for coins with different symbols on Binance
    # Note: ASTER and ASTR are different coins, don't map them
    symbol_mappings = {
        # Add other mappings here if needed, but ASTER ≠ ASTR
    }
    
    # Check if this is a base symbol that needs mapping
    for old_symbol, new_symbol in symbol_mappings.items():
        if s == old_symbol or s.startswith(old_symbol):
            s = s.replace(old_symbol, new_symbol)
            break
    
    return _append_usdt_if_base_only(s)

def get_price(symbol: str, futures: bool = False) -> float:
    """Get price with enhanced validation and error handling"""
    sym = normalize_symbol(symbol)
    base = _base_url(futures)
    ep = "/fapi/v1/ticker/price" if futures else "/api/v3/ticker/price"
    
    # Enhanced retry mechanism with exponential backoff
    max_retries = 3
    base_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            r = _http.get(base + ep, params={"symbol": sym})
            data = r.json()
            
            # Enhanced error detection and handling
            if isinstance(data, dict):
                if "code" in data:
                    error_code = data.get("code")
                    error_msg = data.get("msg", "Unknown error")
                    
                    # Specific error handling
                    if error_code == -1121:
                        raise ValueError(f"Symbol {sym} not found on Binance: {error_msg}")
                    elif error_code == -1003:  # Too many requests
                        if attempt < max_retries - 1:
                            time.sleep(base_delay * (2 ** attempt))
                            continue
                        raise ValueError(f"Rate limit exceeded for {sym}")
                    elif error_code in [-1000, -1001, -1002]:
                        raise ValueError(f"Binance API error {error_code}: {error_msg}")
                    else:
                        raise ValueError(f"Binance error {error_code}: {error_msg}")
                
                # Enhanced price data validation
                if "price" in data:
                    try:
                        price = float(data["price"])
                        
                        # Comprehensive price validation
                        if price <= 0:
                            raise ValueError(f"Invalid price for {sym}: {price}")
                        
                        # Range validation (reasonable price range)
                        if not (0.000001 <= price <= 10000000):
                            raise ValueError(f"Price out of reasonable range for {sym}: {price}")
                        
                        # Check for NaN or infinite values
                        if not (price == price):  # NaN check
                            raise ValueError(f"Price is NaN for {sym}")
                        
                        if price == float('inf') or price == float('-inf'):
                            raise ValueError(f"Price is infinite for {sym}")
                        
                        return price
                        
                    except (ValueError, TypeError) as e:
                        raise ValueError(f"Price conversion error for {sym}: {e}")
                else:
                    raise ValueError(f"No price field in response for {sym}")
            else:
                raise ValueError(f"Unexpected response format for {sym}: {type(data)}")
                
        except ValueError:
            # Re-raise ValueError as is (no retry)
            raise
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
                continue
            # Convert other exceptions to ValueError for consistency
            raise ValueError(f"Failed to get price for {sym} after {max_retries} attempts: {str(e)}")
    
    raise ValueError(f"Exhausted all retry attempts for {sym}")

def get_enhanced_ticker_data(symbol: str, futures: bool = False) -> Dict[str, Any]:
    """Get comprehensive 24h ticker data with validation"""
    sym = normalize_symbol(symbol)
    base = _base_url(futures)
    ep = "/fapi/v1/ticker/24hr" if futures else "/api/v3/ticker/24hr"
    
    try:
        r = _http.get(base + ep, params={"symbol": sym})
        data = r.json()
        
        # Enhanced error handling
        if isinstance(data, dict) and "code" in data:
            error_code = data.get("code")
            error_msg = data.get("msg", "Unknown error")
            raise ValueError(f"Binance ticker error {error_code} for {sym}: {error_msg}")
        
        # Comprehensive data validation
        required_fields = ['lastPrice', 'priceChangePercent', 'volume', 'highPrice', 'lowPrice', 'count']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields for {sym}: {missing_fields}")
        
        # Extract and validate numeric data
        try:
            price = float(data['lastPrice'])
            change_24h = float(data['priceChangePercent'])
            volume = float(data['volume'])
            high_24h = float(data['highPrice'])
            low_24h = float(data['lowPrice'])
            trade_count = int(data['count'])
            
            # Sanity checks
            if not (0 < price <= 10000000):
                raise ValueError(f"Invalid price range for {sym}: {price}")
            
            if not (low_24h <= price <= high_24h):
                raise ValueError(f"Price {price} not within 24h range [{low_24h}, {high_24h}] for {sym}")
            
            if volume < 0:
                raise ValueError(f"Negative volume for {sym}: {volume}")
            
            if trade_count < 0:
                raise ValueError(f"Negative trade count for {sym}: {trade_count}")
            
            # Calculate additional metrics
            volume_usd = volume * price
            spread_percent = ((high_24h - low_24h) / low_24h * 100) if low_24h > 0 else 0
            
            return {
                'symbol': sym,
                'price': price,
                'change_24h': change_24h,
                'volume': volume,
                'volume_usd': volume_usd,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'trade_count': trade_count,
                'spread_percent': spread_percent,
                'open_time': data.get('openTime'),
                'close_time': data.get('closeTime'),
                'source': 'binance_futures' if futures else 'binance_spot',
                'validated': True
            }
            
        except (ValueError, TypeError) as e:
            raise ValueError(f"Data conversion error for {sym}: {e}")
            
    except Exception as e:
        raise ValueError(f"Failed to get ticker data for {sym}: {str(e)}")

def get_24h_change(symbol: str) -> float:
    """Get 24h percentage change quickly"""
    try:
        ticker = get_enhanced_ticker_data(symbol)
        return float(ticker.get('change_24h', 0))
    except:
        return 0.0

def validate_symbol_exists(symbol: str, futures: bool = False) -> bool:
    """Validate if symbol exists on Binance with comprehensive checking"""
    try:
        sym = normalize_symbol(symbol)
        
        # Try to get exchange info first (more reliable)
        exchange_data = exchange_info(sym, futures)
        
        if 'symbols' in exchange_data:
            symbols = exchange_data['symbols']
            if isinstance(symbols, list) and len(symbols) > 0:
                symbol_data = symbols[0]
                status = symbol_data.get('status', '')
                return status == 'TRADING'
        
        # Fallback: try to get price
        try:
            price = get_price(sym, futures)
            return price > 0
        except:
            return False
            
    except Exception:
        return False

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
