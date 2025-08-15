import os
import time
import logging
import requests
from data_provider import DataProvider
from datetime import datetime
from typing import Dict, Any, Optional, List

class CryptoAPI:
    """
    Unified API class yang menggabungkan data dari Binance dan CoinMarketCap
    Menyediakan data real-time untuk spot dan futures
    """

    def __init__(self):
        # Check for CoinAPI key
        self.coinapi_key = os.getenv('COINAPI_API_KEY') or os.getenv('COINAPI_KEY') or os.getenv('COINAPI_IO_KEY')
        self.coinapi_base_url = "https://rest.coinapi.io/v1"

        if self.coinapi_key:
            print("✅ CryptoAPI initialized with CoinAPI + Binance + CoinMarketCap")
        else:
            print("⚠️ CryptoAPI initialized without CoinAPI key - using Binance + CoinMarketCap only")

        self.data_provider = DataProvider()
        self._cache = {}
        self._cache_expiry = 60  # Cache for 60 seconds

    def get_coinapi_price(self, symbol):
        """Get price from CoinAPI (primary source)"""
        if not self.coinapi_key:
            return {'error': 'CoinAPI key not configured'}

        try:
            # Convert symbol to CoinAPI format
            if symbol.upper() == 'BTC':
                coinapi_symbol = 'BTC'
            elif symbol.upper() == 'ETH':
                coinapi_symbol = 'ETH'
            else:
                coinapi_symbol = symbol.upper()

            headers = {
                'X-CoinAPI-Key': self.coinapi_key,
                'Accept': 'application/json'
            }

            # Get current price
            url = f"{self.coinapi_base_url}/exchangerate/{coinapi_symbol}/USD"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                price = data.get('rate', 0)

                if price > 0:
                    return {
                        'price': price,
                        'source': 'coinapi',
                        'symbol': symbol.upper(),
                        'timestamp': time.time()
                    }
            else:
                print(f"CoinAPI error {response.status_code}: {response.text}")
                return {'error': f'CoinAPI HTTP {response.status_code}'}

        except Exception as e:
            print(f"CoinAPI request failed: {e}")
            return {'error': f'CoinAPI request failed: {str(e)}'}

        return {'error': 'No valid price data from CoinAPI'}

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get cryptocurrency price with caching and fallback"""
        cache_key = f"price_{symbol.lower()}_{int(time.time() // self._cache_expiry)}"

        if not force_refresh and cache_key in self._cache:
            print(f"📦 Cache hit for {cache_key}")
            return self._cache[cache_key]

        print(f"🔄 Fetching fresh price data for {symbol}")

        # Try CoinAPI first (if available)
        if self.coinapi_key:
            coinapi_result = self.get_coinapi_price(symbol)
            if 'error' not in coinapi_result:
                self._cache[cache_key] = coinapi_result
                print(f"✅ Got price for {symbol} from CoinAPI: ${coinapi_result['price']:,.4f}")
                return coinapi_result
            else:
                print(f"⚠️ CoinAPI failed for {symbol}: {coinapi_result['error']}")

        # Fallback to data provider (CoinMarketCap + Binance)
        price_data = self.data_provider.get_cryptocurrency_prices([symbol])

        if price_data and symbol.upper() in price_data:
            result = price_data[symbol.upper()]
            result['source'] = 'data_provider'
            self._cache[cache_key] = result
            print(f"✅ Got price for {symbol} from DataProvider")
            return result
        else:
            return {
                'error': f'Failed to get price for {symbol} from any source',
                'source_attempted': 'coinapi, data_provider',
                'success': False
            }


    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Mendapatkan harga untuk multiple symbols sekaligus
        """
        try:
            price_data = self.data_provider.get_realtime_prices(symbols)
            return price_data

        except Exception as e:
            logging.error(f"Error in get_multiple_prices: {e}")
            return {'error': f'Multiple prices error: {str(e)}', 'success': False}

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan funding rate dari Binance
        """
        try:
            futures_data = self.data_provider.get_futures_data(symbol)

            if futures_data.get('success'):
                funding_details = futures_data.get('data', {}).get('funding_details', {})
                if funding_details:
                    return {
                        'symbol': symbol,
                        'funding_rate': funding_details.get('current_rate', 0),
                        'funding_time': funding_details.get('funding_time', ''),
                        'source': 'binance',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }

            return {'error': f'Failed to get funding rate for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting funding rate for {symbol}: {e}")
            return {'error': f'Funding rate error: {str(e)}', 'success': False}

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan Open Interest dari Binance
        """
        try:
            futures_data = self.data_provider.get_futures_data(symbol)

            if futures_data.get('success'):
                oi_data = futures_data.get('data', {}).get('open_interest', {})
                if oi_data:
                    return {
                        'symbol': symbol,
                        'open_interest': oi_data.get('total', 0),
                        'dominant_exchange': oi_data.get('dominant_exchange', 'Binance'),
                        'source': 'binance',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }

            return {'error': f'Failed to get open interest for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting open interest for {symbol}: {e}")
            return {'error': f'Open interest error: {str(e)}', 'success': False}

    def get_long_short_ratio(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Mendapatkan Long/Short ratio dari Binance
        """
        try:
            futures_data = self.data_provider.get_futures_data(symbol)

            if futures_data.get('success'):
                ls_data = futures_data.get('data', {}).get('long_short', {})
                if ls_data:
                    return {
                        'symbol': symbol,
                        'long_ratio': ls_data.get('long_ratio', 50),
                        'short_ratio': ls_data.get('short_ratio', 50),
                        'ratio_value': ls_data.get('ratio_value', 1.0),
                        'sentiment': ls_data.get('sentiment', 'Neutral'),
                        'timeframe': timeframe,
                        'source': 'binance',
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    }

            return {'error': f'Failed to get long/short ratio for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting long/short ratio for {symbol}: {e}")
            return {'error': f'Long/short ratio error: {str(e)}', 'success': False}

    def get_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data futures dari Binance untuk compatibility
        """
        try:
            futures_data = self.data_provider.get_futures_data(symbol)

            if futures_data.get('success'):
                data = futures_data.get('data', {})

                # Extract key metrics for compatibility
                result = {
                    'symbol': symbol,
                    'long_ratio': data.get('long_short', {}).get('long_ratio', 50),
                    'short_ratio': data.get('long_short', {}).get('short_ratio', 50),
                    'funding_rate': data.get('funding_details', {}).get('current_rate', 0),
                    'open_interest': data.get('open_interest', {}).get('total', 0),
                    'price': data.get('ticker', {}).get('price', 0),
                    'volume_24h': data.get('ticker', {}).get('volume_24h', 0),
                    'price_change_24h': data.get('ticker', {}).get('price_change_24h', 0),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'binance',
                    'success': True
                }
                return result
            else:
                return {'error': f'Failed to get futures data for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting futures data for {symbol}: {e}")
            return {'error': f'Futures data error: {str(e)}', 'success': False}

    def get_comprehensive_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data futures lengkap dari Binance
        """
        try:
            futures_data = self.data_provider.get_futures_data(symbol)

            if futures_data.get('success'):
                result = {
                    'symbol': symbol,
                    'ticker_data': futures_data.get('data', {}).get('ticker', {}),
                    'open_interest_data': futures_data.get('data', {}).get('open_interest', {}),
                    'long_short_data': futures_data.get('data', {}).get('long_short', {}),
                    'funding_rate_data': futures_data.get('data', {}).get('funding_details', {}),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'binance_comprehensive',
                    'success': True
                }

                # Add data quality score
                available_fields = len([k for k, v in futures_data.get('data', {}).items() if v])
                result['data_quality'] = {
                    'available_fields': available_fields,
                    'total_fields_expected': 4,
                    'quality_score': (available_fields / 4) * 100
                }

                return result

            return {'error': f'Failed to get comprehensive futures data for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting comprehensive futures data for {symbol}: {e}")
            return {'error': f'Comprehensive futures data error: {str(e)}', 'success': False}

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Mendapatkan overview pasar dari CoinMarketCap
        """
        try:
            return self.data_provider.get_market_overview()

        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {'error': f'Market overview error: {str(e)}', 'success': False}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi detail crypto dari CoinMarketCap
        """
        try:
            return self.data_provider.get_coin_info(symbol)

        except Exception as e:
            logging.error(f"Error getting crypto info for {symbol}: {e}")
            return {'error': f'Crypto info error: {str(e)}', 'success': False}

    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test koneksi ke semua API providers
        """
        try:
            return self.data_provider.test_all_apis()

        except Exception as e:
            logging.error(f"Error testing API connections: {e}")
            return {
                'error': f'API connection test failed: {str(e)}',
                'overall_status': 'error',
                'working_apis': 0,
                'total_apis': 2
            }

    # Legacy compatibility methods
    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """Legacy method untuk compatibility"""
        return self.get_crypto_price(symbol)

    def get_crypto_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Placeholder untuk crypto news (bisa diimplementasi nanti)
        """
        logging.warning("get_crypto_news is not implemented in the new provider.")
        return []

    def get_candlestick_data(self, symbol: str, timeframe: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get candlestick data from Binance
        """
        try:
            binance_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()

            from config import BINANCE_ENDPOINTS, get_binance_headers
            import requests

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

    def analyze_supply_demand(self, symbol, timeframe='1h'):
        """Analyze Supply & Demand zones for a cryptocurrency"""
        try:
            # Get current price first
            price_data = self.get_crypto_price(symbol)
            if not price_data.get('success') or 'error' in price_data:
                current_price = 50000  # Fallback price for BTC
            else:
                current_price = price_data.get('price', 50000)

            # Get candlestick data from Binance
            candlestick_data = self.get_candlestick_data(symbol, timeframe, 200)

            if not candlestick_data.get('success') or 'error' in candlestick_data:
                # Generate fallback SnD zones if API fails
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
                # Generate fallback if insufficient data
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
                prev1 = candles[i-1]
                prev2 = candles[i-2]
                next1 = candles[i+1]
                next2 = candles[i+2]

                high = current['high']
                low = current['low']
                volume = current['volume']

                # Swing High detection (Supply zones)
                if (high > prev1['high'] and high > prev2['high'] and
                    high > next1['high'] and high > next2['high'] and volume > 0):
                    supply_zones.append({
                        'price': high,
                        'strength': min(100, (volume / 1000000) * 5 + 50),
                        'type': 'supply'
                    })

                # Swing Low detection (Demand zones)
                if (low < prev1['low'] and low < prev2['low'] and
                    low < next1['low'] and low < next2['low'] and volume > 0):
                    demand_zones.append({
                        'price': low,
                        'strength': min(100, (volume / 1000000) * 5 + 50),
                        'type': 'demand'
                    })

            # Sort by proximity to current price
            supply_zones.sort(key=lambda x: abs(x['price'] - current_price))
            demand_zones.sort(key=lambda x: abs(x['price'] - current_price))

            # Get top 2 supply and demand zones
            supply_1 = supply_zones[0]['price'] if len(supply_zones) > 0 else current_price * 1.025
            supply_2 = supply_zones[1]['price'] if len(supply_zones) > 1 else current_price * 1.05
            demand_1 = demand_zones[0]['price'] if len(demand_zones) > 0 else current_price * 0.975
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

# Global instance
crypto_api = CryptoAPI()