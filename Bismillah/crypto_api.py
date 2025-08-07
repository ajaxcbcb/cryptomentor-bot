
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from data_provider import data_provider

class CryptoAPI:
    """
    Unified API class yang menggabungkan data dari Binance dan CoinMarketCap
    Menyediakan data real-time untuk spot dan futures
    """

    def __init__(self):
        self.provider = data_provider
        logging.info("CryptoAPI initialized with Binance + CoinMarketCap DataProvider")

    def get_crypto_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Mendapatkan harga crypto real-time dengan fallback strategy
        Priority: CoinMarketCap -> Binance -> Error
        """
        try:
            symbol = symbol.upper().replace('USDT', '')
            
            # Get prices using the provider
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
        """
        Mendapatkan harga untuk multiple symbols sekaligus
        """
        try:
            price_data = self.provider.get_realtime_prices(symbols)
            return price_data
            
        except Exception as e:
            logging.error(f"Error in get_multiple_prices: {e}")
            return {'error': f'Multiple prices error: {str(e)}', 'success': False}

    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan funding rate dari Binance
        """
        try:
            futures_data = self.provider.get_futures_data(symbol)
            
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
            futures_data = self.provider.get_futures_data(symbol)
            
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
            futures_data = self.provider.get_futures_data(symbol)
            
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

    def get_comprehensive_futures_data(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan data futures lengkap dari Binance
        """
        try:
            futures_data = self.provider.get_futures_data(symbol)
            
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
            return self.provider.get_market_overview()

        except Exception as e:
            logging.error(f"Error getting market overview: {e}")
            return {'error': f'Market overview error: {str(e)}', 'success': False}

    def get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """
        Mendapatkan informasi detail crypto dari CoinMarketCap
        """
        try:
            return self.provider.get_coin_info(symbol)

        except Exception as e:
            logging.error(f"Error getting crypto info for {symbol}: {e}")
            return {'error': f'Crypto info error: {str(e)}', 'success': False}

    def test_all_connections(self) -> Dict[str, Any]:
        """
        Test koneksi ke semua API providers
        """
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

# Global instance
crypto_api = CryptoAPI()
