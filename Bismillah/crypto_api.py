import os
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.providers.binance_provider import get_price, fetch_klines, normalize_symbol

class CryptoAPI:
    """
    Crypto API provider menggunakan Binance API sebagai pengganti CoinMarketCap
    Mempertahankan interface yang sama untuk kompatibilitas
    """

    def __init__(self):
        self.binance_available = True
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes

        logging.info("CryptoAPI initialized with Binance provider")

    def _make_request(self, url: str, headers: dict, params: dict = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Generic request method - sekarang menggunakan Binance provider
        """
        # This method is kept for compatibility but uses Binance internally
        return {'status': 'using_binance_provider'}

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Mendapatkan harga crypto dari Binance API
        """
        try:
            # Check cache first
            cache_key = f"price_{symbol.upper()}"
            if not force_refresh and cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if (time.time() - timestamp) < self._cache_timeout:
                    return cached_data

            # Normalize symbol for Binance
            normalized_symbol = normalize_symbol(symbol)

            # Get spot price from Binance
            spot_price = get_price(normalized_symbol, futures=False)

            if spot_price <= 0:
                return {'error': f'Invalid price data for {symbol}'}

            # Get 24h ticker data for additional metrics
            try:
                from app.providers.binance_provider import _http, _base_url

                # Get 24h ticker stats
                ticker_url = f"{_base_url(False)}/api/v3/ticker/24hr"
                response = _http.get(ticker_url, params={'symbol': normalized_symbol})
                ticker_data = response.json()

                change_24h = float(ticker_data.get('priceChangePercent', 0))
                volume_24h = float(ticker_data.get('volume', 0)) * spot_price  # Volume in USD
                high_24h = float(ticker_data.get('highPrice', spot_price))
                low_24h = float(ticker_data.get('lowPrice', spot_price))

            except Exception as e:
                logging.warning(f"Could not get 24h stats for {symbol}: {e}")
                change_24h = 0
                volume_24h = 0
                high_24h = spot_price
                low_24h = spot_price

            # Estimate market cap (simplified calculation)
            # For major coins, use approximate supply
            supply_estimates = {
                'BTC': 19700000,
                'ETH': 120300000,
                'BNB': 160000000,
                'SOL': 580000000,
                'XRP': 100000000000,
                'ADA': 35000000000
            }

            base_symbol = symbol.upper().replace('USDT', '')
            estimated_supply = supply_estimates.get(base_symbol, 1000000000)
            market_cap = spot_price * estimated_supply

            result = {
                'symbol': base_symbol,
                'price': spot_price,
                'change_24h': change_24h,
                'volume_24h': volume_24h,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'market_cap': market_cap,
                'last_updated': datetime.now().isoformat(),
                'source': 'binance'
            }

            # Cache the result
            self._cache[cache_key] = (result, time.time())

            return result

        except Exception as e:
            logging.error(f"Error getting crypto price for {symbol}: {e}")
            return {'error': f'Failed to get price for {symbol}: {str(e)}'}

    def get_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data futures dari Binance
        """
        try:
            normalized_symbol = normalize_symbol(symbol)

            # Get futures price
            futures_price = get_price(normalized_symbol, futures=True)

            if futures_price <= 0:
                return {'error': f'Invalid futures data for {symbol}'}

            # Get futures 24h ticker
            try:
                from app.providers.binance_provider import _http, _base_url

                ticker_url = f"{_base_url(True)}/fapi/v1/ticker/24hr"
                response = _http.get(ticker_url, params={'symbol': normalized_symbol})
                ticker_data = response.json()

                change_24h = float(ticker_data.get('priceChangePercent', 0))
                volume_24h = float(ticker_data.get('volume', 0)) * futures_price

            except Exception as e:
                logging.warning(f"Could not get futures 24h stats for {symbol}: {e}")
                change_24h = 0
                volume_24h = 0

            return {
                'symbol': symbol.upper().replace('USDT', ''),
                'futures_price': futures_price,
                'change_24h': change_24h,
                'volume_24h': volume_24h,
                'source': 'binance_futures',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logging.error(f"Error getting futures data for {symbol}: {e}")
            return {'error': f'Failed to get futures data for {symbol}: {str(e)}'}

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Mendapatkan overview pasar dari data Binance (estimasi global metrics)
        """
        try:
            # Get data for major cryptocurrencies to estimate market overview
            major_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'MATIC', 'AVAX', 'UNI']

            total_market_cap = 0
            total_volume_24h = 0
            total_change = 0
            successful_requests = 0

            for symbol in major_symbols:
                try:
                    price_data = self.get_crypto_price(symbol, force_refresh=True)
                    if 'error' not in price_data:
                        total_market_cap += price_data.get('market_cap', 0)
                        total_volume_24h += price_data.get('volume_24h', 0)
                        total_change += price_data.get('change_24h', 0)
                        successful_requests += 1
                except Exception:
                    continue

            if successful_requests == 0:
                return {'error': 'No market data available', 'success': False}

            avg_change = total_change / successful_requests

            # Estimate BTC dominance
            btc_data = self.get_crypto_price('BTC', force_refresh=True)
            btc_dominance = 58.5  # Default estimate
            if 'error' not in btc_data and total_market_cap > 0:
                btc_dominance = (btc_data.get('market_cap', 0) / total_market_cap) * 100

            return {
                'success': True,
                'global_metrics': {
                    'total_market_cap': total_market_cap,
                    'total_volume_24h': total_volume_24h,
                    'market_cap_change_24h': avg_change,
                    'btc_dominance': btc_dominance,
                    'eth_dominance': 14.2,  # Estimate
                    'active_cryptocurrencies': 9500,  # Estimate
                    'active_exchanges': 500  # Estimate
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'binance_estimated'
            }

        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {'error': f'Market overview error: {str(e)}', 'success': False}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi detail crypto (data terbatas dari Binance)
        """
        try:
            # Get basic price data
            price_data = self.get_crypto_price(symbol, force_refresh=True)

            if 'error' in price_data:
                return price_data

            # Return basic info (Binance doesn't provide detailed coin info)
            return {
                'symbol': symbol.upper().replace('USDT', ''),
                'name': self._get_coin_name(symbol),
                'description': f'Trading data for {symbol} from Binance',
                'price': price_data.get('price', 0),
                'change_24h': price_data.get('change_24h', 0),
                'volume_24h': price_data.get('volume_24h', 0),
                'market_cap': price_data.get('market_cap', 0),
                'source': 'binance_basic_info',
                'timestamp': datetime.now().isoformat(),
                'success': True
            }

        except Exception as e:
            logging.error(f"Error getting crypto info for {symbol}: {e}")
            return {'error': f'Crypto info error: {str(e)}', 'success': False}

    def _get_coin_name(self, symbol: str) -> str:
        """Get coin name mapping"""
        names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum', 
            'BNB': 'BNB',
            'SOL': 'Solana',
            'XRP': 'XRP',
            'ADA': 'Cardano',
            'DOT': 'Polkadot',
            'MATIC': 'Polygon',
            'AVAX': 'Avalanche',
            'UNI': 'Uniswap'
        }
        return names.get(symbol.upper().replace('USDT', ''), symbol.upper())

    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test koneksi ke Binance API
        """
        results = {}

        try:
            # Test Binance Spot
            btc_price = get_price('BTCUSDT', futures=False)
            success = isinstance(btc_price, (int, float)) and btc_price > 0
            results['Binance Spot'] = {
                'success': success, 
                'error': None if success else 'Invalid price returned',
                'sample_price': btc_price if success else None
            }
        except Exception as e:
            results['Binance Spot'] = {'success': False, 'error': str(e)}

        try:
            # Test Binance Futures  
            btc_futures_price = get_price('BTCUSDT', futures=True)
            success = isinstance(btc_futures_price, (int, float)) and btc_futures_price > 0
            results['Binance Futures'] = {
                'success': success,
                'error': None if success else 'Invalid futures price returned',
                'sample_price': btc_futures_price if success else None
            }
        except Exception as e:
            results['Binance Futures'] = {'success': False, 'error': str(e)}

        # Overall status
        successful_apis = sum(1 for result in results.values() if result.get('success'))
        total_apis = len(results)

        overall_status = 'excellent' if successful_apis == total_apis else 'good' if successful_apis > 0 else 'poor'

        return {
            'timestamp': datetime.now().isoformat(),
            'apis': results,
            'overall_status': overall_status,
            'working_apis': successful_apis,
            'total_apis': total_apis,
            'provider': 'binance_only'
        }

# Global instance
crypto_api = CryptoAPI()