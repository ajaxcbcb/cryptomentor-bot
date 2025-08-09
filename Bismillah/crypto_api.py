"""
Unified Crypto API Handler
Combines data from multiple sources with fallback strategy
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from data_provider import data_provider

class CryptoAPI:
    """
    Unified API class for crypto data from multiple sources
    Priority: CoinMarketCap -> Binance -> Error
    """

    def __init__(self):
        self.provider = data_provider
        self._cache = {}
        self._cache_timeout = 30  # seconds
        logging.info("CryptoAPI initialized with Binance + CoinMarketCap")

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache:
            return False

        cache_time = self._cache[key].get('timestamp', 0)
        return (datetime.now().timestamp() - cache_time) < self._cache_timeout

    def _set_cache(self, key: str, data: Any):
        """Set cache with timestamp"""
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.now().timestamp()
        }

    def _get_cache(self, key: str) -> Any:
        """Get cached data"""
        return self._cache.get(key, {}).get('data')

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get real-time crypto price with caching
        """
        try:
            symbol = symbol.upper().replace('USDT', '')
            cache_key = f"price_{symbol}"

            # Return cached data if valid and not forcing refresh
            if not force_refresh and self._is_cache_valid(cache_key):
                cached_data = self._get_cache(cache_key)
                if cached_data:
                    return cached_data

            # Get fresh data
            price_data = self.provider.get_realtime_prices([symbol])

            if price_data.get('success') and symbol in price_data.get('prices', {}):
                symbol_data = price_data['prices'][symbol]

                result = {
                    'symbol': symbol,
                    'price': symbol_data.get('price', 0),
                    'change_24h': symbol_data.get('change_24h', 0),
                    'change_7d': symbol_data.get('change_7d', 0),
                    'volume_24h': symbol_data.get('volume_24h', 0),
                    'market_cap': symbol_data.get('market_cap', 0),
                    'rank': symbol_data.get('rank', 0),
                    'source': price_data.get('source', 'unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

                # Cache the result
                self._set_cache(cache_key, result)
                return result
            else:
                return {
                    'error': f'Failed to get price for {symbol}',
                    'source_attempted': price_data.get('source', 'unknown'),
                    'success': False
                }

        except Exception as e:
            logging.error(f"Error in get_crypto_price for {symbol}: {e}")
            return {'error': f'Price API error: {str(e)}', 'success': False}

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """Get prices for multiple symbols"""
        try:
            return self.provider.get_realtime_prices(symbols)
        except Exception as e:
            logging.error(f"Error in get_multiple_prices: {e}")
            return {'error': f'Multiple prices error: {str(e)}', 'success': False}

    def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview with caching"""
        try:
            cache_key = "market_overview"

            if self._is_cache_valid(cache_key):
                cached_data = self._get_cache(cache_key)
                if cached_data:
                    return cached_data

            result = self.provider.get_market_overview()

            if result.get('success'):
                self._set_cache(cache_key, result)

            return result

        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {'error': f'Market overview error: {str(e)}', 'success': False}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """Get detailed crypto information"""
        try:
            return self.provider.get_coin_info(symbol)
        except Exception as e:
            logging.error(f"Error getting crypto info for {symbol}: {e}")
            return {'error': f'Crypto info error: {str(e)}', 'success': False}

    def get_futures_data(self, symbol: str) -> Dict[str, Any]:
        """Get futures data from Binance"""
        try:
            return self.provider.get_futures_data(symbol)
        except Exception as e:
            logging.error(f"Error getting futures data for {symbol}: {e}")
            return {'error': f'Futures data error: {str(e)}', 'success': False}

    def analyze_supply_demand(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze Supply and Demand zones using candlestick data
        """
        try:
            # Get current price first
            price_data = self.get_crypto_price(symbol)
            if not price_data.get('success'):
                current_price = 50000  # Fallback
            else:
                current_price = price_data.get('price', 50000)

            # Get candlestick data from Binance
            candlestick_data = self.get_candlestick_data(symbol, '1h', 200)

            if not candlestick_data.get('success'):
                # Generate fallback SnD zones
                return {
                    'Supply 1': current_price * 1.025,
                    'Supply 2': current_price * 1.05,
                    'Demand 1': current_price * 0.975,
                    'Demand 2': current_price * 0.95,
                    'source': 'fallback',
                    'success': True
                }

            candles = candlestick_data.get('data', [])
            if len(candles) < 50:
                return {
                    'Supply 1': current_price * 1.025,
                    'Supply 2': current_price * 1.05,
                    'Demand 1': current_price * 0.975,
                    'Demand 2': current_price * 0.95,
                    'source': 'fallback_insufficient_data',
                    'success': True
                }

            supply_zones = []
            demand_zones = []

            # Analyze candlestick data for swing highs and lows
            for i in range(2, len(candles) - 2):
                current = candles[i]
                prev1, prev2 = candles[i-1], candles[i-2]
                next1, next2 = candles[i+1], candles[i+2]

                high = current['high']
                low = current['low']
                volume = current['volume']

                # Swing High detection (Supply zones)
                if (high > prev1['high'] and high > prev2['high'] and
                    high > next1['high'] and high > next2['high'] and volume > 0):
                    supply_zones.append({
                        'price': high,
                        'strength': min(100, (volume / 1000000) * 5 + 50)
                    })

                # Swing Low detection (Demand zones)
                if (low < prev1['low'] and low < prev2['low'] and
                    low < next1['low'] and low < next2['low'] and volume > 0):
                    demand_zones.append({
                        'price': low,
                        'strength': min(100, (volume / 1000000) * 5 + 50)
                    })

            # Sort by proximity to current price
            supply_zones.sort(key=lambda x: abs(x['price'] - current_price))
            demand_zones.sort(key=lambda x: abs(x['price'] - current_price))

            # Get top 2 zones
            supply_1 = supply_zones[0]['price'] if supply_zones else current_price * 1.025
            supply_2 = supply_zones[1]['price'] if len(supply_zones) > 1 else current_price * 1.05
            demand_1 = demand_zones[0]['price'] if demand_zones else current_price * 0.975
            demand_2 = demand_zones[1]['price'] if len(demand_zones) > 1 else current_price * 0.95

            return {
                'Supply 1': supply_1,
                'Supply 2': supply_2,
                'Demand 1': demand_1,
                'Demand 2': demand_2,
                'source': 'binance_analysis',
                'success': True,
                'zones_found': {
                    'supply_count': len(supply_zones),
                    'demand_count': len(demand_zones)
                }
            }

        except Exception as e:
            logging.error(f"Error in analyze_supply_demand for {symbol}: {e}")
            # Return fallback zones on error
            fallback_price = 50000 if symbol.upper() == 'BTC' else 3000 if symbol.upper() == 'ETH' else 100
            return {
                'Supply 1': fallback_price * 1.025,
                'Supply 2': fallback_price * 1.05,
                'Demand 1': fallback_price * 0.975,
                'Demand 2': fallback_price * 0.95,
                'source': 'error_fallback',
                'success': True,
                'error': str(e)
            }

    def get_candlestick_data(self, symbol: str, timeframe: str, limit: int = 100) -> Dict[str, Any]:
        """Get candlestick data from Binance"""
        try:
            from config import BINANCE_ENDPOINTS, get_binance_headers
            import requests

            binance_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()

            params = {
                'symbol': binance_symbol,
                'interval': timeframe,
                'limit': limit
            }

            response = requests.get(
                BINANCE_ENDPOINTS['klines'],
                headers=get_binance_headers(),
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                candlesticks = []

                for candle in data:
                    candlesticks.append({
                        'timestamp': int(candle[0]),
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    })

                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'data': candlesticks,
                    'source': 'binance',
                    'success': True
                }
            else:
                return {'error': f'Binance API error: {response.status_code}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting candlestick data: {e}")
            return {'error': f'Candlestick data error: {str(e)}', 'success': False}

    def test_all_connections(self) -> Dict[str, Any]:
        """Test all API connections"""
        try:
            return self.provider.test_all_apis()
        except Exception as e:
            logging.error(f"Error testing API connections: {e}")
            return {
                'error': f'API connection test failed: {str(e)}',
                'overall_status': 'error',
                'working_apis': 0,
                'total_apis': 2
            }

# Global instance
crypto_api = CryptoAPI()