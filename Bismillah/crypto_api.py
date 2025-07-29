import requests
import os
import time
from datetime import datetime, timezone
from binance_provider import BinanceFuturesProvider

class CryptoAPI:
    def __init__(self):
        self.provider = BinanceFuturesProvider()
        self.cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
        self.coinapi_key = os.getenv("COINAPI_KEY")
        self.coinapi_url = "https://rest.coinapi.io/v1"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1"
        self.binance_spot_url = "https://api.binance.com/api/v3"  # Add missing spot URL

        # CoinAPI-exclusive configuration for price data
        print("🚀 CryptoAPI initialized with CoinAPI-exclusive mode")
        print(f"📊 CoinAPI Base URL: {self.coinapi_url}")
        print(f"🔑 CoinAPI Key: {'✅ Enabled' if self.coinapi_key else '❌ Disabled'}")
        print(f"📈 Binance Futures API: {self.binance_futures_url} (for advanced data)")
        print(f"📊 Binance Spot API: {self.binance_spot_url} (for candlestick data)")
        print(f"📰 CryptoNews API: {'✅ Enabled' if self.cryptonews_key else '❌ Disabled'}")
        print("🎯 All price data centralized to CoinAPI only")

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

    def get_coinapi_price(self, symbol, force_refresh=False):
        """Get real-time price from CoinAPI with enhanced error handling and USDT validation"""
        try:
            if not self.coinapi_key:
                return {
                    'error': 'CoinAPI key not found in secrets',
                    'symbol': symbol,
                    'api_call_successful': False,
                    'error_type': 'missing_api_key'
                }

            # Symbol validation and normalization
            original_symbol = symbol.upper().strip()

            # Remove USDT suffix if present for CoinAPI format
            if original_symbol.endswith('USDT'):
                base_symbol = original_symbol[:-4]  # Remove 'USDT'
            else:
                base_symbol = original_symbol

            # For CoinAPI, we use BASE/USDT format
            coinapi_symbol = f"{base_symbol}/USDT"

            print(f"✅ Symbol validation: {original_symbol} → {coinapi_symbol}")

            # Enhanced deployment detection
            deployment_indicators = {
                'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
                'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1',
                'REPLIT_ENVIRONMENT': os.getenv('REPLIT_ENVIRONMENT') == 'deployment',
                'REPL_SLUG': bool(os.getenv('REPL_SLUG')),
                'REPL_OWNER': bool(os.getenv('REPL_OWNER')),
                'REPL_DB_URL': bool(os.getenv('REPL_DB_URL')),
                'deployment_flag_file': os.path.exists('/tmp/repl_deployment_flag')
            }

            is_deployment = any(deployment_indicators.values())
            print(f"🔍 DEPLOYMENT DETECTION:")
            for key, value in deployment_indicators.items():
                status = "✅" if value else "❌"
                print(f"  {status} {key}: {value}")
            print(f"📊 Result: {'🚀 DEPLOYMENT MODE' if is_deployment else '🔧 DEVELOPMENT MODE'}")

            # ALWAYS force refresh in deployment for real-time data
            if is_deployment:
                force_refresh = True
                print(f"🚀 DEPLOYMENT: Force refresh ENABLED - ensuring real-time price data")
                try:
                    with open('/tmp/repl_deployment_flag', 'w') as f:
                        f.write(f"deployment_active_{int(time.time())}")
                except:
                    pass
            else:
                print(f"🔧 DEVELOPMENT: Force refresh = {force_refresh}")

            # CoinAPI headers with API key
            headers = {
                'X-CoinAPI-Key': self.coinapi_key,
                'User-Agent': 'CryptoMentorAI/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }

            # Cache control for development
            if not is_deployment or force_refresh:
                headers.update({
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                })

            # CoinAPI endpoint
            endpoint = f"{self.coinapi_url}/exchangerate/{base_symbol}/USDT"

            print(f"📡 CoinAPI Request: {endpoint}")
            print(f"📊 Headers: API Key present = {bool(self.coinapi_key)}")

            try:
                # Make request with enhanced timeout handling
                response = requests.get(
                    endpoint,
                    timeout=30 if is_deployment else 15,
                    headers=headers,
                    allow_redirects=True
                )

                print(f"📊 Response Status: {response.status_code}")
                print(f"📊 Response Size: {len(response.content)} bytes")

                # Enhanced status code handling
                if response.status_code == 429:
                    print(f"⏳ Rate limited by CoinAPI")
                    return {
                        'error': 'CoinAPI rate limit exceeded',
                        'symbol': original_symbol,
                        'api_call_successful': False,
                        'error_type': 'rate_limit'
                    }
                elif response.status_code == 401:
                    print(f"🔒 Unauthorized - Invalid CoinAPI key")
                    return {
                        'error': 'Invalid CoinAPI key',
                        'symbol': original_symbol,
                        'api_call_successful': False,
                        'error_type': 'invalid_api_key'
                    }
                elif response.status_code != 200:
                    error_msg = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = f"HTTP {response.status_code}: {error_data.get('error', 'Unknown error')}"
                        print(f"❌ CoinAPI Error: {error_data}")
                    except:
                        print(f"❌ Non-JSON error response: {response.text[:100]}")
                    return {
                        'error': f"CoinAPI error: {error_msg}",
                        'symbol': original_symbol,
                        'api_call_successful': False,
                        'error_type': 'api_error'
                    }

                response.raise_for_status()

                # Parse JSON response
                try:
                    data = response.json()
                    print(f"📊 JSON parsing successful, data type: {type(data)}")
                    print(f"📊 CoinAPI Response: {data}")

                except ValueError as json_error:
                    print(f"❌ JSON parsing failed: {json_error}")
                    print(f"📊 Raw response (first 300 chars): {response.text[:300]}")
                    return {
                        'error': f"JSON parsing error: {json_error}",
                        'symbol': original_symbol,
                        'api_call_successful': False,
                        'error_type': 'json_error'
                    }

                # Validate response structure
                if not data or not isinstance(data, dict):
                    print(f"❌ Invalid response structure for {coinapi_symbol}")
                    return {
                        'error': 'Invalid CoinAPI response format',
                        'symbol': original_symbol,
                        'api_call_successful': False,
                        'error_type': 'invalid_response'
                    }

                # Extract rate (price) from CoinAPI response
                if 'rate' not in data:
                    print(f"❌ Rate field missing in CoinAPI response")
                    return {
                        'error': 'Rate field missing in CoinAPI response',
                        'symbol': original_symbol,
                        'api_call_successful': False,
                        'error_type': 'missing_rate_field'
                    }

                # Price validation
                price_result = self._extract_and_validate_coinapi_price(data, coinapi_symbol)
                if price_result['error']:
                    print(f"❌ Price validation failed: {price_result['error']}")
                    return {
                        'error': price_result['error'],
                        'symbol': original_symbol,
                        'api_call_successful': False,
                        'error_type': 'price_validation_failed'
                    }

                price = price_result['price']
                print(f"✅ Price validation successful: {coinapi_symbol} = ${price:,.8f}")

                # Get timestamp from response
                last_updated = data.get('time', datetime.now().isoformat())

                # Build result
                result = {
                    'symbol': original_symbol,
                    'price': price,
                    'change_24h': 0,  # CoinAPI exchange rate doesn't include 24h change
                    'high_24h': 0,    # Not available in exchange rate endpoint
                    'low_24h': 0,     # Not available in exchange rate endpoint
                    'volume_24h': 0,  # Not available in exchange rate endpoint
                    'source': 'coinapi_exchange_rate',
                    'api_call_successful': True,
                    'price_validation_passed': True,
                    'raw_rate': data.get('rate'),
                    'deployment_mode': is_deployment,
                    'last_updated': last_updated,
                    'coinapi_symbol': coinapi_symbol
                }

                print(f"✅ CoinAPI SUCCESS: {coinapi_symbol} = ${price:,.6f}")
                return result

            except requests.exceptions.Timeout as e:
                error_msg = f"CoinAPI timeout: {str(e)}"
                print(f"⏰ {error_msg}")
                return {
                    'error': error_msg,
                    'symbol': original_symbol,
                    'api_call_successful': False,
                    'error_type': 'timeout'
                }
            except requests.exceptions.ConnectionError as e:
                error_msg = f"CoinAPI connection error: {str(e)}"
                print(f"🔌 {error_msg}")
                return {
                    'error': error_msg,
                    'symbol': original_symbol,
                    'api_call_successful': False,
                    'error_type': 'connection_error'
                }
            except Exception as e:
                error_msg = f"CoinAPI unexpected error: {str(e)}"
                print(f"❌ {error_msg}")
                return {
                    'error': error_msg,
                    'symbol': original_symbol,
                    'api_call_successful': False,
                    'error_type': 'unexpected_error'
                }

        except Exception as e:
            error_msg = f"CoinAPI price retrieval completely failed for {symbol}: {str(e)}"
            print(f"💥 COMPLETE FAILURE: {error_msg}")

            return {
                'error': error_msg,
                'symbol': symbol,
                'api_call_successful': False,
                'error_type': 'complete_coinapi_failure',
                'deployment_mode': is_deployment,
                'price': None,
                'zero_price_prevention': True
            }

    def _ensure_non_zero_price(self, price_data, symbol):
        """Ensure price is never zero or None - critical for deployment"""
        try:
            price = price_data.get('price', 0)

            # Check for zero, None, or invalid prices
            if price is None or price <= 0 or price != price:  # price != price checks for NaN
                print(f"⛔ ZERO PRICE DETECTED for {symbol}: {price}")
                print(f"🔧 Returning error instead of zero price to prevent 0.0000 display")

                return {
                    'error': f'Invalid price data for {symbol} - price is {price}',
                    'symbol': symbol,
                    'api_call_successful': False,
                    'error_type': 'zero_price_prevention',
                    'original_price': price,
                    'zero_prevented': True
                }

            return price_data

        except Exception as e:
            print(f"❌ Error in zero price prevention: {e}")
            return price_data

    def _extract_and_validate_coinapi_price(self, data, symbol):
        """Extract and validate price from CoinAPI response"""
        try:
            raw_rate = data.get('rate')

            print(f"🔍 Extracting rate from CoinAPI for {symbol}: {raw_rate} (type: {type(raw_rate)})")

            # Null/None check
            if raw_rate is None:
                return {'error': f'Rate field is None in CoinAPI response for {symbol}', 'price': None}

            # Empty string check
            if isinstance(raw_rate, str):
                raw_rate = raw_rate.strip()
                if raw_rate == '':
                    return {'error': f'Rate field is empty string for {symbol}', 'price': None}

                # Check for invalid strings
                if raw_rate.lower() in ['null', 'none', 'undefined', 'nan', 'inf', '-inf']:
                    return {'error': f'Rate field contains invalid value: {raw_rate}', 'price': None}

            # Convert to float
            try:
                price = float(raw_rate)
                print(f"🔢 Successfully converted rate to float: {price}")
            except (ValueError, TypeError, OverflowError) as conversion_error:
                print(f"❌ Rate conversion failed: {conversion_error}")
                return {'error': f'Cannot convert rate to float: {raw_rate} ({conversion_error})', 'price': None}

            # Comprehensive validation checks
            validation_checks = [
                (price <= 0, f"❌ ZERO/NEGATIVE: Rate is {price} - must be positive"),
                (price != price, f"❌ NaN: Rate is NaN"),
                (price == float('inf'), f"❌ INFINITY: Rate is positive infinity"),
                (price == float('-inf'), f"❌ NEG_INFINITY: Rate is negative infinity"),
                (price > 50000000, f"❌ TOO_HIGH: Rate {price} exceeds reasonable limit ($50M)"),
                (price < 0.00000001, f"❌ TOO_LOW: Rate {price} below minimum threshold (0.00000001)")
            ]

            for check_condition, error_message in validation_checks:
                if check_condition:
                    print(error_message)
                    return {'error': error_message, 'price': None}

            # Final validation
            if not isinstance(price, (int, float)) or abs(price) == float('inf'):
                return {'error': f'Rate validation failed - invalid number type: {type(price)}', 'price': None}

            print(f"✅ CoinAPI rate validation PASSED: {symbol} = ${price:,.8f}")
            return {'error': None, 'price': price}

        except Exception as e:
            error_msg = f"Unexpected error in CoinAPI rate validation: {str(e)}"
            print(f"💥 CRITICAL: {error_msg}")
            return {'error': error_msg, 'price': None}

    def _extract_and_validate_price(self, data, price_field, symbol, source_type):
        """Extract and validate price with comprehensive checks and multiple fallback methods"""
        try:
            # Try multiple price fields as fallback
            price_fields_to_try = [price_field]
            if price_field == 'lastPrice':
                price_fields_to_try.extend(['price', 'close', 'closePrice'])
            elif price_field == 'price':
                price_fields_to_try.extend(['lastPrice', 'close', 'closePrice'])

            raw_price = None
            used_field = None

            # Try each price field until we find a valid one
            for field in price_fields_to_try:
                raw_price = data.get(field)
                if raw_price is not None:
                    used_field = field
                    break

            print(f"🔍 Extracting price from {source_type} using field '{used_field}': {raw_price} (type: {type(raw_price)})")

            # Null/None check
            if raw_price is None:
                return {'error': f'No valid price field found in {source_type} (tried: {price_fields_to_try})', 'price': None}

            # Empty string check
            if isinstance(raw_price, str):
                raw_price = raw_price.strip()
                if raw_price == '':
                    return {'error': f'Price field {used_field} is empty string in {source_type}', 'price': None}

                # Check for obviously invalid strings
                if raw_price.lower() in ['null', 'none', 'undefined', 'nan', 'inf', '-inf']:
                    return {'error': f'Price field {used_field} contains invalid value: {raw_price}', 'price': None}

                # Enhanced numeric validation
                cleaned_price = raw_price.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '')
                if not cleaned_price.isdigit() and cleaned_price != '':
                    # Try scientific notation parsing
                    try:
                        test_conversion = float(raw_price)
                        print(f"🔬 Scientific notation detected and validated: {raw_price} = {test_conversion}")
                    except ValueError:
                        return {'error': f'Price field {used_field} contains non-numeric data: {raw_price}', 'price': None}

            # Convert to float with comprehensive error handling
            try:
                price = float(raw_price)
                print(f"🔢 Successfully converted to float: {price}")
            except (ValueError, TypeError, OverflowError) as conversion_error:
                print(f"❌ Price conversion failed: {conversion_error}")
                return {'error': f'Cannot convert {used_field} to float: {raw_price} ({conversion_error})', 'price': None}

            # Comprehensive validation checks with stricter bounds
            validation_checks = [
                (price <= 0, f"❌ ZERO/NEGATIVE: Price is {price} - must be positive"),
                (price != price, f"❌ NaN: Price is NaN"),  # NaN check
                (price == float('inf'), f"❌ INFINITY: Price is positive infinity"),
                (price == float('-inf'), f"❌ NEG_INFINITY: Price is negative infinity"),
                (price > 50000000, f"❌ TOO_HIGH: Price {price} exceeds reasonable limit ($50M)"),  # Reduced from $100M
                (price < 0.00000001, f"❌ TOO_LOW: Price {price} below minimum threshold (0.00000001)")   # 1 satoshi
            ]

            for check_condition, error_message in validation_checks:
                if check_condition:
                    print(error_message)
                    return {'error': error_message, 'price': None}

            # USDT-specific validation
            if 'USDT' in symbol:
                # Additional checks for USDT pairs
                if symbol in ['USDUSDT', 'USDTUSDT']:  # These shouldn't exist
                    return {'error': f'Invalid USDT pair detected: {symbol}', 'price': None}

                # Most legitimate USDT pairs should be within reasonable ranges
                if price > 10000000:  # $10M per token is very high even for legitimate tokens
                    print(f"⚠️ WARNING: Very high price for {symbol}: ${price:,.2f}")

            # Final validation - ensure price is a clean number
            if not isinstance(price, (int, float)) or abs(price) == float('inf'):
                return {'error': f'Price validation failed - invalid number type: {type(price)}', 'price': None}

            print(f"✅ Price validation PASSED: {symbol} = ${price:,.8f} (field: {used_field})")
            return {'error': None, 'price': price}

        except Exception as e:
            error_msg = f"Unexpected error in price validation: {str(e)}"
            print(f"💥 CRITICAL: {error_msg}")
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

    def is_deployment_mode(self):
        """Check if running in deployment mode"""
        return (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
            os.path.exists('/tmp/repl_deployment_flag') or
            bool(os.getenv('REPL_SLUG')) or
            bool(os.getenv('REPL_DB_URL')) or
            bool(os.getenv('REPL_OWNER'))
        )

    def get_market_overview(self):
        """Get market overview using CoinAPI as primary source"""
        print("📊 Getting market overview from CoinAPI...")
        return self._get_coinapi_market_overview()

    def _get_coinapi_market_overview(self):
        """Get market overview using CoinAPI data with enhanced error handling"""
        try:
            # Get major cryptocurrencies from CoinAPI
            major_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'DOT', 'AVAX']
            market_data = {}
            total_estimated_volume = 0
            successful_requests = 0

            print(f"📊 Fetching market data for {len(major_symbols)} symbols from CoinAPI...")

            for symbol in major_symbols:
                try:
                    price_data = self.get_coinapi_price(symbol, force_refresh=True)
                    if 'error' not in price_data and price_data.get('price', 0) > 0:
                        market_data[symbol] = price_data
                        # Estimate volume based on price and market activity
                        price = price_data.get('price', 0)
                        estimated_daily_volume = price * 50000000  # Estimate based on price
                        total_estimated_volume += estimated_daily_volume
                        successful_requests += 1
                        print(f"✅ {symbol}: ${price:,.4f}")
                    else:
                        print(f"❌ {symbol}: {price_data.get('error', 'Failed')}")
                except Exception as e:
                    print(f"⚠️ Failed to get {symbol} from CoinAPI: {e}")
                    continue

            if not market_data or successful_requests < 2:
                print(f"❌ Insufficient market data: {successful_requests}/{len(major_symbols)} successful")
                return {'error': f'Insufficient market data from CoinAPI ({successful_requests}/{len(major_symbols)} successful)'}

            # Calculate market metrics with improved accuracy
            btc_data = market_data.get('BTC', {})
            eth_data = market_data.get('ETH', {})
            bnb_data = market_data.get('BNB', {})

            # Calculate market cap with current supply estimates
            btc_price = btc_data.get('price', 0)
            eth_price = eth_data.get('price', 0)
            bnb_price = bnb_data.get('price', 0)

            # Market cap calculations with current supply
            btc_supply = 19700000  # Updated BTC supply
            eth_supply = 120000000  # ETH supply estimate
            bnb_supply = 147000000  # BNB supply estimate

            btc_market_cap = btc_price * btc_supply if btc_price > 0 else 0
            eth_market_cap = eth_price * eth_supply if eth_price > 0 else 0
            bnb_market_cap = bnb_price * bnb_supply if bnb_price > 0 else 0

            # Estimate total market cap (BTC + ETH + others)
            major_caps = btc_market_cap + eth_market_cap + bnb_market_cap
            estimated_total_market_cap = major_caps * 2.2  # Multiply by 2.2 to account for other cryptos

            # Calculate dominance
            btc_dominance = (btc_market_cap / estimated_total_market_cap * 100) if estimated_total_market_cap > 0 else 45.0
            eth_dominance = (eth_market_cap / estimated_total_market_cap * 100) if estimated_total_market_cap > 0 else 18.0

            # Calculate average price change (mock data since CoinAPI exchange rate doesn't provide 24h change)
            avg_change = 2.1  # Positive market assumption

            print(f"📈 Market Overview Generated:")
            print(f"   - Total Market Cap: ${estimated_total_market_cap:,.0f}")
            print(f"   - BTC Dominance: {btc_dominance:.1f}%")
            print(f"   - Successful API calls: {successful_requests}/{len(major_symbols)}")

            return {
                'total_market_cap': estimated_total_market_cap,
                'total_volume': total_estimated_volume,
                'market_cap_change_percentage_24h_usd': avg_change,
                'market_cap_percentage': {
                    'btc': btc_dominance,
                    'eth': eth_dominance
                },
                'btc_price': btc_price,
                'eth_price': eth_price,
                'bnb_price': bnb_price,
                'active_cryptocurrencies': len(market_data),
                'successful_api_calls': successful_requests,
                'total_api_calls': len(major_symbols),
                'data_quality': 'excellent' if successful_requests >= 8 else 'good' if successful_requests >= 5 else 'partial',
                'updated_at': int(datetime.now().timestamp()),
                'source': 'coinapi_market_overview'
            }

        except Exception as e:
            print(f"❌ CoinAPI market overview error: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f"CoinAPI market overview error: {str(e)}"}
</```python

    def test_coinapi_connectivity(self, symbol='BTC'):
        """Test CoinAPI connection and response validation"""
        print(f"🔧 Testing CoinAPI connectivity for {symbol}/USDT...")

        test_results = {
            'api_key_present': bool(self.coinapi_key),
            'exchange_rate_test': False,
            'price_value': None,
            'deployment_mode': self.is_deployment_mode(),
            'timestamp': datetime.now().isoformat()
        }

        # Test API key presence
        if not self.coinapi_key:
            print(f"❌ CoinAPI key not found in secrets")
            test_results['overall_health'] = False
            return test_results
        else:
            print(f"✅ CoinAPI key present")

        # Test price retrieval
        try:
            price_data = self.get_coinapi_price(symbol)
            if 'error' not in price_data and price_data.get('price', 0) > 0:
                test_results['exchange_rate_test'] = True
                test_results['price_value'] = price_data.get('price')
                print(f"💰 {symbol}/USDT price: ✅ ${price_data.get('price'):,.2f}")
            else:
                print(f"❌ CoinAPI price failed: {price_data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ CoinAPI price exception: {e}")

        # Overall assessment
        working_endpoints = sum([
            test_results['api_key_present'],
            test_results['exchange_rate_test']
        ])

        test_results['overall_health'] = working_endpoints >= 2
        test_results['working_endpoints'] = f"{working_endpoints}/2"

        print(f"📊 Overall CoinAPI Health: {'✅ GOOD' if test_results['overall_health'] else '❌ POOR'} ({working_endpoints}/2 checks passed)")

        return test_results

    # === PRICE METHODS (BINANCE ONLY) ===

    def get_price(self, symbol, force_refresh=False):
        """Get price from CoinAPI with enhanced deployment detection"""
        # Check if in deployment mode using comprehensive method
        is_deployment = self.is_deployment_mode()

        # Always force refresh in deployment for real-time data
        if is_deployment:
            force_refresh = True
            print(f"🚀 DEPLOYMENT MODE: Force refresh enabled for {symbol}")

        return self.get_coinapi_price(symbol, force_refresh)

    def get_multi_api_price(self, symbol, force_refresh=False):
        """Get price from CoinAPI - centralized to CoinAPI with enhanced validation"""
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
            bool(os.getenv('REPL_OWNER'))
        )

        # ALWAYS force refresh in deployment for real-time data
        if is_deployment:
            force_refresh = True

        # Enhanced logging for deployment mode
        mode = "DEPLOYMENT REAL-TIME" if is_deployment else "STANDARD"
        print(f"🔄 {mode} MODE: Fetching price data for {symbol} from CoinAPI (Force: {force_refresh})")

        # Use CoinAPI as primary source
        try:
            print("📡 Trying CoinAPI...")
            coinapi_data = self.get_coinapi_price(symbol, force_refresh)

            if 'error' not in coinapi_data and coinapi_data.get('price', 0) > 0:
                price_str = f"${coinapi_data.get('price', 0):,.4f}"
                print(f"🎯 SUCCESS: {symbol} = {price_str} ✅ (CoinAPI)")
                return coinapi_data
            else:
                print(f"❌ CoinAPI failed: {coinapi_data.get('error', 'Unknown error')}")
                return coinapi_data

        except Exception as e:
            print(f"💥 CoinAPI exception for {symbol}: {e}")
            error_msg = f"CoinAPI failed for {symbol}: {str(e)}"
            return {
                'error': error_msg,
                'symbol': symbol,
                'deployment_mode': is_deployment,
                'all_apis_failed': True,
                'api_call_successful': False
            }

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

    def get_multiple_coinapi_prices(self, symbols):
        """Get prices for multiple symbols from CoinAPI"""
        prices_data = {}

        for symbol in symbols:
            try:
                price_data = self.get_coinapi_price(symbol)
                if 'error' not in price_data and price_data.get('price', 0) > 0:
                    prices_data[symbol] = {
                        'price': price_data.get('price', 0),
                        'change_24h': price_data.get('change_24h', 0),
                        'volume_24h': price_data.get('volume_24h', 0),
                        'high_24h': price_data.get('high_24h', 0),
                        'low_24h': price_data.get('low_24h', 0),
                        'source': 'coinapi_exchange_rate'
                    }

            except Exception as e:
                print(f"Error getting CoinAPI price for {symbol}: {e}")
                continue

        return prices_data if prices_data else {'error': 'No CoinAPI price data available'}

    def get_multiple_prices(self, symbols):
        """Get multiple prices using CoinAPI"""
        return self.get_multiple_coinapi_prices(symbols)

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
        """Check CoinAPI health status comprehensively"""
        try:
            # Test CoinAPI price endpoint
            coinapi_price_ok = False
            coinapi_price_value = None
            try:
                btc_coinapi = self.get_coinapi_price('BTC')
                coinapi_price_ok = 'error' not in btc_coinapi and btc_coinapi.get('price', 0) > 0
                if coinapi_price_ok:
                    coinapi_price_value = btc_coinapi.get('price')
            except:
                coinapi_price_ok = False

            # Test Binance Futures API for advanced data
            futures_ping = False
            try:
                futures_test = requests.get(f"{self.binance_futures_url}/ping", timeout=5)
                futures_ping = futures_test.status_code == 200
            except:
                futures_ping = False

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

            # Test CoinAPI key presence
            coinapi_key_ok = bool(self.coinapi_key)

            # Calculate overall health
            core_coinapi_ok = coinapi_key_ok and coinapi_price_ok
            advanced_ok = advanced_endpoints_ok >= 4  # At least 4 out of 6 working

            overall_health = core_coinapi_ok

            return {
                'coinapi_key_present': coinapi_key_ok,
                'coinapi_price_test': coinapi_price_ok,
                'coinapi_price_value': coinapi_price_value,
                'binance_futures_ping': futures_ping,
                'binance_advanced_endpoints': f"{advanced_endpoints_ok}/{total_advanced}",
                'binance_advanced_ok': advanced_ok,
                'cryptonews': news_ok,
                'overall_health': overall_health,
                'primary_source': 'coinapi_exclusive',
                'api_coverage': 'complete' if overall_health else 'partial'
            }
        except Exception as e:
            return {
                'coinapi_key_present': False,
                'coinapi_price_test': False,
                'coinapi_price_value': None,
                'binance_futures_ping': False,
                'binance_advanced_endpoints': '0/6',
                'binance_advanced_ok': False,
                'cryptonews': False,
                'overall_health': False,
                'primary_source': 'coinapi_exclusive',
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

    def _fallback_price(self, symbol, error_msg):
        """Fallback price data when CoinAPI fails"""
        # In deployment mode, never use mock data - return error instead
        is_deployment = (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
            os.path.exists('/tmp/repl_deployment_flag') or
            bool(os.getenv('REPL_SLUG')) or
            bool(os.getenv('REPL_OWNER'))
        )

        if is_deployment:
            print(f"❌ DEPLOYMENT: No fallback data for {symbol} - CoinAPI-only mode")
            return {
                'error': f'CoinAPI unavailable for {symbol} in deployment mode',
                'symbol': symbol.upper(),
                'error_reason': error_msg,
                'deployment_mode': True
            }

        # Only use simulation data in development as last resort
        import random
        print(f"⚠️ Using simulation data for {symbol} - CoinAPI unavailable")

        mock_prices = {
            'BTC': random.uniform(65000, 75000),
            'ETH': random.uniform(3000, 4000),
            'BNB': random.uniform(500, 700),
            'ADA': random.uniform(0.4, 0.6),
            'SOL': random.uniform(150, 250),
            'XRP': random.uniform(0.5, 0.7),
            'DOGE': random.uniform(0.08, 0.12),
            'MATIC': random.uniform(0.8, 1.2),
            'DOT': random.uniform(5, 8),
            'AVAX': random.uniform(25, 40)
        }

        base_symbol = symbol.upper().replace('USDT', '')
        base_price = mock_prices.get(base_symbol, random.uniform(1, 100))

        return {
            'symbol': symbol.upper(),
            'price': base_price,
            'change_24h': random.uniform(-5, 5),
            'high_24h': base_price * random.uniform(1.01, 1.05),
            'low_24h': base_price * random.uniform(0.95, 0.99),
            'volume_24h': random.uniform(10000000, 100000000),
            'source': 'coinapi_simulation',
            'error_reason': error_msg,
            'warning': 'SIMULATION DATA - CoinAPI unavailable (Development Only)'
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
        """Enhanced Supply and Demand analysis with order block detection"""
        try:
            print(f"🔍 Starting SnD analysis for {symbol} ({timeframe})")

            # Get current price from CoinAPI
            current_price_data = self.get_coinapi_price(symbol, force_refresh=True)
            if 'error' in current_price_data:
                return {
                    'error': f"Cannot get current price: {current_price_data['error']}",
                    'symbol': symbol,
                    'analysis_successful': False
                }

            current_price = current_price_data.get('price', 0)
            if current_price <= 0:
                return {
                    'error': 'Invalid current price',
                    'symbol': symbol,
                    'analysis_successful': False
                }

            # Get candlestick data from Binance for technical analysis
            candle_data = self.get_binance_candlestick(symbol, timeframe, 200)

            if 'error' in candle_data:
                print(f"❌ Candlestick data error for {symbol}: {candle_data['error']}")
                # Use simplified SnD analysis without candlestick data
                return self._simplified_snd_analysis(symbol, current_price)

            candlesticks = candle_data.get('candlesticks', [])
            if len(candlesticks) < 50:
                print(f"⚠️ Insufficient candlestick data ({len(candlesticks)}), using simplified analysis")
                return self._simplified_snd_analysis(symbol, current_price)

            print(f"📊 Analyzing {len(candlesticks)} candlesticks for {symbol}")

            # Extract OHLCV data
            opens = [c['open'] for c in candlesticks]
            highs = [c['high'] for c in candlesticks]
            lows = [c['low'] for c in candlesticks]
            closes = [c['close'] for c in candlesticks]
            volumes = [c['volume'] for c in candlesticks]

            # Enhanced SnD Analysis
            snd_result = self._enhanced_snd_analysis(
                symbol, current_price, opens, highs, lows, closes, volumes, timeframe
            )

            return snd_result

        except Exception as e:
            print(f"❌ SnD analysis error for {symbol}: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': f"SnD analysis failed: {str(e)}",
                'symbol': symbol,
                'analysis_successful': False
            }

    def _enhanced_snd_analysis(self, symbol, current_price, opens, highs, lows, closes, volumes, timeframe):
        """Enhanced Supply and Demand analysis with multiple techniques"""
        try:
            # 1. Order Block Detection
            order_blocks = self._detect_order_blocks(opens, highs, lows, closes, volumes)

            # 2. Support/Resistance Levels
            support_resistance = self._find_support_resistance_levels(highs, lows, volumes)

            # 3. Volume Analysis
            volume_analysis = self._analyze_volume_pressure(closes, volumes)

            # 4. Market Structure Analysis
            market_structure = self._analyze_market_structure(highs, lows, closes)

            # 5. Entry/Exit Point Calculation
            entry_points = self._calculate_entry_exit_points(
                current_price, support_resistance, order_blocks, market_structure
            )

            # 6. Overall SnD Score
            snd_score = self._calculate_snd_score(
                current_price, support_resistance, order_blocks, volume_analysis, market_structure
            )

            # 7. Generate Trading Signals
            signals = self._generate_snd_signals(
                current_price, support_resistance, order_blocks, snd_score, entry_points
            )

            return {
                'symbol': symbol,
                'current_price': current_price,
                'timeframe': timeframe,
                'order_blocks': order_blocks,
                'support_levels': support_resistance['support'],
                'resistance_levels': support_resistance['resistance'],
                'volume_pressure': volume_analysis,
                'market_structure': market_structure,
                'entry_exit_points': entry_points,
                'snd_score': snd_score,
                'signals': signals,
                'analysis_successful': True,
                'data_points': len(closes),
                'source': 'enhanced_snd_analysis'
            }

        except Exception as e:
            print(f"❌ Enhanced SnD analysis error: {e}")
            return self._simplified_snd_analysis(symbol, current_price)

    def _detect_order_blocks(self, opens, highs, lows, closes, volumes):
        """Detect order blocks (institutional levels)"""
        order_blocks = {'bullish': [], 'bearish': []}

        try:
            for i in range(3, len(closes) - 3):
                # Bullish Order Block: Strong buying pressure followed by upward movement
                if (closes[i] > opens[i] and  # Green candle
                    volumes[i] > sum(volumes[i-3:i]) / 3 * 1.5 and  # High volume
                    closes[i+1] > closes[i] and closes[i+2] > closes[i+1]):  # Upward continuation

                    order_blocks['bullish'].append({
                        'high': highs[i],
                        'low': lows[i],
                        'price': (highs[i] + lows[i]) / 2,
                        'volume': volumes[i],
                        'strength': volumes[i] / (sum(volumes) / len(volumes)) * 100,
                        'index': i
                    })

                # Bearish Order Block: Strong selling pressure followed by downward movement
                elif (closes[i] < opens[i] and  # Red candle
                      volumes[i] > sum(volumes[i-3:i]) / 3 * 1.5 and  # High volume
                      closes[i+1] < closes[i] and closes[i+2] < closes[i+1]):  # Downward continuation

                    order_blocks['bearish'].append({
                        'high': highs[i],
                        'low': lows[i],
                        'price': (highs[i] + lows[i]) / 2,
                        'volume': volumes[i],
                        'strength': volumes[i] / (sum(volumes) / len(volumes)) * 100,
                        'index': i
                    })

            # Sort by strength and keep top 5
```python
            order_blocks['bullish'] = sorted(order_blocks['bullish'], key=lambda x: x['strength'], reverse=True)[:5]
            order_blocks['bearish'] = sorted(order_blocks['bearish'], key=lambda x: x['strength'], reverse=True)[:5]

            return order_blocks

        except Exception as e:
            print(f"⚠️ Order block detection error: {e}")
            return {'bullish': [], 'bearish': []}

    def _find_support_resistance_levels(self, highs, lows, volumes):
        """Find support and resistance levels using pivot points"""
        support_levels = []
        resistance_levels = []

        try:
            # Find pivot highs (resistance)
            for i in range(5, len(highs) - 5):
                if (highs[i] == max(highs[i-5:i+6])):  # Local maximum
                    resistance_levels.append({
                        'price': highs[i],
                        'strength': volumes[i],
                        'touches': 1,
                        'index': i
                    })

            # Find pivot lows (support)
            for i in range(5, len(lows) - 5):
                if (lows[i] == min(lows[i-5:i+6])):  # Local minimum
                    support_levels.append({
                        'price': lows[i],
                        'strength': volumes[i],
                        'touches': 1,
                        'index': i
                    })

            # Consolidate nearby levels
            support_levels = self._consolidate_levels(support_levels)
            resistance_levels = self._consolidate_levels(resistance_levels)

            # Sort by strength
            support_levels = sorted(support_levels, key=lambda x: x['strength'], reverse=True)[:10]
            resistance_levels = sorted(resistance_levels, key=lambda x: x['strength'], reverse=True)[:10]

            return {
                'support': support_levels,
                'resistance': resistance_levels
            }

        except Exception as e:
            print(f"⚠️ Support/Resistance detection error: {e}")
            return {'support': [], 'resistance': []}

    def _consolidate_levels(self, levels):
        """Consolidate nearby price levels"""
        if not levels:
            return []

        consolidated = []
        levels.sort(key=lambda x: x['price'])

        current_group = [levels[0]]

        for i in range(1, len(levels)):
            # If price is within 1% of current group average, add to group
            group_avg = sum(l['price'] for l in current_group) / len(current_group)
            if abs(levels[i]['price'] - group_avg) / group_avg < 0.01:
                current_group.append(levels[i])
            else:
                # Consolidate current group
                if current_group:
                    consolidated_level = {
                        'price': sum(l['price'] for l in current_group) / len(current_group),
                        'strength': sum(l['strength'] for l in current_group),
                        'touches': len(current_group)
                    }
                    consolidated.append(consolidated_level)

                current_group = [levels[i]]

        # Don't forget the last group
        if current_group:
            consolidated_level = {
                'price': sum(l['price'] for l in current_group) / len(current_group),
                'strength': sum(l['strength'] for l in current_group),
                'touches': len(current_group)
            }
            consolidated.append(consolidated_level)

        return consolidated

    def _analyze_volume_pressure(self, closes, volumes):
        """Analyze volume pressure for supply/demand imbalance"""
        try:
            if len(closes) < 20 or len(volumes) < 20:
                return {'pressure_type': 'neutral', 'strength': 50}

            # Calculate volume-weighted pressure
            recent_closes = closes[-20:]
            recent_volumes = volumes[-20:]

            buying_volume = sum(v for i, v in enumerate(recent_volumes) 
                              if recent_closes[i] > recent_closes[i-1] if i > 0 else False)
            selling_volume = sum(v for i, v in enumerate(recent_volumes) 
                               if recent_closes[i] < recent_closes[i-1] if i > 0 else False)

            total_volume = buying_volume + selling_volume

            if total_volume == 0:
                return {'pressure_type': 'neutral', 'strength': 50}

            buying_pressure = (buying_volume / total_volume) * 100

            if buying_pressure > 60:
                pressure_type = 'buying_pressure'
                strength = min(100, buying_pressure * 1.2)
            elif buying_pressure < 40:
                pressure_type = 'selling_pressure'  
                strength = min(100, (100 - buying_pressure) * 1.2)
            else:
                pressure_type = 'balanced'
                strength = 50

            return {
                'pressure_type': pressure_type,
                'strength': strength,
                'buying_pressure': buying_pressure,
                'selling_pressure': 100 - buying_pressure
            }

        except Exception as e:
            print(f"⚠️ Volume pressure analysis error: {e}")
            return {'pressure_type': 'neutral', 'strength': 50}

    def _analyze_market_structure(self, highs, lows, closes):
        """Analyze market structure for trend direction"""
        try:
            if len(closes) < 50:
                return {'structure': 'unknown', 'trend': 'sideways'}

            recent_highs = highs[-20:]
            recent_lows = lows[-20:]
            recent_closes = closes[-20:]

            # Higher highs and higher lows = uptrend
            higher_highs = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
            higher_lows = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] > recent_lows[i-1])

            # Lower highs and lower lows = downtrend
            lower_highs = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] < recent_highs[i-1])
            lower_lows = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] < recent_lows[i-1])

            if higher_highs > lower_highs and higher_lows > lower_lows:
                structure = 'bullish_structure'
                trend = 'uptrend'
            elif lower_highs > higher_highs and lower_lows > higher_lows:
                structure = 'bearish_structure'
                trend = 'downtrend'
            else:
                structure = 'ranging_structure'
                trend = 'sideways'

            # Calculate structure strength
            total_points = len(recent_highs) + len(recent_lows) - 2
            if trend == 'uptrend':
                strength = ((higher_highs + higher_lows) / total_points) * 100
            elif trend == 'downtrend':
                strength = ((lower_highs + lower_lows) / total_points) * 100
            else:
                strength = 50

            return {
                'structure': structure,
                'trend': trend,
                'strength': strength,
                'higher_highs': higher_highs,
                'higher_lows': higher_lows,
                'lower_highs': lower_highs,
                'lower_lows': lower_lows
            }

        except Exception as e:
            print(f"⚠️ Market structure analysis error: {e}")
            return {'structure': 'unknown', 'trend': 'sideways', 'strength': 50}

    def _calculate_entry_exit_points(self, current_price, support_resistance, order_blocks, market_structure):
        """Calculate optimal entry and exit points based on SnD analysis"""
        try:
            entry_points = {'long': [], 'short': []}

            # Find nearest support for long entries
            supports = support_resistance.get('support', [])
            resistances = support_resistance.get('resistance', [])

            for support in supports[:3]:  # Top 3 support levels
                distance = abs(current_price - support['price']) / current_price * 100
                if distance < 5:  # Within 5% of current price
                    entry_points['long'].append({
                        'type': 'support_bounce',
                        'entry_price': support['price'] * 1.001,  # Slightly above support
                        'stop_loss': support['price'] * 0.995,   # 0.5% below support
                        'take_profit_1': current_price * 1.02,   # 2% profit
                        'take_profit_2': current_price * 1.04,   # 4% profit
                        'confidence': min(90, 70 + support['strength']/1000),
                        'risk_reward': 4.0  # 1:4 risk reward
                    })

            # Find nearest resistance for short entries
            for resistance in resistances[:3]:  # Top 3 resistance levels
                distance = abs(current_price - resistance['price']) / current_price * 100
                if distance < 5:  # Within 5% of current price
                    entry_points['short'].append({
                        'type': 'resistance_rejection',
                        'entry_price': resistance['price'] * 0.999,  # Slightly below resistance
                        'stop_loss': resistance['price'] * 1.005,    # 0.5% above resistance
                        'take_profit_1': current_price * 0.98,       # 2% profit
                        'take_profit_2': current_price * 0.96,       # 4% profit
                        'confidence': min(90, 70 + resistance['strength']/1000),
                        'risk_reward': 4.0  # 1:4 risk reward
                    })

            # Add order block entries
            bullish_blocks = order_blocks.get('bullish', [])
            bearish_blocks = order_blocks.get('bearish', [])

            for block in bullish_blocks[:2]:  # Top 2 bullish order blocks
                distance = abs(current_price - block['price']) / current_price * 100
                if distance < 3:  # Within 3% of current price
                    entry_points['long'].append({
                        'type': 'bullish_order_block',
                        'entry_price': block['low'] * 1.002,
                        'stop_loss': block['low'] * 0.995,
                        'take_profit_1': current_price * 1.025,
                        'take_profit_2': current_price * 1.05,
                        'confidence': min(95, 75 + block['strength']/10),
                        'risk_reward': 5.0
                    })

            for block in bearish_blocks[:2]:  # Top 2 bearish order blocks
                distance = abs(current_price - block['price']) / current_price * 100
                if distance < 3:  # Within 3% of current price
                    entry_points['short'].append({
                        'type': 'bearish_order_block',
                        'entry_price': block['high'] * 0.998,
                        'stop_loss': block['high'] * 1.005,
                        'take_profit_1': current_price * 0.975,
                        'take_profit_2': current_price * 0.95,
                        'confidence': min(95, 75 + block['strength']/10),
                        'risk_reward': 5.0
                    })

            return entry_points

        except Exception as e:
            print(f"⚠️ Entry/Exit calculation error: {e}")
            return {'long': [], 'short': []}

    def _calculate_snd_score(self, current_price, support_resistance, order_blocks, volume_analysis, market_structure):
        """Calculate overall Supply and Demand score (0-100)"""
        try:
            score = 50  # Base neutral score
            factors = []

            # 1. Support/Resistance proximity (±20 points)
            supports = support_resistance.get('support', [])
            resistances = support_resistance.get('resistance', [])

            nearest_support = min(supports, key=lambda x: abs(x['price'] - current_price)) if supports else None
            nearest_resistance = min(resistances, key=lambda x: abs(x['price'] - current_price)) if resistances else None

            if nearest_support:
                support_distance = abs(current_price - nearest_support['price']) / current_price * 100
                if support_distance < 2:  # Very close to support
                    score += 15
                    factors.append("Very close to strong support")
                elif support_distance < 5:
                    score += 8
                    factors.append("Near support level")

            if nearest_resistance:
                resistance_distance = abs(current_price - nearest_resistance['price']) / current_price * 100
                if resistance_distance < 2:  # Very close to resistance
                    score -= 15
                    factors.append("Very close to strong resistance")
                elif resistance_distance < 5:
                    score -= 8
                    factors.append("Near resistance level")

            # 2. Volume pressure (±15 points)
            pressure_type = volume_analysis.get('pressure_type', 'neutral')
            pressure_strength = volume_analysis.get('strength', 50)

            if pressure_type == 'buying_pressure':
                score += (pressure_strength - 50) / 50 * 15
                factors.append(f"Strong buying pressure ({pressure_strength:.0f}%)")
            elif pressure_type == 'selling_pressure':
                score -= (pressure_strength - 50) / 50 * 15
                factors.append(f"Strong selling pressure ({pressure_strength:.0f}%)")

            # 3. Market structure (±10 points)
            structure_trend = market_structure.get('trend', 'sideways')
            structure_strength = market_structure.get('strength', 50)

            if structure_trend == 'uptrend':
                score += structure_strength / 50 * 10
                factors.append("Bullish market structure")
            elif structure_trend == 'downtrend':
                score -= structure_strength / 50 * 10
                factors.append("Bearish market structure")

            # 4. Order blocks (±10 points)
            bullish_blocks = order_blocks.get('bullish', [])
            bearish_blocks = order_blocks.get('bearish', [])

            if bullish_blocks:
                avg_bullish_strength = sum(b['strength'] for b in bullish_blocks) / len(bullish_blocks)
                score += min(10, avg_bullish_strength / 20)
                factors.append("Strong bullish order blocks present")

            if bearish_blocks:
                avg_bearish_strength = sum(b['strength'] for b in bearish_blocks) / len(bearish_blocks)
                score -= min(10, avg_bearish_strength / 20)
                factors.append("Strong bearish order blocks present")

            # Ensure score stays within bounds
            score = max(0, min(100, score))

            # Determine bias and recommendation
            if score >= 70:
                bias = "Strong Demand"
                recommendation = "STRONG BUY"
                confidence = "High"
            elif score >= 60:
                bias = "Moderate Demand"
                recommendation = "BUY"
                confidence = "Medium"
            elif score <= 30:
                bias = "Strong Supply"
                recommendation = "STRONG SELL"
                confidence = "High"
            elif score <= 40:
                bias = "Moderate Supply"
                recommendation = "SELL"
                confidence = "Medium"
            else:
                bias = "Balanced"
                recommendation = "HOLD"
                confidence = "Low"

            return {
                'score': round(score, 1),
                'bias': bias,
                'recommendation': recommendation,
                'confidence': confidence,
                'factors': factors
            }

        except Exception as e:
            print(f"⚠️ SnD score calculation error: {e}")
            return {
                'score': 50,
                'bias': 'Balanced',
                'recommendation': 'HOLD',
                'confidence': 'Low',
                'factors': ['Error in calculation']
            }

    def _generate_snd_signals(self, current_price, support_resistance, order_blocks, snd_score, entry_points):
        """Generate trading signals based on SnD analysis"""
        try:
            signals = []
            score = snd_score.get('score', 50)

            # Generate signals based on score and entry points
            long_entries = entry_points.get('long', [])
            short_entries = entry_points.get('short', [])

            # Strong buy signals
            if score >= 70 and long_entries:
                best_long = max(long_entries, key=lambda x: x['confidence'])
                signals.append({
                    'type': 'BUY',
                    'strength': 'STRONG',
                    'confidence': best_long['confidence'],
                    'entry_price': best_long['entry_price'],
                    'stop_loss': best_long['stop_loss'],
                    'take_profit_1': best_long['take_profit_1'],
                    'take_profit_2': best_long['take_profit_2'],
                    'risk_reward': best_long['risk_reward'],
                    'reason': f"Strong demand zone + {best_long['type']}",
                    'setup_type': best_long['type']
                })

            # Strong sell signals
            elif score <= 30 and short_entries:
                best_short = max(short_entries, key=lambda x: x['confidence'])
                signals.append({
                    'type': 'SELL',
                    'strength': 'STRONG',
                    'confidence': best_short['confidence'],
                    'entry_price': best_short['entry_price'],
                    'stop_loss': best_short['stop_loss'],
                    'take_profit_1': best_short['take_profit_1'],
                    'take_profit_2': best_short['take_profit_2'],
                    'risk_reward': best_short['risk_reward'],
                    'reason': f"Strong supply zone + {best_short['type']}",
                    'setup_type': best_short['type']
                })

            # Moderate signals
            elif 60 <= score < 70 and long_entries:
                best_long = max(long_entries, key=lambda x: x['confidence'])
                signals.append({
                    'type': 'BUY',
                    'strength': 'MODERATE',
                    'confidence': best_long['confidence'] * 0.8,  # Reduce confidence
                    'entry_price': best_long['entry_price'],
                    'stop_loss': best_long['stop_loss'],
                    'take_profit_1': best_long['take_profit_1'],
                    'take_profit_2': best_long['take_profit_2'],
                    'risk_reward': best_long['risk_reward'],
                    'reason': f"Moderate demand + {best_long['type']}",
                    'setup_type': best_long['type']
                })

            elif 30 < score <= 40 and short_entries:
                best_short = max(short_entries, key=lambda x: x['confidence'])
                signals.append({
                    'type': 'SELL',
                    'strength': 'MODERATE',  
                    'confidence': best_short['confidence'] * 0.8,
                    'entry_price': best_short['entry_price'],
                    'stop_loss': best_short['stop_loss'],
                    'take_profit_1': best_short['take_profit_1'],
                    'take_profit_2': best_short['take_profit_2'],
                    'risk_reward': best_short['risk_reward'],
                    'reason': f"Moderate supply + {best_short['type']}",
                    'setup_type': best_short['type']
                })

            return signals

        except Exception as e:
            print(f"⚠️ Signal generation error: {e}")
            return []

    def _simplified_snd_analysis(self, symbol, current_price):
        """Simplified SnD analysis when candlestick data is unavailable"""
        try:
            # Get additional price data for basic analysis
            futures_price_data = self.get_binance_futures_price(symbol)

            # Basic support/resistance calculation
            support_price = current_price * 0.95  # 5% below current
            resistance_price = current_price * 1.05  # 5% above current

            # Basic analysis based on futures data if available
            score = 50
            factors = ["Using simplified analysis - limited data available"]
            bias = "Balanced"
            recommendation = "HOLD"

            if 'error' not in futures_price_data:
                change_24h = futures_price_data.get('change_24h', 0)
                if change_24h > 5:
                    score = 65
                    bias = "Moderate Demand"
                    recommendation = "BUY"
                    factors.append(f"Strong positive momentum (+{change_24h:.1f}%)")
                elif change_24h < -5:
                    score = 35
                    bias = "Moderate Supply"
                    recommendation = "SELL"
                    factors.append(f"Strong negative momentum ({change_24h:.1f}%)")

            return {
                'symbol': symbol,
                'current_price': current_price,
                'support_levels': [{'price': support_price, 'strength': 100, 'type': 'calculated'}],
                'resistance_levels': [{'price': resistance_price, 'strength': 100, 'type': 'calculated'}],
                'snd_score': {
                    'score': score,
                    'bias': bias,
                    'recommendation': recommendation,
                    'confidence': 'Medium',
                    'factors': factors
                },
                'signals': [],
                'analysis_successful': True,
                'source': 'simplified_snd_analysis',
                'note': 'Basic analysis due to limited data availability'
            }

        except Exception as e:
            print(f"❌ Simplified SnD analysis error: {e}")
            return {
                'error': f"Simplified SnD analysis failed: {str(e)}",
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