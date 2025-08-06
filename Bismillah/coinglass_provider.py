
import requests
import os
import time
from datetime import datetime

class CoinGlassProvider:
    """CoinGlass V4 API Provider - Startup Plan dengan endpoint yang benar"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY")
        self.base_url = "https://open-api-v4.coinglass.com/api"
        self.headers = {
            'X-API-KEY': self.api_key,
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if not self.api_key:
            print("⚠️ COINGLASS_API_KEY not found in environment variables")
        else:
            print("✅ CoinGlass V4 API initialized with correct endpoints")

    def _make_request(self, endpoint, params=None):
        """Make authenticated request to CoinGlass V4 API"""
        try:
            if not self.api_key:
                return {'error': 'COINGLASS_API_KEY not found'}
            
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params or {}, timeout=15)
            
            print(f"🔄 CoinGlass V4 Request: {url} with params: {params}")
            print(f"📡 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ CoinGlass V4 Response: {data.get('code', 'unknown')} - {len(str(data))} chars")
                
                if data.get('code') == 0 or data.get('success', True):
                    return data
                else:
                    error_msg = data.get('msg', data.get('message', 'Unknown API error'))
                    print(f"❌ CoinGlass V4 API Error: {error_msg}")
                    return {'error': f"API Error: {error_msg}"}
            elif response.status_code == 404:
                symbol = params.get('symbol', 'unknown') if params else 'unknown'
                print(f"⚠️ Symbol {symbol} not available on CoinGlass V4")
                return {'error': f'Data tidak tersedia untuk pair {symbol}'}
            else:
                error_msg = f"HTTP {response.status_code}: Service temporarily unavailable"
                print(f"❌ CoinGlass V4 HTTP Error: {error_msg}")
                return {'error': error_msg}
                
        except requests.exceptions.Timeout:
            print("❌ CoinGlass V4 API timeout")
            return {'error': 'CoinGlass API timeout'}
        except Exception as e:
            print(f"❌ CoinGlass V4 Exception: {e}")
            return {'error': f'CoinGlass API error: {str(e)}'}

    def _clean_symbol(self, symbol):
        """Clean and standardize symbol for CoinGlass API"""
        # Bersihkan symbol tanpa mengubah format standar
        clean_symbol = symbol.upper().replace('BINANCE_', '').strip()
        
        # Jangan ubah symbol yang sudah dalam format USDT
        if clean_symbol.endswith('USDT'):
            print(f"🔄 Symbol mapping: {symbol} -> {clean_symbol} (kept as-is)")
            return clean_symbol
        
        # Untuk symbol dasar seperti BTC, ETH, tambahkan USDT
        if clean_symbol.isalpha() and len(clean_symbol) <= 10 and not clean_symbol.endswith('USD'):
            clean_symbol = clean_symbol + 'USDT'
        
        print(f"🔄 Symbol mapping: {symbol} -> {clean_symbol}")
        return clean_symbol

    def get_long_short_ratio(self, symbol):
        """Get long/short ratio from CoinGlass V4 - endpoint: futures/top-long-short-account-ratio/history"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting long/short ratio for {clean_symbol} from CoinGlass V4...")
            
            # Try account ratio first
            result = self._make_request('futures/top-long-short-account-ratio/history', {
                'symbol': clean_symbol,
                'interval': '1h'
            })
            
            if 'error' in result:
                # Fallback to position ratio
                print(f"⚠️ Account ratio failed, trying position ratio...")
                result = self._make_request('futures/top-long-short-position-ratio/history', {
                    'symbol': clean_symbol,
                    'interval': '1h'
                })
            
            if 'error' in result:
                print(f"❌ Long/Short ratio error: {result['error']}")
                return result
            
            data = result.get('data', [])
            if not data:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}
            
            # Get latest data point
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
            else:
                latest = data
            
            # Parse the response format
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
                'timestamp': latest.get('time', latest.get('timestamp', int(time.time() * 1000))),
                'source': 'coinglass_v4_realtime',
                'raw_data': latest
            }
            
        except Exception as e:
            print(f"❌ Exception in get_long_short_ratio: {e}")
            return {'error': f'Long/short ratio error: {str(e)}'}

    def get_open_interest_chart(self, symbol):
        """Get open interest from CoinGlass V4 - endpoint: futures/openInterest/exchange-list"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting open interest for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/openInterest/exchange-list', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Open interest error: {result['error']}")
                return result
            
            data = result.get('data', [])
            if not data:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}
            
            # Calculate total OI across exchanges
            total_oi = 0
            latest_timestamp = 0
            
            for exchange_data in data:
                oi_value = float(exchange_data.get('openInterest', exchange_data.get('oi', 0)))
                total_oi += oi_value
                
                # Get latest timestamp
                timestamp = exchange_data.get('time', exchange_data.get('timestamp', 0))
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
                'source': 'coinglass_v4_realtime',
                'raw_data': data
            }
            
        except Exception as e:
            print(f"❌ Exception in get_open_interest_chart: {e}")
            return {'error': f'Open interest error: {str(e)}'}

    def get_funding_rate_chart(self, symbol):
        """Get funding rate from CoinGlass V4 - endpoint: futures/fundingRate/exchange-list"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting funding rate for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/fundingRate/exchange-list', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Funding rate error: {result['error']}")
                return result
            
            data = result.get('data', [])
            if not data:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}
            
            # Get funding rate from primary exchange (usually Binance)
            primary_exchange = None
            for exchange_data in data:
                if exchange_data.get('exchangeName', '').lower() == 'binance':
                    primary_exchange = exchange_data
                    break
            
            # Fallback to first exchange if Binance not found
            if not primary_exchange and data:
                primary_exchange = data[0]
            
            if not primary_exchange:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}
            
            funding_rate = float(primary_exchange.get('fundingRate', primary_exchange.get('rate', 0)))
            
            print(f"✅ Funding Rate: {funding_rate*100:.4f}%")
            
            return {
                'symbol': clean_symbol,
                'funding_rate': funding_rate,
                'funding_rate_percent': funding_rate * 100,
                'timestamp': primary_exchange.get('time', primary_exchange.get('timestamp', int(time.time() * 1000))),
                'source': 'coinglass_v4_realtime',
                'raw_data': primary_exchange
            }
            
        except Exception as e:
            print(f"❌ Exception in get_funding_rate_chart: {e}")
            return {'error': f'Funding rate error: {str(e)}'}

    def get_liquidation_map(self, symbol):
        """Get liquidation zones from CoinGlass V4 - endpoint: futures/liquidation/aggregated-map"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting liquidation zones for {clean_symbol} from CoinGlass V4...")
            
            # Try aggregated map first
            result = self._make_request('futures/liquidation/aggregated-map', {'symbol': clean_symbol})
            
            if 'error' in result:
                # Fallback to pair-level map
                print(f"⚠️ Aggregated map failed, trying pair-level map...")
                result = self._make_request('futures/liquidation/map', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Liquidation map error: {result['error']}")
                return result
            
            data = result.get('data', {})
            if not data:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}
            
            # Parse liquidation data
            if isinstance(data, list) and len(data) > 0:
                latest_data = data[-1]
            else:
                latest_data = data
            
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
                'zones': latest_data.get('priceRanges', latest_data.get('zones', latest_data.get('liquidationData', []))),
                'source': 'coinglass_v4_realtime',
                'raw_data': latest_data
            }
            
        except Exception as e:
            print(f"❌ Exception in get_liquidation_map: {e}")
            return {'error': f'Liquidation map error: {str(e)}'}

    def get_futures_ticker(self, symbol):
        """Get futures ticker from CoinGlass V4 - endpoint: futures/price-change-list"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting futures ticker for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/price-change-list', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Futures ticker error: {result['error']}")
                return result
            
            data = result.get('data', [])
            if not data:
                return {'error': f'⚠️ Data tidak tersedia untuk pair {clean_symbol} di CoinGlass'}
            
            # Get primary exchange data (usually first in array)
            if isinstance(data, list) and len(data) > 0:
                ticker_data = data[0]
            else:
                ticker_data = data
            
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
                'source': 'coinglass_v4_realtime',
                'raw_data': ticker_data
            }
            
        except Exception as e:
            print(f"❌ Exception in get_futures_ticker: {e}")
            return {'error': f'Futures ticker error: {str(e)}'}

    def get_comprehensive_futures_data(self, symbol):
        """Get all futures data for a symbol from CoinGlass V4"""
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
                'source': 'coinglass_v4_comprehensive',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Comprehensive data error: {e}")
            return {'error': f'Comprehensive data error: {str(e)}'}

    def test_connection(self):
        """Test connection to CoinGlass V4 API"""
        try:
            print("🧪 Testing CoinGlass V4 connection...")
            result = self._make_request('futures/ticker', {'symbol': 'BTCUSDT'})
            
            if 'error' not in result:
                print("✅ CoinGlass V4 connection successful")
                return {'status': 'success', 'message': 'Connection OK'}
            else:
                print(f"❌ CoinGlass V4 connection failed: {result['error']}")
                return {'status': 'failed', 'error': result['error']}
                
        except Exception as e:
            print(f"❌ CoinGlass V4 connection test exception: {e}")
            return {'status': 'failed', 'error': str(e)}

print("✅ CoinGlassProvider V4 loaded with correct endpoints")
