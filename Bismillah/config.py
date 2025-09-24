import os
import logging
from typing import Dict

# API Base URLs - Only Binance
BINANCE_FUTURES_BASE_URL = "https://fapi.binance.com/fapi/v1"
BINANCE_SPOT_BASE_URL = "https://api.binance.com/api/v3"

# API Keys from Environment - No API keys needed for public Binance endpoints
# CMC_API_KEY = os.getenv("CMC_API_KEY") or os.getenv("COINMARKETCAP_API_KEY")

# Headers Configuration
# Removed get_coinmarketcap_headers
def get_binance_headers() -> Dict[str, str]:
    """
    Headers untuk Binance API (public endpoints tidak perlu API key)
    """
    return {
        'Accept': 'application/json',
        'User-Agent': 'CryptoMentor-Bot'
    }

# API Endpoints
# Removed COINMARKETCAP_ENDPOINTS
BINANCE_ENDPOINTS = {
    'spot_price': f"{BINANCE_SPOT_BASE_URL}/ticker/price",
    'spot_24hr': f"{BINANCE_SPOT_BASE_URL}/ticker/24hr",
    'spot_klines': f"{BINANCE_SPOT_BASE_URL}/klines",
    'futures_price': f"{BINANCE_FUTURES_BASE_URL}/ticker/price",
    'futures_24hr': f"{BINANCE_FUTURES_BASE_URL}/ticker/24hr",
    'futures_klines': f"{BINANCE_FUTURES_BASE_URL}/klines",
    'exchange_info': f"{BINANCE_SPOT_BASE_URL}/exchangeInfo"
}

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# API Status Check
def check_api_keys():
    status = {
        # 'coinmarketcap': bool(CMC_API_KEY), # Removed CMC status
        'binance': True  # Public API, no key needed
    }

    # logging.info(f"API Keys Status: CMC={'✅' if status['coinmarketcap'] else '❌'}, Binance=✅") # Removed CMC logging
    logging.info(f"API Keys Status: Binance=✅")


    return status

# Cache Configuration
CACHE_TIMEOUT = {
    'price_data': 30,      # 30 seconds for price data
    'futures_data': 60,    # 1 minute for futures data
    'market_data': 300,    # 5 minutes for market overview
    'coin_info': 3600      # 1 hour for coin info
}