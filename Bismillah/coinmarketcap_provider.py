import os
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_coinmarketcap_headers, COINMARKETCAP_ENDPOINTS

class CoinMarketCapProvider:
    """
    CoinMarketCap API Provider untuk data cryptocurrency real-time
    Menggunakan Pro API dengan authentication
    """

    def __init__(self):
        self.api_key = os.getenv("COINMARKETCAP_API_KEY") or os.getenv("CMC_API_KEY")
        self.base_url = "https://pro-api.coinmarketcap.com"
        self.sandbox_url = "https://sandbox-api.coinmarketcap.com"

        # Use sandbox if no API key (for testing)
        self.use_sandbox = not bool(self.api_key)
        self.current_url = self.sandbox_url if self.use_sandbox else self.base_url

        # Headers for authentication
        self.headers = {
            'Accepts': 'application/json',
            'Accept-Encoding': 'deflate, gzip',
        }

        if self.api_key:
            self.headers['X-CMC_PRO_API_KEY'] = self.api_key

        # Cache untuk mengurangi API calls
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes

        logging.info(f"CoinMarketCap Provider initialized: {'Sandbox' if self.use_sandbox else 'Production'}")

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """
        Membuat request ke CoinMarketCap API dengan error handling
        """
        try:
            url = f"{self.current_url}{endpoint}"

            response = requests.get(
                url,
                headers=self.headers,
                params=params or {},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('status', {}).get('error_code') == 0:
                    return data
                else:
                    error_msg = data.get('status', {}).get('error_message', 'Unknown API error')
                    return {'error': f'CMC API Error: {error_msg}'}
            else:
                return {'error': f'HTTP {response.status_code}: {response.text[:100]}'}

        except requests.exceptions.Timeout:
            return {'error': 'Request timeout - CMC API slow response'}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error - CMC API unavailable'}
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}

    def get_cryptocurrency_quotes(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan quote data real-time untuk cryptocurrency

        Args:
            symbol: Symbol crypto (BTC, ETH, dll)

        Returns:
            Dict berisi price, volume, market_cap, changes, dll
        """
        try:
            symbol = symbol.upper().replace('USDT', '')

            # Check cache first
            cache_key = f"quotes_{symbol}"
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                    return cached_data

            # API call
            endpoint = "/v1/cryptocurrency/quotes/latest"
            params = {
                'symbol': symbol,
                'convert': 'USD'
            }

            response_data = self._make_request(endpoint, params)

            if 'error' in response_data:
                return response_data

            # Parse response
            crypto_data = response_data.get('data', {}).get(symbol, {})
            if not crypto_data:
                return {'error': f'No data found for {symbol}'}

            quote_usd = crypto_data.get('quote', {}).get('USD', {})

            result = {
                'symbol': symbol,
                'name': crypto_data.get('name', ''),
                'price': float(quote_usd.get('price', 0)),
                'volume_24h': float(quote_usd.get('volume_24h', 0)),
                'volume_change_24h': float(quote_usd.get('volume_change_24h', 0)),
                'percent_change_1h': float(quote_usd.get('percent_change_1h', 0)),
                'percent_change_24h': float(quote_usd.get('percent_change_24h', 0)),
                'percent_change_7d': float(quote_usd.get('percent_change_7d', 0)),
                'percent_change_30d': float(quote_usd.get('percent_change_30d', 0)),
                'market_cap': float(quote_usd.get('market_cap', 0)),
                'market_cap_dominance': float(quote_usd.get('market_cap_dominance', 0)),
                'fully_diluted_market_cap': float(quote_usd.get('fully_diluted_market_cap', 0)),
                'circulating_supply': float(crypto_data.get('circulating_supply', 0)),
                'total_supply': float(crypto_data.get('total_supply', 0)),
                'max_supply': crypto_data.get('max_supply'),  # Can be None
                'cmc_rank': int(crypto_data.get('cmc_rank', 0)),
                'last_updated': quote_usd.get('last_updated', ''),
                'source': 'coinmarketcap'
            }

            # Cache the result
            self._cache[cache_key] = (result, datetime.now().timestamp())

            return result

        except Exception as e:
            return {'error': f'Error parsing CMC quotes: {str(e)}'}

    def get_cryptocurrency_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi metadata cryptocurrency
        """
        try:
            symbol = symbol.upper().replace('USDT', '')

            endpoint = "/v1/cryptocurrency/info"
            params = {'symbol': symbol}

            response_data = self._make_request(endpoint, params)

            if 'error' in response_data:
                return response_data

            crypto_info = response_data.get('data', {}).get(symbol, {})
            if not crypto_info:
                return {'error': f'No info found for {symbol}'}

            return {
                'symbol': symbol,
                'name': crypto_info.get('name', ''),
                'description': crypto_info.get('description', ''),
                'category': crypto_info.get('category', ''),
                'logo': crypto_info.get('logo', ''),
                'website': crypto_info.get('urls', {}).get('website', []),
                'technical_doc': crypto_info.get('urls', {}).get('technical_doc', []),
                'twitter': crypto_info.get('urls', {}).get('twitter', []),
                'reddit': crypto_info.get('urls', {}).get('reddit', []),
                'tags': crypto_info.get('tags', []),
                'date_added': crypto_info.get('date_added', ''),
                'source': 'coinmarketcap_info'
            }

        except Exception as e:
            return {'error': f'Error getting CMC info: {str(e)}'}

    def get_enhanced_market_overview(self) -> Dict[str, Any]:
        """
        Mendapatkan overview pasar crypto komprehensif
        """
        try:
            # Global metrics
            global_endpoint = "/v1/global-metrics/quotes/latest"
            global_data = self._make_request(global_endpoint)

            # Top cryptocurrencies
            listings_endpoint = "/v1/cryptocurrency/listings/latest"
            listings_params = {
                'start': 1,
                'limit': 10,
                'convert': 'USD'
            }
            listings_data = self._make_request(listings_endpoint, listings_params)

            result = {
                'global_metrics': {},
                'top_cryptocurrencies': {},
                'fear_greed_index': {'value': 50, 'value_classification': 'Neutral'}  # Placeholder
            }

            # Parse global metrics
            if 'error' not in global_data:
                global_quote = global_data.get('data', {}).get('quote', {}).get('USD', {})
                result['global_metrics'] = {
                    'total_market_cap': float(global_quote.get('total_market_cap', 0)),
                    'total_volume_24h': float(global_quote.get('total_volume_24h', 0)),
                    'market_cap_change_24h': float(global_quote.get('total_market_cap_yesterday_percentage_change', 0)),
                    'btc_dominance': float(global_data.get('data', {}).get('btc_dominance', 0)),
                    'eth_dominance': float(global_data.get('data', {}).get('eth_dominance', 0)),
                    'active_cryptocurrencies': int(global_data.get('data', {}).get('active_cryptocurrencies', 0)),
                    'active_exchanges': int(global_data.get('data', {}).get('active_exchanges', 0)),
                    'active_market_pairs': int(global_data.get('data', {}).get('active_market_pairs', 0))
                }

            # Parse top cryptocurrencies
            if 'error' not in listings_data:
                result['top_cryptocurrencies'] = listings_data

            return result

        except Exception as e:
            return {'error': f'Error getting market overview: {str(e)}'}

    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """
        Simplified method untuk mendapatkan harga saja
        """
        quotes_data = self.get_cryptocurrency_quotes(symbol)

        if 'error' in quotes_data:
            return quotes_data

        return {
            'symbol': quotes_data['symbol'],
            'price': quotes_data['price'],
            'change_24h': quotes_data['percent_change_24h'],
            'volume_24h': quotes_data['volume_24h'],
            'source': 'coinmarketcap'
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test koneksi ke CoinMarketCap API
        """
        try:
            endpoint = "/v1/cryptocurrency/quotes/latest"
            params = {'symbol': 'BTC'}

            response_data = self._make_request(endpoint, params)

            if 'error' in response_data:
                return {
                    'status': 'failed',
                    'error': response_data['error'],
                    'api_key_status': 'available' if self.api_key else 'missing'
                }

            return {
                'status': 'success',
                'api_key_status': 'valid',
                'rate_limit_remaining': response_data.get('status', {}).get('credit_count', 'unknown'),
                'mode': 'sandbox' if self.use_sandbox else 'production'
            }

        except Exception as e:
            return {
                'status': 'failed',
                'error': f'Connection test failed: {str(e)}',
                'api_key_status': 'available' if self.api_key else 'missing'
            }