
import os

# Utama: COINAPI_API_KEY (baru). Legacy nama lama tetap di-support.
COINAPI_API_KEY = os.getenv("COINAPI_API_KEY") or os.getenv("COIN_API_KEY") or ""

# Optional fallbacks untuk spot price cepat
BINANCE_BASE = "https://api.binance.com"

# Default symbol mapping
SYMBOL_ALIAS = {
    "btc": "BTC",
    "eth": "ETH",
}

# Caching
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "15"))
