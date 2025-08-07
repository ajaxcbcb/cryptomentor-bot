
import os
import requests
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from config import (
    COINGLASS_ENDPOINTS, COINMARKETCAP_ENDPOINTS, BINANCE_ENDPOINTS,
    get_coinglass_headers, get_coinmarketcap_headers, get_binance_headers,
    CACHE_TIMEOUT, check_api_keys
)

class DataProvider:
    """
    Comprehensive data provider for CoinGlass v4, CoinMarketCap, and Binance APIs
    """
    
    def __init__(self):
        self.api_status = check_api_keys()
        self._cache = {}
        
        # Initialize API availability
        self.coinglass_available = self.api_status['coinglass']
        self.coinmarketcap_available = self.api_status['coinmarketcap']
        self.binance_available = True
        
        logging.info("DataProvider initialized with modular API architecture")

    def _make_request(self, url: str, headers: dict, params: dict = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Generic request method with comprehensive error handling
        """
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params or {},
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return {
                    'error': f'HTTP {response.status_code}',
                    'message': response.text[:200]
                }
                
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error'}
        except requests.exceptions.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}

    def is_dummy_data(self, response_data: Dict[str, Any], data_type: str = "general") -> bool:
        """
        Check if response contains dummy data from CoinGlass
        """
        if 'error' in response_data:
            return True
            
        data = response_data.get('data', {})
        if not data:
            return True
            
        # Check for CoinGlass dummy data patterns
        if data_type == "funding_rate":
            # Check if all funding rates are 0
            if isinstance(data, list):
                funding_rates = [float(item.get('fundingRate', 0)) for item in data]
                if all(rate == 0 for rate in funding_rates):
                    logging.warning("⚠️ CoinGlass returned dummy funding rate data (all zeros)")
                    return True
                    
        elif data_type == "long_short_ratio":
            # Check if all ratios are exactly 1.0
            if isinstance(data, list):
                ratios = []
                for item in data:
                    long_ratio = float(item.get('longAccount', 50))
                    short_ratio = float(item.get('shortAccount', 50))
                    if short_ratio > 0:
                        ratios.append(long_ratio / short_ratio)
                
                if all(abs(ratio - 1.0) < 0.001 for ratio in ratios):
                    logging.warning("⚠️ CoinGlass returned dummy long/short ratio data (all 1.0)")
                    return True
                    
        elif data_type == "ticker":
            # Check if all volumes are 0
            if isinstance(data, list):
                volumes = [float(item.get('volume24h', 0)) for item in data]
                if all(vol == 0 for vol in volumes):
                    logging.warning("⚠️ CoinGlass returned dummy ticker data (all volumes zero)")
                    return True
                    
        elif data_type == "open_interest":
            # Check if all OI values are 0
            if isinstance(data, list):
                oi_values = [float(item.get('openInterest', 0)) for item in data]
                if all(oi == 0 for oi in oi_values):
                    logging.warning("⚠️ CoinGlass returned dummy open interest data (all zeros)")
                    return True
        
        return False

    def _get_cache_key(self, method: str, symbol: str, **kwargs) -> str:
        """Generate cache key"""
        extra = "_".join([f"{k}_{v}" for k, v in kwargs.items()])
        return f"{method}_{symbol}_{extra}".lower()

    def _check_cache(self, cache_key: str, cache_type: str) -> Optional[Dict[str, Any]]:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return None
            
        cached_data, timestamp = self._cache[cache_key]
        timeout = CACHE_TIMEOUT.get(cache_type, 300)
        
        if time.time() - timestamp < timeout:
            logging.info(f"📦 Cache hit for {cache_key}")
            return cached_data
            
        # Remove expired cache
        del self._cache[cache_key]
        return None

    def _update_cache(self, cache_key: str, data: Dict[str, Any]):
        """Update cache with new data"""
        self._cache[cache_key] = (data, time.time())

    def get_realtime_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get real-time prices from CoinMarketCap with CoinGlass and Binance fallback
        """
        cache_key = self._get_cache_key("prices", "_".join(symbols[:3]))  # Use first 3 symbols for cache
        cached_data = self._check_cache(cache_key, "price_data")
        
        if cached_data:
            return cached_data

        result = {
            'prices': {},
            'source': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'errors': []
        }

        # Try CoinMarketCap first (most reliable for spot prices)
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
                    logging.info(f"✅ CoinMarketCap: Successfully fetched prices for {len(result['prices'])} symbols")
                    return result
                else:
                    error_msg = response.get('status', {}).get('error_message', 'Unknown CMC error')
                    result['errors'].append(f'CoinMarketCap: {error_msg}')
                    
            except Exception as e:
                result['errors'].append(f'CoinMarketCap exception: {str(e)}')
                logging.error(f"CoinMarketCap error: {e}")

        # Fallback to CoinGlass
        if self.coinglass_available:
            try:
                for symbol in symbols:
                    clean_symbol = symbol.upper().replace('USDT', '')
                    params = {'symbol': clean_symbol}
                    
                    response = self._make_request(
                        COINGLASS_ENDPOINTS['ticker'],
                        get_coinglass_headers(),
                        params
                    )
                    
                    if 'error' not in response and not self.is_dummy_data(response, "ticker"):
                        data_list = response.get('data', [])
                        if data_list and isinstance(data_list, list):
                            primary_data = data_list[0]
                            
                            result['prices'][symbol] = {
                                'symbol': clean_symbol,
                                'price': float(primary_data.get('price', 0)),
                                'change_24h': float(primary_data.get('priceChangePercent', 0)),
                                'volume_24h': float(primary_data.get('volume24h', 0)),
                                'high_24h': float(primary_data.get('high24h', 0)),
                                'low_24h': float(primary_data.get('low24h', 0)),
                                'exchange': primary_data.get('exchangeName', 'Binance')
                            }
                
                if result['prices']:
                    result['source'] = 'coinglass'
                    result['success'] = True
                    self._update_cache(cache_key, result)
                    logging.info(f"✅ CoinGlass: Successfully fetched prices for {len(result['prices'])} symbols")
                    return result
                    
            except Exception as e:
                result['errors'].append(f'CoinGlass exception: {str(e)}')
                logging.error(f"CoinGlass error: {e}")

        # Final fallback to Binance
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
                logging.info(f"✅ Binance: Successfully fetched prices for {len(result['prices'])} symbols")
                return result
                
        except Exception as e:
            result['errors'].append(f'Binance exception: {str(e)}')
            logging.error(f"Binance error: {e}")

        result['success'] = False
        result['error'] = 'All price APIs failed'
        logging.error(f"❌ All APIs failed for price data: {result['errors']}")
        return result

    def get_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive futures data from CoinGlass v4 with Binance fallback
        """
        cache_key = self._get_cache_key("futures", symbol)
        cached_data = self._check_cache(cache_key, "futures_data")
        
        if cached_data:
            return cached_data

        clean_symbol = symbol.upper().replace('USDT', '')
        result = {
            'symbol': clean_symbol,
            'timestamp': datetime.now().isoformat(),
            'source': 'unknown',
            'success': False,
            'data': {}
        }

        if not self.coinglass_available:
            result['error'] = 'CoinGlass API key not available'
            return result

        try:
            params = {'symbol': clean_symbol}
            futures_data = {}

            # Get ticker data
            ticker_response = self._make_request(
                COINGLASS_ENDPOINTS['ticker'],
                get_coinglass_headers(),
                params
            )
            
            if 'error' not in ticker_response and not self.is_dummy_data(ticker_response, "ticker"):
                ticker_list = ticker_response.get('data', [])
                if ticker_list:
                    primary_ticker = ticker_list[0]
                    futures_data['ticker'] = {
                        'price': float(primary_ticker.get('price', 0)),
                        'funding_rate': float(primary_ticker.get('fundingRate', 0)),
                        'funding_time': primary_ticker.get('fundingTime', ''),
                        'volume_24h': float(primary_ticker.get('volume24h', 0)),
                        'price_change_24h': float(primary_ticker.get('priceChangePercent', 0)),
                        'exchange': primary_ticker.get('exchangeName', 'Binance')
                    }

            # Get open interest
            oi_response = self._make_request(
                COINGLASS_ENDPOINTS['open_interest'],
                get_coinglass_headers(),
                params
            )
            
            if 'error' not in oi_response and not self.is_dummy_data(oi_response, "open_interest"):
                oi_list = oi_response.get('data', [])
                if oi_list:
                    total_oi = sum(float(item.get('openInterest', 0)) for item in oi_list)
                    futures_data['open_interest'] = {
                        'total': total_oi,
                        'exchanges_count': len(oi_list),
                        'dominant_exchange': oi_list[0].get('exchangeName', 'Binance') if oi_list else 'Unknown'
                    }

            # Get funding rate details
            funding_response = self._make_request(
                COINGLASS_ENDPOINTS['funding_rate'],
                get_coinglass_headers(),
                params
            )
            
            if 'error' not in funding_response and not self.is_dummy_data(funding_response, "funding_rate"):
                funding_list = funding_response.get('data', [])
                if funding_list:
                    valid_rates = [float(item.get('fundingRate', 0)) for item in funding_list if float(item.get('fundingRate', 0)) != 0]
                    if valid_rates:
                        avg_funding = sum(valid_rates) / len(valid_rates)
                        futures_data['funding_details'] = {
                            'average_rate': avg_funding,
                            'exchanges_count': len(valid_rates),
                            'trend': 'Positive' if avg_funding > 0.005 else 'Negative' if avg_funding < -0.002 else 'Neutral'
                        }

            # Get long/short ratio
            ls_response = self._make_request(
                COINGLASS_ENDPOINTS['long_short_ratio'],
                get_coinglass_headers(),
                params
            )
            
            if 'error' not in ls_response and not self.is_dummy_data(ls_response, "long_short_ratio"):
                ls_list = ls_response.get('data', [])
                if ls_list:
                    latest = ls_list[-1] if isinstance(ls_list, list) else ls_list
                    long_ratio = float(latest.get('longAccount', 50))
                    short_ratio = float(latest.get('shortAccount', 50))
                    
                    futures_data['long_short'] = {
                        'long_ratio': long_ratio,
                        'short_ratio': short_ratio,
                        'ratio_value': long_ratio / short_ratio if short_ratio > 0 else 1.0,
                        'sentiment': 'Bullish' if long_ratio > 55 else 'Bearish' if long_ratio < 45 else 'Neutral'
                    }

            if futures_data:
                result['data'] = futures_data
                result['source'] = 'coinglass_v4'
                result['success'] = True
                self._update_cache(cache_key, result)
                logging.info(f"✅ CoinGlass v4: Comprehensive futures data for {clean_symbol}")
                return result

        except Exception as e:
            logging.error(f"CoinGlass futures data error for {symbol}: {e}")

        # Fallback to Binance for basic futures data
        try:
            binance_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()
            
            # Get ticker
            ticker_params = {'symbol': binance_symbol}
            ticker_response = self._make_request(
                BINANCE_ENDPOINTS['futures_ticker'],
                get_binance_headers(),
                ticker_params
            )
            
            # Get funding rate
            funding_response = self._make_request(
                BINANCE_ENDPOINTS['futures_funding'],
                get_binance_headers(),
                ticker_params
            )
            
            binance_data = {}
            
            if 'error' not in ticker_response and 'symbol' in ticker_response:
                binance_data['ticker'] = {
                    'price': float(ticker_response.get('lastPrice', 0)),
                    'volume_24h': float(ticker_response.get('volume', 0)),
                    'price_change_24h': float(ticker_response.get('priceChangePercent', 0)),
                    'high_24h': float(ticker_response.get('highPrice', 0)),
                    'low_24h': float(ticker_response.get('lowPrice', 0))
                }
            
            if 'error' not in funding_response and 'fundingRate' in funding_response:
                binance_data['funding_details'] = {
                    'current_rate': float(funding_response.get('fundingRate', 0)),
                    'funding_time': funding_response.get('fundingTime', ''),
                    'exchanges_count': 1,
                    'trend': 'Binance Only'
                }
            
            if binance_data:
                result['data'] = binance_data
                result['source'] = 'binance_fallback'
                result['success'] = True
                self._update_cache(cache_key, result)
                logging.info(f"✅ Binance fallback: Basic futures data for {clean_symbol}")
                return result
                
        except Exception as e:
            logging.error(f"Binance fallback error for {symbol}: {e}")

        result['error'] = 'All futures APIs failed'
        logging.error(f"❌ All APIs failed for futures data: {symbol}")
        return result

    def get_coin_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed coin information from CoinMarketCap
        """
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
                        'tags': crypto_info.get('tags', [])[:10],  # Limit tags
                        'website': crypto_info.get('urls', {}).get('website', [])[:3],  # Limit URLs
                        'twitter': crypto_info.get('urls', {}).get('twitter', [])[:2],
                        'date_added': crypto_info.get('date_added', ''),
                        'source': 'coinmarketcap',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }
                    
                    self._update_cache(cache_key, result)
                    logging.info(f"✅ CoinMarketCap: Coin info for {clean_symbol}")
                    return result
                    
        except Exception as e:
            logging.error(f"CoinMarketCap info error for {symbol}: {e}")
            
        return {'error': f'Failed to get coin info for {symbol}', 'success': False}

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive market overview from CoinMarketCap
        """
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
                for crypto in crypto_list[:10]:  # Top 10
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
                logging.info("✅ CoinMarketCap: Market overview data fetched")
                return result
                
        except Exception as e:
            logging.error(f"Market overview error: {e}")
            
        return {'error': 'Failed to get market overview', 'success': False}

    def test_all_apis(self) -> Dict[str, Any]:
        """
        Test all API connections and return status
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'apis': {},
            'overall_status': 'unknown'
        }
        
        # Test CoinGlass
        if self.coinglass_available:
            try:
                test_response = self._make_request(
                    COINGLASS_ENDPOINTS['ticker'],
                    get_coinglass_headers(),
                    {'symbol': 'BTC'}
                )
                
                if 'error' not in test_response and not self.is_dummy_data(test_response, "ticker"):
                    results['apis']['coinglass'] = {
                        'status': 'success',
                        'version': 'v4',
                        'sample_data': bool(test_response.get('data'))
                    }
                else:
                    results['apis']['coinglass'] = {
                        'status': 'failed',
                        'error': test_response.get('error', 'Dummy data detected')
                    }
            except Exception as e:
                results['apis']['coinglass'] = {
                    'status': 'failed',
                    'error': str(e)
                }
        else:
            results['apis']['coinglass'] = {
                'status': 'unavailable',
                'error': 'API key not configured'
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
        elif successful_apis >= 2:
            results['overall_status'] = 'good'
        elif successful_apis >= 1:
            results['overall_status'] = 'limited'
        else:
            results['overall_status'] = 'poor'
        
        results['working_apis'] = successful_apis
        results['total_apis'] = total_apis
        
        logging.info(f"API Test Results: {successful_apis}/{total_apis} APIs working - Status: {results['overall_status']}")
        
        return results

# Global instance
data_provider = DataProvider()
