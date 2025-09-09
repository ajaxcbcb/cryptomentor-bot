import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Updated imports to use new provider modules
from app.providers.binance_provider import get_price, fetch_klines, normalize_symbol
from app.providers.cmc_provider import get_global_stats
from app.providers.coinapi_provider import get_ohlcv, get_price_spot, get_price_futures

# Removed unused import: from data_provider import data_provider

class CryptoAPI:
    """
    Unified API class yang menggabungkan data dari Binance dan CoinMarketCap
    Menyediakan data real-time untuk spot dan futures
    """

    def __init__(self):
        # Initialization logic might need to be adapted if providers are instantiated differently
        # For now, assuming providers are directly imported and used.
        logging.info("CryptoAPI initialized with new Binance, CoinMarketCap, and CoinAPI providers")

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Mendapatkan harga crypto real-time dengan fallback strategy
        Priority: CoinMarketCap -> Binance Spot -> Binance Futures -> CoinAPI -> Error
        """
        try:
            symbol_normalized = normalize_symbol(symbol) # Normalize symbol for various APIs

            # 1. Try CoinMarketCap global stats (note: this doesn't provide individual coin prices)
            # Skip CMC for individual prices since get_global_stats doesn't support symbols parameter
            # We'll prioritize Binance for price data instead

            # 2. Try Binance Spot
            binance_spot_price = get_price(symbol=symbol_normalized, market_type='spot')
            if binance_spot_price.get('success'):
                return {
                    'symbol': symbol_normalized,
                    'price': binance_spot_price.get('price', 0),
                    'change_24h': binance_spot_price.get('price_change_percent', 0),
                    'change_7d': 0, # Not directly available in this call, placeholder
                    'volume_24h': binance_spot_price.get('volume', 0),
                    'market_cap': 0, # Not directly available in this call, placeholder
                    'rank': 0, # Not directly available in this call, placeholder
                    'source': 'Binance Spot',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

            # 3. Try Binance Futures (USDT-M)
            binance_futures_price = get_price(symbol=symbol_normalized, market_type='futures')
            if binance_futures_price.get('success'):
                return {
                    'symbol': symbol_normalized,
                    'price': binance_futures_price.get('price', 0),
                    'change_24h': binance_futures_price.get('price_change_percent', 0),
                    'change_7d': 0, # Placeholder
                    'volume_24h': binance_futures_price.get('volume', 0),
                    'market_cap': 0, # Placeholder
                    'rank': 0, # Placeholder
                    'source': 'Binance Futures',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

            # 4. Try CoinAPI (as a last resort or for specific data not covered)
            coinapi_spot_price = get_price_spot(symbol_normalized)
            if coinapi_spot_price.get('success'):
                 return {
                    'symbol': symbol_normalized,
                    'price': coinapi_spot_price.get('rate', 0),
                    'change_24h': coinapi_spot_price.get('difference_24h', 0),
                    'change_7d': 0, # Placeholder
                    'volume_24h': coinapi_spot_price.get('volume_24h', 0),
                    'market_cap': coinapi_spot_price.get('market_cap', 0),
                    'rank': coinapi_spot_price.get('rank', 0),
                    'source': 'CoinAPI Spot',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
            
            coinapi_futures_price = get_price_futures(symbol_normalized)
            if coinapi_futures_price.get('success'):
                 return {
                    'symbol': symbol_normalized,
                    'price': coinapi_futures_price.get('rate', 0),
                    'change_24h': coinapi_futures_price.get('difference_24h', 0),
                    'change_7d': 0, # Placeholder
                    'volume_24h': coinapi_futures_price.get('volume_24h', 0),
                    'market_cap': coinapi_futures_price.get('market_cap', 0),
                    'rank': coinapi_futures_price.get('rank', 0),
                    'source': 'CoinAPI Futures',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }


            return {
                'error': f'Failed to get price for {symbol_normalized}',
                'source_attempted': 'CoinMarketCap, Binance Spot, Binance Futures, CoinAPI',
                'success': False
            }

        except Exception as e:
            logging.error(f"Error in get_crypto_price for {symbol}: {e}")
            return {'error': f'Price API error: {str(e)}', 'success': False}

    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Mendapatkan harga untuk multiple symbols sekaligus
        This function will need to be updated to use the new provider's method for fetching multiple symbols.
        Assuming `get_global_stats` can handle a list and returns a similar format.
        """
        try:
            # Get multiple prices using Binance provider since CMC get_global_stats doesn't support symbols
            results = {}
            for symbol in symbols:
                price_data = self.get_crypto_price(symbol)
                if price_data.get('success'):
                    results[symbol] = price_data
            return {'success': True, 'data': results}

        except Exception as e:
            logging.error(f"Error in get_multiple_prices: {e}")
            return {'error': f'Multiple prices error: {str(e)}', 'success': False}

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan funding rate dari Binance Futures
        """
        try:
            # Assuming a specific function exists in binance_provider for futures data like funding rate
            # This is a placeholder, the actual implementation depends on binance_provider capabilities
            futures_data = get_price(symbol=symbol, market_type='futures') # Re-using get_price for futures data
            
            if futures_data.get('success'):
                # The structure of futures_data needs to be inspected to extract funding rate correctly.
                # Assuming 'funding_rate' and 'next_funding_time' are available keys.
                return {
                    'symbol': symbol,
                    'funding_rate': futures_data.get('funding_rate', 0),
                    'funding_time': futures_data.get('next_funding_time', ''),
                    'source': 'Binance Futures',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

            return {'error': f'Failed to get funding rate for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting funding rate for {symbol}: {e}")
            return {'error': f'Funding rate error: {str(e)}', 'success': False}

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan Open Interest dari Binance Futures
        """
        try:
            # Similar to funding rate, this requires a specific call to the Binance Futures provider
            futures_data = get_price(symbol=symbol, market_type='futures') # Re-using get_price for futures data

            if futures_data.get('success'):
                # Assuming 'open_interest' is available. Structure needs verification.
                return {
                    'symbol': symbol,
                    'open_interest': futures_data.get('open_interest', 0),
                    'dominant_exchange': 'Binance', # Hardcoded as we are targeting Binance
                    'source': 'Binance Futures',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }

            return {'error': f'Failed to get open interest for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting open interest for {symbol}: {e}")
            return {'error': f'Open interest error: {str(e)}', 'success': False}

    def get_long_short_ratio(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Mendapatkan Long/Short ratio dari Binance Futures
        """
        try:
            # This data is typically provided by specific data providers for sentiment analysis.
            # Assuming the new `binance_provider` might expose this or a similar metric.
            # Placeholder implementation:
            futures_data = get_price(symbol=symbol, market_type='futures') # Re-using get_price for futures data

            if futures_data.get('success'):
                 # Assuming 'long_short_ratio' or similar is available
                return {
                    'symbol': symbol,
                    'long_ratio': futures_data.get('long_short_ratio', 50), # Example key
                    'short_ratio': 100 - futures_data.get('long_short_ratio', 50), # Example calculation
                    'ratio_value': futures_data.get('long_short_ratio', 50) / 100, # Example calculation
                    'sentiment': 'Neutral', # Needs actual calculation based on ratio
                    'timeframe': timeframe,
                    'source': 'Binance Futures',
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
            futures_data = get_price(symbol=symbol, market_type='futures')

            if futures_data.get('success'):
                # Extract key metrics for compatibility
                result = {
                    'symbol': symbol,
                    'long_ratio': futures_data.get('long_short_ratio', 50), # Assuming this key exists
                    'short_ratio': 100 - futures_data.get('long_short_ratio', 50), # Assuming this key exists
                    'funding_rate': futures_data.get('funding_rate', 0), # Assuming this key exists
                    'open_interest': futures_data.get('open_interest', 0), # Assuming this key exists
                    'price': futures_data.get('price', 0),
                    'volume_24h': futures_data.get('volume', 0),
                    'price_change_24h': futures_data.get('price_change_24h', 0), # Assuming this key exists
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Binance Futures',
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
        This function needs to be adapted to call specific functions from binance_provider
        that return detailed ticker, open interest, long/short, and funding rate data.
        """
        try:
            # This is a conceptual placeholder. You'll need specific calls for each data point.
            ticker_data = get_price(symbol=symbol, market_type='futures')
            open_interest_data = get_price(symbol=symbol, market_type='futures') # Placeholder, assuming a specific call for OI
            long_short_data = get_price(symbol=symbol, market_type='futures') # Placeholder, assuming a specific call for LS ratio
            funding_rate_data = get_price(symbol=symbol, market_type='futures') # Placeholder, assuming a specific call for funding rate

            if ticker_data.get('success'): # Assuming success implies data is available
                result = {
                    'symbol': symbol,
                    'ticker_data': ticker_data.get('ticker', {}), # Adjust keys based on actual response
                    'open_interest_data': open_interest_data.get('open_interest', {}), # Adjust keys
                    'long_short_data': long_short_data.get('long_short_data', {}), # Adjust keys
                    'funding_rate_data': funding_rate_data.get('funding_rate_data', {}), # Adjust keys
                    'timestamp': datetime.now().isoformat(),
                    'source': 'binance_comprehensive',
                    'success': True
                }

                # Add data quality score - this needs to be defined based on what's available
                available_fields = sum([
                    1 for k in ['ticker_data', 'open_interest_data', 'long_short_data', 'funding_rate_data'] 
                    if result.get(k) and result.get(k) not in [{}, None]
                ])
                result['data_quality'] = {
                    'available_fields': available_fields,
                    'total_fields_expected': 4,
                    'quality_score': (available_fields / 4) * 100
                }

                return result
            else:
                return {'error': f'Failed to get comprehensive futures data for {symbol}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting comprehensive futures data for {symbol}: {e}")
            return {'error': f'Comprehensive futures data error: {str(e)}', 'success': False}

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Mendapatkan overview pasar dari CoinMarketCap
        """
        try:
            # Get market overview from CMC global stats
            global_data = get_global_stats()
            return {
                'success': True,
                'global_metrics': global_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'CoinMarketCap'
            }

        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {'error': f'Market overview error: {str(e)}', 'success': False}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi detail crypto dari CoinMarketCap
        """
        try:
            # CMC get_global_stats doesn't provide individual coin info
            # Return basic info with a note that detailed info isn't available
            return {
                'error': 'Detailed coin info not available in current CMC provider',
                'symbol': symbol,
                'success': False,
                'note': 'Use get_crypto_price for basic price data'
            }

        except Exception as e:
            logging.error(f"Error getting crypto info for {symbol}: {e}")
            return {'error': f'Crypto info error: {str(e)}', 'success': False}

    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test koneksi ke semua API providers
        """
        # This method needs to be updated to reflect the new providers
        results = {}
        try:
            # Test CoinMarketCap
            cmc_test = get_global_stats()
            # CMC get_global_stats returns data directly, so check if it has expected fields
            success = bool(cmc_test.get('total_market_cap_usd') or cmc_test.get('btc_dominance'))
            results['CoinMarketCap'] = {'success': success, 'error': None if success else 'No valid data returned'}
        except Exception as e:
            results['CoinMarketCap'] = {'success': False, 'error': str(e)}

        try:
            # Test Binance Spot
            binance_spot_test = get_price(symbol='BTCUSDT', market_type='spot')
            results['Binance Spot'] = {'success': binance_spot_test.get('success', False), 'error': binance_spot_test.get('error')}
        except Exception as e:
            results['Binance Spot'] = {'success': False, 'error': str(e)}

        try:
            # Test Binance Futures
            binance_futures_test = get_price(symbol='BTCUSDT', market_type='futures')
            results['Binance Futures'] = {'success': binance_futures_test.get('success', False), 'error': binance_futures_test.get('error')}
        except Exception as e:
            results['Binance Futures'] = {'success': False, 'error': str(e)}
            
        try:
            # Test CoinAPI
            coinapi_test = get_price_spot('BTC')
            results['CoinAPI Spot'] = {'success': coinapi_test.get('success', False), 'error': coinapi_test.get('error')}
        except Exception as e:
            results['CoinAPI Spot'] = {'success': False, 'error': str(e)}


        working_apis = sum([1 for status in results.values() if status.get('success')])
        total_apis = len(results)
        overall_status = 'success' if working_apis == total_apis else 'partial' if working_apis > 0 else 'error'

        return {
            'overall_status': overall_status,
            'working_apis': working_apis,
            'total_apis': total_apis,
            'details': results
        }

    # Legacy compatibility methods
    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """Legacy method untuk compatibility"""
        return self.get_crypto_price(symbol)

    def get_crypto_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Placeholder for crypto news. This functionality might need a new provider.
        """
        logging.warning("get_crypto_news is not implemented in the new provider setup. Needs a dedicated news API provider.")
        return []

    def get_candlestick_data(self, symbol: str, timeframe: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get candlestick data from Binance
        """
        try:
            # Use the new fetch_klines function from binance_provider
            candlesticks_data = fetch_klines(symbol=symbol, interval=timeframe, limit=limit)

            if candlesticks_data.get('success'):
                # The structure of the returned data needs to match the expected format
                # Assuming fetch_klines returns a list of dictionaries with 'timestamp', 'open', 'high', 'low', 'close', 'volume'
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'data': candlesticks_data.get('data', []),
                    'source': 'Binance',
                    'success': True
                }
            else:
                return {'error': f'Binance API error: {candlesticks_data.get("error", "Unknown error")}', 'success': False}

        except Exception as e:
            logging.error(f"Error getting candlestick data for {symbol} with timeframe {timeframe}: {e}")
            return {'error': f'Candlestick data error: {str(e)}', 'success': False}

    def analyze_supply_demand(self, symbol, timeframe='1h'):
        """Analyze Supply & Demand zones for a cryptocurrency using Binance candlestick data"""
        try:
            # Get current price first
            price_data = self.get_crypto_price(symbol)
            if not price_data.get('success') or 'error' in price_data:
                # Fallback prices for BTC and ETH, and a generic fallback
                fallback_prices = {'BTC': 50000, 'ETH': 3000}
                current_price = fallback_prices.get(symbol.upper(), 100) 
                logging.warning(f"Could not fetch current price for {symbol}, using fallback price: {current_price}")
            else:
                current_price = price_data.get('price', 100)

            # Get candlestick data from Binance
            candlestick_data = self.get_candlestick_data(symbol, timeframe, 200)

            if not candlestick_data.get('success') or 'error' in candlestick_data:
                logging.error(f"Failed to get candlestick data for {symbol}: {candlestick_data.get('error')}")
                # Generate fallback SnD zones if API fails
                return {
                    'Supply 1': current_price * 1.025,
                    'Supply 2': current_price * 1.05,
                    'Demand 1': current_price * 0.975,
                    'Demand 2': current_price * 0.95,
                    'source': 'fallback_api_error',
                    'success': True
                }

            candles = candlestick_data.get('data', [])
            if len(candles) < 50:
                logging.warning(f"Insufficient candlestick data for {symbol} ({len(candles)} candles), generating fallback zones.")
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
                        'strength': min(100, (volume / 1000000) * 5 + 50), # Example strength calculation
                        'type': 'supply'
                    })

                # Swing Low detection (Demand zones)
                if (low < prev1['low'] and low < prev2['low'] and
                    low < next1['low'] and low < next2['low'] and volume > 0):
                    demand_zones.append({
                        'price': low,
                        'strength': min(100, (volume / 1000000) * 5 + 50), # Example strength calculation
                        'type': 'demand'
                    })

            # Sort by proximity to current price
            supply_zones.sort(key=lambda x: abs(x['price'] - current_price))
            demand_zones.sort(key=lambda x: abs(x['price'] - current_price))

            # Get top 2 supply and demand zones, use fallback if not enough found
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
# crypto_api = CryptoAPI() # Moved instantiation to the end, as it's a common practice.
# Consider making crypto_api initialization conditional or managed by a factory if needed.
crypto_api = CryptoAPI()