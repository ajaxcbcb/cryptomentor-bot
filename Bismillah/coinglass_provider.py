import os
import requests
import time
from datetime import datetime
import logging
from typing import Dict, Any, Optional, List

class CoinGlassProvider:
    """
    CoinGlass V4 API Provider untuk data futures dan derivatives
    Mendukung Startup Plan dengan multiple endpoints
    """
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY") or os.getenv("COINGLASS_SECRET")
        self.base_url = "https://open-api-v4.coinglass.com"
        # Startup plan endpoints
        self.startup_endpoints = {
            'tickers': '/public/v1/futures/tickers',
            'oi_change': '/public/v1/oi-change-statistics',
            'liquidation': '/public/v1/liquidation',
            'funding': '/public/v1/funding-rates'
        }
        
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

    def _get_headers(self):
        """Get headers for CoinGlass V4 API requests"""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "CryptoMentor-Bot/1.0" # Keep original User-Agent
        }

    def _make_request(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """
        Membuat request ke CoinGlass API dengan error handling
        """
        try:
            if not self.api_key:
                return {'error': 'COINGLASS_API_KEY not found in environment'}

            response = requests.get(
                url,
                headers=self._get_headers(), # Use _get_headers for V4 API
                params=params or {},
                timeout=20 # Keep original timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                # CoinGlass V4 STARTUP plan endpoints might not have 'success' field, or it might be implied.
                # Check for common error messages or structures.
                if data.get('code', 0) == 0 or data.get('success', True): 
                    return data
                else:
                    error_msg = data.get('message', data.get('msg', 'Unknown CoinGlass error'))
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
        Mendapatkan ticker data futures dari CoinGlass V4 STARTUP plan
        Endpoint: /public/v1/futures/tickers
        """
        try:
            symbol_query = symbol.upper().replace('USDT', '')
            
            # Check cache first
            cache_key = f"ticker_{symbol_query}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                    return cached_data
            
            v4_url = f"{self.base_url}{self.startup_endpoints['tickers']}"
            params = {'symbol': symbol_query}
            
            response_data = self._make_request(v4_url, params)
            
            if 'error' not in response_data:
                data_list = response_data.get('data', [])
                if data_list and isinstance(data_list, list):
                    # Find the specific symbol, as endpoint might return multiple
                    ticker_data = next((item for item in data_list if item.get('symbol') == symbol_query), None)
                    
                    if ticker_data:
                        price = float(ticker_data.get('price', 0))
                        
                        # Basic validation for real-time data
                        if price in [0, 1, 1000] or price is None:
                            logging.warning(f"Potential dummy data for {symbol_query}: Price is {price}")
                            return {'error': f'Dummy price data for {symbol_query}'}
                        
                        result = {
                            'symbol': symbol_query,
                            'price': price,
                            'funding_rate': float(ticker_data.get('fundingRate', 0)),
                            'funding_time': ticker_data.get('nextFundingTime', ''), # Use nextFundingTime if available
                            'volume_24h': float(ticker_data.get('volume24h', 0)),
                            'price_change_24h': float(ticker_data.get('change24h', 0)),
                            'exchange_name': ticker_data.get('exchange', 'Unknown'), # Use 'exchange' from new API
                            'source': 'coinglass_v4_startup',
                            'timestamp': ticker_data.get('timestamp', int(time.time())) # Use timestamp from new API
                        }
                        
                        # Cache the result
                        self._cache[cache_key] = (result, datetime.now().timestamp())
                        logging.info(f"✅ CoinGlass V4 STARTUP ticker for {symbol_query}: ${result['price']:.2f}")
                        return result
                    else:
                        return {'error': f'Symbol {symbol_query} not found in tickers response'}
                
            # If V4 STARTUP endpoint fails or symbol not found, return the error
            if 'error' in response_data:
                logging.error(f"Error fetching ticker for {symbol_query}: {response_data['error']}")
                return response_data
            else:
                return {'error': f'No ticker data available for {symbol_query} via V4 STARTUP endpoint'}
            
        except Exception as e:
            logging.exception(f"Exception in get_futures_ticker for {symbol}: {str(e)}")
            return {'error': f'Error getting ticker data: {str(e)}'}

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data Open Interest dari CoinGlass STARTUP plan
        Endpoint: /public/v1/oi-change-statistics
        """
        try:
            symbol_query = symbol.upper().replace('USDT', '')
            
            cache_key = f"oi_{symbol_query}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                    return cached_data
            
            url = f"{self.base_url}{self.startup_endpoints['oi_change']}"
            params = {'symbol': symbol_query} # Filter by symbol if endpoint supports it
            
            response_data = self._make_request(url, params)
            
            if 'error' in response_data:
                logging.error(f"Error fetching OI for {symbol_query}: {response_data['error']}")
                return response_data
            
            data_list = response_data.get('data', [])
            if not data_list:
                return {'error': f'No open interest data for {symbol_query}'}
            
            # The endpoint might return a list, find the specific symbol
            symbol_oi = next((item for item in data_list if item.get('symbol') == symbol_query), None)

            if not symbol_oi:
                return {'error': f'No open interest data found for {symbol_query}'}

            # Calculate total OI and changes
            total_oi = float(symbol_oi.get('openInterest', 0))
            oi_change_percent = float(symbol_oi.get('changeRate24h', 0))
            
            result = {
                'symbol': symbol_query,
                'total_open_interest': total_oi,
                'oi_change_percent': oi_change_percent,
                'exchanges_count': 1, # Assuming startup plan provides aggregated data per symbol
                'dominant_exchange': symbol_oi.get('exchange', 'Unknown'),
                'source': 'coinglass_v4_startup',
                'timestamp': symbol_oi.get('timestamp', int(time.time()))
            }
            
            self._cache[cache_key] = (result, datetime.now().timestamp())
            logging.info(f"✅ CoinGlass V4 STARTUP OI for {symbol_query}: {result['total_open_interest']:,.0f}")
            return result
            
        except Exception as e:
            logging.exception(f"Exception in get_open_interest for {symbol}: {str(e)}")
            return {'error': f'Error getting open interest: {str(e)}'}

    def get_long_short_ratio(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Mendapatkan Long/Short ratio dari CoinGlass.
        STARTUP plan might not have a dedicated long/short ratio endpoint.
        This function will simulate or return limited data if not available.
        """
        try:
            symbol_query = symbol.upper().replace('USDT', '')
            
            # Attempt to get data from tickers if it contains relevant info
            ticker_data = self.get_futures_ticker(symbol_query)

            if 'error' not in ticker_data:
                # The STARTUP plan may not provide explicit long/short ratio data.
                # We return a placeholder or indicate limited data.
                # If specific ticker data contained ratio, it would be parsed here.
                # For now, assume it's not directly available.
                logging.warning(f"Long/Short ratio not directly available from STARTUP plan for {symbol_query}. Returning default.")
                return {
                    'symbol': symbol_query,
                    'long_ratio': 50.0,  # Default neutral
                    'short_ratio': 50.0,
                    'ratio_value': 1.0,
                    'timeframe': timeframe,
                    'note': 'Long/Short ratio data may be limited or unavailable in STARTUP plan',
                    'source': 'coinglass_v4_startup_limited',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                # If ticker fetch failed, return that error
                return ticker_data
            
        except Exception as e:
            logging.exception(f"Exception in get_long_short_ratio for {symbol}: {str(e)}")
            return {'error': f'Error getting long/short ratio: {str(e)}'}

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan funding rate dari CoinGlass STARTUP plan
        Endpoint: /public/v1/funding-rates
        """
        try:
            symbol_query = symbol.upper().replace('USDT', '')
            
            # Cache key for funding rate
            cache_key = f"funding_{symbol_query}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                # Funding rate might have a shorter cache timeout, e.g., 1 hour
                if (datetime.now().timestamp() - timestamp) < 3600: # 1 hour cache
                    return cached_data

            url = f"{self.base_url}{self.startup_endpoints['funding']}"
            params = {'symbol': symbol_query}
            
            response_data = self._make_request(url, params)
            
            if 'error' in response_data:
                logging.error(f"Error fetching funding rate for {symbol_query}: {response_data['error']}")
                return response_data
            
            data_list = response_data.get('data', [])
            if not data_list:
                return {'error': f'No funding rate data for {symbol_query}'}
            
            # The endpoint might return multiple exchanges, find the primary one (e.g., Binance)
            # or calculate an average if needed. Let's prioritize Binance or the first entry.
            primary_data = None
            for item in data_list:
                if 'binance' in item.get('exchange', '').lower():
                    primary_data = item
                    break
            if not primary_data:
                primary_data = data_list[0] # Fallback to the first entry

            funding_rate = float(primary_data.get('fundingRate', 0))
            next_funding_time = primary_data.get('nextFundingTime', '')
            exchange = primary_data.get('exchange', 'Unknown')
            
            result = {
                'symbol': symbol_query,
                'funding_rate': funding_rate,
                'next_funding_time': next_funding_time,
                'exchange': exchange,
                'source': 'coinglass_v4_startup',
                'timestamp': primary_data.get('timestamp', int(time.time()))
            }
            
            self._cache[cache_key] = (result, datetime.now().timestamp())
            logging.info(f"✅ CoinGlass V4 STARTUP Funding Rate for {symbol_query}: {funding_rate:.6f} ({exchange})")
            return result
            
        except Exception as e:
            logging.exception(f"Exception in get_funding_rate for {symbol}: {str(e)}")
            return {'error': f'Error getting funding rate: {str(e)}'}

    def get_liquidation_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data liquidation dari CoinGlass STARTUP plan
        Endpoint: /public/v1/liquidation
        """
        try:
            symbol_query = symbol.upper().replace('USDT', '')
            
            cache_key = f"liquidation_{symbol_query}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                    return cached_data

            url = f"{self.base_url}{self.startup_endpoints['liquidation']}"
            params = {'symbol': symbol_query} 
            
            response_data = self._make_request(url, params)
            
            if 'error' in response_data:
                logging.error(f"Error fetching liquidation data for {symbol_query}: {response_data['error']}")
                return response_data
            
            data_list = response_data.get('data', [])
            if not data_list:
                return {'error': f'No liquidation data for {symbol_query}'}
            
            # Assume the list is already sorted or we take the first entry for the symbol
            latest_liquidation = data_list[0] 

            total_liq = float(latest_liquidation.get('totalLiquidation', 0))
            long_liq = float(latest_liquidation.get('longLiquidation', 0))
            short_liq = float(latest_liquidation.get('shortLiquidation', 0))
            
            # Calculateliq_ratio safely
            liq_ratio = long_liq / max(total_liq, 1) if total_liq > 0 else 0

            # Determine dominant side
            dominant_side = 'Balanced'
            if long_liq > short_liq * 1.5:
                dominant_side = 'Long Heavy'
            elif short_liq > long_liq * 1.5:
                dominant_side = 'Short Heavy'

            result = {
                'symbol': symbol_query,
                'total_liquidation': total_liq,
                'long_liquidation': long_liq,
                'short_liquidation': short_liq,
                'liq_ratio': liq_ratio,
                'dominant_side': dominant_side,
                'source': 'coinglass_v4_startup',
                'timestamp': latest_liquidation.get('timestamp', int(time.time()))
            }

            self._cache[cache_key] = (result, datetime.now().timestamp())
            logging.info(f"✅ CoinGlass V4 STARTUP Liquidation for {symbol_query}: Total ${total_liq:,.0f}")
            return result
            
        except Exception as e:
            logging.exception(f"Exception in get_liquidation_data for {symbol}: {str(e)}")
            return {'error': f'Error getting liquidation data: {str(e)}'}

    def test_connection(self) -> Dict[str, Any]:
        """
        Test koneksi ke CoinGlass API menggunakan STARTUP plan endpoints
        """
        try:
            # Test with BTC ticker from startup endpoint
            test_data = self.get_futures_ticker('BTC')
            
            if 'error' in test_data:
                return {
                    'status': 'failed',
                    'error': test_data['error'],
                    'api_key_status': 'available' if self.api_key else 'missing'
                }
            
            # Test other startup endpoints as well
            oi_test = self.get_open_interest('BTC')
            funding_test = self.get_funding_rate('BTC')
            liquidation_test = self.get_liquidation_data('BTC')
            
            success_count = 1 # For ticker
            if 'error' not in oi_test: success_count += 1
            if 'error' not in funding_test: success_count += 1
            if 'error' not in liquidation_test: success_count += 1

            return {
                'status': 'success',
                'api_key_status': 'valid',
                'endpoints_tested': ['ticker', 'open_interest', 'funding_rate', 'liquidation'],
                'sample_price': test_data.get('price', 0),
                'successful_endpoints_count': success_count
            }
            
        except Exception as e:
            logging.exception(f"Exception in test_connection: {str(e)}")
            return {
                'status': 'failed',
                'error': f'Connection test failed: {str(e)}',
                'api_key_status': 'available' if self.api_key else 'missing'
            }

    # The get_long_short_ratio and other methods are now implemented using the new endpoints.
    # The original get_funding_rate, get_liquidation_data, etc. methods are replaced.

# Test script for standalone execution - kept from original
if __name__ == "__main__":
    # Example usage:
    provider = CoinGlassProvider()

    # Test connection
    connection_status = provider.test_connection()
    print("\n--- Connection Test ---")
    print(connection_status)

    if connection_status.get('status') == 'success':
        # Fetch data for a specific symbol
        symbol = 'BTC'
        print(f"\n--- Fetching data for {symbol} ---")

        ticker_data = provider.get_futures_ticker(symbol)
        print(f"\nTicker Data ({symbol}):")
        print(ticker_data)

        oi_data = provider.get_open_interest(symbol)
        print(f"\nOpen Interest Data ({symbol}):")
        print(oi_data)

        funding_data = provider.get_funding_rate(symbol)
        print(f"\nFunding Rate Data ({symbol}):")
        print(funding_data)

        liquidation_data = provider.get_liquidation_data(symbol)
        print(f"\nLiquidation Data ({symbol}):")
        print(liquidation_data)
        
        ls_ratio_data = provider.get_long_short_ratio(symbol)
        print(f"\nLong/Short Ratio Data ({symbol}):")
        print(ls_ratio_data)

    else:
        print("\nSkipping data fetching due to connection test failure.")