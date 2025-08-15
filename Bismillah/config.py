import os
import logging

# API Base URLs - Only Binance and CoinMarketCap
COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com"
BINANCE_FUTURES_BASE_URL = "https://fapi.binance.com/fapi/v1"
BINANCE_SPOT_BASE_URL = "https://api.binance.com/api/v3"

# API Keys from Environment - Only CMC needed
CMC_API_KEY = os.getenv("CMC_API_KEY") or os.getenv("COINMARKETCAP_API_KEY")

# Headers Configuration
def get_coinmarketcap_headers():
    headers = {
        "Accepts": "application/json",
        "Accept-Encoding": "deflate, gzip",
        "User-Agent": "CryptoMentor-Bot/2.0"
    }
    if CMC_API_KEY:
        headers["X-CMC_PRO_API_KEY"] = CMC_API_KEY
    return headers

def get_binance_headers():
    return {
        "User-Agent": "CryptoMentor-Bot/2.0",
        "Accept": "application/json"
    }

# API Endpoints
COINMARKETCAP_ENDPOINTS = {
    "quotes": f"{COINMARKETCAP_BASE_URL}/v1/cryptocurrency/quotes/latest",
    "info": f"{COINMARKETCAP_BASE_URL}/v1/cryptocurrency/info",
    "global_metrics": f"{COINMARKETCAP_BASE_URL}/v1/global-metrics/quotes/latest",
    "listings": f"{COINMARKETCAP_BASE_URL}/v1/cryptocurrency/listings/latest"
}

BINANCE_ENDPOINTS = {
    "futures_ticker": f"{BINANCE_FUTURES_BASE_URL}/ticker/24hr",
    "futures_funding": f"{BINANCE_FUTURES_BASE_URL}/fundingRate",
    "futures_open_interest": f"{BINANCE_FUTURES_BASE_URL}/openInterest",
    "long_short_ratio": f"{BINANCE_FUTURES_BASE_URL}/topLongShortAccountRatio",
    "long_short_position": f"{BINANCE_FUTURES_BASE_URL}/topLongShortPositionRatio",
    "spot_ticker": f"{BINANCE_SPOT_BASE_URL}/ticker/24hr",
    "exchange_info": f"{BINANCE_FUTURES_BASE_URL}/exchangeInfo",
    "klines": f"{BINANCE_FUTURES_BASE_URL}/klines"
}

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API Status Check
def check_api_keys():
    status = {
        'coinmarketcap': bool(CMC_API_KEY),
        'binance': True  # Public API, no key needed
    }

    logging.info(f"API Keys Status: CMC={'✅' if status['coinmarketcap'] else '❌'}, Binance=✅")

    return status

# Cache Configuration
CACHE_TIMEOUT = {
    'price_data': 30,      # 30 seconds for price data
    'futures_data': 60,    # 1 minute for futures data
    'market_data': 300,    # 5 minutes for market overview
    'coin_info': 3600      # 1 hour for coin info
}
import os
from dotenv import load_dotenv

load_dotenv()

# Feature flags for enabling/disabling specific features
AUTO_SIGNALS_ENABLED = os.getenv("AUTO_SIGNALS_ENABLED", "false").lower() in ("1", "true", "yes")
USE_LEGACY_FUTURES_SIGNALS = os.getenv("USE_LEGACY_FUTURES_SIGNALS", "true").lower() in ("1","true","yes")

# Bot configuration
BOT_TOKEN = os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
ADMIN2_USER_ID = os.getenv('ADMIN2_USER_ID')
ADMIN = os.getenv('ADMIN')

# API Keys
COINMARKETCAP_API_KEY = os.getenv('CMC_API_KEY') or os.getenv('COINMARKETCAP_API_KEY')
COINAPI_KEY = os.getenv('COINAPI_API_KEY')

print(f"🔧 Config loaded - Auto Signals: {'ON' if AUTO_SIGNALS_ENABLED else 'OFF'}")