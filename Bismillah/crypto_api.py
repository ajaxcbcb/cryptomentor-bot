
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from coinmarketcap_provider import CoinMarketCapProvider
from coinglass_provider import CoinGlassProvider

class CryptoAPI:
    """
    Unified API class yang menggabungkan CoinMarketCap dan CoinGlass
    Menyediakan data real-time untuk spot dan futures
    """
    
    def __init__(self):
        # Initialize providers
        self.cmc_provider = CoinMarketCapProvider()
        self.coinglass_provider = CoinGlassProvider()
        
        # Check API keys
        self.coinmarketcap_key = os.getenv("COINMARKETCAP_API_KEY") or os.getenv("CMC_API_KEY")
        self.coinglass_key = os.getenv("COINGLASS_API_KEY") or os.getenv("COINGLASS_SECRET")
        
        # Cache untuk performance
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
        logging.info(f"CryptoAPI initialized - CMC: {'✅' if self.coinmarketcap_key else '❌'}, CoinGlass: {'✅' if self.coinglass_key else '❌'}")

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Mendapatkan harga crypto real-time dengan fallback strategy
        Priority: CoinMarketCap -> CoinGlass -> Error
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
            if self.coinmarketcap_key:
                cmc_data = self.cmc_provider.get_cryptocurrency_quotes(symbol)
                
                if 'error' not in cmc_data and cmc_data.get('price', 0) > 0:
                    result = {
                        'symbol': symbol,
                        'price': cmc_data['price'],
                        'change_24h': cmc_data['percent_change_24h'],
                        'change_7d': cmc_data['percent_change_7d'],
                        'volume_24h': cmc_data['volume_24h'],
                        'market_cap': cmc_data['market_cap'],
                        'rank': cmc_data['cmc_rank'],
                        'source': 'coinmarketcap',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Cache result
                    self._cache[cache_key] = (result, datetime.now().timestamp())
                    return result
                else:
                    logging.warning(f"CoinMarketCap failed for {symbol}: {cmc_data.get('error', 'Unknown error')}")
            
            # Fallback to CoinGlass (untuk futures price)
            if self.coinglass_key:
                coinglass_data = self.coinglass_provider.get_futures_ticker(symbol)
                
                if 'error' not in coinglass_data and coinglass_data.get('price', 0) > 0:
                    result = {
                        'symbol': symbol,
                        'price': coinglass_data['price'],
                        'change_24h': coinglass_data['price_change_24h'],
                        'volume_24h': coinglass_data['volume_24h'],
                        'high_24h': coinglass_data.get('high_24h', 0),
                        'low_24h': coinglass_data.get('low_24h', 0),
                        'source': 'coinglass',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self._cache[cache_key] = (result, datetime.now().timestamp())
                    return result
                else:
                    logging.warning(f"CoinGlass failed for {symbol}: {coinglass_data.get('error', 'Unknown error')}")
            
            # No working API
            return {
                'error': f'All price APIs failed for {symbol}',
                'cmc_available': bool(self.coinmarketcap_key),
                'coinglass_available': bool(self.coinglass_key)
            }
            
        except Exception as e:
            logging.error(f"Error in get_crypto_price for {symbol}: {e}")
            return {'error': f'Price API error: {str(e)}'}

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan funding rate dari CoinGlass
        """
        try:
            if not self.coinglass_key:
                return {'error': 'CoinGlass API key required for funding rate data'}
            
            return self.coinglass_provider.get_funding_rate(symbol)
            
        except Exception as e:
            logging.error(f"Error getting funding rate for {symbol}: {e}")
            return {'error': f'Funding rate error: {str(e)}'}

    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan Open Interest dari CoinGlass
        """
        try:
            if not self.coinglass_key:
                return {'error': 'CoinGlass API key required for open interest data'}
            
            return self.coinglass_provider.get_open_interest(symbol)
            
        except Exception as e:
            logging.error(f"Error getting open interest for {symbol}: {e}")
            return {'error': f'Open interest error: {str(e)}'}

    def get_long_short_ratio(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Mendapatkan Long/Short ratio dari CoinGlass
        """
        try:
            if not self.coinglass_key:
                return {'error': 'CoinGlass API key required for long/short ratio data'}
            
            return self.coinglass_provider.get_long_short_ratio(symbol, timeframe)
            
        except Exception as e:
            logging.error(f"Error getting long/short ratio for {symbol}: {e}")
            return {'error': f'Long/short ratio error: {str(e)}'}

    def get_comprehensive_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data futures lengkap dari CoinGlass
        """
        try:
            if not self.coinglass_key:
                return {'error': 'CoinGlass API key required for futures data'}
            
            # Get all futures data
            ticker_data = self.coinglass_provider.get_futures_ticker(symbol)
            oi_data = self.coinglass_provider.get_open_interest(symbol)
            ls_data = self.coinglass_provider.get_long_short_ratio(symbol)
            funding_data = self.coinglass_provider.get_funding_rate(symbol)
            liquidation_data = self.coinglass_provider.get_liquidation_data(symbol)
            
            # Combine all data
            result = {
                'symbol': symbol,
                'ticker_data': ticker_data,
                'open_interest_data': oi_data,
                'long_short_data': ls_data,
                'funding_rate_data': funding_data,
                'liquidation_data': liquidation_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'coinglass_comprehensive'
            }
            
            # Count successful API calls
            successful_calls = sum([
                'error' not in data for data in [ticker_data, oi_data, ls_data, funding_data, liquidation_data]
            ])
            
            result['data_quality'] = {
                'successful_calls': successful_calls,
                'total_calls': 5,
                'quality_score': (successful_calls / 5) * 100
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
            if not self.coinmarketcap_key:
                return {'error': 'CoinMarketCap API key required for market overview'}
            
            return self.cmc_provider.get_enhanced_market_overview()
            
        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {'error': f'Market overview error: {str(e)}'}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi detail crypto dari CoinMarketCap
        """
        try:
            if not self.coinmarketcap_key:
                return {'error': 'CoinMarketCap API key required for crypto info'}
            
            return self.cmc_provider.get_cryptocurrency_info(symbol)
            
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
        
        # Test CoinMarketCap
        try:
            cmc_test = self.cmc_provider.test_connection()
            results['apis']['coinmarketcap'] = cmc_test
        except Exception as e:
            results['apis']['coinmarketcap'] = {
                'status': 'failed',
                'error': f'CMC test failed: {str(e)}'
            }
        
        # Test CoinGlass
        try:
            coinglass_test = self.coinglass_provider.test_connection()
            results['apis']['coinglass'] = coinglass_test
        except Exception as e:
            results['apis']['coinglass'] = {
                'status': 'failed',
                'error': f'CoinGlass test failed: {str(e)}'
            }
        
        # Overall status
        cmc_ok = results['apis']['coinmarketcap'].get('status') == 'success'
        coinglass_ok = results['apis']['coinglass'].get('status') == 'success'
        
        results['overall_status'] = 'excellent' if (cmc_ok and coinglass_ok) else 'good' if (cmc_ok or coinglass_ok) else 'poor'
        results['working_apis'] = sum([cmc_ok, coinglass_ok])
        results['total_apis'] = 2
        
        return results

    # Legacy compatibility methods
    def get_price_data(self, symbol: str) -> Dict[str, Any]:
        """Legacy method untuk compatibility"""
        return self.get_crypto_price(symbol)

    def get_crypto_news(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Placeholder untuk crypto news (bisa diimplementasi nanti)
        """
        return []

    def get_candlestick_data(self, symbol: str, timeframe: str, limit: int = 100) -> Dict[str, Any]:
        """
        Placeholder untuk candlestick data (bisa menggunakan Binance API)
        """
        return {'error': 'Candlestick data not implemented yet'}
