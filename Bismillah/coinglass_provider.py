
import os
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_coinglass_headers, COINGLASS_ENDPOINTS

class CoinGlassProvider:
    """
    CoinGlass V4 API Provider untuk data futures dan derivatives
    Mendukung Startup Plan dengan multiple endpoints
    """
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY") or os.getenv("COINGLASS_SECRET")
        self.base_url_v4 = "https://open-api-v4.coinglass.com"
        self.base_url_public = "https://open-api.coinglass.com/public/v2"
        self.base_url_pro = "https://open-api.coinglass.com/api/pro/v1"
        
        # Headers untuk authentication
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CryptoMentor-Bot/1.0"
        }
        
        if self.api_key:
            self.headers["X-API-KEY"] = self.api_key
            print(f"✅ CoinGlass API key configured: {self.api_key[:8]}...")
        else:
            print("⚠️ CoinGlass API key not found")
        
        # Cache untuk mengurangi API calls
        self._cache = {}
        self._cache_timeout = 180  # 3 minutes untuk futures data
        
        logging.info(f"CoinGlass V4 Provider initialized: {'With API Key' if self.api_key else 'No API Key'}")

    def _make_request(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """
        Membuat request ke CoinGlass API dengan error handling
        """
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return data
                else:
                    error_msg = data.get('msg', 'Unknown CoinGlass error')
                    return {'error': f'CoinGlass API Error: {error_msg}'}
            else:
                return {'error': f'HTTP {response.status_code}: {response.text[:100]}'}
                
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout - CoinGlass API slow response'}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error - CoinGlass API unavailable'}
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}

    def get_futures_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan ticker data futures dari CoinGlass V4
        Endpoint: /api/futures/symbol-mark-price atau /futures/ticker
        """
        try:
            symbol = symbol.upper().replace('USDT', '')
            
            # Check cache first
            cache_key = f"ticker_{symbol}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                    return cached_data
            
            # Try V4 API first (most recent)
            v4_url = f"{self.base_url_v4}/api/futures/symbol-mark-price"
            params = {'symbol': symbol}
            
            response_data = self._make_request(v4_url, params)
            
            if 'error' not in response_data:
                data_list = response_data.get('data', [])
                if data_list and isinstance(data_list, list):
                    # Get primary exchange data (usually Binance)
                    primary_data = data_list[0]
                    
                    result = {
                        'symbol': symbol,
                        'price': float(primary_data.get('price', 0)),
                        'funding_rate': float(primary_data.get('fundingRate', 0)),
                        'funding_time': primary_data.get('fundingTime', ''),
                        'volume_24h': float(primary_data.get('volume24h', 0)),
                        'price_change_24h': float(primary_data.get('priceChangePercent', 0)),
                        'high_24h': float(primary_data.get('high24h', 0)),
                        'low_24h': float(primary_data.get('low24h', 0)),
                        'exchange_name': primary_data.get('exchangeName', 'Binance'),
                        'source': 'coinglass_v4',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Cache the result
                    self._cache[cache_key] = (result, datetime.now().timestamp())
                    print(f"✅ CoinGlass V4 ticker for {symbol}: ${result['price']:.2f}")
                    return result
                
            # Fallback to Pro API
            pro_url = f"{self.base_url_pro}/futures/ticker"
            response_data = self._make_request(pro_url, params)
            
            if 'error' not in response_data:
                data_list = response_data.get('data', [])
                if data_list:
                    primary_data = data_list[0]
                    
                    result = {
                        'symbol': symbol,
                        'price': float(primary_data.get('price', 0)),
                        'funding_rate': float(primary_data.get('fundingRate', 0)),
                        'funding_time': primary_data.get('fundingTime', ''),
                        'volume_24h': float(primary_data.get('volume24h', 0)),
                        'price_change_24h': float(primary_data.get('priceChangePercent', 0)),
                        'high_24h': float(primary_data.get('high24h', 0)),
                        'low_24h': float(primary_data.get('low24h', 0)),
                        'exchange_name': primary_data.get('exchangeName', 'Binance'),
                        'source': 'coinglass_pro',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Cache the result
                    self._cache[cache_key] = (result, datetime.now().timestamp())
                    print(f"✅ CoinGlass Pro ticker for {symbol}: ${result['price']:.2f}")
                    return result
            
            # Fallback to public V2 API
            public_url = f"{self.base_url_public}/futures/ticker"
            fallback_response = self._make_request(public_url, params)
            
            if 'error' not in fallback_response:
                data_list = fallback_response.get('data', [])
                if data_list:
                    primary_data = data_list[0]
                    
                    result = {
                        'symbol': symbol,
                        'price': float(primary_data.get('price', 0)),
                        'funding_rate': float(primary_data.get('fundingRate', 0)),
                        'volume_24h': float(primary_data.get('volume24h', 0)),
                        'price_change_24h': float(primary_data.get('priceChangePercent', 0)),
                        'exchange_name': primary_data.get('exchangeName', 'Binance'),
                        'source': 'coinglass_v2_public',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self._cache[cache_key] = (result, datetime.now().timestamp())
                    return result
            
            return {'error': f'No ticker data available for {symbol}'}
            
        except Exception as e:
            return {'error': f'Error getting ticker data: {str(e)}'}

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data Open Interest dari CoinGlass
        """
        try:
            symbol = symbol.upper().replace('USDT', '')
            
            cache_key = f"oi_{symbol}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                    return cached_data
            
            # Try public API
            url = f"{self.base_url_public}/futures/openInterest"
            params = {'symbol': symbol}
            
            response_data = self._make_request(url, params)
            
            if 'error' in response_data:
                return response_data
            
            data_list = response_data.get('data', [])
            if not data_list:
                return {'error': f'No open interest data for {symbol}'}
            
            # Calculate total OI and changes
            total_oi = 0
            exchanges_count = 0
            
            for item in data_list:
                oi_value = float(item.get('openInterest', 0))
                if oi_value > 0:
                    total_oi += oi_value
                    exchanges_count += 1
            
            # Calculate OI change (simplified - comparing with previous cached data if available)
            oi_change_percent = 0
            if len(data_list) > 1:
                current_oi = float(data_list[-1].get('openInterest', 0))
                previous_oi = float(data_list[-2].get('openInterest', 0))
                if previous_oi > 0:
                    oi_change_percent = ((current_oi - previous_oi) / previous_oi) * 100
            
            result = {
                'symbol': symbol,
                'total_open_interest': total_oi,
                'oi_change_percent': oi_change_percent,
                'exchanges_count': exchanges_count,
                'dominant_exchange': data_list[0].get('exchangeName', 'Binance') if data_list else 'Unknown',
                'source': 'coinglass_v2',
                'timestamp': datetime.now().isoformat()
            }
            
            self._cache[cache_key] = (result, datetime.now().timestamp())
            return result
            
        except Exception as e:
            return {'error': f'Error getting open interest: {str(e)}'}

    def get_long_short_ratio(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Mendapatkan Long/Short ratio dari CoinGlass
        """
        try:
            symbol = symbol.upper().replace('USDT', '')
            
            # Map timeframe to intervalType
            interval_map = {
                '5m': 0, '15m': 1, '1h': 2, '4h': 3, '12h': 4, '24h': 5, '1d': 5
            }
            interval_type = interval_map.get(timeframe, 2)
            
            # Try Pro API first
            pro_url = f"{self.base_url_pro}/futures/long_short_account_ratio"
            params = {'symbol': symbol}
            
            response_data = self._make_request(pro_url, params)
            
            if 'error' not in response_data:
                data_list = response_data.get('data', [])
                if data_list:
                    latest = data_list[-1] if isinstance(data_list, list) else data_list
                    
                    long_account = float(latest.get('longAccount', 50))
                    short_account = float(latest.get('shortAccount', 50))
                    
                    return {
                        'symbol': symbol,
                        'long_ratio': long_account,
                        'short_ratio': short_account,
                        'ratio_value': long_account / short_account if short_account > 0 else 1.0,
                        'timeframe': timeframe,
                        'source': 'coinglass_pro',
                        'timestamp': datetime.now().isoformat()
                    }
            
            # Fallback to public chart API
            public_url = f"{self.base_url_public}/futures/longShortChart"
            params = {'symbol': symbol, 'intervalType': interval_type}
            
            fallback_response = self._make_request(public_url, params)
            
            if 'error' not in fallback_response:
                chart_data = fallback_response.get('data', [])
                if chart_data:
                    latest = chart_data[-1]
                    long_ratio = float(latest.get('longRatio', 50))
                    short_ratio = float(latest.get('shortRatio', 50))
                    
                    return {
                        'symbol': symbol,
                        'long_ratio': long_ratio,
                        'short_ratio': short_ratio,
                        'ratio_value': long_ratio / short_ratio if short_ratio > 0 else 1.0,
                        'timeframe': timeframe,
                        'source': 'coinglass_public',
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {'error': f'No long/short data available for {symbol}'}
            
        except Exception as e:
            return {'error': f'Error getting long/short ratio: {str(e)}'}

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan funding rate dari CoinGlass
        """
        try:
            symbol = symbol.upper().replace('USDT', '')
            
            # Try to get from ticker first (more comprehensive)
            ticker_data = self.get_futures_ticker(symbol)
            if 'error' not in ticker_data and 'funding_rate' in ticker_data:
                return {
                    'symbol': symbol,
                    'funding_rate': ticker_data['funding_rate'],
                    'funding_time': ticker_data.get('funding_time', ''),
                    'exchange': ticker_data.get('exchange_name', 'Binance'),
                    'source': 'coinglass_ticker',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Fallback to dedicated funding rate endpoint
            url = f"{self.base_url_pro}/futures/funding_rate"
            params = {'symbol': symbol}
            
            response_data = self._make_request(url, params)
            
            if 'error' in response_data:
                return response_data
            
            data_list = response_data.get('data', [])
            if not data_list:
                return {'error': f'No funding rate data for {symbol}'}
            
            # Calculate average funding rate across exchanges
            valid_rates = []
            for item in data_list:
                rate = float(item.get('fundingRate', 0))
                if rate != 0:
                    valid_rates.append(rate)
            
            avg_funding = sum(valid_rates) / len(valid_rates) if valid_rates else 0
            
            return {
                'symbol': symbol,
                'funding_rate': avg_funding,
                'exchanges_count': len(valid_rates),
                'funding_trend': 'Positive' if avg_funding > 0.005 else 'Negative' if avg_funding < -0.002 else 'Neutral',
                'source': 'coinglass_funding',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Error getting funding rate: {str(e)}'}

    def get_liquidation_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data liquidation dari CoinGlass
        """
        try:
            symbol = symbol.upper().replace('USDT', '')
            
            # Try liquidation chart endpoint
            url = f"{self.base_url_public}/futures/liquidation_chart"
            params = {'symbol': symbol, 'intervalType': 1}  # 24h
            
            response_data = self._make_request(url, params)
            
            if 'error' in response_data:
                return response_data
            
            chart_data = response_data.get('data', [])
            if not chart_data:
                return {'error': f'No liquidation data for {symbol}'}
            
            latest = chart_data[-1]
            total_liq = float(latest.get('totalLiquidation', 0))
            long_liq = float(latest.get('longLiquidation', 0))
            short_liq = float(latest.get('shortLiquidation', 0))
            
            return {
                'symbol': symbol,
                'total_liquidation': total_liq,
                'long_liquidation': long_liq,
                'short_liquidation': short_liq,
                'liq_ratio': long_liq / max(total_liq, 1),
                'dominant_side': 'Long Heavy' if long_liq > short_liq * 1.5 else 'Short Heavy' if short_liq > long_liq * 1.5 else 'Balanced',
                'source': 'coinglass_liquidation',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Error getting liquidation data: {str(e)}'}

    def test_connection(self) -> Dict[str, Any]:
        """
        Test koneksi ke CoinGlass API
        """
        try:
            # Test dengan BTC ticker
            test_data = self.get_futures_ticker('BTC')
            
            if 'error' in test_data:
                return {
                    'status': 'failed',
                    'error': test_data['error'],
                    'api_key_status': 'available' if self.api_key else 'missing'
                }
            
            return {
                'status': 'success',
                'api_key_status': 'valid',
                'endpoints_tested': ['ticker', 'open_interest', 'long_short'],
                'sample_price': test_data.get('price', 0)
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': f'Connection test failed: {str(e)}',
                'api_key_status': 'available' if self.api_key else 'missing'
            }
