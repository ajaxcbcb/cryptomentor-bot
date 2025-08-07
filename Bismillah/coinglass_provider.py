
import os
import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

class CoinGlassProvider:
    """
    CoinGlass V4 API Provider for STARTUP Plan
    Provides real-time futures data with proper error handling
    """
    
    def __init__(self):
        self.api_key = os.getenv("COINGLASS_API_KEY") or os.getenv("COINGLASS_SECRET")
        self.base_url = "https://open-api-v4.coinglass.com"
        self.startup_endpoints = {
            'tickers': '/public/v1/futures/tickers',
            'oi_statistics': '/public/v1/oi-change-statistics',
            'liquidation': '/public/v1/liquidation_chart',
            'funding': '/public/v1/funding_rates',
            'long_short': '/public/v1/long_short_account_ratio'
        }
        
        if not self.api_key:
            print("⚠️ COINGLASS_API_KEY not found in environment variables")
            print("💡 Please set COINGLASS_API_KEY in Replit Secrets")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "X-API-Key": self.api_key,
            "accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            if not self.api_key:
                return {'error': 'CoinGlass API key not configured'}
            
            url = f"{self.base_url}{endpoint}"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    return data
                else:
                    return {'error': f"API returned success=false: {data.get('msg', 'Unknown error')}"}
            elif response.status_code == 401:
                return {'error': 'Invalid API key or unauthorized access'}
            elif response.status_code == 429:
                return {'error': 'Rate limit exceeded - STARTUP plan limits reached'}
            else:
                return {'error': f"HTTP {response.status_code}: {response.text[:100]}"}
                
        except requests.exceptions.Timeout:
            return {'error': 'Request timeout - CoinGlass API slow response'}
        except requests.exceptions.ConnectionError:
            return {'error': 'Connection error - CoinGlass API unreachable'}
        except Exception as e:
            return {'error': f"Unexpected error: {str(e)}"}
    
    def get_futures_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get futures ticker data for a specific symbol"""
        try:
            clean_symbol = symbol.upper().replace('USDT', '')
            
            # Call STARTUP plan endpoint
            result = self._make_request(self.startup_endpoints['tickers'])
            
            if 'error' in result:
                return result
            
            tickers = result.get('data', [])
            if not tickers:
                return {'error': 'No ticker data received'}
            
            # Find the symbol in tickers
            symbol_data = None
            for ticker in tickers:
                if ticker.get('symbol', '').upper() == clean_symbol:
                    symbol_data = ticker
                    break
            
            if not symbol_data:
                return {'error': f'Symbol {clean_symbol} not found in tickers'}
            
            # Validate data quality
            price = float(symbol_data.get('price', 0))
            if price in [0, 1, 1000] or price is None:
                print(f"⚠️ Warning: {clean_symbol} price {price} may be dummy data")
                data_quality = 'dummy_detected'
            else:
                data_quality = 'real_time'
            
            return {
                'symbol': clean_symbol,
                'price': price,
                'change_24h': float(symbol_data.get('change24h', 0)),
                'volume_24h': float(symbol_data.get('volume24h', 0)),
                'funding_rate': float(symbol_data.get('fundingRate', 0)),
                'exchange': symbol_data.get('exchangeName', 'Binance'),
                'data_quality': data_quality,
                'source': 'coinglass_v4_startup',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Ticker processing error: {str(e)}'}
    
    def get_oi_change_statistics(self) -> Dict[str, Any]:
        """Get Open Interest change statistics for all coins"""
        try:
            result = self._make_request(self.startup_endpoints['oi_statistics'])
            
            if 'error' in result:
                return result
            
            oi_data = result.get('data', [])
            if not oi_data:
                return {'error': 'No OI statistics data received'}
            
            print(f"✅ Retrieved OI data for {len(oi_data)} coins")
            
            # Process and validate data
            processed_data = []
            for coin in oi_data[:10]:  # Top 10 coins
                symbol = coin.get('symbol', 'Unknown')
                change_24h = float(coin.get('changeRate24h', 0))
                
                processed_data.append({
                    'symbol': symbol,
                    'oi_change_24h': change_24h,
                    'open_interest': float(coin.get('openInterest', 0)),
                    'trend': 'increasing' if change_24h > 5 else 'decreasing' if change_24h < -5 else 'stable'
                })
                
                print(f"📊 {symbol}: OI Change 24H = {change_24h:+.2f}%")
            
            return {
                'data': processed_data,
                'total_coins': len(oi_data),
                'source': 'coinglass_v4_startup',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'OI statistics processing error: {str(e)}'}
    
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """Get specific symbol's open interest data"""
        try:
            clean_symbol = symbol.upper().replace('USDT', '')
            
            # Get from OI statistics
            oi_stats = self.get_oi_change_statistics()
            
            if 'error' in oi_stats:
                return oi_stats
            
            # Find symbol in data
            symbol_oi = None
            for coin in oi_stats.get('data', []):
                if coin.get('symbol', '').upper() == clean_symbol:
                    symbol_oi = coin
                    break
            
            if not symbol_oi:
                return {'error': f'OI data not found for {clean_symbol}'}
            
            return {
                'symbol': clean_symbol,
                'open_interest': symbol_oi.get('open_interest', 0),
                'oi_change_percent': symbol_oi.get('oi_change_24h', 0),
                'trend': symbol_oi.get('trend', 'stable'),
                'source': 'coinglass_v4_startup'
            }
            
        except Exception as e:
            return {'error': f'Open Interest error: {str(e)}'}
    
    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """Get funding rate for a specific symbol"""
        try:
            # Get from ticker data which includes funding rate
            ticker_data = self.get_futures_ticker(symbol)
            
            if 'error' in ticker_data:
                return ticker_data
            
            funding_rate = ticker_data.get('funding_rate', 0)
            
            return {
                'symbol': ticker_data.get('symbol'),
                'funding_rate': funding_rate,
                'funding_trend': 'positive' if funding_rate > 0.005 else 'negative' if funding_rate < -0.002 else 'neutral',
                'exchange': ticker_data.get('exchange', 'Binance'),
                'next_funding_time': '',  # Not available in STARTUP plan
                'source': 'coinglass_v4_startup'
            }
            
        except Exception as e:
            return {'error': f'Funding rate error: {str(e)}'}
    
    def get_long_short_ratio(self, symbol: str, timeframe: str = '1h') -> Dict[str, Any]:
        """Get long/short ratio (limited in STARTUP plan)"""
        try:
            # STARTUP plan has limited access to this endpoint
            # We'll try but expect it might not work
            params = {
                'symbol': symbol.upper().replace('USDT', ''),
                'intervalType': 2  # 1 hour
            }
            
            result = self._make_request('/public/v1/long_short_account_ratio', params)
            
            if 'error' in result:
                # Fallback: estimate from other data
                return {
                    'error': 'Long/Short ratio not available in STARTUP plan',
                    'estimated_long_ratio': 55.0,  # Default estimate
                    'estimated_short_ratio': 45.0,
                    'note': 'Estimated values - upgrade to PRO for real data'
                }
            
            # If we get data, process it
            ls_data = result.get('data', [])
            if ls_data:
                latest = ls_data[-1]
                long_ratio = float(latest.get('longAccount', 50))
                short_ratio = float(latest.get('shortAccount', 50))
                
                return {
                    'symbol': symbol.upper().replace('USDT', ''),
                    'long_ratio': long_ratio,
                    'short_ratio': short_ratio,
                    'ratio_value': long_ratio / short_ratio if short_ratio > 0 else 1.0,
                    'source': 'coinglass_v4_startup'
                }
            
            return {'error': 'No long/short data available'}
            
        except Exception as e:
            return {'error': f'Long/Short ratio error: {str(e)}'}
    
    def get_liquidation_data(self, symbol: str) -> Dict[str, Any]:
        """Get liquidation data (simplified for STARTUP plan)"""
        try:
            # STARTUP plan may have limited liquidation data
            params = {
                'symbol': symbol.upper().replace('USDT', ''),
                'intervalType': 1  # 24h
            }
            
            result = self._make_request('/public/v1/liquidation_chart', params)
            
            if 'error' in result:
                return {'error': 'Liquidation data not available in STARTUP plan'}
            
            liq_data = result.get('data', [])
            if liq_data:
                latest = liq_data[-1]
                total_liq = float(latest.get('totalLiquidation', 0))
                long_liq = float(latest.get('longLiquidation', 0))
                short_liq = float(latest.get('shortLiquidation', 0))
                
                return {
                    'symbol': symbol.upper().replace('USDT', ''),
                    'total_liquidation': total_liq,
                    'long_liquidation': long_liq,
                    'short_liquidation': short_liq,
                    'dominant_side': 'Long Heavy' if long_liq > short_liq * 1.5 else 'Short Heavy' if short_liq > long_liq * 1.5 else 'Balanced',
                    'source': 'coinglass_v4_startup'
                }
            
            return {'error': 'No liquidation data available'}
            
        except Exception as e:
            return {'error': f'Liquidation data error: {str(e)}'}
    
    def test_startup_plan_access(self) -> Dict[str, Any]:
        """Test STARTUP plan access to all available endpoints"""
        print("🧪 Testing CoinGlass V4 STARTUP Plan Access...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'endpoints_tested': 0,
            'successful_endpoints': 0,
            'failed_endpoints': 0,
            'endpoint_results': {}
        }
        
        # Test futures tickers
        print("🔍 Testing /futures/tickers...")
        ticker_result = self.get_futures_ticker('BTC')
        results['endpoints_tested'] += 1
        
        if 'error' not in ticker_result:
            results['successful_endpoints'] += 1
            results['endpoint_results']['tickers'] = '✅ Working'
            print(f"✅ Tickers: BTC Price = ${ticker_result.get('price', 0):.2f}")
        else:
            results['failed_endpoints'] += 1
            results['endpoint_results']['tickers'] = f'❌ {ticker_result["error"]}'
            print(f"❌ Tickers failed: {ticker_result['error']}")
        
        # Test OI statistics
        print("🔍 Testing /oi-change-statistics...")
        oi_result = self.get_oi_change_statistics()
        results['endpoints_tested'] += 1
        
        if 'error' not in oi_result:
            results['successful_endpoints'] += 1
            results['endpoint_results']['oi_statistics'] = '✅ Working'
            print(f"✅ OI Statistics: {oi_result.get('total_coins', 0)} coins")
        else:
            results['failed_endpoints'] += 1
            results['endpoint_results']['oi_statistics'] = f'❌ {oi_result["error"]}'
            print(f"❌ OI Statistics failed: {oi_result['error']}")
        
        # Calculate success rate
        success_rate = (results['successful_endpoints'] / results['endpoints_tested']) * 100 if results['endpoints_tested'] > 0 else 0
        results['success_rate'] = success_rate
        results['total_endpoints'] = results['endpoints_tested']
        
        print(f"\n📊 STARTUP Plan Test Results:")
        print(f"✅ Success Rate: {success_rate:.1f}%")
        print(f"📈 Working Endpoints: {results['successful_endpoints']}/{results['endpoints_tested']}")
        
        if success_rate >= 80:
            print("🟢 STARTUP Plan: Excellent access")
        elif success_rate >= 50:
            print("🟡 STARTUP Plan: Partial access")
        else:
            print("🔴 STARTUP Plan: Limited access")
        
        return results
    
    def test_connection(self) -> Dict[str, Any]:
        """Test basic connection to CoinGlass V4 API"""
        try:
            if not self.api_key:
                return {
                    'status': 'failed',
                    'error': 'API key not configured',
                    'solution': 'Set COINGLASS_API_KEY in Replit Secrets'
                }
            
            # Simple test with tickers endpoint
            result = self._make_request(self.startup_endpoints['tickers'])
            
            if 'error' not in result:
                return {
                    'status': 'success',
                    'message': 'CoinGlass V4 STARTUP plan connected successfully',
                    'data_available': len(result.get('data', [])) > 0
                }
            else:
                return {
                    'status': 'failed',
                    'error': result['error'],
                    'endpoint': 'futures/tickers'
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'error': f'Connection test failed: {str(e)}'
            }

# Test execution function
def run_startup_test():
    """Run the STARTUP plan test as requested"""
    print("🚀 Menjalankan CoinGlass V4 STARTUP Analysis...\n")
    
    provider = CoinGlassProvider()
    
    # Test futures tickers
    print("🔍 Memanggil endpoint /futures/tickers")
    ticker_result = provider.get_futures_ticker('BTC')
    
    if 'error' not in ticker_result:
        price = ticker_result.get('price', 0)
        change_24h = ticker_result.get('change_24h', 0)
        print(f"✅ BTC Price: ${price}, 24H Change: {change_24h:+.2f}%")
        
        if price in [0, 1, 1000] or price is None:
            print("⚠ Terindikasi dummy data (harga tidak wajar).")
        else:
            print("✅ Data kemungkinan besar real-time.")
    else:
        print(f"❌ Gagal panggil API: {ticker_result['error']}")
    
    time.sleep(1)
    
    # Test OI statistics
    print("\n🔍 Memanggil endpoint /oi-change-statistics")
    oi_result = provider.get_oi_change_statistics()
    
    if 'error' not in oi_result:
        total_coins = oi_result.get('total_coins', 0)
        print(f"✅ Total coins dengan data OI: {total_coins}")
    else:
        print(f"❌ Gagal panggil API: {oi_result['error']}")
    
    # Run comprehensive test
    print("\n🧪 Running comprehensive STARTUP plan test...")
    test_results = provider.test_startup_plan_access()
    
    return test_results

if __name__ == "__main__":
    run_startup_test()
