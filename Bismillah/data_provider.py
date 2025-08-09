
import os
import time
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List

from config import (
    COINMARKETCAP_ENDPOINTS, 
    BINANCE_ENDPOINTS,
    get_coinmarketcap_headers,
    get_binance_headers,
    CACHE_TIMEOUT,
    check_api_keys
)

class DataProvider:
    """
    Unified data provider for CoinMarketCap and Binance APIs
    Handles real-time price data, futures data, and market overview
    """

    def __init__(self):
        self.api_status = check_api_keys()
        self._cache = {}
        self.coinmarketcap_available = self.api_status['coinmarketcap']
        self.binance_available = True
        logging.info("DataProvider initialized with Binance + CoinMarketCap")

    def _make_request(self, url: str, headers: dict, params: dict = None, timeout: int = 30) -> Dict[str, Any]:
        """Make HTTP request with comprehensive error handling"""
        try:
            response = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}', 'message': response.text[:200]}
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error'}
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}

    def _get_cache_key(self, method: str, symbol: str, **kwargs) -> str:
        """Generate cache key for data caching"""
        extra = "_".join([f"{k}_{v}" for k, v in kwargs.items()])
        return f"{method}_{symbol}_{extra}".lower()

    def _check_cache(self, cache_key: str, cache_type: str) -> Optional[Dict[str, Any]]:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return None
        
        cached_data, timestamp = self._cache[cache_key]
        timeout = CACHE_TIMEOUT.get(cache_type, 300)
        
        if time.time() - timestamp < timeout:
            logging.info(f"Cache hit for {cache_key}")
            return cached_data
        
        del self._cache[cache_key]
        return None

    def _update_cache(self, cache_key: str, data: Dict[str, Any]):
        """Update cache with new data"""
        self._cache[cache_key] = (data, time.time())

    def get_realtime_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get real-time prices from CoinMarketCap with Binance fallback"""
        cache_key = self._get_cache_key("prices", "_".join(symbols[:3]))
        cached_data = self._check_cache(cache_key, "price_data")

        if cached_data:
            return cached_data

        result = {
            'prices': {},
            'source': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'errors': [],
            'success': False
        }

        # Try CoinMarketCap first
        if self.coinmarketcap_available:
            try:
                symbols_str = ",".join([s.upper().replace('USDT', '') for s in symbols])
                params = {'symbol': symbols_str, 'convert': 'USD'}

                response = self._make_request(
                    COINMARKETCAP_ENDPOINTS['quotes'],
                    get_coinmarketcap_headers(),
                    params
                )

                if 'error' not in response and response.get('status', {}).get('error_code') == 0:
                    data = response.get('data', {})
                    for symbol in symbols:
                        clean_symbol = symbol.upper().replace('USDT', '')
                        if clean_symbol in data:
                            crypto_data = data[clean_symbol]
                            quote_usd = crypto_data.get('quote', {}).get('USD', {})

                            result['prices'][symbol] = {
                                'symbol': clean_symbol,
                                'price': float(quote_usd.get('price', 0)),
                                'change_24h': float(quote_usd.get('percent_change_24h', 0)),
                                'change_7d': float(quote_usd.get('percent_change_7d', 0)),
                                'volume_24h': float(quote_usd.get('volume_24h', 0)),
                                'market_cap': float(quote_usd.get('market_cap', 0)),
                                'rank': int(crypto_data.get('cmc_rank', 0))
                            }

                    result['source'] = 'coinmarketcap'
                    result['success'] = True
                    self._update_cache(cache_key, result)
                    logging.info(f"CoinMarketCap: Successfully fetched prices for {len(result['prices'])} symbols")
                    return result
                else:
                    error_msg = response.get('status', {}).get('error_message', 'Unknown CMC error')
                    result['errors'].append(f'CoinMarketCap: {error_msg}')

            except Exception as e:
                result['errors'].append(f'CoinMarketCap exception: {str(e)}')
                logging.error(f"CoinMarketCap error: {e}")

        # Fallback to Binance
        try:
            for symbol in symbols:
                binance_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()
                params = {'symbol': binance_symbol}

                response = self._make_request(
                    BINANCE_ENDPOINTS['futures_ticker'],
                    get_binance_headers(),
                    params
                )

                if 'error' not in response and 'symbol' in response:
                    result['prices'][symbol] = {
                        'symbol': symbol.upper().replace('USDT', ''),
                        'price': float(response.get('lastPrice', 0)),
                        'change_24h': float(response.get('priceChangePercent', 0)),
                        'volume_24h': float(response.get('volume', 0)),
                        'high_24h': float(response.get('highPrice', 0)),
                        'low_24h': float(response.get('lowPrice', 0))
                    }

            if result['prices']:
                result['source'] = 'binance'
                result['success'] = True
                self._update_cache(cache_key, result)
                logging.info(f"Binance: Successfully fetched prices for {len(result['prices'])} symbols")
                return result

        except Exception as e:
            result['errors'].append(f'Binance exception: {str(e)}')
            logging.error(f"Binance error: {e}")

        result['error'] = 'All price APIs failed'
        logging.error(f"All APIs failed for price data: {result['errors']}")
        return result

    def get_futures_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive futures data from Binance API"""
        cache_key = self._get_cache_key("futures", symbol)
        cached_data = self._check_cache(cache_key, "futures_data")

        if cached_data:
            return cached_data

        binance_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()
        result = {
            'symbol': symbol.upper().replace('USDT', ''),
            'timestamp': datetime.now().isoformat(),
            'source': 'binance',
            'success': False,
            'data': {}
        }

        try:
            futures_data = {}
            params = {'symbol': binance_symbol}

            # Get ticker data
            ticker_response = self._make_request(
                BINANCE_ENDPOINTS['futures_ticker'],
                get_binance_headers(),
                params
            )

            if 'error' not in ticker_response and 'symbol' in ticker_response:
                futures_data['ticker'] = {
                    'price': float(ticker_response.get('lastPrice', 0)),
                    'volume_24h': float(ticker_response.get('volume', 0)),
                    'price_change_24h': float(ticker_response.get('priceChangePercent', 0)),
                    'high_24h': float(ticker_response.get('highPrice', 0)),
                    'low_24h': float(ticker_response.get('lowPrice', 0)),
                    'exchange': 'binance'
                }

            # Get funding rate
            funding_response = self._make_request(
                BINANCE_ENDPOINTS['futures_funding'],
                get_binance_headers(),
                params
            )

            if 'error' not in funding_response and isinstance(funding_response, list) and len(funding_response) > 0:
                latest_funding = funding_response[-1]
                futures_data['funding_details'] = {
                    'current_rate': float(latest_funding.get('fundingRate', 0)),
                    'funding_time': latest_funding.get('fundingTime', ''),
                    'exchanges_count': 1,
                    'trend': 'Binance Data'
                }

            # Get open interest
            oi_response = self._make_request(
                BINANCE_ENDPOINTS['futures_open_interest'],
                get_binance_headers(),
                params
            )

            if 'error' not in oi_response and 'openInterest' in oi_response:
                futures_data['open_interest'] = {
                    'total': float(oi_response.get('openInterest', 0)),
                    'exchanges_count': 1,
                    'dominant_exchange': 'Binance'
                }

            # Get long/short ratio
            ls_params = {'symbol': binance_symbol, 'period': '1h', 'limit': 1}
            ls_response = self._make_request(
                BINANCE_ENDPOINTS['long_short_ratio'],
                get_binance_headers(),
                ls_params
            )

            if 'error' not in ls_response and isinstance(ls_response, list) and len(ls_response) > 0:
                latest_ls = ls_response[0]
                long_account = float(latest_ls.get('longAccount', 50))
                short_account = float(latest_ls.get('shortAccount', 50))

                futures_data['long_short'] = {
                    'long_ratio': long_account,
                    'short_ratio': short_account,
                    'ratio_value': long_account / short_account if short_account > 0 else 1.0,
                    'sentiment': 'Bullish' if long_account > 55 else 'Bearish' if long_account < 45 else 'Neutral'
                }

            if futures_data:
                result['data'] = futures_data
                result['success'] = True
                self._update_cache(cache_key, result)
                logging.info(f"Binance: Comprehensive futures data for {binance_symbol}")
                return result

        except Exception as e:
            logging.error(f"Binance futures data error for {symbol}: {e}")

        result['error'] = 'Failed to get futures data from Binance'
        return result

    def get_coin_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed coin information from CoinMarketCap"""
        cache_key = self._get_cache_key("coin_info", symbol)
        cached_data = self._check_cache(cache_key, "coin_info")

        if cached_data:
            return cached_data

        if not self.coinmarketcap_available:
            return {'error': 'CoinMarketCap API key required for coin info'}

        clean_symbol = symbol.upper().replace('USDT', '')

        try:
            params = {'symbol': clean_symbol}
            response = self._make_request(
                COINMARKETCAP_ENDPOINTS['info'],
                get_coinmarketcap_headers(),
                params
            )

            if 'error' not in response and response.get('status', {}).get('error_code') == 0:
                crypto_info = response.get('data', {}).get(clean_symbol, {})
                if crypto_info:
                    result = {
                        'symbol': clean_symbol,
                        'name': crypto_info.get('name', ''),
                        'description': crypto_info.get('description', '')[:500] + '...' if len(crypto_info.get('description', '')) > 500 else crypto_info.get('description', ''),
                        'category': crypto_info.get('category', ''),
                        'tags': crypto_info.get('tags', [])[:10],
                        'website': crypto_info.get('urls', {}).get('website', [])[:3],
                        'twitter': crypto_info.get('urls', {}).get('twitter', [])[:2],
                        'date_added': crypto_info.get('date_added', ''),
                        'source': 'coinmarketcap',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }

                    self._update_cache(cache_key, result)
                    logging.info(f"CoinMarketCap: Coin info for {clean_symbol}")
                    return result

        except Exception as e:
            logging.error(f"CoinMarketCap info error for {symbol}: {e}")

        return {'error': f'Failed to get coin info for {symbol}', 'success': False}

    def get_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview from CoinMarketCap"""
        cache_key = "market_overview_global"
        cached_data = self._check_cache(cache_key, "market_data")

        if cached_data:
            return cached_data

        if not self.coinmarketcap_available:
            return {'error': 'CoinMarketCap API key required for market overview'}

        try:
            # Get global metrics
            global_response = self._make_request(
                COINMARKETCAP_ENDPOINTS['global_metrics'],
                get_coinmarketcap_headers()
            )

            # Get top cryptocurrencies
            listings_params = {'start': 1, 'limit': 20, 'convert': 'USD'}
            listings_response = self._make_request(
                COINMARKETCAP_ENDPOINTS['listings'],
                get_coinmarketcap_headers(),
                listings_params
            )

            result = {
                'global_metrics': {},
                'top_cryptocurrencies': [],
                'timestamp': datetime.now().isoformat(),
                'source': 'coinmarketcap',
                'success': False
            }

            # Parse global metrics
            if 'error' not in global_response and global_response.get('status', {}).get('error_code') == 0:
                global_data = global_response.get('data', {})
                global_quote = global_data.get('quote', {}).get('USD', {})

                result['global_metrics'] = {
                    'total_market_cap': float(global_quote.get('total_market_cap', 0)),
                    'total_volume_24h': float(global_quote.get('total_volume_24h', 0)),
                    'market_cap_change_24h': float(global_quote.get('total_market_cap_yesterday_percentage_change', 0)),
                    'btc_dominance': float(global_data.get('btc_dominance', 0)),
                    'eth_dominance': float(global_data.get('eth_dominance', 0)),
                    'active_cryptocurrencies': int(global_data.get('active_cryptocurrencies', 0)),
                    'active_exchanges': int(global_data.get('active_exchanges', 0))
                }

            # Parse top cryptocurrencies
            if 'error' not in listings_response and listings_response.get('status', {}).get('error_code') == 0:
                crypto_list = listings_response.get('data', [])
                for crypto in crypto_list[:10]:
                    quote_usd = crypto.get('quote', {}).get('USD', {})
                    result['top_cryptocurrencies'].append({
                        'symbol': crypto.get('symbol', ''),
                        'name': crypto.get('name', ''),
                        'rank': crypto.get('cmc_rank', 0),
                        'price': float(quote_usd.get('price', 0)),
                        'change_24h': float(quote_usd.get('percent_change_24h', 0)),
                        'market_cap': float(quote_usd.get('market_cap', 0)),
                        'volume_24h': float(quote_usd.get('volume_24h', 0))
                    })

            if result['global_metrics'] or result['top_cryptocurrencies']:
                result['success'] = True
                self._update_cache(cache_key, result)
                logging.info("CoinMarketCap: Market overview data fetched")
                return result

        except Exception as e:
            logging.error(f"Market overview error: {e}")

        return {'error': 'Failed to get market overview', 'success': False}

    def test_all_apis(self) -> Dict[str, Any]:
        """Test all API connections and return status"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'apis': {},
            'overall_status': 'unknown'
        }

        # Test CoinMarketCap
        if self.coinmarketcap_available:
            try:
                test_response = self._make_request(
                    COINMARKETCAP_ENDPOINTS['quotes'],
                    get_coinmarketcap_headers(),
                    {'symbol': 'BTC'}
                )

                if 'error' not in test_response and test_response.get('status', {}).get('error_code') == 0:
                    results['apis']['coinmarketcap'] = {
                        'status': 'success',
                        'rate_limit_remaining': test_response.get('status', {}).get('credit_count', 'unknown'),
                        'sample_data': bool(test_response.get('data'))
                    }
                else:
                    error_msg = test_response.get('status', {}).get('error_message', 'Unknown error')
                    results['apis']['coinmarketcap'] = {
                        'status': 'failed',
                        'error': error_msg
                    }
            except Exception as e:
                results['apis']['coinmarketcap'] = {
                    'status': 'failed',
                    'error': str(e)
                }
        else:
            results['apis']['coinmarketcap'] = {
                'status': 'unavailable',
                'error': 'API key not configured'
            }

        # Test Binance
        try:
            test_response = self._make_request(
                BINANCE_ENDPOINTS['futures_ticker'],
                get_binance_headers(),
                {'symbol': 'BTCUSDT'}
            )

            if 'error' not in test_response and 'symbol' in test_response:
                results['apis']['binance'] = {
                    'status': 'success',
                    'type': 'public',
                    'sample_data': bool(test_response.get('lastPrice'))
                }
            else:
                results['apis']['binance'] = {
                    'status': 'failed',
                    'error': test_response.get('error', 'No data')
                }
        except Exception as e:
            results['apis']['binance'] = {
                'status': 'failed',
                'error': str(e)
            }

        # Determine overall status
        successful_apis = sum(1 for api_result in results['apis'].values() if api_result.get('status') == 'success')
        total_apis = len(results['apis'])

        if successful_apis == total_apis:
            results['overall_status'] = 'excellent'
        elif successful_apis >= 1:
            results['overall_status'] = 'good'
        else:
            results['overall_status'] = 'poor'

        results['working_apis'] = successful_apis
        results['total_apis'] = total_apis

        logging.info(f"API Test Results: {successful_apis}/{total_apis} APIs working - Status: {results['overall_status']}")
        return results

# Global instance
data_provider = DataProvider()
