import os
import requests
import time
from typing import Dict, Any, Optional

# Mapping symbol user-friendly ke CoinGlass format
SYMBOL_MAP = {
    "BTC": "BINANCE_BTCUSDT",
    "ETH": "BINANCE_ETHUSDT",
    "BNB": "BINANCE_BNBUSDT",
    "SOL": "BINANCE_SOLUSDT",
    "XRP": "BINANCE_XRPUSDT",
    "ADA": "BINANCE_ADAUSDT",
    "DOGE": "BINANCE_DOGEUSDT",
    "AVAX": "BINANCE_AVAXUSDT",
    "DOT": "BINANCE_DOTUSDT",
    "LINK": "BINANCE_LINKUSDT",
    "MATIC": "BINANCE_MATICUSDT",
    "LTC": "BINANCE_LTCUSDT",
    "BCH": "BINANCE_BCHUSDT",
    "NEAR": "BINANCE_NEARUSDT",
    "UNI": "BINANCE_UNIUSDT",
    "APT": "BINANCE_APTUSDT",
    "ATOM": "BINANCE_ATOMUSDT",
    "FIL": "BINANCE_FILUSDT",
    "ETC": "BINANCE_ETCUSDT",
    "ALGO": "BINANCE_ALGOUSDT",
    "VET": "BINANCE_VETUSDT",
    "MANA": "BINANCE_MANAUSDT",
    "SAND": "BINANCE_SANDUSDT"
}

BASE_URL = "https://open-api-v4.coinglass.com/public/v4/futures/"
HEADERS = {
    "accept": "application/json",
    "X-API-KEY": os.getenv("COINGLASS_API_KEY")
}

def map_symbol(symbol: str) -> str:
    """Map user input symbol to CoinGlass format"""
    clean_symbol = symbol.upper().replace('USDT', '')
    return SYMBOL_MAP.get(clean_symbol, f"BINANCE_{clean_symbol}USDT")

def _make_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make request to CoinGlass API with error handling"""
    if not HEADERS["X-API-KEY"]:
        return {'error': 'CoinGlass API key not configured'}
    
    try:
        url = BASE_URL + endpoint
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Check if the response structure is as expected or contains an error message
            if "data" in data:
                return data["data"]
            elif "msg" in data:
                return {'error': f'API returned error: {data.get("msg", "Unknown error")}'}
            else:
                # Handle cases where the response is 200 but doesn't contain expected 'data' or 'msg'
                return {'error': f'API returned unexpected success format: {data}'}
        else:
            return {'error': f'HTTP {response.status_code}: {response.text[:100]}'}
            
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout'}
    except requests.exceptions.RequestException as e:
        return {'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_futures_ticker(symbol: str) -> Dict[str, Any]:
    """Get futures ticker data"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'time_type': '15min',
        'currency': 'USDT'
    }
    
    return _make_request('ticker', params)

def get_open_interest_chart(symbol: str, time_type: str = "15min") -> Dict[str, Any]:
    """Get open interest chart data"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'time_type': time_type,
        'currency': 'USDT'
    }
    
    return _make_request('openInterest', params)

def get_funding_rate_chart(symbol: str, time_type: str = "15min") -> Dict[str, Any]:
    """Get funding rate chart data"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'time_type': time_type,
        'currency': 'USDT'
    }
    
    return _make_request('fundingRate', params)

def get_long_short_ratio(symbol: str, time_type: str = "15min") -> Dict[str, Any]:
    """Get long/short ratio data"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'time_type': time_type,
        'currency': 'USDT'
    }
    
    return _make_request('longShortRatio', params)

def get_liquidation_map(symbol: str, time_type: str = "15min") -> Dict[str, Any]:
    """Get liquidation map data"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'time_type': time_type,
        'currency': 'USDT'
    }
    
    return _make_request('liquidationMap', params)

def get_liquidation_chart(symbol: str, time_type: str = "15min") -> Dict[str, Any]:
    """Get liquidation chart data"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'time_type': time_type,
        'currency': 'USDT'
    }
    
    return _make_request('liquidation', params)

def get_open_interest_by_exchange(symbol: str) -> Dict[str, Any]:
    """Get open interest by exchange"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'currency': 'USDT'
    }
    
    return _make_request('openInterest/oiWeight', params)

def get_volume_chart(symbol: str, time_type: str = "15min") -> Dict[str, Any]:
    """Get volume chart data"""
    mapped_symbol = map_symbol(symbol)
    
    params = {
        'symbol': mapped_symbol,
        'time_type': time_type,
        'currency': 'USDT'
    }
    
    return _make_request('volume', params)

def get_comprehensive_data(symbol: str) -> Dict[str, Any]:
    """Get comprehensive data from all available endpoints"""
    if not HEADERS["X-API-KEY"]:
        return {'error': 'CoinGlass API key not configured'}

    print(f"🔄 Getting comprehensive CoinGlass data for {symbol}...")
    
    data_container = {
        'symbol': symbol,
        'mapped_symbol': map_symbol(symbol),
        'endpoints_called': 0,
        'endpoints_successful': 0,
        'data_quality': 'unknown',
        'timestamp': int(time.time())
    }
    
    # Get data from all endpoints
    endpoints = [
        ('ticker', get_futures_ticker),
        ('open_interest', get_open_interest_chart),
        ('funding_rate', get_funding_rate_chart),
        ('long_short_ratio', get_long_short_ratio),
        ('liquidation_map', get_liquidation_map),
        ('liquidation_chart', get_liquidation_chart),
        ('volume', get_volume_chart)
    ]
    
    for endpoint_name, endpoint_func in endpoints:
        try:
            data_container['endpoints_called'] += 1
            result = endpoint_func(symbol)
            
            if 'error' not in result:
                data_container[endpoint_name] = result
                data_container['endpoints_successful'] += 1
            else:
                data_container[endpoint_name] = result
                
        except Exception as e:
            data_container[endpoint_name] = {'error': f'Exception: {str(e)}'}
    
    # Calculate data quality
    if data_container['endpoints_called'] > 0:
        success_rate = data_container['endpoints_successful'] / data_container['endpoints_called']
        
        if success_rate >= 0.8:
            data_container['data_quality'] = 'excellent'
        elif success_rate >= 0.6:
            data_container['data_quality'] = 'good'
        elif success_rate >= 0.4:
            data_container['data_quality'] = 'partial'
        else:
            data_container['data_quality'] = 'poor'
    else:
        data_container['data_quality'] = 'no_endpoints'
    
    print(f"✅ CoinGlass data: {data_container['endpoints_successful']}/{data_container['endpoints_called']} endpoints successful")
    return data_container
    

def test_connection() -> Dict[str, Any]:
    """Test CoinGlass API connection"""
    if not HEADERS["X-API-KEY"]:
        return {'status': 'failed', 'error': 'API key not configured'}
    
    try:
        # Test with BTC ticker
        result = get_futures_ticker('BTC')
        
        if 'error' not in result:
            return {'status': 'success', 'message': 'CoinGlass API connection successful'}
        else:
            return {'status': 'failed', 'error': result['error']}
            
    except Exception as e:
        return {'status': 'failed', 'error': f'Connection test failed: {str(e)}'}

def get_supported_symbols() -> list:
    """Get list of supported symbols"""
    return list(SYMBOL_MAP.keys())

def is_symbol_supported(symbol: str) -> bool:
    """Check if symbol is supported"""
    clean_symbol = symbol.upper().replace('USDT', '')
    return clean_symbol in SYMBOL_MAP

# If CoinGlass API key is not set, print a warning
if not HEADERS["X-API-KEY"]:
    print("⚠️ COINGLASS_API_KEY not found in environment variables")
    print("💡 Please set COINGLASS_API_KEY in Replit Secrets")