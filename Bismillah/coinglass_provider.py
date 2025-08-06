
import requests
import os
import time
from datetime import datetime

class CoinGlassProvider:
    """CoinGlass V4 API Provider - Startup Plan dengan endpoint yang benar"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY")
        self.base_url = "https://open-api-v4.coinglass.com/public/v4"
        self.headers = {
            'X-API-KEY': self.api_key,
            'accept': 'application/json'
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
        # Bersihkan symbol dan standardisasi
        clean_symbol = symbol.upper().replace('BINANCE_', '').replace('USD', '')
        
        # Jika belum ada USDT, tambahkan
        if not clean_symbol.endswith('USDT'):
            # Hanya untuk symbol yang tidak mengandung karakter khusus
            if clean_symbol.isalpha() and len(clean_symbol) <= 10:
                clean_symbol = clean_symbol + 'USDT'
        
        print(f"🔄 Symbol mapping: {symbol} -> {clean_symbol}")
        return clean_symbol

    def get_long_short_ratio(self, symbol):
        """Get long/short ratio from CoinGlass V4 - endpoint: futures/longShortRate"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting long/short ratio for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/longShortRate', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Long/Short ratio error: {result['error']}")
                return result
            
            # Parse CoinGlass V4 response structure
            data = result.get('data', [])
            if not data:
                return {'error': f'No long/short data for {clean_symbol}'}
            
            # Get latest data point
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
            else:
                latest = data
            
            # Parse the response format
            long_ratio = float(latest.get('longRate', latest.get('longRatio', 50)))
            short_ratio = 100 - long_ratio
            
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
        """Get open interest from CoinGlass V4 - endpoint: futures/openInterest"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting open interest for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/openInterest', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Open interest error: {result['error']}")
                return result
            
            data = result.get('data', [])
            if not data:
                return {'error': f'No open interest data for {clean_symbol}'}
            
            # Handle different response formats
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                previous = data[-2] if len(data) > 1 else latest
            else:
                latest = data
                previous = latest
            
            current_oi = float(latest.get('openInterest', latest.get('oi', 0)))
            previous_oi = float(previous.get('openInterest', previous.get('oi', current_oi)))
            
            oi_change_percent = ((current_oi - previous_oi) / max(previous_oi, 1)) * 100 if previous_oi > 0 else 0
            
            print(f"✅ Open Interest: ${current_oi/1000000:.1f}M ({oi_change_percent:+.1f}%)")
            
            return {
                'symbol': clean_symbol,
                'open_interest': current_oi,
                'oi_change_percent': oi_change_percent,
                'timestamp': latest.get('time', latest.get('timestamp', int(time.time() * 1000))),
                'source': 'coinglass_v4_realtime',
                'raw_data': latest
            }
            
        except Exception as e:
            print(f"❌ Exception in get_open_interest_chart: {e}")
            return {'error': f'Open interest error: {str(e)}'}

    def get_funding_rate_chart(self, symbol):
        """Get funding rate from CoinGlass V4 - endpoint: futures/fundingRate"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting funding rate for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/fundingRate', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Funding rate error: {result['error']}")
                return result
            
            data = result.get('data', [])
            if not data:
                return {'error': f'No funding rate data for {clean_symbol}'}
            
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
            else:
                latest = data
            
            funding_rate = float(latest.get('fundingRate', latest.get('rate', 0)))
            
            print(f"✅ Funding Rate: {funding_rate*100:.4f}%")
            
            return {
                'symbol': clean_symbol,
                'funding_rate': funding_rate,
                'funding_rate_percent': funding_rate * 100,
                'timestamp': latest.get('time', latest.get('timestamp', int(time.time() * 1000))),
                'source': 'coinglass_v4_realtime',
                'raw_data': latest
            }
            
        except Exception as e:
            print(f"❌ Exception in get_funding_rate_chart: {e}")
            return {'error': f'Funding rate error: {str(e)}'}

    def get_liquidation_map(self, symbol):
        """Get liquidation zones from CoinGlass V4 - endpoint: futures/liquidationMap"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting liquidation zones for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/liquidationMap', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Liquidation map error: {result['error']}")
                return result
            
            data = result.get('data', {})
            if not data:
                return {'error': f'No liquidation data for {clean_symbol}'}
            
            # Parse liquidation data
            if isinstance(data, list) and len(data) > 0:
                latest_data = data[-1]
            else:
                latest_data = data
            
            long_liquidation = float(latest_data.get('longLiquidation', latest_data.get('longs', 0)))
            short_liquidation = float(latest_data.get('shortLiquidation', latest_data.get('shorts', 0)))
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
                'zones': latest_data.get('priceRanges', latest_data.get('zones', [])),
                'source': 'coinglass_v4_realtime',
                'raw_data': latest_data
            }
            
        except Exception as e:
            print(f"❌ Exception in get_liquidation_map: {e}")
            return {'error': f'Liquidation map error: {str(e)}'}

    def get_futures_ticker(self, symbol):
        """Get futures ticker from CoinGlass V4 - endpoint: futures/ticker"""
        try:
            clean_symbol = self._clean_symbol(symbol)
            print(f"🔄 Getting futures ticker for {clean_symbol} from CoinGlass V4...")
            
            result = self._make_request('futures/ticker', {'symbol': clean_symbol})
            
            if 'error' in result:
                print(f"❌ Futures ticker error: {result['error']}")
                return result
            
            data = result.get('data', [])
            if not data:
                return {'error': f'No ticker data for {clean_symbol}'}
            
            # Get primary exchange data (usually first in array)
            if isinstance(data, list) and len(data) > 0:
                ticker_data = data[0]
            else:
                ticker_data = data
            
            price = float(ticker_data.get('price', ticker_data.get('lastPrice', 0)))
            volume_24h = float(ticker_data.get('volume24h', ticker_data.get('volume', 0)))
            price_change_24h = float(ticker_data.get('priceChangePercent', ticker_data.get('change', 0)))
            
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
