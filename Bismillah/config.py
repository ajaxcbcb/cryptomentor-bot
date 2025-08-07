
import os
import logging

# API Base URLs
COINGLASS_V4_BASE_URL = "https://open-api.coinglass.com/public/v4"
COINGLASS_PRO_BASE_URL = "https://open-api.coinglass.com/api/pro/v1"
COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com"
BINANCE_FUTURES_BASE_URL = "https://fapi.binance.com/fapi/v1"
BINANCE_SPOT_BASE_URL = "https://api.binance.com/api/v3"

# API Keys from Environment
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")
CMC_API_KEY = os.getenv("CMC_API_KEY") or os.getenv("COINMARKETCAP_API_KEY")

# Headers Configuration
def get_coinglass_headers():
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "CryptoMentor-Bot/2.0"
    }
    if COINGLASS_API_KEY:
        headers["X-API-KEY"] = COINGLASS_API_KEY
    return headers

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
COINGLASS_ENDPOINTS = {
    "ticker": f"{COINGLASS_V4_BASE_URL}/ticker",
    "open_interest": f"{COINGLASS_V4_BASE_URL}/openInterest", 
    "funding_rate": f"{COINGLASS_V4_BASE_URL}/fundingRate",
    "long_short_ratio": f"{COINGLASS_PRO_BASE_URL}/futures/long_short_account_ratio",
    "liquidation": f"{COINGLASS_PRO_BASE_URL}/futures/liquidation_chart"
}

COINMARKETCAP_ENDPOINTS = {
    "quotes": f"{COINMARKETCAP_BASE_URL}/v1/cryptocurrency/quotes/latest",
    "info": f"{COINMARKETCAP_BASE_URL}/v1/cryptocurrency/info",
    "global_metrics": f"{COINMARKETCAP_BASE_URL}/v1/global-metrics/quotes/latest",
    "listings": f"{COINMARKETCAP_BASE_URL}/v1/cryptocurrency/listings/latest"
}

BINANCE_ENDPOINTS = {
    "futures_ticker": f"{BINANCE_FUTURES_BASE_URL}/ticker/24hr",
    "futures_funding": f"{BINANCE_FUTURES_BASE_URL}/fundingRate",
    "spot_ticker": f"{BINANCE_SPOT_BASE_URL}/ticker/24hr",
    "exchange_info": f"{BINANCE_FUTURES_BASE_URL}/exchangeInfo"
}

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API Status Check
def check_api_keys():
    status = {
        'coinglass': bool(COINGLASS_API_KEY),
        'coinmarketcap': bool(CMC_API_KEY),
        'binance': True  # Public API, no key needed
    }
    
    logging.info(f"API Keys Status: CoinGlass={'✅' if status['coinglass'] else '❌'}, "
                f"CMC={'✅' if status['coinmarketcap'] else '❌'}, Binance=✅")
    
    return status

# Cache Configuration
CACHE_TIMEOUT = {
    'price_data': 30,      # 30 seconds for price data
    'futures_data': 60,    # 1 minute for futures data
    'market_data': 300,    # 5 minutes for market overview
    'coin_info': 3600      # 1 hour for coin info
}
