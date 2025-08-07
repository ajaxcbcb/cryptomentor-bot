import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

import data_provider # Import the new modular data_provider

class CryptoAPI:
    """
    Unified API class yang menggabungkan data dari berbagai sumber
    Menyediakan data real-time untuk spot dan futures
    """

    def __init__(self):
        self.provider = data_provider
        logging.info("CryptoAPI initialized with modular DataProvider")

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Mendapatkan harga crypto real-time dengan fallback strategy
        Priority: CoinMarketCap -> CoinGlass -> Binance -> Error
        """
        try:
            symbol = symbol.upper().replace('USDT', '')

            # Check cache first (unless force refresh)
            cache_key = f"price_{symbol}"
            if not force_refresh and cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                    return cached_data

            # Try CoinMarketCap first (lebih comprehensive untuk spot price)
            cmc_data = self.provider.get_realtime_prices(symbols=[symbol])

            if 'error' not in cmc_data and cmc_data and symbol in cmc_data and cmc_data[symbol].get('price', 0) > 0:
                result = {
                    'symbol': symbol,
                    'price': cmc_data[symbol]['price'],
                    'change_24h': cmc_data[symbol].get('percent_change_24h'),
                    'change_7d': cmc_data[symbol].get('percent_change_7d'),
                    'volume_24h': cmc_data[symbol].get('volume_24h'),
                    'market_cap': cmc_data[symbol].get('market_cap'),
                    'rank': cmc_data[symbol].get('cmc_rank'),
                    'source': 'coinmarketcap',
                    'timestamp': datetime.now().isoformat()
                }

                # Cache result
                self._cache[cache_key] = (result, datetime.now().timestamp())
                return result
            else:
                logging.warning(f"CoinMarketCap failed or returned no data for {symbol}: {cmc_data.get('error', 'Unknown error')}")

            # Fallback to CoinGlass (untuk futures price)
            coinglass_data = self.provider.get_futures_data(symbols=[symbol])

            if 'error' not in coinglass_data and coinglass_data and symbol in coinglass_data and coinglass_data[symbol].get('price', 0) > 0:
                result = {
                    'symbol': symbol,
                    'price': coinglass_data[symbol]['price'],
                    'change_24h': coinglass_data[symbol].get('price_change_24h'),
                    'volume_24h': coinglass_data[symbol].get('volume_24h'),
                    'high_24h': coinglass_data[symbol].get('high_24h', 0),
                    'low_24h': coinglass_data[symbol].get('low_24h', 0),
                    'source': 'coinglass',
                    'timestamp': datetime.now().isoformat()
                }

                self._cache[cache_key] = (result, datetime.now().timestamp())
                return result
            else:
                logging.warning(f"CoinGlass failed or returned no data for {symbol}: {coinglass_data.get('error', 'Unknown error')}")

            # Fallback to Binance (for spot price if CoinGlass also fails)
            binance_data = self.provider.get_realtime_prices(symbols=[symbol], exchange='binance')
            if 'error' not in binance_data and binance_data and symbol in binance_data and binance_data[symbol].get('price', 0) > 0:
                result = {
                    'symbol': symbol,
                    'price': binance_data[symbol]['price'],
                    'change_24h': binance_data[symbol].get('price_change_percent'), # Binance uses price_change_percent
                    'volume_24h': binance_data[symbol].get('volume'),
                    'high_24h': binance_data[symbol].get('high_price'),
                    'low_24h': binance_data[symbol].get('low_price'),
                    'source': 'binance',
                    'timestamp': datetime.now().isoformat()
                }
                self._cache[cache_key] = (result, datetime.now().timestamp())
                return result
            else:
                logging.warning(f"Binance failed or returned no data for {symbol}: {binance_data.get('error', 'Unknown error')}")


            # No working API
            return {
                'error': f'All price APIs failed for {symbol}',
                'sources_attempted': ['coinmarketcap', 'coinglass', 'binance']
            }

        except Exception as e:
            logging.error(f"Error in get_crypto_price for {symbol}: {e}")
            return {'error': f'Price API error: {str(e)}'}

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan funding rate dari CoinGlass
        """
        try:
            # Use the new provider method
            funding_data = self.provider.get_futures_data(symbols=[symbol])
            if 'error' in funding_data:
                return {'error': funding_data['error']}
            if not funding_data or symbol not in funding_data:
                return {'error': f"No funding rate data found for {symbol}"}
            
            return funding_data[symbol].get('fundingRate', {'error': f"Funding rate not available for {symbol}"})

        except Exception as e:
            logging.error(f"Error getting funding rate for {symbol}: {e}")
            return {'error': f'Funding rate error: {str(e)}'}

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan Open Interest dari CoinGlass
        """
        try:
            # Use the new provider method
            oi_data = self.provider.get_futures_data(symbols=[symbol])
            if 'error' in oi_data:
                return {'error': oi_data['error']}
            if not oi_data or symbol not in oi_data:
                return {'error': f"No open interest data found for {symbol}"}

            return oi_data[symbol].get('openInterest', {'error': f"Open interest not available for {symbol}"})

        except Exception as e:
            logging.error(f"Error getting open interest for {symbol}: {e}")
            return {'error': f'Open interest error: {str(e)}'}

    def get_long_short_ratio(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Mendapatkan Long/Short ratio dari CoinGlass
        """
        try:
            # Use the new provider method, filtering by timeframe if possible
            ls_data = self.provider.get_futures_data(symbols=[symbol]) # Assuming this can fetch LSR
            if 'error' in ls_data:
                return {'error': ls_data['error']}
            if not ls_data or symbol not in ls_data:
                return {'error': f"No long/short ratio data found for {symbol}"}
            
            # The structure of LSR data might vary, need to adapt based on actual provider output
            # Assuming it's directly available in the futures data for the symbol
            return ls_data[symbol].get('longShortRatio', {'error': f"Long/short ratio not available for {symbol}"})

        except Exception as e:
            logging.error(f"Error getting long/short ratio for {symbol}: {e}")
            return {'error': f'Long/short ratio error: {str(e)}'}

    def get_comprehensive_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data futures lengkap dari CoinGlass
        """
        try:
            # Use the new provider method to get all futures data for the symbol
            futures_data = self.provider.get_futures_data(symbols=[symbol])

            if 'error' in futures_data:
                return {'error': futures_data['error']}
            
            if not futures_data or symbol not in futures_data:
                return {'error': f"No futures data found for {symbol}"}

            # Extract relevant parts, assuming they are nested within the symbol's data
            result = {
                'symbol': symbol,
                'ticker_data': futures_data[symbol].get('ticker', {}), # Assuming ticker data is available
                'open_interest_data': futures_data[symbol].get('openInterest', {}),
                'long_short_data': futures_data[symbol].get('longShortRatio', {}), # Assuming LSR is available
                'funding_rate_data': futures_data[symbol].get('fundingRate', {}),
                # Liquidation data might need a separate call if not included in get_futures_data
                'liquidation_data': {}, # Placeholder
                'timestamp': datetime.now().isoformat(),
                'source': 'coinglass_comprehensive'
            }
            
            # Add a placeholder for quality score calculation if needed, based on available data
            result['data_quality'] = {
                'available_fields': [k for k, v in futures_data[symbol].items() if v != {} and v != 0 and v != 1.0],
                'total_fields_expected': 5 # Example, adjust as needed
            }

            return result

        except Exception as e:
            logging.error(f"Error getting comprehensive futures data for {symbol}: {e}")
            return {'error': f'Comprehensive futures data error: {str(e)}'}

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Mendapatkan overview pasar dari CoinMarketCap
        """
        try:
            # Use the new provider method to get market overview
            return self.provider.get_coin_info(return_all=True) # Assuming this fetches overview

        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {'error': f'Market overview error: {str(e)}'}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi detail crypto dari CoinMarketCap
        """
        try:
            # Use the new provider method to get specific crypto info
            return self.provider.get_coin_info(symbols=[symbol])

        except Exception as e:
            logging.error(f"Error getting crypto info for {symbol}: {e}")
            return {'error': f'Crypto info error: {str(e)}'}

    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test koneksi ke semua API providers
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'apis': {}
        }

        # Test CoinMarketCap via provider
        try:
            cmc_test = self.provider.test_connection(exchange='coinmarketcap')
            results['apis']['coinmarketcap'] = cmc_test
        except Exception as e:
            results['apis']['coinmarketcap'] = {
                'status': 'failed',
                'error': f'CMC test failed: {str(e)}'
            }

        # Test CoinGlass via provider
        try:
            coinglass_test = self.provider.test_connection(exchange='coinglass')
            results['apis']['coinglass'] = coinglass_test
        except Exception as e:
            results['apis']['coinglass'] = {
                'status': 'failed',
                'error': f'CoinGlass test failed: {str(e)}'
            }

        # Test Binance via provider
        try:
            binance_test = self.provider.test_connection(exchange='binance')
            results['apis']['binance'] = binance_test
        except Exception as e:
            results['apis']['binance'] = {
                'status': 'failed',
                'error': f'Binance test failed: {str(e)}'
            }

        # Overall status
        cmc_ok = results['apis']['coinmarketcap'].get('status') == 'success'
        coinglass_ok = results['apis']['coinglass'].get('status') == 'success'
        binance_ok = results['apis']['binance'].get('status') == 'success'

        working_apis_count = sum([cmc_ok, coinglass_ok, binance_ok])
        total_apis_count = 3

        if working_apis_count == total_apis_count:
            results['overall_status'] = 'excellent'
        elif working_apis_count > 0:
            results['overall_status'] = 'good'
        else:
            results['overall_status'] = 'poor'
        
        results['working_apis'] = working_apis_count
        results['total_apis'] = total_apis_count

        return results

    # Legacy compatibility methods
    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """Legacy method untuk compatibility"""
        return self.get_crypto_price(symbol)

    def get_crypto_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Placeholder untuk crypto news (bisa diimplementasi nanti)
        """
        # This functionality might need to be integrated into the new data_provider
        # For now, returning an empty list or an error if not implemented
        logging.warning("get_crypto_news is not yet implemented with the new data provider.")
        return []

    def get_candlestick_data(self, symbol: str, timeframe: str, limit: int = 100) -> Dict[str, Any]:
        """
        Placeholder untuk candlestick data (bisa menggunakan Binance API)
        """
        # This functionality might need to be integrated into the new data_provider
        # For now, returning an error message
        logging.warning("get_candlestick_data is not yet implemented with the new data provider.")
        return {'error': 'Candlestick data not implemented yet'}