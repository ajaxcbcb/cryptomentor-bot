import requests
import os
import time
from datetime import datetime

class CoinGlassProvider:
    """CoinGlass API Provider - Startup Plan with correct endpoints"""

    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY")
        # CoinGlass V2/V4 API endpoints - Fixed URLs
        self.base_url = "https://open-api.coinglass.com"
        self.endpoints = {
            'futures_ticker': '/public/v2/futures/ticker',
            'long_short_ratio': '/public/v2/futures/longShortChart',
            'open_interest': '/public/v2/futures/openInterest',
            'funding_rate': '/public/v2/futures/fundingRate',
            'liquidation_map': '/public/v2/futures/liquidation_chart'
        }

        if not self.api_key:
            print("⚠️ COINGLASS_API_KEY not found in environment variables")
        else:
            print("✅ CoinGlass API initialized")

    def _make_coinglass_request(self, endpoint, params=None):
        """Make authenticated request to CoinGlass V2/V4 API with proper error handling"""
        if not self.api_key:
            return {'error': 'CoinGlass API key not configured'}

        url = f"{self.base_url}{endpoint}"
        headers = {
            "accept": "application/json",
            "X-API-KEY": self.api_key
        }

        # Clean up params - remove None values
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        print(f"🔄 CoinGlass Request: {url} with params: {params}")

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            print(f"📡 Response Status: {response.status_code}")

            if response.status_code == 404:
                symbol = params.get('symbol', 'N/A') if params else 'N/A'
                print(f"⚠️ Symbol {symbol} not available on CoinGlass")
                return {'error': f'⚠️ Data tidak tersedia untuk pair {symbol} di CoinGlass'}
            elif response.status_code == 401:
                return {'error': 'API key invalid atau tidak aktif'}
            elif response.status_code == 429:
                return {'error': 'Rate limit exceeded, coba lagi nanti'}
            elif response.status_code != 200:
                return {'error': f'CoinGlass API error: HTTP {response.status_code}'}

            data = response.json()
            print(f"✅ CoinGlass Response: {response.status_code} - {len(str(data))} chars")

            # Check for API-specific success indicators
            if 'success' in data and not data['success']:
                return {'error': f"CoinGlass API failed: {data.get('msg', data.get('message', 'Unknown error'))}"}

            return data

        except requests.Timeout:
            print(f"❌ CoinGlass request timeout")
            return {'error': 'Request timeout - coba lagi'}
        except requests.RequestException as e:
            print(f"❌ CoinGlass request error: {e}")
            return {'error': f'Network error: {str(e)[:50]}...'}
        except Exception as e:
            print(f"❌ CoinGlass processing error: {e}")
            return {'error': f'Processing error: {str(e)[:50]}...'}

    def _clean_symbol(self, symbol):
        """Map symbol to CoinGlass format - keep standard pairs as-is"""
        if not symbol:
            return 'BTC'  # Default fallback - use clean symbol

        symbol = symbol.upper().strip()

        # Remove any exchange prefixes and suffixes
        symbol = symbol.replace('BINANCE_', '').replace('COINBASE_', '')
        symbol = symbol.replace('USDT', '').replace('USD', '').replace('BUSD', '')

        # Return clean symbol - CoinGlass V2 uses clean symbols like BTC, ETH
        return symbol

    def get_long_short_ratio(self, symbol):
        """Get long/short ratio from CoinGlass V2 API"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting long/short ratio for {clean_symbol} from CoinGlass...")

            result = self._make_coinglass_request(self.endpoints['long_short_ratio'], {
                'symbol': clean_symbol,
                'interval': '1h',
                'limit': 1 # Get latest data
            })

            if 'error' in result:
                print(f"❌ Long/Short ratio error: {result['error']}")
                return result

            data = result.get('data', {})
            if not data or not data.get('list'):
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}

            # Get latest data point
            latest = data['list'][-1]

            # CoinGlass V2 uses different keys for long/short ratios
            long_ratio = float(latest.get('longAccount', latest.get('longRatio', latest.get('longRate', 50))))
            short_ratio = float(latest.get('shortAccount', latest.get('shortRatio', latest.get('shortRate', 50))))

            # Normalize to 100%
            total = long_ratio + short_ratio
            if total > 0:
                long_ratio = (long_ratio / total) * 100
                short_ratio = (short_ratio / total) * 100
            else:
                long_ratio = 50
                short_ratio = 50

            print(f"✅ Long/Short data: {long_ratio:.1f}% / {short_ratio:.1f}%")

            return {
                'symbol': clean_symbol,
                'long_ratio': long_ratio,
                'short_ratio': short_ratio,
                'timestamp': latest.get('timestamp', int(time.time() * 1000)),
                'source': 'coinglass_v2_realtime',
                'raw_data': latest
            }

        except Exception as e:
            print(f"❌ Exception in get_long_short_ratio: {e}")
            return {'error': f'Long/short ratio error: {str(e)[:50]}...'}

    def get_open_interest_chart(self, symbol):
        """Get open interest from CoinGlass V2 API"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting open interest for {clean_symbol} from CoinGlass...")

            result = self._make_coinglass_request(self.endpoints['open_interest'], {'symbol': clean_symbol})

            if 'error' in result:
                print(f"❌ Open interest error: {result['error']}")
                return result

            data = result.get('data', {})
            if not data or not data.get('list'):
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}

            # Calculate total OI across exchanges
            total_oi = 0
            latest_timestamp = 0

            for exchange_data in data['list']:
                oi_value = float(exchange_data.get('openInterest', exchange_data.get('oi', 0)))
                total_oi += oi_value

                # Get latest timestamp
                timestamp = exchange_data.get('timestamp', 0)
                if timestamp > latest_timestamp:
                    latest_timestamp = timestamp

            # Simple change calculation (mock for now)
            oi_change_percent = 0  # Will be calculated properly with historical data

            print(f"✅ Open Interest: ${total_oi/1000000:.1f}M")

            return {
                'symbol': clean_symbol,
                'open_interest': total_oi,
                'oi_change_percent': oi_change_percent,
                'timestamp': latest_timestamp or int(time.time() * 1000),
                'source': 'coinglass_v2_realtime',
                'raw_data': data['list']
            }

        except Exception as e:
            print(f"❌ Exception in get_open_interest_chart: {e}")
            return {'error': f'Open interest error: {str(e)[:50]}...'}

    def get_funding_rate_chart(self, symbol):
        """Get funding rate from CoinGlass V2 API"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting funding rate for {clean_symbol} from CoinGlass...")

            result = self._make_coinglass_request(self.endpoints['funding_rate'], {'symbol': clean_symbol})

            if 'error' in result:
                print(f"❌ Funding rate error: {result['error']}")
                return result

            data = result.get('data', {})
            if not data or not data.get('list'):
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}

            # Get funding rate from primary exchange (usually Binance)
            primary_exchange = None
            for exchange_data in data['list']:
                if exchange_data.get('exchangeName', '').lower() == 'binance':
                    primary_exchange = exchange_data
                    break

            # Fallback to first exchange if Binance not found
            if not primary_exchange and data['list']:
                primary_exchange = data['list'][0]

            if not primary_exchange:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}

            funding_rate = float(primary_exchange.get('fundingRate', primary_exchange.get('rate', 0)))

            print(f"✅ Funding Rate: {funding_rate*100:.4f}%")

            return {
                'symbol': clean_symbol,
                'funding_rate': funding_rate,
                'funding_rate_percent': funding_rate * 100,
                'timestamp': primary_exchange.get('timestamp', int(time.time() * 1000)),
                'source': 'coinglass_v2_realtime',
                'raw_data': primary_exchange
            }

        except Exception as e:
            print(f"❌ Exception in get_funding_rate_chart: {e}")
            return {'error': f'Funding rate error: {str(e)[:50]}...'}

    def get_liquidation_map(self, symbol):
        """Get liquidation zones from CoinGlass V2 API"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting liquidation zones for {clean_symbol} from CoinGlass...")

            result = self._make_coinglass_request(self.endpoints['liquidation_map'], {'symbol': clean_symbol})

            if 'error' in result:
                print(f"❌ Liquidation map error: {result['error']}")
                return result

            data = result.get('data', {})
            if not data or not data.get('list'):
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}

            # Parse liquidation data - use the latest entry
            latest_data = data['list'][-1]

            long_liquidation = float(latest_data.get('longLiquidation', latest_data.get('longs', latest_data.get('buyLiquidation', 0))))
            short_liquidation = float(latest_data.get('shortLiquidation', latest_data.get('shorts', latest_data.get('sellLiquidation', 0))))
            total_liquidation = long_liquidation + short_liquidation

            dominant_side = 'Long' if long_liquidation > short_liquidation else 'Short'

            print(f"✅ Liquidations: ${total_liquidation/1000000:.1f}M (Dominant: {dominant_side})")

            return {
                'symbol': clean_symbol,
                'long_liquidation': long_liquidation,
                'short_liquidation': short_liquidation,
                'total_liquidation': total_liquidation,
                'long_percentage': (long_liquidation / max(total_liquidation, 1)) * 100,
                'short_percentage': (short_liquidation / max(total_liquidation, 1)) * 100,
                'dominant_side': dominant_side,
                'zones': latest_data.get('priceRanges', latest_data.get('zones', latest_data.get('liquidationData', [])),
                'source': 'coinglass_v2_realtime',
                'raw_data': latest_data
            }

        except Exception as e:
            print(f"❌ Exception in get_liquidation_map: {e}")
            return {'error': f'Liquidation map error: {str(e)[:50]}...'}

    def get_futures_ticker(self, symbol):
        """Get futures ticker from CoinGlass V2 API"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting futures ticker for {clean_symbol} from CoinGlass...")

            result = self._make_coinglass_request(self.endpoints['futures_ticker'], {'symbol': clean_symbol})

            if 'error' in result:
                print(f"❌ Futures ticker error: {result['error']}")
                return result

            data = result.get('data', {})
            if not data or not data.get('list'):
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}

            # Get primary exchange data (usually first in array)
            ticker_data = data['list'][0]

            price = float(ticker_data.get('price', ticker_data.get('lastPrice', ticker_data.get('last', 0))))
            volume_24h = float(ticker_data.get('volume24h', ticker_data.get('volume', ticker_data.get('vol', 0))))
            price_change_24h = float(ticker_data.get('priceChangePercent', ticker_data.get('change', ticker_data.get('changePercent', 0))))

            # Ensure we don't return dummy data
            if price <= 0:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}

            print(f"✅ Ticker: ${price:.2f} ({price_change_24h:+.2f}%)")

            return {
                'symbol': clean_symbol,
                'price': price,
                'volume_24h': volume_24h,
                'price_change_24h': price_change_24h,
                'exchange': ticker_data.get('exchangeName', ticker_data.get('exchange', 'Binance')),
                'source': 'coinglass_v2_realtime',
                'raw_data': ticker_data
            }

        except Exception as e:
            print(f"❌ Exception in get_futures_ticker: {e}")
            return {'error': f'Futures ticker error: {str(e)[:50]}...'}

    def get_comprehensive_futures_data(self, symbol):
        """Get all futures data for a symbol from CoinGlass API"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting comprehensive futures data for {clean_symbol}...")

            # Get all data concurrently
            ticker_data = self.get_futures_ticker(clean_symbol)
            ls_data = self.get_long_short_ratio(clean_symbol)
            oi_data = self.get_open_interest_chart(clean_symbol)
            funding_data = self.get_funding_rate_chart(clean_symbol)
            liq_data = self.get_liquidation_map(clean_symbol)

            # Count successful calls
            successful_calls = 0
            for data in [ticker_data, ls_data, oi_data, funding_data, liq_data]:
                if 'error' not in data:
                    successful_calls += 1

            data_quality = 'excellent' if successful_calls >= 4 else 'good' if successful_calls >= 3 else 'partial' if successful_calls >= 2 else 'poor'

            print(f"✅ Comprehensive data: {successful_calls}/5 endpoints successful ({data_quality})")

            return {
                'symbol': clean_symbol,
                'ticker_data': ticker_data,
                'long_short_data': ls_data,
                'open_interest_data': oi_data,
                'funding_rate_data': funding_data,
                'liquidation_data': liq_data,
                'successful_calls': successful_calls,
                'total_calls': 5,
                'data_quality': data_quality,
                'source': 'coinglass_v2_comprehensive',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Comprehensive data error: {e}")
            return {'error': f'Comprehensive data error: {str(e)[:50]}...'}

    def test_connection(self):
        """Test connection to CoinGlass API"""
        try:
            print("🧪 Testing CoinGlass connection...")
            result = self._make_coinglass_request(self.endpoints['futures_ticker'], {'symbol': 'BTC'})

            if 'error' not in result:
                print("✅ CoinGlass connection successful")
                return {'status': 'success', 'message': 'Connection OK'}
            else:
                print(f"❌ CoinGlass connection failed: {result['error']}")
                return {'status': 'failed', 'error': result['error']}

        except Exception as e:
            print(f"❌ CoinGlass connection test exception: {e}")
            return {'status': 'failed', 'error': str(e)}

print("✅ CoinGlassProvider V2 loaded with correct endpoints")