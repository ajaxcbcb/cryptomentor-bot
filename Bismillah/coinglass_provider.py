
import os
import requests
import time
from typing import Dict, Any, Optional

class CoinGlassProvider:
    """CoinGlass V4 API Provider with symbol mapping"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY")
        self.base_url = "https://open-api-v4.coinglass.com/public/v4/futures"
        
        # Symbol mapping for CoinGlass API
        self.SYMBOL_MAP = {
            "BTC": "BINANCE_BTCUSDT",
            "ETH": "BINANCE_ETHUSDT", 
            "BNB": "BINANCE_BNBUSDT",
            "ADA": "BINANCE_ADAUSDT",
            "SOL": "BINANCE_SOLUSDT",
            "XRP": "BINANCE_XRPUSDT",
            "DOGE": "BINANCE_DOGEUSDT",
            "AVAX": "BINANCE_AVAXUSDT",
            "SHIB": "BINANCE_SHIBUSDT",
            "DOT": "BINANCE_DOTUSDT",
            "LINK": "BINANCE_LINKUSDT",
            "TRX": "BINANCE_TRXUSDT",
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
        
        if not self.api_key:
            print("⚠️ COINGLASS_API_KEY not found in environment variables")
            print("💡 Please set COINGLASS_API_KEY in Replit Secrets")

    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for CoinGlass API"""
        return {
            "accept": "application/json",
            "X-API-KEY": self.api_key
        }

    def _map_symbol(self, symbol: str) -> str:
        """Map user input symbol to CoinGlass format"""
        clean_symbol = symbol.upper().replace('USDT', '')
        return self.SYMBOL_MAP.get(clean_symbol, f"BINANCE_{clean_symbol}USDT")

    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to CoinGlass API with error handling"""
        if not self.api_key:
            return {'error': 'CoinGlass API key not configured'}
        
        try:
            url = f"{self.base_url}/{endpoint}"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data
                else:
                    return {'error': f'API returned error: {data.get("msg", "Unknown error")}'}
            else:
                return {'error': f'HTTP {response.status_code}: {response.text[:100]}'}
                
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout'}
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}

    def get_futures_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get futures ticker data"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'time_type': '15min',
            'currency': 'USDT'
        }
        
        return self._make_request('ticker', params)

    def get_open_interest_chart(self, symbol: str, time_type: str = "15min") -> Dict[str, Any]:
        """Get open interest chart data"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'time_type': time_type,
            'currency': 'USDT'
        }
        
        return self._make_request('openInterest', params)

    def get_funding_rate_chart(self, symbol: str, time_type: str = "15min") -> Dict[str, Any]:
        """Get funding rate chart data"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'time_type': time_type,
            'currency': 'USDT'
        }
        
        return self._make_request('fundingRate', params)

    def get_long_short_ratio(self, symbol: str, time_type: str = "15min") -> Dict[str, Any]:
        """Get long/short ratio data"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'time_type': time_type,
            'currency': 'USDT'
        }
        
        return self._make_request('longShortRatio', params)

    def get_liquidation_map(self, symbol: str, time_type: str = "15min") -> Dict[str, Any]:
        """Get liquidation map data"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'time_type': time_type,
            'currency': 'USDT'
        }
        
        return self._make_request('liquidationMap', params)

    def get_liquidation_chart(self, symbol: str, time_type: str = "15min") -> Dict[str, Any]:
        """Get liquidation chart data"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'time_type': time_type,
            'currency': 'USDT'
        }
        
        return self._make_request('liquidation', params)

    def get_open_interest_by_exchange(self, symbol: str) -> Dict[str, Any]:
        """Get open interest by exchange"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'currency': 'USDT'
        }
        
        return self._make_request('openInterest/oiWeight', params)

    def get_volume_chart(self, symbol: str, time_type: str = "15min") -> Dict[str, Any]:
        """Get volume chart data"""
        mapped_symbol = self._map_symbol(symbol)
        
        params = {
            'symbol': mapped_symbol,
            'time_type': time_type,
            'currency': 'USDT'
        }
        
        return self._make_request('volume', params)

    def get_comprehensive_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive data from all available endpoints"""
        try:
            print(f"🔄 Getting comprehensive CoinGlass data for {symbol}...")
            
            data_container = {
                'symbol': symbol,
                'mapped_symbol': self._map_symbol(symbol),
                'endpoints_called': 0,
                'endpoints_successful': 0,
                'data_quality': 'unknown',
                'timestamp': int(time.time())
            }
            
            # Get data from all endpoints
            endpoints = [
                ('ticker', self.get_futures_ticker),
                ('open_interest', self.get_open_interest_chart),
                ('funding_rate', self.get_funding_rate_chart),
                ('long_short_ratio', self.get_long_short_ratio),
                ('liquidation_map', self.get_liquidation_map),
                ('liquidation_chart', self.get_liquidation_chart),
                ('volume', self.get_volume_chart)
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
            success_rate = data_container['endpoints_successful'] / data_container['endpoints_called']
            
            if success_rate >= 0.8:
                data_container['data_quality'] = 'excellent'
            elif success_rate >= 0.6:
                data_container['data_quality'] = 'good'
            elif success_rate >= 0.4:
                data_container['data_quality'] = 'partial'
            else:
                data_container['data_quality'] = 'poor'
            
            print(f"✅ CoinGlass data: {data_container['endpoints_successful']}/{data_container['endpoints_called']} endpoints successful")
            return data_container
            
        except Exception as e:
            return {'error': f'Comprehensive data fetch failed: {str(e)}'}

    def test_connection(self) -> Dict[str, Any]:
        """Test CoinGlass API connection"""
        if not self.api_key:
            return {'status': 'failed', 'error': 'API key not configured'}
        
        try:
            # Test with BTC ticker
            result = self.get_futures_ticker('BTC')
            
            if 'error' not in result:
                return {'status': 'success', 'message': 'CoinGlass API connection successful'}
            else:
                return {'status': 'failed', 'error': result['error']}
                
        except Exception as e:
            return {'status': 'failed', 'error': f'Connection test failed: {str(e)}'}

    def get_supported_symbols(self) -> list:
        """Get list of supported symbols"""
        return list(self.SYMBOL_MAP.keys())

    def is_symbol_supported(self, symbol: str) -> bool:
        """Check if symbol is supported"""
        clean_symbol = symbol.upper().replace('USDT', '')
        return clean_symbol in self.SYMBOL_MAP
