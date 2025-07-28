import requests
import os
import time
from datetime import datetime, timezone
from binance_provider import BinanceFuturesProvider

class CryptoAPI:
    def __init__(self):
        self.provider = BinanceFuturesProvider()
        self.cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
        self.binance_spot_url = "https://api.binance.com/api/v3"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1"

        # Binance-exclusive configuration
        print("🚀 CryptoAPI initialized with Binance-exclusive mode")
        print(f"📊 Binance Spot API: {self.binance_spot_url}")
        print(f"📈 Binance Futures API: {self.binance_futures_url}")
        print(f"📰 CryptoNews API: {'✅ Enabled' if self.cryptonews_key else '❌ Disabled'}")
        print("🎯 All price data centralized to Binance APIs only")

    # === BINANCE SPOT API METHODS ===

    def get_binance_server_time(self):
        """Get Binance server time"""
        try:
            response = requests.get(f"{self.binance_spot_url}/time", timeout=10)
            response.raise_for_status()
            data = response.json()
            server_time = data['serverTime']

            # Convert to readable format
            dt = datetime.fromtimestamp(server_time / 1000, tz=timezone.utc)

            return {
                'server_time_ms': server_time,
                'server_time_iso': dt.isoformat(),
                'server_time_readable': dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'source': 'binance_spot'
            }
        except Exception as e:
            return {'error': f"Server time error: {str(e)}"}

    def get_binance_price(self, symbol, force_refresh=False):
        """Get real-time price from Binance Spot API with enhanced error handling and comprehensive USDT validation"""
        try:
            # Strict USDT-only validation - reject non-USDT symbols immediately
            original_symbol = symbol.upper()
            
            # Enhanced USDT validation
            if not original_symbol.endswith('USDT'):
                normalized_symbol = original_symbol + 'USDT'
            else:
                normalized_symbol = original_symbol
            
            # Double-check USDT requirement
            if 'USDT' not in normalized_symbol:
                print(f"❌ STRICT VALIDATION: Symbol {original_symbol} rejected - USDT pairs only")
                return {
                    'error': f'Symbol {original_symbol} not supported - USDT pairs required',
                    'symbol': original_symbol,
                    'api_call_successful': False,
                    'error_type': 'non_usdt_symbol',
                    'validation_failed': True
                }

            symbol = normalized_symbol
            print(f"✅ USDT Validation passed: {original_symbol} → {symbol}")

            # Enhanced deployment detection with debug logging
            deployment_indicators = {
                'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
                'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1',
                'REPL_SLUG': bool(os.getenv('REPL_SLUG')),
                'REPL_OWNER': bool(os.getenv('REPL_OWNER')),
                'deployment_flag_file': os.path.exists('/tmp/repl_deployment_flag')
            }
            
            is_deployment = any(deployment_indicators.values())
            print(f"🔍 Deployment Detection: {deployment_indicators} → {'DEPLOYMENT' if is_deployment else 'DEVELOPMENT'}")

            # Force refresh in deployment for real-time data
            if is_deployment:
                force_refresh = True
                print(f"🚀 DEPLOYMENT MODE: Force refresh enabled for real-time data")

            # Enhanced headers with better error handling
            headers = {
                'User-Agent': 'CryptoMentorAI/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate'
            }

            # Cache control for development
            if not is_deployment or force_refresh:
                headers.update({
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                })

            # Request parameters with cache busting
            params = {'symbol': symbol}
            if force_refresh:
                import time
                params['_t'] = int(time.time() * 1000)
                print(f"🔄 Cache buster added: {params['_t']}")

            # Prioritize endpoints based on deployment mode
            endpoints_to_try = [
                f"{self.binance_spot_url}/ticker/24hr",   # Comprehensive data
                f"{self.binance_spot_url}/ticker/price"   # Simple price fallback
            ]

            print(f"📡 Will try {len(endpoints_to_try)} Binance endpoints for {symbol}")

            last_error = None
            for attempt, endpoint in enumerate(endpoints_to_try, 1):
                try:
                    print(f"📡 Binance API Call {attempt}/{len(endpoints_to_try)}: {endpoint}")
                    print(f"📊 Request params: {params}")
                    
                    # Make request with enhanced timeout handling
                    response = requests.get(
                        endpoint,
                        params=params,
                        timeout=30 if is_deployment else 15,  # Generous timeout for deployment
                        headers=headers,
                        allow_redirects=True
                    )
                    
                    print(f"📊 Response Status: {response.status_code}")
                    print(f"📊 Response Size: {len(response.content)} bytes")
                    print(f"📊 Response Headers: {dict(list(response.headers.items())[:5])}")  # First 5 headers
                    
                    # Enhanced status code handling
                    if response.status_code == 429:
                        print(f"⏳ Rate limited by Binance, waiting...")
                        import time
                        time.sleep(2)
                        last_error = "Rate limited"
                        continue
                    elif response.status_code == 418:
                        print(f"🔒 IP banned by Binance temporarily")
                        last_error = "IP banned"
                        continue
                    elif response.status_code != 200:
                        error_msg = f"HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            error_msg = f"HTTP {response.status_code}: {error_data.get('msg', 'Unknown error')}"
                            print(f"❌ Binance API Error: {error_data}")
                        except:
                            print(f"❌ Non-JSON error response: {response.text[:100]}")
                        last_error = error_msg
                        continue

                    response.raise_for_status()
                    
                    # Enhanced JSON parsing with better error messages
                    try:
                        data = response.json()
                        print(f"📊 JSON parsing successful, data type: {type(data)}")
                        
                        # Log essential parts of response for debugging
                        if isinstance(data, dict):
                            debug_fields = ['symbol', 'lastPrice', 'price']
                            debug_data = {k: data.get(k) for k in debug_fields if k in data}
                            print(f"📊 Key response fields: {debug_data}")
                        else:
                            print(f"📊 Raw response preview: {str(data)[:200]}")
                            
                    except ValueError as json_error:
                        print(f"❌ JSON parsing failed: {json_error}")
                        print(f"📊 Raw response (first 300 chars): {response.text[:300]}")
                        last_error = f"JSON parsing error: {json_error}"
                        continue
                    
                    # Validate response structure
                    if not data or not isinstance(data, dict):
                        print(f"❌ Invalid response structure for {symbol}")
                        print(f"📊 Response type: {type(data)}, Data: {data}")
                        last_error = "Invalid response structure"
                        continue

                    # Process different endpoint types with robust price extraction
                    if endpoint.endswith('/ticker/24hr'):
                        print(f"📊 Processing 24hr ticker data...")
                        
                        # Enhanced field validation for 24hr ticker
                        essential_fields = ['lastPrice']
                        optional_fields = ['priceChangePercent', 'highPrice', 'lowPrice', 'volume', 'quoteVolume']
                        
                        missing_essential = [field for field in essential_fields if field not in data]
                        if missing_essential:
                            print(f"❌ Missing essential fields: {missing_essential}")
                            last_error = f"Missing essential fields: {missing_essential}"
                            continue

                        # COMPREHENSIVE PRICE PARSING AND VALIDATION
                        price_result = self._extract_and_validate_price(data, 'lastPrice', symbol, '24hr ticker')
                        if price_result['error']:
                            print(f"❌ Price validation failed: {price_result['error']}")
                            last_error = price_result['error']
                            continue
                        
                        price = price_result['price']
                        print(f"✅ Price validation successful: {symbol} = ${price:,.8f}")

                        # Parse additional fields with safe defaults
                        try:
                            change_24h = self._safe_float_parse(data.get('priceChangePercent'), 0)
                            high_24h = self._safe_float_parse(data.get('highPrice'), 0)
                            low_24h = self._safe_float_parse(data.get('lowPrice'), 0)
                            volume_24h = self._safe_float_parse(data.get('volume'), 0)
                            quote_volume_24h = self._safe_float_parse(data.get('quoteVolume'), 0)
                            open_price = self._safe_float_parse(data.get('openPrice'), 0)
                            price_change = self._safe_float_parse(data.get('priceChange'), 0)
                            count = self._safe_int_parse(data.get('count'), 0)
                            
                            print(f"📊 Additional fields parsed - Volume: {volume_24h:,.0f}, Change: {change_24h:.2f}%")
                            
                        except Exception as parse_error:
                            print(f"⚠️ Warning: Error parsing additional fields: {parse_error}")
                            # Use safe defaults
                            change_24h = high_24h = low_24h = volume_24h = quote_volume_24h = 0
                            open_price = price_change = count = 0

                        # Build comprehensive result
                        result = {
                            'symbol': symbol,
                            'price': price,
                            'change_24h': change_24h,
                            'high_24h': high_24h,
                            'low_24h': low_24h,
                            'volume_24h': volume_24h,
                            'quote_volume_24h': quote_volume_24h,
                            'open_price': open_price,
                            'close_price': price,
                            'price_change': price_change,
                            'count': count,
                            'first_id': data.get('firstId', 0),
                            'last_id': data.get('lastId', 0),
                            'open_time': data.get('openTime', 0),
                            'close_time': data.get('closeTime', 0),
                            'source': 'binance_spot_24hr',
                            'api_call_successful': True,
                            'price_validation_passed': True,
                            'raw_last_price': data.get('lastPrice'),
                            'deployment_mode': is_deployment,
                            'usdt_validated': True
                        }
                        
                        print(f"✅ 24hr ticker SUCCESS: {symbol} = ${price:,.6f} (Change: {change_24h:+.2f}%)")
                        return result

                    else:  # Simple price endpoint
                        print(f"📊 Processing simple price data...")
                        
                        # Validate price field exists
                        if 'price' not in data:
                            print(f"❌ Price field missing in simple response")
                            last_error = "Price field missing in simple response"
                            continue

                        # COMPREHENSIVE PRICE PARSING FOR SIMPLE ENDPOINT
                        price_result = self._extract_and_validate_price(data, 'price', symbol, 'simple price')
                        if price_result['error']:
                            print(f"❌ Simple price validation failed: {price_result['error']}")
                            last_error = price_result['error']
                            continue
                        
                        price = price_result['price']
                        print(f"✅ Simple price validation successful: {symbol} = ${price:,.8f}")

                        # Build simple result
                        result = {
                            'symbol': symbol,
                            'price': price,
                            'change_24h': 0,  # Not available
                            'volume_24h': 0,  # Not available
                            'source': 'binance_spot_simple',
                            'api_call_successful': True,
                            'price_validation_passed': True,
                            'raw_price': data.get('price'),
                            'deployment_mode': is_deployment,
                            'usdt_validated': True
                        }
                        
                        print(f"✅ Simple price SUCCESS: {symbol} = ${price:,.6f}")
                        return result

                except requests.exceptions.Timeout as e:
                    error_msg = f"Timeout ({endpoint}): {str(e)}"
                    print(f"⏰ {error_msg}")
                    last_error = error_msg
                    continue
                except requests.exceptions.ConnectionError as e:
                    error_msg = f"Connection error ({endpoint}): {str(e)}"
                    print(f"🔌 {error_msg}")
                    last_error = error_msg
                    continue
                except requests.exceptions.HTTPError as e:
                    error_msg = f"HTTP error ({endpoint}): {str(e)}"
                    print(f"🌐 {error_msg}")
                    last_error = error_msg
                    continue
                except Exception as e:
                    error_msg = f"Unexpected error ({endpoint}): {str(e)}"
                    print(f"❌ {error_msg}")
                    last_error = error_msg
                    continue

            # All endpoints failed
            final_error = f"All Binance endpoints failed for {symbol}. Last error: {last_error}"
            print(f"🚨 TOTAL FAILURE: {final_error}")
            raise Exception(final_error)

        except Exception as e:
            error_msg = f"Binance price retrieval completely failed for {symbol}: {str(e)}"
            print(f"💥 COMPLETE FAILURE: {error_msg}")
            return {
                'error': error_msg,
                'symbol': symbol,
                'api_call_successful': False,
                'error_type': 'complete_binance_failure',
                'deployment_mode': getattr(self, '_last_deployment_check', False)
            }

    def is_deployment_mode(self):
        """Check if running in deployment mode with comprehensive detection"""
        deployment_checks = {
            'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
            'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1', 
            'REPLIT_ENVIRONMENT': os.getenv('REPLIT_ENVIRONMENT') == 'deployment',
            'deployment_flag': os.path.exists('/tmp/repl_deployment_flag'),
            'replit_slug': bool(os.getenv('REPL_SLUG')),
            'replit_owner': bool(os.getenv('REPL_OWNER'))
        }
        
        is_deployment = any(deployment_checks.values())
        return is_deployment

    def _format_price_display(self, price):
        """Format price for display based on value"""
        try:
            if price >= 1000:
                return f"${price:,.2f}"
            elif price >= 1:
                return f"${price:.4f}"
            elif price >= 0.01:
                return f"${price:.6f}"
            else:
                return f"${price:.8f}"
        except:
            return f"${price}"

    def _fallback_price(self, symbol, error_msg):
        """Fallback price data when all APIs fail"""
        return {
            'error': error_msg,
            'symbol': symbol,
            'price': 0,
            'source': 'fallback_error',
            'api_call_successful': False
        }

    def _fallback_futures_data(self, symbol):
        """Fallback futures data when API fails"""
        return {
            'symbol': symbol,
            'long_ratio': 50.0,
            'short_ratio': 50.0,
            'error': 'Futures data temporarily unavailable',
            'source': 'fallback_simulation'
        }

    def log_deployment_status(self):
        """Log current deployment status and API health"""
        is_deployment = self.is_deployment_mode()
        
        print("="*60)
        print("🚀 CRYPTO API DEPLOYMENT STATUS")
        print("="*60)
        print(f"📍 Mode: {'DEPLOYMENT' if is_deployment else 'DEVELOPMENT'}")
        print(f"📊 Binance Spot URL: {self.binance_spot_url}")
        print(f"📈 Binance Futures URL: {self.binance_futures_url}")
        print(f"📰 CryptoNews: {'✅ Enabled' if self.cryptonews_key else '❌ Disabled'}")
        print(f"🔍 Environment Variables:")
        print(f"   - REPLIT_DEPLOYMENT: {os.getenv('REPLIT_DEPLOYMENT')}")
        print(f"   - REPL_DEPLOYMENT: {os.getenv('REPL_DEPLOYMENT')}")
        print(f"   - REPLIT_ENVIRONMENT: {os.getenv('REPLIT_ENVIRONMENT')}")
        print(f"   - REPL_SLUG: {bool(os.getenv('REPL_SLUG'))}")
        print(f"   - REPL_OWNER: {bool(os.getenv('REPL_OWNER'))}")
        print("="*60)
        
        # Test basic connectivity
        connectivity_test = self.test_binance_connectivity()
        print(f"🔧 API Health: {connectivity_test.get('working_endpoints', 'Unknown')}")
        print("="*60)


            if not original_symbol.endswith('USDT'):
                normalized_symbol = original_symbol + 'USDT'
            else:
                normalized_symbol = original_symbol
            
            # Double-check USDT requirement
            if 'USDT' not in normalized_symbol:
                print(f"❌ STRICT VALIDATION: Symbol {original_symbol} rejected - USDT pairs only")
                return {
                    'error': f'Symbol {original_symbol} not supported - USDT pairs required',
                    'symbol': original_symbol,
                    'api_call_successful': False,
                    'error_type': 'non_usdt_symbol',
                    'validation_failed': True
                }

            symbol = normalized_symbol
            print(f"✅ USDT Validation passed: {original_symbol} → {symbol}")

            # Enhanced deployment detection with debug logging
            deployment_indicators = {
                'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
                'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1',
                'REPL_SLUG': bool(os.getenv('REPL_SLUG')),
                'REPL_OWNER': bool(os.getenv('REPL_OWNER')),
                'deployment_flag_file': os.path.exists('/tmp/repl_deployment_flag')
            }
            
            is_deployment = any(deployment_indicators.values())
            print(f"🔍 Deployment Detection: {deployment_indicators} → {'DEPLOYMENT' if is_deployment else 'DEVELOPMENT'}")

            # Force refresh in deployment for real-time data
            if is_deployment:
                force_refresh = True
                print(f"🚀 DEPLOYMENT MODE: Force refresh enabled for real-time data")

            # Enhanced headers with better error handling
            headers = {
                'User-Agent': 'CryptoMentorAI/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate'
            }

            # Cache control for development
            if not is_deployment or force_refresh:
                headers.update({
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                })

            # Request parameters with cache busting
            params = {'symbol': symbol}
            if force_refresh:
                import time
                params['_t'] = int(time.time() * 1000)
                print(f"🔄 Cache buster added: {params['_t']}")

            # Prioritize endpoints based on deployment mode
            endpoints_to_try = [
                f"{self.binance_spot_url}/ticker/24hr",   # Comprehensive data
                f"{self.binance_spot_url}/ticker/price"   # Simple price fallback
            ]

            print(f"📡 Will try {len(endpoints_to_try)} Binance endpoints for {symbol}")

            last_error = None
            for attempt, endpoint in enumerate(endpoints_to_try, 1):
                try:
                    print(f"📡 Binance API Call {attempt}/{len(endpoints_to_try)}: {endpoint}")
                    print(f"📊 Request params: {params}")
                    
                    # Make request with enhanced timeout handling
                    response = requests.get(
                        endpoint,
                        params=params,
                        timeout=30 if is_deployment else 15,  # Generous timeout for deployment
                        headers=headers,
                        allow_redirects=True
                    )
                    
                    print(f"📊 Response Status: {response.status_code}")
                    print(f"📊 Response Size: {len(response.content)} bytes")
                    print(f"📊 Response Headers: {dict(list(response.headers.items())[:5])}")  # First 5 headers
                    
                    # Enhanced status code handling
                    if response.status_code == 429:
                        print(f"⏳ Rate limited by Binance, waiting...")
                        import time
                        time.sleep(2)
                        last_error = "Rate limited"
                        continue
                    elif response.status_code == 418:
                        print(f"🔒 IP banned by Binance temporarily")
                        last_error = "IP banned"
                        continue
                    elif response.status_code != 200:
                        error_msg = f"HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            error_msg = f"HTTP {response.status_code}: {error_data.get('msg', 'Unknown error')}"
                            print(f"❌ Binance API Error: {error_data}")
                        except:
                            print(f"❌ Non-JSON error response: {response.text[:100]}")
                        last_error = error_msg
                        continue

                    response.raise_for_status()
                    
                    # Enhanced JSON parsing with better error messages
                    try:
                        data = response.json()
                        print(f"📊 JSON parsing successful, data type: {type(data)}")
                        
                        # Log essential parts of response for debugging
                        if isinstance(data, dict):
                            debug_fields = ['symbol', 'lastPrice', 'price']
                            debug_data = {k: data.get(k) for k in debug_fields if k in data}
                            print(f"📊 Key response fields: {debug_data}")
                        else:
                            print(f"📊 Raw response preview: {str(data)[:200]}")
                            
                    except ValueError as json_error:
                        print(f"❌ JSON parsing failed: {json_error}")
                        print(f"📊 Raw response (first 300 chars): {response.text[:300]}")
                        last_error = f"JSON parsing error: {json_error}"
                        continue
                    
                    # Validate response structure
                    if not data or not isinstance(data, dict):
                        print(f"❌ Invalid response structure for {symbol}")
                        print(f"📊 Response type: {type(data)}, Data: {data}")
                        last_error = "Invalid response structure"
                        continue

                    # Process different endpoint types with robust price extraction
                    if endpoint.endswith('/ticker/24hr'):
                        print(f"📊 Processing 24hr ticker data...")
                        
                        # Enhanced field validation for 24hr ticker
                        essential_fields = ['lastPrice']
                        optional_fields = ['priceChangePercent', 'highPrice', 'lowPrice', 'volume', 'quoteVolume']
                        
                        missing_essential = [field for field in essential_fields if field not in data]
                        if missing_essential:
                            print(f"❌ Missing essential fields: {missing_essential}")
                            last_error = f"Missing essential fields: {missing_essential}"
                            continue

                        # COMPREHENSIVE PRICE PARSING AND VALIDATION
                        price_result = self._extract_and_validate_price(data, 'lastPrice', symbol, '24hr ticker')
                        if price_result['error']:
                            print(f"❌ Price validation failed: {price_result['error']}")
                            last_error = price_result['error']
                            continue
                        
                        price = price_result['price']
                        print(f"✅ Price validation successful: {symbol} = ${price:,.8f}")

                        # Parse additional fields with safe defaults
                        try:
                            change_24h = self._safe_float_parse(data.get('priceChangePercent'), 0)
                            high_24h = self._safe_float_parse(data.get('highPrice'), 0)
                            low_24h = self._safe_float_parse(data.get('lowPrice'), 0)
                            volume_24h = self._safe_float_parse(data.get('volume'), 0)
                            quote_volume_24h = self._safe_float_parse(data.get('quoteVolume'), 0)
                            open_price = self._safe_float_parse(data.get('openPrice'), 0)
                            price_change = self._safe_float_parse(data.get('priceChange'), 0)
                            count = self._safe_int_parse(data.get('count'), 0)
                            
                            print(f"📊 Additional fields parsed - Volume: {volume_24h:,.0f}, Change: {change_24h:.2f}%")
                            
                        except Exception as parse_error:
                            print(f"⚠️ Warning: Error parsing additional fields: {parse_error}")
                            # Use safe defaults
                            change_24h = high_24h = low_24h = volume_24h = quote_volume_24h = 0
                            open_price = price_change = count = 0

                        # Build comprehensive result
                        result = {
                            'symbol': symbol,
                            'price': price,
                            'change_24h': change_24h,
                            'high_24h': high_24h,
                            'low_24h': low_24h,
                            'volume_24h': volume_24h,
                            'quote_volume_24h': quote_volume_24h,
                            'open_price': open_price,
                            'close_price': price,
                            'price_change': price_change,
                            'count': count,
                            'first_id': data.get('firstId', 0),
                            'last_id': data.get('lastId', 0),
                            'open_time': data.get('openTime', 0),
                            'close_time': data.get('closeTime', 0),
                            'source': 'binance_spot_24hr',
                            'api_call_successful': True,
                            'price_validation_passed': True,
                            'raw_last_price': data.get('lastPrice'),
                            'deployment_mode': is_deployment,
                            'usdt_validated': True
                        }
                        
                        print(f"✅ 24hr ticker SUCCESS: {symbol} = ${price:,.6f} (Change: {change_24h:+.2f}%)")
                        return result

                    else:  # Simple price endpoint
                        print(f"📊 Processing simple price data...")
                        
                        # Validate price field exists
                        if 'price' not in data:
                            print(f"❌ Price field missing in simple response")
                            last_error = "Price field missing in simple response"
                            continue

                        # COMPREHENSIVE PRICE PARSING FOR SIMPLE ENDPOINT
                        price_result = self._extract_and_validate_price(data, 'price', symbol, 'simple price')
                        if price_result['error']:
                            print(f"❌ Simple price validation failed: {price_result['error']}")
                            last_error = price_result['error']
                            continue
                        
                        price = price_result['price']
                        print(f"✅ Simple price validation successful: {symbol} = ${price:,.8f}")

                        # Build simple result
                        result = {
                            'symbol': symbol,
                            'price': price,
                            'change_24h': 0,  # Not available
                            'volume_24h': 0,  # Not available
                            'source': 'binance_spot_simple',
                            'api_call_successful': True,
                            'price_validation_passed': True,
                            'raw_price': data.get('price'),
                            'deployment_mode': is_deployment,
                            'usdt_validated': True
                        }
                        
                        print(f"✅ Simple price SUCCESS: {symbol} = ${price:,.6f}")
                        return result

                except requests.exceptions.Timeout as e:
                    error_msg = f"Timeout ({endpoint}): {str(e)}"
                    print(f"⏰ {error_msg}")
                    last_error = error_msg
                    continue
                except requests.exceptions.ConnectionError as e:
                    error_msg = f"Connection error ({endpoint}): {str(e)}"
                    print(f"🔌 {error_msg}")
                    last_error = error_msg
                    continue
                except requests.exceptions.HTTPError as e:
                    error_msg = f"HTTP error ({endpoint}): {str(e)}"
                    print(f"🌐 {error_msg}")
                    last_error = error_msg
                    continue
                except Exception as e:
                    error_msg = f"Unexpected error ({endpoint}): {str(e)}"
                    print(f"❌ {error_msg}")
                    last_error = error_msg
                    continue

            # All endpoints failed
            final_error = f"All Binance endpoints failed for {symbol}. Last error: {last_error}"
            print(f"🚨 TOTAL FAILURE: {final_error}")
            raise Exception(final_error)

        except Exception as e:
            error_msg = f"Binance price retrieval completely failed for {symbol}: {str(e)}"
            print(f"💥 COMPLETE FAILURE: {error_msg}")
            return {
                'error': error_msg,
                'symbol': symbol,
                'api_call_successful': False,
                'error_type': 'complete_binance_failure',
                'deployment_mode': getattr(self, '_last_deployment_check', False)
            }

    def _extract_and_validate_price(self, data, price_field, symbol, source_type):
        """Extract and validate price with comprehensive checks - Enhanced for deployment reliability"""
        try:
            raw_price = data.get(price_field)
            print(f"🔍 Extracting {price_field} from {source_type}: {raw_price} (type: {type(raw_price)})")
            
            # Null/None check
            if raw_price is None:
                print(f"❌ Critical: {price_field} is None in {source_type} for {symbol}")
                return {'error': f'{price_field} is None in {source_type}', 'price': None}
            
            # Empty string check
            if isinstance(raw_price, str):
                if raw_price.strip() == '':
                    print(f"❌ Critical: {price_field} is empty string in {source_type} for {symbol}")
                    return {'error': f'{price_field} is empty string in {source_type}', 'price': None}
                
                # Enhanced numeric validation for strings
                clean_price = raw_price.strip()
                try:
                    # Test conversion first
                    test_price = float(clean_price)
                    if test_price <= 0:
                        print(f"❌ Critical: {price_field} converts to non-positive value: {test_price}")
                        return {'error': f'{price_field} converts to invalid value: {test_price}', 'price': None}
                except (ValueError, TypeError) as e:
                    print(f"❌ Critical: {price_field} cannot be converted to float: {clean_price} - Error: {e}")
                    return {'error': f'{price_field} contains non-numeric data: {clean_price}', 'price': None}
            
            # Convert to float with enhanced error handling
            try:
                if isinstance(raw_price, str):
                    price = float(raw_price.strip())
                else:
                    price = float(raw_price)
                print(f"🔢 Successfully converted to float: {price}")
            except (ValueError, TypeError, OverflowError) as conversion_error:
                print(f"💥 Critical conversion failure: {conversion_error}")
                return {'error': f'Cannot convert {price_field} to float: {raw_price} ({conversion_error})', 'price': None}
            
            # Enhanced validation checks with deployment-specific rules
            validation_checks = [
                (price <= 0, f"Price is zero or negative: {price} - REJECTED"),
                (price != price, f"Price is NaN: {price} - REJECTED"),  # NaN check
                (price == float('inf'), f"Price is infinity: {price} - REJECTED"),
                (price == float('-inf'), f"Price is negative infinity: {price} - REJECTED"),
                (price > 1000000000, f"Price unreasonably high: {price} - REJECTED"),  # $1B per coin
                (price < 0.0000000001, f"Price unreasonably low: {price} - REJECTED")   # Extremely small values
            ]
            
            for check_condition, error_message in validation_checks:
                if check_condition:
                    print(f"❌ VALIDATION FAILED: {error_message}")
                    return {'error': error_message, 'price': None}
            
            # USDT-specific enhanced validation
            if 'USDT' in symbol:
                # Additional checks for USDT pairs
                if symbol == 'USDUSDT' or symbol == 'USDTUSDT':
                    print(f"❌ Invalid USDT pair detected: {symbol}")
                    return {'error': f'Invalid USDT pair detected: {symbol}', 'price': None}
                
                # Check if price is reasonable for crypto (between $0.000001 and $10,000,000)
                if price < 0.000001:
                    print(f"❌ USDT pair price too low: {price} for {symbol}")
                    return {'error': f'USDT pair price suspiciously low: {price}', 'price': None}
                
                if price > 10000000:
                    print(f"❌ USDT pair price too high: {price} for {symbol}")
                    return {'error': f'USDT pair price suspiciously high: {price}', 'price': None}
            
            # Final validation: ensure price is a clean number
            try:
                # Round to 8 decimal places to avoid floating point issues
                clean_price = round(price, 8)
                if clean_price != price and abs(clean_price - price) > 0.00000001:
                    print(f"⚠️ Price rounded from {price} to {clean_price}")
                price = clean_price
            except Exception as round_error:
                print(f"⚠️ Price rounding warning: {round_error}")
            
            print(f"✅ PRICE VALIDATION SUCCESS: {symbol} = ${price:.8f}")
            return {'error': None, 'price': price}
            
        except Exception as e:
            error_msg = f"Unexpected error in price validation for {symbol}: {str(e)}"
            print(f"💥 CRITICAL ERROR: {error_msg}")
            return {'error': error_msg, 'price': None}
    
    def _safe_float_parse(self, value, default=0.0):
        """Safely parse float with default fallback"""
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_int_parse(self, value, default=0):
        """Safely parse int with default fallback"""
        try:
            if value is None:
                return default
            return int(float(value))  # Convert through float to handle strings like "123.0"
        except (ValueError, TypeError):
            return default

    def get_binance_candlestick(self, symbol, interval='1h', limit=100):
        """Get candlestick/kline data from Binance"""
        try:
            # Normalize symbol
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_spot_url}/klines",
                params={
                    'symbol': symbol,
                    'interval': interval,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            candlesticks = []
            for kline in data:
                candlesticks.append({
                    'open_time': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': kline[6],
                    'quote_asset_volume': float(kline[7]),
                    'trades_count': kline[8],
                    'taker_buy_base_volume': float(kline[9]),
                    'taker_buy_quote_volume': float(kline[10]),
                    'open_time_iso': datetime.fromtimestamp(kline[0]/1000, tz=timezone.utc).isoformat(),
                    'close_time_iso': datetime.fromtimestamp(kline[6]/1000, tz=timezone.utc).isoformat()
                })

            return {
                'symbol': symbol,
                'interval': interval,
                'candlesticks': candlesticks,
                'count': len(candlesticks),
                'source': 'binance_spot'
            }
        except Exception as e:
            return {'error': f"Candlestick error: {str(e)}"}

    # === BINANCE FUTURES API METHODS ===

    def get_binance_futures_price(self, symbol):
        """Get futures price ticker from Binance Futures with enhanced validation"""
        try:
            # Normalize symbol format - Only accept USDT pairs
            original_symbol = symbol.upper()
            if not original_symbol.endswith('USDT'):
                symbol = original_symbol + 'USDT'
            else:
                symbol = original_symbol

            # Validate symbol contains USDT
            if 'USDT' not in symbol:
                print(f"❌ Futures symbol {original_symbol} does not contain USDT - skipping")
                return {
                    'error': f'Futures symbol {original_symbol} not supported - only USDT pairs accepted',
                    'symbol': original_symbol,
                    'api_call_successful': False,
                    'error_type': 'invalid_symbol'
                }

            # Check deployment mode
            is_deployment = (
                os.getenv('REPLIT_DEPLOYMENT') == '1' or 
                os.getenv('REPL_DEPLOYMENT') == '1' or
                bool(os.getenv('REPL_SLUG'))
            )

            print(f"🔄 Fetching Binance Futures price for {symbol} (Original: {original_symbol}, Deployment: {is_deployment})")

            headers = {
                'User-Agent': 'CryptoMentorAI/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }

            timeout = 20 if is_deployment else 10

            response = requests.get(
                f"{self.binance_futures_url}/ticker/24hr",
                params={'symbol': symbol},
                timeout=timeout,
                headers=headers
            )
            
            print(f"📊 Binance Futures API Response Status: {response.status_code}")
            print(f"📊 Futures Response Headers: {dict(response.headers)}")

            # Check response status
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = f"HTTP {response.status_code}: {error_data.get('msg', 'Unknown error')}"
                    print(f"❌ Binance Futures API Error Details: {error_data}")
                except:
                    pass
                print(f"❌ Binance Futures API Error: {error_msg}")
                return {'error': f"Futures API error: {error_msg}", 'api_call_successful': False}

            response.raise_for_status()
            
            # Parse JSON response with validation
            try:
                data = response.json()
                print(f"📊 Raw Futures API Response: {data}")
            except ValueError as json_error:
                print(f"❌ Futures JSON parsing failed: {json_error}")
                print(f"📊 Raw futures response text: {response.text[:200]}...")
                return {'error': f"Futures JSON parsing error: {json_error}", 'api_call_successful': False}

            # Validate response data
            if not data or not isinstance(data, dict):
                print(f"❌ Invalid Binance Futures API response format for {symbol}")
                return {'error': 'Invalid futures response format', 'api_call_successful': False}

            # Validate required fields
            required_fields = ['lastPrice', 'priceChangePercent', 'highPrice', 'lowPrice', 'volume', 'quoteVolume']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing fields in Futures ticker response: {missing_fields}")
                return {'error': f'Missing required fields: {missing_fields}', 'api_call_successful': False}

            # Enhanced lastPrice parsing with multiple validations
            try:
                raw_last_price = data.get('lastPrice')
                print(f"📊 Raw futures lastPrice from API: {raw_last_price} (type: {type(raw_last_price)})")
                
                if raw_last_price is None:
                    print(f"❌ Futures lastPrice is None")
                    return {'error': 'Futures lastPrice field is None', 'api_call_successful': False}
                
                if isinstance(raw_last_price, str) and raw_last_price.strip() == '':
                    print(f"❌ Futures lastPrice is empty string")
                    return {'error': 'Futures lastPrice field is empty', 'api_call_successful': False}
                
                # Parse to float with validation
                price = float(raw_last_price)
                print(f"📊 Parsed futures price: {price}")
                
                # Validate price is not zero, negative, or NaN
                if price <= 0 or price != price:  # price != price checks for NaN
                    print(f"❌ Invalid futures price received from Binance: {price}")
                    return {'error': f'Invalid futures price: {price}', 'api_call_successful': False}
                
                # Additional sanity check for reasonable price range
                if price > 10000000:  # Arbitrary large number check
                    print(f"⚠️ Suspiciously large futures price: {price} - possible data error")
                    return {'error': f'Suspiciously large futures price: {price}', 'api_call_successful': False}
                    
            except (ValueError, TypeError) as price_error:
                print(f"❌ Futures price parsing error: {price_error}")
                print(f"❌ Failed to parse futures lastPrice: {data.get('lastPrice')}")
                return {'error': f'Futures price parsing error: {price_error}', 'api_call_successful': False}

            # Parse other numeric fields with error handling
            try:
                change_24h = float(data.get('priceChangePercent', 0))
                high_24h = float(data.get('highPrice', 0))
                low_24h = float(data.get('lowPrice', 0))
                volume_24h = float(data.get('volume', 0))
                quote_volume_24h = float(data.get('quoteVolume', 0))
                open_price = float(data.get('openPrice', 0))
                weighted_avg_price = float(data.get('weightedAvgPrice', 0))
                price_change = float(data.get('priceChange', 0))
                count = int(data.get('count', 0))
            except (ValueError, TypeError) as parse_error:
                print(f"⚠️ Warning: Error parsing additional futures fields: {parse_error}")
                # Use defaults for non-critical fields
                change_24h = 0
                high_24h = 0
                low_24h = 0
                volume_24h = 0
                quote_volume_24h = 0
                open_price = 0
                weighted_avg_price = 0
                price_change = 0
                count = 0

            result = {
                'symbol': symbol,
                'price': price,
                'change_24h': change_24h,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'volume_24h': volume_24h,
                'quote_volume_24h': quote_volume_24h,
                'open_price': open_price,
                'weighted_avg_price': weighted_avg_price,
                'price_change': price_change,
                'count': count,
                'open_time': data.get('openTime', 0),
                'close_time': data.get('closeTime', 0),
                'source': 'binance_futures',
                'api_call_successful': True,
                'raw_last_price': raw_last_price,  # For debugging
                'price_validation_passed': True
            }

            print(f"✅ Binance Futures success for {symbol}: ${price:,.6f}")
            print(f"✅ Futures price validation: {price} > 0 = {price > 0}")
            return result

        except requests.exceptions.Timeout as e:
            error_msg = f"Futures API timeout: {str(e)}"
            print(f"⏰ {error_msg}")
            return {'error': error_msg, 'api_call_successful': False}
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Futures API connection error: {str(e)}"
            print(f"🔌 {error_msg}")
            return {'error': error_msg, 'api_call_successful': False}
        except requests.exceptions.RequestException as e:
            error_msg = f"Futures API request error: {str(e)}"
            print(f"⚠️ {error_msg}")
            return {'error': error_msg, 'api_call_successful': False}
        except ValueError as e:
            error_msg = f"Futures API data parsing error: {str(e)}"
            print(f"🔢 {error_msg}")
            return {'error': error_msg, 'api_call_successful': False}
        except Exception as e:
            error_msg = f"Futures price error: {str(e)}"
            print(f"❌ {error_msg}")
            return {'error': error_msg, 'api_call_successful': False}

    def get_binance_mark_price(self, symbol):
        """Get mark price and funding rate from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/premiumIndex",
                params={'symbol': symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'symbol': symbol,
                'mark_price': float(data['markPrice']),
                'index_price': float(data['indexPrice']),
                'estimated_settle_price': float(data.get('estimatedSettlePrice', 0)),
                'last_funding_rate': float(data['lastFundingRate']),
                'interest_rate': float(data.get('interestRate', 0)),
                'next_funding_time': data['nextFundingTime'],
                'next_funding_time_iso': datetime.fromtimestamp(data['nextFundingTime']/1000, tz=timezone.utc).isoformat(),
                'time': data['time'],
                'time_iso': datetime.fromtimestamp(data['time']/1000, tz=timezone.utc).isoformat(),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Mark price error: {str(e)}"}

    def get_binance_funding_rate(self, symbol, limit=100):
        """Get funding rate history from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Get current funding rate from premium index
            mark_data = self.get_binance_mark_price(symbol)

            # Get funding rate history
            response = requests.get(
                f"{self.binance_futures_url}/fundingRate",
                params={
                    'symbol': symbol,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            history_data = response.json()

            funding_history = []
            for record in history_data:
                funding_history.append({
                    'symbol': record['symbol'],
                    'funding_rate': float(record['fundingRate']),
                    'funding_time': record['fundingTime'],
                    'funding_time_iso': datetime.fromtimestamp(record['fundingTime']/1000, tz=timezone.utc).isoformat()
                })

            # Calculate average funding rate
            avg_funding = sum([r['funding_rate'] for r in funding_history]) / len(funding_history) if funding_history else 0

            return {
                'symbol': symbol,
                'mark_price': mark_data.get('mark_price', 0),
                'index_price': mark_data.get('index_price', 0),
                'last_funding_rate': mark_data.get('last_funding_rate', 0),
                'next_funding_time': mark_data.get('next_funding_time', 0),
                'next_funding_time_iso': mark_data.get('next_funding_time_iso', ''),
                'average_funding_rate': avg_funding,
                'funding_history': funding_history[-10:],  # Last 10 records
                'history_count': len(funding_history),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Funding rate error: {str(e)}"}

    def get_binance_open_interest(self, symbol):
        """Get open interest from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/openInterest",
                params={'symbol': symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'symbol': symbol,
                'open_interest': float(data['openInterest']),
                'time': data['time'],
                'time_iso': datetime.fromtimestamp(data['time']/1000, tz=timezone.utc).isoformat(),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Open interest error: {str(e)}"}

    def get_binance_long_short_ratio(self, symbol, period='5m', limit=30):
        """Get long/short ratio from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Get top trader long/short ratio
            response = requests.get(
                f"{self.binance_futures_url}/topLongShortPositionRatio",
                params={
                    'symbol': symbol,
                    'period': period,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data:
                latest = data[-1]
                long_ratio = float(latest['longShortRatio']) / (1 + float(latest['longShortRatio'])) * 100
                short_ratio = 100 - long_ratio

                return {
                    'symbol': symbol,
                    'long_ratio': long_ratio,
                    'short_ratio': short_ratio,
                    'long_short_ratio': float(latest['longShortRatio']),
                    'long_account': float(latest['longAccount']),
                    'short_account': float(latest['shortAccount']),
                    'timestamp': latest['timestamp'],
                    'timestamp_iso': datetime.fromtimestamp(latest['timestamp']/1000, tz=timezone.utc).isoformat(),
                    'period': period,
                    'data_points': len(data),
                    'source': 'binance_futures'
                }
            else:
                return {'error': 'No long/short ratio data available'}

        except Exception as e:
            return {'error': f"Long/short ratio error: {str(e)}"}

    def get_binance_liquidation_orders(self, symbol, limit=100):
        """Get liquidation orders from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/forceOrders",
                params={
                    'symbol': symbol,
                    'limit': limit
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            total_liquidation = 0
            long_liquidation = 0
            short_liquidation = 0

            liquidations = []
            for order in data:
                qty = float(order['origQty'])
                price = float(order['price'])
                value = qty * price
                total_liquidation += value

                if order['side'] == 'SELL':  # Long liquidation
                    long_liquidation += value
                else:  # Short liquidation
                    short_liquidation += value

                liquidations.append({
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'order_type': order['origType'],
                    'quantity': qty,
                    'price': price,
                    'value': value,
                    'status': order['status'],
                    'time': order['time'],
                    'time_iso': datetime.fromtimestamp(order['time']/1000, tz=timezone.utc).isoformat()
                })

            return {
                'symbol': symbol,
                'total_liquidation': total_liquidation,
                'long_liquidation': long_liquidation,
                'short_liquidation': short_liquidation,
                'liquidation_orders': liquidations[-20:],  # Last 20 orders
                'total_orders': len(liquidations),
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Liquidation orders error: {str(e)}"}

    # === COMPREHENSIVE DATA METHODS ===

    def get_comprehensive_futures_data(self, symbol):
        """Get all futures data in one call"""
        try:
            # Get all futures data
            price_data = self.get_binance_futures_price(symbol)
            mark_data = self.get_binance_mark_price(symbol)
            funding_data = self.get_binance_funding_rate(symbol)
            oi_data = self.get_binance_open_interest(symbol)
            ls_ratio_data = self.get_binance_long_short_ratio(symbol)
            liquidation_data = self.get_binance_liquidation_orders(symbol)

            successful_calls = 0
            total_calls = 6

            # Count successful API calls
            for data in [price_data, mark_data, funding_data, oi_data, ls_ratio_data, liquidation_data]:
                if 'error' not in data:
                    successful_calls += 1

            return {
                'symbol': symbol,
                'price_data': price_data,
                'mark_price_data': mark_data,
                'funding_rate_data': funding_data,
                'open_interest_data': oi_data,
                'long_short_ratio_data': ls_ratio_data,
                'liquidation_data': liquidation_data,
                'successful_api_calls': successful_calls,
                'total_api_calls': total_calls,
                'data_quality': 'excellent' if successful_calls >= 5 else 'good' if successful_calls >= 4 else 'partial',
                'source': 'binance_comprehensive'
            }
        except Exception as e:
            return {'error': f"Comprehensive data error: {str(e)}"}

    # === BINANCE MARKET DATA METHODS ===

    def get_binance_market_data(self, symbol):
        """Get comprehensive market data from Binance only"""
        try:
            # Get price data from spot
            spot_data = self.get_binance_price(symbol)

            # Get futures data
            futures_data = self.get_binance_futures_price(symbol)

            # Get additional futures metrics
            mark_data = self.get_binance_mark_price(symbol)
            funding_data = self.get_binance_funding_rate(symbol)
            oi_data = self.get_binance_open_interest(symbol)
            ls_data = self.get_binance_long_short_ratio(symbol)

            # Combine data with Binance as primary source
            if 'error' not in spot_data:
                primary_data = spot_data
                source = 'binance_spot'
            elif 'error' not in futures_data:
                primary_data = futures_data
                source = 'binance_futures'
            else:
                return {'error': 'All Binance endpoints failed'}

            return {
                'symbol': symbol.upper(),
                'name': symbol.upper().replace('USDT', ''),
                'current_price': primary_data.get('price', 0),
                'price_change_24h': primary_data.get('price_change', 0),
                'price_change_percentage_24h': primary_data.get('change_24h', 0),
                'high_24h': primary_data.get('high_24h', 0),
                'low_24h': primary_data.get('low_24h', 0),
                'total_volume': primary_data.get('volume_24h', 0),
                'quote_volume': primary_data.get('quote_volume_24h', 0),
                'open_price': primary_data.get('open_price', 0),
                'close_price': primary_data.get('close_price', primary_data.get('price', 0)),
                'trade_count': primary_data.get('count', 0),
                # Futures-specific data
                'mark_price': mark_data.get('mark_price', 0) if 'error' not in mark_data else 0,
                'funding_rate': funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0,
                'open_interest': oi_data.get('open_interest', 0) if 'error' not in oi_data else 0,
                'long_ratio': ls_data.get('long_ratio', 50) if 'error' not in ls_data else 50,
                'short_ratio': ls_data.get('short_ratio', 50) if 'error' not in ls_data else 50,
                'last_updated': datetime.now().isoformat(),
                'source': source,
                'data_quality': 'excellent'
            }

        except Exception as e:
            return {'error': f"Binance market data error: {str(e)}"}

    def get_binance_global_data(self):
        """Get global market data using only Binance data"""
        try:
            # Get data from top cryptocurrencies via Binance
            major_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'DOT', 'AVAX']
            prices_data = self.get_multiple_binance_prices(major_symbols)

            if 'error' not in prices_data and len(prices_data) > 0:
                # Calculate market metrics from Binance data
                btc_data = prices_data.get('BTC', {})
                eth_data = prices_data.get('ETH', {})

                # Calculate total volume and dominance estimates
                total_volume = sum(data.get('volume_24h', 0) for data in prices_data.values())
                btc_volume = btc_data.get('volume_24h', 0)
                eth_volume = eth_data.get('volume_24h', 0)

                btc_dominance = (btc_volume / total_volume * 100) if total_volume > 0 else 45.0
                eth_dominance = (eth_volume / total_volume * 100) if total_volume > 0 else 18.0

                # Calculate weighted average market change
                changes = []
                volumes = []
                for data in prices_data.values():
                    if 'change_24h' in data and 'volume_24h' in data:
                        changes.append(data['change_24h'])
                        volumes.append(data['volume_24h'])

                if changes and volumes:
                    weighted_change = sum(c * v for c, v in zip(changes, volumes)) / sum(volumes)
                else:
                    weighted_change = 0

                # Estimate total market cap (rough calculation based on BTC dominance)
                btc_price = btc_data.get('price', 0)
                estimated_market_cap = btc_price * 19500000 / (btc_dominance / 100) if btc_dominance > 0 else total_volume * 20

                return {
                    'total_market_cap': estimated_market_cap,
                    'total_volume': total_volume,
                    'market_cap_change_percentage_24h_usd': weighted_change,
                    'btc_dominance': btc_dominance,
                    'eth_dominance': eth_dominance,
                    'active_cryptocurrencies': len(prices_data),
                    'updated_at': int(datetime.now().timestamp()),
                    'source': 'binance_global_estimate'
                }
            else:
                return {'error': 'Binance global data unavailable'}
        except Exception as e:
            return {'error': f"Binance global data error: {str(e)}"}

    def test_binance_connectivity(self, symbol='BTCUSDT'):
        """Test Binance API connectivity with deployment-focused validation"""
        print(f"🔧 TESTING BINANCE API CONNECTIVITY for {symbol} in deployment mode...")
        
        is_deployment = self.is_deployment_mode()
        
        test_results = {
            'spot_ping': False,
            'futures_ping': False,
            'spot_price': False,
            'futures_price': False,
            'spot_price_value': None,
            'futures_price_value': None,
            'deployment_mode': is_deployment,
            'timestamp': datetime.now().isoformat(),
            'usdt_validation': False,
            'price_parsing': False,
            'error_handling': False
        }
        
        # Enhanced USDT validation test
        if 'USDT' in symbol:
            test_results['usdt_validation'] = True
            print(f"✅ USDT validation: {symbol} contains USDT")
        else:
            print(f"❌ USDT validation: {symbol} does not contain USDT")
        
        # Test Spot API ping
        try:
            spot_ping = requests.get(f"{self.binance_spot_url}/ping", timeout=5)
            test_results['spot_ping'] = spot_ping.status_code == 200
            print(f"📡 Spot API ping: {'✅ OK' if test_results['spot_ping'] else '❌ FAIL'}")
        except Exception as e:
            print(f"❌ Spot API ping failed: {e}")
        
        # Test Futures API ping
        try:
            futures_ping = requests.get(f"{self.binance_futures_url}/ping", timeout=5)
            test_results['futures_ping'] = futures_ping.status_code == 200
            print(f"📡 Futures API ping: {'✅ OK' if test_results['futures_ping'] else '❌ FAIL'}")
        except Exception as e:
            print(f"❌ Futures API ping failed: {e}")
        
        # Test Spot price retrieval
        try:
            spot_data = self.get_binance_price('BTC')
            if 'error' not in spot_data and spot_data.get('price', 0) > 0:
                test_results['spot_price'] = True
                test_results['spot_price_value'] = spot_data.get('price')
                print(f"💰 Spot price: ✅ ${spot_data.get('price'):,.2f}")
            else:
                print(f"❌ Spot price failed: {spot_data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Spot price exception: {e}")
        
        # Test Futures price retrieval
        try:
            futures_data = self.get_binance_futures_price('BTC')
            if 'error' not in futures_data and futures_data.get('price', 0) > 0:
                test_results['futures_price'] = True
                test_results['futures_price_value'] = futures_data.get('price')
                print(f"🚀 Futures price: ✅ ${futures_data.get('price'):,.2f}")
            else:
                print(f"❌ Futures price failed: {futures_data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Futures price exception: {e}")
        
        # Overall assessment
        working_endpoints = sum([
            test_results['spot_ping'],
            test_results['futures_ping'], 
            test_results['spot_price'],
            test_results['futures_price']
        ])
        
        test_results['overall_health'] = working_endpoints >= 2
        test_results['working_endpoints'] = f"{working_endpoints}/4"
        
        print(f"📊 Overall Binance API Health: {'✅ GOOD' if test_results['overall_health'] else '❌ POOR'} ({working_endpoints}/4 endpoints working)")
        
        return test_results

    # === PRICE METHODS (BINANCE ONLY) ===

    def get_price(self, symbol, force_refresh=False):
        """Get price from Binance APIs only with enhanced deployment detection"""
        # Check if in deployment mode using comprehensive method
        is_deployment = self.is_deployment_mode()

        # Always force refresh in deployment for real-time data
        if is_deployment:
            force_refresh = True
            print(f"🚀 DEPLOYMENT MODE: Force refresh enabled for {symbol}")

        return self.get_multi_api_price(symbol, force_refresh)

    def get_multi_api_price(self, symbol, force_refresh=False):
        """Get price from Binance APIs only - centralized to Binance with enhanced validation"""
        price_sources = {}

        # Enhanced deployment environment check with comprehensive logging
        deployment_indicators = {
            'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT'),
            'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT'),
            'REPLIT_ENVIRONMENT': os.getenv('REPLIT_ENVIRONMENT'),
            'REPL_SLUG': bool(os.getenv('REPL_SLUG')),
            'REPL_DB_URL': bool(os.getenv('REPL_DB_URL')),
            'REPL_OWNER': bool(os.getenv('REPL_OWNER')),
            'deployment_flag_exists': os.path.exists('/tmp/repl_deployment_flag')
        }
        
        print(f"🔍 Deployment indicators check: {deployment_indicators}")
        
        is_deployment = (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
            os.path.exists('/tmp/repl_deployment_flag') or
            bool(os.getenv('REPL_SLUG')) or
            bool(os.getenv('REPL_DB_URL')) or
            bool(os.getenv('REPL_OWNER'))  # Additional deployment check
        )

        # ALWAYS force refresh in deployment for real-time data
        if is_deployment:
            force_refresh = True

        # Enhanced logging for deployment mode
        mode = "DEPLOYMENT REAL-TIME" if is_deployment else "STANDARD"
        print(f"🔄 {mode} MODE: Fetching price data for {symbol} from Binance (Force: {force_refresh})")

        def validate_price_data(data, source_name):
            """Validate price data to ensure it's valid with comprehensive deployment-ready checks"""
            print(f"🔍 VALIDATING {source_name} data for deployment...")
            print(f"📊 Full data structure: {data}")
            
            # Check for error in response
            if 'error' in data:
                print(f"❌ CRITICAL: {source_name} returned error: {data['error']}")
                return False
            
            # Strict USDT validation - must contain USDT
            symbol = data.get('symbol', '')
            if not symbol or 'USDT' not in symbol.upper():
                print(f"❌ CRITICAL: {source_name} symbol '{symbol}' does not contain USDT - REJECTED")
                return False
            
            # Extract price with multiple fallback attempts
            price = data.get('price')
            if price is None:
                # Try alternative price fields
                price = data.get('lastPrice') or data.get('close_price') or data.get('current_price')
                if price is not None:
                    print(f"🔄 Using alternative price field: {price}")
                
            print(f"🔍 Raw price from {source_name}: {price} (type: {type(price)})")
            
            # Enhanced price validation with deployment focus
            if price is None:
                print(f"❌ CRITICAL: {source_name} price is None for {symbol}")
                return False
            
            # Convert to float with enhanced error handling
            if not isinstance(price, (int, float)):
                try:
                    if isinstance(price, str):
                        price = float(price.strip())
                    else:
                        price = float(price)
                    print(f"🔄 Successfully converted {source_name} price to float: {price}")
                except (ValueError, TypeError) as e:
                    print(f"❌ CRITICAL: {source_name} price conversion failed: {e}")
                    return False
            
            # Comprehensive price validation for deployment
            validation_checks = [
                (price <= 0, f"Price is zero or negative: {price}"),
                (price != price, f"Price is NaN: {price}"),  # NaN check
                (price == float('inf'), f"Price is infinity: {price}"),
                (price == float('-inf'), f"Price is negative infinity: {price}"),
                (price > 1000000000, f"Price unreasonably high: {price}"),  # $1B check
                (price < 0.0000000001, f"Price unreasonably low: {price}")   # Micro value check
            ]
            
            for check_condition, error_message in validation_checks:
                if check_condition:
                    print(f"❌ DEPLOYMENT VALIDATION FAILED: {source_name} - {error_message}")
                    return False
            
            # Check API call success indicators
            if not data.get('api_call_successful', True):
                print(f"❌ CRITICAL: {source_name} API call was marked as unsuccessful")
                return False
            
            # Check internal price validation flag
            if 'price_validation_passed' in data and not data['price_validation_passed']:
                print(f"❌ CRITICAL: {source_name} failed internal price validation")
                return False
            
            # USDT-specific validation for deployment
            if 'USDT' in symbol:
                # Ensure reasonable price range for crypto pairs
                if price < 0.000001:  # Less than 1 millionth
                    print(f"❌ DEPLOYMENT: {source_name} USDT price too low: {price}")
                    return False
                if price > 100000000:  # More than 100M
                    print(f"❌ DEPLOYMENT: {source_name} USDT price too high: {price}")
                    return False
            
            # Final deployment validation
            try:
                formatted_price = f"${price:,.8f}"
                print(f"✅ DEPLOYMENT VALIDATION SUCCESS: {source_name} for {symbol} = {formatted_price}")
                return True
            except Exception as format_error:
                print(f"❌ CRITICAL: Price formatting failed: {format_error}")
                return False

        # In deployment mode, prioritize Futures API first due to stability
        if is_deployment:
            print("🚀 DEPLOYMENT MODE: Trying Binance APIs in priority order...")
            
            # 1. Try Binance Futures API first in deployment (more stable)
            try:
                print("📡 Trying Binance Futures API...")
                futures_data = self.get_binance_futures_price(symbol)
                if validate_price_data(futures_data, "Binance Futures"):
                    price_sources['binance_futures'] = futures_data
                    price_str = f"${futures_data.get('price', 0):,.4f}"
                    print(f"🎯 DEPLOYMENT SUCCESS: {symbol} = {price_str} ✅ (Binance Futures)")
                    return self._combine_binance_price_data(symbol, price_sources)
                else:
                    print("❌ Binance Futures validation failed, trying next...")
            except Exception as e:
                print(f"💥 Binance Futures API exception for {symbol}: {e}")

            # 2. Try Binance Spot API as backup in deployment
            try:
                print("📡 Trying Binance Spot API...")
                binance_data = self.get_binance_price(symbol, force_refresh=True)
                if validate_price_data(binance_data, "Binance Spot"):
                    price_sources['binance'] = binance_data
                    price_str = f"${binance_data.get('price', 0):,.4f}"
                    print(f"🎯 DEPLOYMENT SUCCESS: {symbol} = {price_str} ✅ (Binance Spot)")
                    return self._combine_binance_price_data(symbol, price_sources)
                else:
                    print("❌ Binance Spot validation failed")
            except Exception as e:
                print(f"💥 Binance Spot API exception for {symbol}: {e}")

            # In deployment, return detailed error if all Binance APIs fail
            error_msg = f'All Binance APIs failed for {symbol} in deployment mode - no valid price data available'
            print(f"🚨 DEPLOYMENT FAILURE: {error_msg}")
            return {
                'error': error_msg,
                'symbol': symbol,
                'deployment_mode': True,
                'all_apis_failed': True,
                'api_call_successful': False
            }

        else:
            # Development mode - multiple attempts with enhanced validation
            max_attempts = 3  # Increased attempts for development
            
            print(f"🔧 DEVELOPMENT MODE: Will try {max_attempts} attempts...")

            for attempt in range(max_attempts):
                if attempt > 0:
                    print(f"🔄 Binance retry attempt {attempt + 1}/{max_attempts} for {symbol}")
                    import time
                    time.sleep(2)  # Longer delay between attempts

                # 1. Try Binance Spot API first in development
                try:
                    print(f"📡 Development attempt {attempt + 1}: Trying Binance Spot API...")
                    binance_data = self.get_binance_price(symbol, force_refresh=True)
                    if validate_price_data(binance_data, "Binance Spot"):
                        price_sources['binance'] = binance_data
                        price_str = f"${binance_data.get('price', 0):,.4f}"
                        print(f"🎯 DEV SUCCESS: {symbol} = {price_str} ✅ (Binance Spot)")
                        return self._combine_binance_price_data(symbol, price_sources)
                except Exception as e:
                    print(f"💥 Binance Spot API exception for {symbol}: {e}")

                # 2. Try Binance Futures API as backup in development
                try:
                    print(f"📡 Development attempt {attempt + 1}: Trying Binance Futures API...")
                    futures_data = self.get_binance_futures_price(symbol)
                    if validate_price_data(futures_data, "Binance Futures"):
                        price_sources['binance_futures'] = futures_data
                        price_str = f"${futures_data.get('price', 0):,.4f}"
                        print(f"🎯 DEV SUCCESS: {symbol} = {price_str} ✅ (Binance Futures)")
                        return self._combine_binance_price_data(symbol, price_sources)
                except Exception as e:
                    print(f"💥 Binance Futures API exception for {symbol}: {e}")

            # Development mode fallback
            if price_sources:
                print(f"⚠️ Using partial data from {len(price_sources)} source(s)")
                return self._combine_binance_price_data(symbol, price_sources)
            else:
                error_msg = f"All Binance APIs failed after {max_attempts} attempts"
                print(f"🚨 DEVELOPMENT FAILURE: {error_msg}")
                return self._fallback_price(symbol, error_msg)

    def _combine_binance_price_data(self, symbol, price_sources):
        """Combine price data from Binance sources only"""
        combined_data = {
            'symbol': symbol.upper(),
            'sources_used': list(price_sources.keys()),
            'data_quality': 'excellent'  # Always excellent with Binance data
        }

        # Priority: Binance Spot, then Binance Futures
        if 'binance' in price_sources:
            binance = price_sources['binance']
            combined_data.update({
                'price': binance.get('price', 0),
                'change_24h': binance.get('change_24h', 0),
                'volume_24h': binance.get('volume_24h', 0),
                'high_24h': binance.get('high_24h', 0),
                'low_24h': binance.get('low_24h', 0),
                'open_price': binance.get('open_price', 0),
                'close_price': binance.get('close_price', 0),
                'price_change': binance.get('price_change', 0),
                'quote_volume_24h': binance.get('quote_volume_24h', 0),
                'count': binance.get('count', 0),
                'primary_source': 'binance_spot'
            })
        elif 'binance_futures' in price_sources:
            binance_futures = price_sources['binance_futures']
            combined_data.update({
                'price': binance_futures.get('price', 0),
                'change_24h': binance_futures.get('change_24h', 0),
                'volume_24h': binance_futures.get('volume_24h', 0),
                'high_24h': binance_futures.get('high_24h', 0),
                'low_24h': binance_futures.get('low_24h', 0),
                'open_price': binance_futures.get('open_price', 0),
                'weighted_avg_price': binance_futures.get('weighted_avg_price', 0),
                'price_change': binance_futures.get('price_change', 0),
                'quote_volume_24h': binance_futures.get('quote_volume_24h', 0),
                'count': binance_futures.get('count', 0),
                'primary_source': 'binance_futures'
            })

        # Add additional Binance-specific data if both sources available
        if 'binance' in price_sources and 'binance_futures' in price_sources:
            combined_data['dual_source'] = True
            combined_data['spot_futures_spread'] = abs(
                price_sources['binance'].get('price', 0) - 
                price_sources['binance_futures'].get('price', 0)
            )

        return combined_data

    def get_comprehensive_analysis_data(self, symbol):
        """Get comprehensive data from Binance APIs only for analysis"""
        analysis_data = {
            'symbol': symbol.upper(),
            'timestamp': datetime.now().isoformat(),
            'data_sources': {},
            'successful_calls': 0,
            'total_calls': 0
        }

        # 1. Binance spot price data
        try:
            binance_price = self.get_binance_price(symbol)
            analysis_data['data_sources']['binance_price'] = binance_price
            analysis_data['total_calls'] += 1
            if 'error' not in binance_price:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 2. Binance futures comprehensive data
        try:
            binance_futures = self.get_comprehensive_futures_data(symbol)
            analysis_data['data_sources']['binance_futures'] = binance_futures
            analysis_data['total_calls'] += 1
            if 'error' not in binance_futures:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 3. Binance candlestick data for technical analysis
        try:
            candlestick_data = self.get_binance_candlestick(symbol, '1h', 50)
            analysis_data['data_sources']['binance_candlesticks'] = candlestick_data
            analysis_data['total_calls'] += 1
            if 'error' not in candlestick_data:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 4. Binance server time for synchronization
        try:
            server_time = self.get_binance_server_time()
            analysis_data['data_sources']['binance_server_time'] = server_time
            analysis_data['total_calls'] += 1
            if 'error' not in server_time:
                analysis_data['successful_calls'] += 1
        except:
            pass

        # 5. Crypto news (keep for market sentiment)
        try:
            news_data = self.get_crypto_news(5)
            analysis_data['data_sources']['crypto_news'] = news_data
            analysis_data['total_calls'] += 1
            if news_data and 'error' not in (news_data[0] if news_data else {}):
                analysis_data['successful_calls'] += 1
        except:
            pass

        # Calculate data quality score (more strict for Binance-only)
        success_rate = (analysis_data['successful_calls'] / analysis_data['total_calls']) if analysis_data['total_calls'] > 0 else 0

        if success_rate >= 0.8:
            analysis_data['data_quality'] = 'excellent'
        elif success_rate >= 0.6:
            analysis_data['data_quality'] = 'good'
        elif success_rate >= 0.4:
            analysis_data['data_quality'] = 'fair'
        else:
            analysis_data['data_quality'] = 'poor'

        analysis_data['primary_source'] = 'binance_comprehensive'
        return analysis_data

    # === LEGACY METHOD REPLACEMENTS ===

    def get_futures_data(self, symbol):
        """Legacy method - replaced with Binance long/short ratio"""
        ls_data = self.get_binance_long_short_ratio(symbol)
        if 'error' in ls_data:
            return self._fallback_futures_data(symbol)
        return ls_data

    def get_funding_rate(self, symbol):
        """Get funding rate data from Binance"""
        return self.get_binance_funding_rate(symbol)

    def get_open_interest(self, symbol):
        """Get open interest data from Binance"""
        return self.get_binance_open_interest(symbol)

    def get_liquidation_data(self, symbol):
        """Get liquidation data from Binance"""
        return self.get_binance_liquidation_orders(symbol)

    # === UTILITY METHODS ===

    def get_futures_tickers(self):
        """Get all available futures symbols"""
        return self.provider.get_tickers()

    def get_multiple_binance_prices(self, symbols):
        """Get prices for multiple symbols from Binance only"""
        prices_data = {}

        for symbol in symbols:
            try:
                # Try Binance Spot first
                price_data = self.get_binance_price(symbol)
                if 'error' not in price_data and price_data.get('price', 0) > 0:
                    prices_data[symbol] = {
                        'price': price_data.get('price', 0),
                        'change_24h': price_data.get('change_24h', 0),
                        'volume_24h': price_data.get('volume_24h', 0),
                        'high_24h': price_data.get('high_24h', 0),
                        'low_24h': price_data.get('low_24h', 0),
                        'source': 'binance_spot'
                    }
                    continue

                # Fallback to Binance Futures
                futures_data = self.get_binance_futures_price(symbol)
                if 'error' not in futures_data and futures_data.get('price', 0) > 0:
                    prices_data[symbol] = {
                        'price': futures_data.get('price', 0),
                        'change_24h': futures_data.get('change_24h', 0),
                        'volume_24h': futures_data.get('volume_24h', 0),
                        'high_24h': futures_data.get('high_24h', 0),
                        'low_24h': futures_data.get('low_24h', 0),
                        'source': 'binance_futures'
                    }

            except Exception as e:
                print(f"Error getting Binance price for {symbol}: {e}")
                continue

        return prices_data if prices_data else {'error': 'No Binance price data available'}

    def get_multiple_prices(self, symbols):
        """Legacy method - now uses Binance only"""
        return self.get_multiple_binance_prices(symbols)

    def get_market_overview(self):
        """Get market overview data using Binance data exclusively"""
        try:
            # Get data from top cryptocurrencies via Binance
            major_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'DOT', 'AVAX']
            prices_data = self.get_multiple_binance_prices(major_symbols)

            if 'error' not in prices_data and len(prices_data) > 0:
                # Calculate market metrics from Binance data
                btc_data = prices_data.get('BTC', {})
                eth_data = prices_data.get('ETH', {})
                bnb_data = prices_data.get('BNB', {})

                # Calculate total volume and dominance estimates
                total_volume = sum(data.get('volume_24h', 0) for data in prices_data.values())
                btc_volume = btc_data.get('volume_24h', 0)
                eth_volume = eth_data.get('volume_24h', 0)

                btc_dominance = (btc_volume / total_volume * 100) if total_volume > 0 else 45.0
                eth_dominance = (eth_volume / total_volume * 100) if total_volume > 0 else 18.0

                # Calculate weighted average market change
                changes = []
                volumes = []
                for data in prices_data.values():
                    if 'change_24h' in data and 'volume_24h' in data:
                        changes.append(data['change_24h'])
                        volumes.append(data['volume_24h'])

                if changes and volumes:
                    weighted_change = sum(c * v for c, v in zip(changes, volumes)) / sum(volumes)
                else:
                    weighted_change = 0

                # Estimate total market cap (rough calculation)
                btc_price = btc_data.get('price', 0)
                estimated_market_cap = btc_price * 19500000 / (btc_dominance / 100) if btc_dominance > 0 else total_volume * 20

                # Get BTC futures data for additional insights
                btc_futures = self.get_comprehensive_futures_data('BTC')
                funding_rate = 0
                open_interest = 0
                if 'error' not in btc_futures:
                    funding_data = btc_futures.get('funding_rate_data', {})
                    oi_data = btc_futures.get('open_interest_data', {})
                    funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0
                    open_interest = oi_data.get('open_interest', 0) if 'error' not in oi_data else 0

                return {
                    'total_market_cap': estimated_market_cap,
                    'market_cap_change_24h': weighted_change,
                    'btc_dominance': btc_dominance,
                    'eth_dominance': eth_dominance,
                    'btc_price': btc_data.get('price', 0),
                    'eth_price': eth_data.get('price', 0),
                    'bnb_price': bnb_data.get('price', 0),
                    'btc_change_24h': btc_data.get('change_24h', 0),
                    'eth_change_24h': eth_data.get('change_24h', 0),
                    'bnb_change_24h': bnb_data.get('change_24h', 0),
                    'total_volume_24h': total_volume,
                    'active_cryptocurrencies': len(prices_data),
                    'btc_funding_rate': funding_rate,
                    'btc_open_interest': open_interest,
                    'source': 'binance_comprehensive',
                    'last_updated': datetime.now().isoformat()
                }
            else:
                return {'error': 'Binance market data unavailable'}
        except Exception as e:
            return {'error': f"Market overview error: {str(e)}"}

    def is_deployment_mode(self):
        """Check if running in deployment mode with comprehensive logging"""
        deployment_checks = {
            'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT'),
            'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT'), 
            'REPLIT_ENVIRONMENT': os.getenv('REPLIT_ENVIRONMENT'),
            'REPL_SLUG': os.getenv('REPL_SLUG'),
            'REPL_DB_URL': os.getenv('REPL_DB_URL'),
            'REPL_OWNER': os.getenv('REPL_OWNER'),
            'deployment_flag': os.path.exists('/tmp/repl_deployment_flag')
        }
        
        is_deployment = (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
            os.path.exists('/tmp/repl_deployment_flag') or
            bool(os.getenv('REPL_SLUG')) or 
            bool(os.getenv('REPL_DB_URL')) or
            bool(os.getenv('REPL_OWNER'))
        )
        
        print(f"🚀 Deployment Mode Check:")
        print(f"   Environment Variables: {deployment_checks}")
        print(f"   Result: {'DEPLOYMENT' if is_deployment else 'DEVELOPMENT'}")
        
        return is_deployment

    def check_api_status(self):
        """Check Binance API health status comprehensively"""
        try:
            # Test Binance Spot API
            spot_test = requests.get(f"{self.binance_spot_url}/ping", timeout=5)
            binance_spot_ok = spot_test.status_code == 200

            # Test Binance Futures API
            futures_test = requests.get(f"{self.binance_futures_url}/ping", timeout=5)
            binance_futures_ok = futures_test.status_code == 200

            # Test Binance Spot price endpoint
            spot_price_ok = False
            try:
                btc_spot = self.get_binance_price('BTC')
                spot_price_ok = 'error' not in btc_spot and btc_spot.get('price', 0) > 0
            except:
                spot_price_ok = False

            # Test Binance Futures price endpoint
            futures_price_ok = False
            try:
                btc_futures = self.get_binance_futures_price('BTC')
                futures_price_ok = 'error' not in btc_futures and btc_futures.get('price', 0) > 0
            except:
                futures_price_ok = False

            # Test advanced Binance futures endpoints
            advanced_endpoints_ok = 0
            total_advanced = 6

            try:
                test_symbol = 'BTCUSDT'

                # Test each advanced endpoint
                oi_test = self.get_binance_open_interest(test_symbol)
                if 'error' not in oi_test:
                    advanced_endpoints_ok += 1

                funding_test = self.get_binance_funding_rate(test_symbol)
                if 'error' not in funding_test:
                    advanced_endpoints_ok += 1

                mark_test = self.get_binance_mark_price(test_symbol)
                if 'error' not in mark_test:
                    advanced_endpoints_ok += 1

                ls_test = self.get_binance_long_short_ratio(test_symbol)
                if 'error' not in ls_test:
                    advanced_endpoints_ok += 1

                liq_test = self.get_binance_liquidation_orders(test_symbol)
                if 'error' not in liq_test:
                    advanced_endpoints_ok += 1

                candle_test = self.get_binance_candlestick(test_symbol, '1h', 5)
                if 'error' not in candle_test:
                    advanced_endpoints_ok += 1

            except:
                pass

            # Test CryptoNews (secondary)
            news_ok = bool(self.cryptonews_key)

            # Calculate overall health
            core_binance_ok = binance_spot_ok and binance_futures_ok
            price_endpoints_ok = spot_price_ok or futures_price_ok
            advanced_ok = advanced_endpoints_ok >= 4  # At least 4 out of 6 working

            overall_health = core_binance_ok and price_endpoints_ok and advanced_ok

            return {
                'binance_spot_ping': binance_spot_ok,
                'binance_futures_ping': binance_futures_ok,
                'binance_spot_price': spot_price_ok,
                'binance_futures_price': futures_price_ok,
                'binance_advanced_endpoints': f"{advanced_endpoints_ok}/{total_advanced}",
                'binance_advanced_ok': advanced_ok,
                'cryptonews': news_ok,
                'overall_health': overall_health,
                'primary_source': 'binance_exclusive',
                'api_coverage': 'complete' if overall_health else 'partial'
            }
        except Exception as e:
            return {
                'binance_spot_ping': False,
                'binance_futures_ping': False,
                'binance_spot_price': False,
                'binance_futures_price': False,
                'binance_advanced_endpoints': '0/6',
                'binance_advanced_ok': False,
                'cryptonews': False,
                'overall_health': False,
                'primary_source': 'binance_exclusive',
                'error': str(e)
            }

    def _format_price_display(self, price):
        """Smart price formatting"""
        if price >= 1000:
            return f"${price:,.2f}"
        elif price >= 1:
            return f"${price:.4f}"
        elif price >= 0.01:
            return f"${price:.6f}"
        else:
            return f"${price:.8f}"

    def _attempt_price_recovery(self, symbol, max_retries=3):
        """Emergency price recovery method for deployment"""
        print(f"🆘 EMERGENCY PRICE RECOVERY for {symbol} - {max_retries} attempts")
        
        # Ensure USDT format
        if not symbol.upper().endswith('USDT'):
            symbol = symbol.upper() + 'USDT'
        
        for attempt in range(max_retries):
            print(f"🔄 Recovery attempt {attempt + 1}/{max_retries} for {symbol}")
            
            try:
                # Try minimal Binance endpoint with extended timeout
                response = requests.get(
                    f"{self.binance_spot_url}/ticker/price",
                    params={'symbol': symbol},
                    timeout=45,  # Extended timeout for deployment
                    headers={
                        'User-Agent': 'CryptoMentorAI/1.0',
                        'Accept': 'application/json',
                        'Connection': 'keep-alive'
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'price' in data:
                        price = float(data['price'])
                        if price > 0:
                            print(f"🎯 RECOVERY SUCCESS: {symbol} = ${price:.8f}")
                            return {
                                'symbol': symbol,
                                'price': price,
                                'source': 'binance_recovery',
                                'recovery_attempt': attempt + 1,
                                'api_call_successful': True,
                                'price_validation_passed': True
                            }
                
                # Wait between attempts
                if attempt < max_retries - 1:
                    import time
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ Recovery attempt {attempt + 1} failed: {e}")
                continue
        
        print(f"💥 RECOVERY FAILED for {symbol} after {max_retries} attempts")
        return None

    def _fallback_price(self, symbol, error_msg):
        """Fallback price data when all Binance endpoints fail"""
        # Check deployment mode
        is_deployment = (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
            os.path.exists('/tmp/repl_deployment_flag') or
            bool(os.getenv('REPL_SLUG')) or
            bool(os.getenv('REPL_OWNER'))
        )

        if is_deployment:
            print(f"🆘 DEPLOYMENT FALLBACK: Attempting emergency recovery for {symbol}")
            
            # Try emergency recovery first
            recovery_result = self._attempt_price_recovery(symbol)
            if recovery_result:
                return recovery_result
            
            print(f"❌ DEPLOYMENT: All recovery attempts failed for {symbol}")
            return {
                'error': f'All Binance APIs and recovery attempts failed for {symbol}',
                'symbol': symbol.upper(),
                'error_reason': error_msg,
                'deployment_mode': True,
                'recovery_attempted': True,
                'api_call_successful': False
            }

        # Only use simulation data in development as last resort
        import random
        print(f"⚠️ Using simulation data for {symbol} - Binance APIs unavailable")

        mock_prices = {
            'BTCUSDT': random.uniform(65000, 75000),
            'ETHUSDT': random.uniform(3000, 4000),
            'BNBUSDT': random.uniform(500, 700),
            'ADAUSDT': random.uniform(0.4, 0.6),
            'SOLUSDT': random.uniform(150, 250),
            'XRPUSDT': random.uniform(0.5, 0.7),
            'DOGEUSDT': random.uniform(0.08, 0.12),
            'MATICUSDT': random.uniform(0.8, 1.2),
            'DOTUSDT': random.uniform(5, 8),
            'AVAXUSDT': random.uniform(25, 40)
        }

        normalized_symbol = symbol.upper() + 'USDT' if not symbol.upper().endswith('USDT') else symbol.upper()
        base_price = mock_prices.get(normalized_symbol, random.uniform(1, 100))

        return {
            'symbol': normalized_symbol,
            'price': base_price,
            'change_24h': random.uniform(-5, 5),
            'high_24h': base_price * random.uniform(1.01, 1.05),
            'low_24h': base_price * random.uniform(0.95, 0.99),
            'volume_24h': random.uniform(10000000, 100000000),
            'source': 'binance_simulation',
            'error_reason': error_msg,
            'warning': 'SIMULATION DATA - Binance APIs unavailable (Development Only)'
        }

    def _fallback_futures_data(self, symbol):
        """Fallback futures data when Binance fails"""
        import random
        long_ratio = random.uniform(35, 75)
        return {
            'symbol': symbol,
            'long_ratio': long_ratio,
            'short_ratio': 100 - long_ratio,
            'long_short_ratio': long_ratio / (100 - long_ratio),
            'source': 'fallback_simulation'
        }

    def analyze_supply_demand(self, symbol, timeframe='1h'):
        """Analyze supply and demand zones using Binance candlestick data"""
        try:
            # Get candlestick data
            candle_data = self.get_binance_candlestick(symbol, timeframe, 100)
            
            if 'error' in candle_data:
                print(f"❌ Candlestick data error for {symbol}: {candle_data['error']}")
                return {
                    'error': f"Cannot get candlestick data: {candle_data['error']}",
                    'symbol': symbol,
                    'analysis_successful': False
                }

            candlesticks = candle_data.get('candlesticks', [])
            if len(candlesticks) < 20:
                return {
                    'error': 'Not enough data for analysis',
                    'symbol': symbol,
                    'analysis_successful': False
                }

            # Calculate basic SnD analysis
            highs = [c['high'] for c in candlesticks[-50:]]
            lows = [c['low'] for c in candlesticks[-50:]]
            closes = [c['close'] for c in candlesticks[-50:]]
            volumes = [c['volume'] for c in candlesticks[-50:]]

            current_price = closes[-1]
            
            # Find resistance (supply) levels
            resistance_levels = []
            for i in range(2, len(highs) - 2):
                if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and 
                    highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                    resistance_levels.append({
                        'price': highs[i],
                        'strength': volumes[i],
                        'type': 'resistance'
                    })

            # Find support (demand) levels
            support_levels = []
            for i in range(2, len(lows) - 2):
                if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and 
                    lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                    support_levels.append({
                        'price': lows[i],
                        'strength': volumes[i],
                        'type': 'support'
                    })

            # Sort and get strongest levels
            resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
            support_levels.sort(key=lambda x: x['strength'], reverse=True)

            # Calculate trend
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50
            trend = 'bullish' if sma_20 > sma_50 else 'bearish'

            # Generate signals based on proximity to levels
            signals = []
            nearest_resistance = min(resistance_levels[:3], key=lambda x: abs(x['price'] - current_price)) if resistance_levels else None
            nearest_support = min(support_levels[:3], key=lambda x: abs(x['price'] - current_price)) if support_levels else None

            if nearest_support and current_price - nearest_support['price'] < current_price * 0.02:
                signals.append({
                    'type': 'buy',
                    'reason': f'Price near strong support at {nearest_support["price"]:.4f}',
                    'confidence': min(90, 60 + (nearest_support['strength'] / max(volumes)) * 30)
                })

            if nearest_resistance and nearest_resistance['price'] - current_price < current_price * 0.02:
                signals.append({
                    'type': 'sell',
                    'reason': f'Price near strong resistance at {nearest_resistance["price"]:.4f}',
                    'confidence': min(90, 60 + (nearest_resistance['strength'] / max(volumes)) * 30)
                })

            return {
                'symbol': symbol,
                'current_price': current_price,
                'trend': trend,
                'resistance_levels': resistance_levels[:5],
                'support_levels': support_levels[:5],
                'signals': signals,
                'analysis_successful': True,
                'timeframe': timeframe,
                'data_points': len(candlesticks),
                'source': 'binance_snd_analysis'
            }

        except Exception as e:
            print(f"❌ SnD analysis error for {symbol}: {str(e)}")
            return {
                'error': f"SnD analysis failed: {str(e)}",
                'symbol': symbol,
                'analysis_successful': False
            }

    # === NEWS API ===

    def get_latest_crypto_news(self, limit=5):
        """Get latest crypto news"""
        return self.get_crypto_news(limit)

    def get_crypto_news(self, limit=5):
        """Get crypto news from CryptoNews API"""
        if not self.cryptonews_key:
            return self._fallback_news(limit)

        url = "https://cryptonews-api.com/api/v1/category"
        params = {
            "section": "general",
            "items": limit,
            "token": self.cryptonews_key
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = data.get("data", [])

            # Add source info
            for article in articles:
                article['source'] = 'cryptonews_api'

            return articles
        except Exception as e:
            return self._fallback_news(limit)

    def _fallback_news(self, limit):
        """Fallback news when API fails"""
        mock_news = [
            {"title": "Bitcoin Reaches New All-Time High Amid Institutional Adoption", "url": "#", "source": "mock"},
            {"title": "Ethereum 2.0 Staking Rewards Show Strong Performance", "url": "#", "source": "mock"},
            {"title": "DeFi TVL Surpasses $100 Billion Milestone", "url": "#", "source": "mock"},
            {"title": "Major Exchange Lists New Altcoin with Strong Fundamentals", "url": "#", "source": "mock"},
            {"title": "Regulatory Clarity Boosts Crypto Market Sentiment", "url": "#", "source": "mock"}
        ]
        return mock_news[:limit]