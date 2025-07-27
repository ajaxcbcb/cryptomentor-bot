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
        """Get real-time price from Binance Spot API with enhanced USDT validation and deployment optimization"""
        try:
            # Enhanced symbol validation and normalization
            original_symbol = symbol
            if not symbol or not isinstance(symbol, str) or len(symbol.strip()) == 0:
                raise ValueError(f"Invalid symbol provided: {symbol}")
            
            # Clean and normalize symbol
            symbol = symbol.strip().upper()
            
            # Ensure USDT pair - MANDATORY for price display
            if not symbol.endswith('USDT'):
                symbol = symbol + 'USDT'
            
            # Validate USDT requirement for display
            if 'USDT' not in symbol:
                print(f"❌ Symbol {symbol} doesn't contain USDT - skipping for price display")
                return {
                    'error': f'Symbol {symbol} must contain USDT for price display',
                    'symbol': symbol,
                    'api_call_successful': False,
                    'skip_reason': 'non_usdt_pair'
                }

            print(f"🔄 ENHANCED Processing: {original_symbol} -> {symbol} ✅")

            # Comprehensive deployment detection
            is_deployment = (
                os.getenv('REPLIT_DEPLOYMENT') == '1' or 
                os.getenv('REPL_DEPLOYMENT') == '1' or
                os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
                bool(os.getenv('REPL_SLUG')) or
                bool(os.getenv('REPL_DB_URL')) or
                bool(os.getenv('REPL_OWNER')) or
                os.path.exists('/tmp/repl_deployment_flag')
            )

            print(f"🚀 Environment: {'🌍 DEPLOYMENT' if is_deployment else '🛠️ DEVELOPMENT'}")
            print(f"📡 Fetching Binance SPOT price for {symbol} (USDT validated)")

            # Enhanced headers for deployment stability
            headers = {
                'User-Agent': 'CryptoMentorAI/3.0-Binance-Exclusive',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache' if is_deployment else 'no-store'
            }

            # Force real-time data in deployment
            params = {'symbol': symbol}
            if is_deployment or force_refresh:
                import time
                params['_timestamp'] = int(time.time() * 1000)  # Force fresh data

            # Define endpoints with priority
            endpoints_to_try = [
                {
                    'url': f"{self.binance_spot_url}/ticker/24hr",
                    'type': 'full_ticker',
                    'timeout': 25 if is_deployment else 12
                },
                {
                    'url': f"{self.binance_spot_url}/ticker/price",
                    'type': 'simple_price',
                    'timeout': 20 if is_deployment else 10
                }
            ]

            last_error = None
            raw_response_debug = None

            for attempt, endpoint_config in enumerate(endpoints_to_try, 1):
                endpoint_url = endpoint_config['url']
                endpoint_type = endpoint_config['type']
                timeout = endpoint_config['timeout']

                try:
                    print(f"📡 Attempt {attempt}/{len(endpoints_to_try)}: {endpoint_type} -> {endpoint_url}")
                    
                    # Make API request
                    response = requests.get(
                        endpoint_url,
                        params=params,
                        timeout=timeout,
                        headers=headers
                    )
                    
                    print(f"📊 Response Status: {response.status_code}")
                    print(f"📊 Response Headers: {dict(response.headers)}")
                    
                    # Store raw response for debugging
                    try:
                        raw_response_debug = response.text[:500]  # First 500 chars
                        print(f"📊 Raw Response (first 500 chars): {raw_response_debug}")
                    except:
                        pass

                    # Check HTTP status
                    if response.status_code != 200:
                        error_msg = f"HTTP {response.status_code}"
                        try:
                            error_data = response.json()
                            error_msg = f"HTTP {response.status_code}: {error_data.get('msg', 'Unknown error')}"
                        except:
                            pass
                        print(f"❌ HTTP Error: {error_msg}")
                        last_error = error_msg
                        continue

                    # Parse JSON response
                    try:
                        data = response.json()
                        print(f"📊 Parsed JSON successfully, type: {type(data)}")
                        if isinstance(data, dict):
                            print(f"📊 JSON keys: {list(data.keys())}")
                    except Exception as json_error:
                        print(f"❌ JSON parsing failed: {json_error}")
                        last_error = f"JSON parsing error: {json_error}"
                        continue

                    # Validate basic response structure
                    if not data or not isinstance(data, dict):
                        print(f"❌ Invalid response structure: {type(data)}")
                        last_error = "Invalid response structure"
                        continue

                    # Process different endpoint types with enhanced validation
                    if endpoint_type == 'full_ticker':
                        print("🔍 Processing FULL TICKER response with enhanced validation...")
                        
                        # Enhanced price field detection with priority
                        price_field = None
                        price_field_priority = ['lastPrice', 'price', 'close', 'closePrice']
                        
                        for field in price_field_priority:
                            if field in data and data[field] is not None:
                                price_field = field
                                print(f"✅ Found price field: {field}")
                                break
                        
                        if not price_field:
                            available_fields = [k for k, v in data.items() if v is not None]
                            print(f"❌ NO PRICE FIELD found in ticker response!")
                            print(f"📊 Available non-null fields: {available_fields}")
                            last_error = f"No price field in ticker response. Available: {available_fields}"
                            continue

                        # Enhanced price extraction with comprehensive validation
                        try:
                            raw_price = data[price_field]
                            print(f"📊 Raw {price_field} value: '{raw_price}' (type: {type(raw_price)})")
                            
                            # Handle different price formats
                            if raw_price is None:
                                print(f"❌ Price field {price_field} is None")
                                last_error = f"Price field {price_field} is None"
                                continue
                            elif isinstance(raw_price, str):
                                # Clean string and convert
                                cleaned_price = raw_price.strip().replace(',', '')
                                if not cleaned_price or cleaned_price == '0' or cleaned_price == '0.0':
                                    print(f"❌ Empty or zero price string: '{cleaned_price}'")
                                    last_error = f"Empty or zero price string: '{cleaned_price}'"
                                    continue
                                price = float(cleaned_price)
                            elif isinstance(raw_price, (int, float)):
                                price = float(raw_price)
                            else:
                                print(f"❌ Unexpected price type: {type(raw_price)}")
                                last_error = f"Unexpected price type: {type(raw_price)}"
                                continue
                            
                            print(f"📊 Successfully parsed price: {price}")
                            
                        except (ValueError, TypeError, AttributeError) as price_error:
                            print(f"❌ PRICE PARSING FAILED: {price_error}")
                            print(f"📊 Raw price debug: {repr(raw_price)}")
                            last_error = f"Price parsing error: {price_error}"
                            continue

                        # Strict price validation with detailed logging
                        if not isinstance(price, (int, float)):
                            print(f"❌ Price is not numeric after parsing: {price} (type: {type(price)})")
                            last_error = f"Price not numeric: {price}"
                            continue
                        elif price <= 0:
                            print(f"❌ Price is zero or negative: {price}")
                            last_error = f"Invalid price (<=0): {price}"
                            continue
                        elif price > 1000000000:  # Sanity check for extremely high prices
                            print(f"❌ Price suspiciously high: {price}")
                            last_error = f"Price too high: {price}"
                            continue
                        elif str(price) == 'nan' or str(price) == 'inf':
                            print(f"❌ Price is NaN or Inf: {price}")
                            last_error = f"Price is NaN/Inf: {price}"
                            continue
                        
                        print(f"✅ PRICE VALIDATION PASSED: {symbol} = ${price:,.8f}")

                        # Extract other fields with safe fallbacks
                        try:
                            change_24h = float(data.get('priceChangePercent', 0))
                            high_24h = float(data.get('highPrice', price))
                            low_24h = float(data.get('lowPrice', price))
                            volume_24h = float(data.get('volume', 0))
                            quote_volume_24h = float(data.get('quoteVolume', 0))
                            open_price = float(data.get('openPrice', price))
                            price_change = float(data.get('priceChange', 0))
                            count = int(data.get('count', 0))
                        except (ValueError, TypeError) as field_error:
                            print(f"⚠️ Field parsing warning: {field_error}")
                            # Use defaults for non-critical fields
                            change_24h = 0
                            high_24h = price
                            low_24h = price
                            volume_24h = 0
                            quote_volume_24h = 0
                            open_price = price
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
                            'close_price': price,
                            'price_change': price_change,
                            'count': count,
                            'first_id': data.get('firstId', 0),
                            'last_id': data.get('lastId', 0),
                            'open_time': data.get('openTime', 0),
                            'close_time': data.get('closeTime', 0),
                            'source': 'binance_spot_24hr',
                            'api_call_successful': True,
                            'endpoint_used': endpoint_url
                        }

                    elif endpoint_type == 'simple_price':
                        print("🔍 Processing SIMPLE PRICE response with enhanced validation...")
                        
                        # Enhanced price field validation
                        if 'price' not in data:
                            available_fields = list(data.keys())
                            print(f"❌ NO 'price' field in simple response!")
                            print(f"📊 Available fields: {available_fields}")
                            last_error = f"No 'price' field in simple response. Available: {available_fields}"
                            continue

                        # Enhanced price extraction for simple endpoint
                        try:
                            raw_price = data['price']
                            print(f"📊 Raw SIMPLE price: '{raw_price}' (type: {type(raw_price)})")
                            
                            # Comprehensive validation for simple price
                            if raw_price is None:
                                print(f"❌ Simple price is None")
                                last_error = "Simple price is None"
                                continue
                            elif isinstance(raw_price, str):
                                # Clean and validate string
                                cleaned_price = raw_price.strip().replace(',', '')
                                if not cleaned_price or cleaned_price == '0' or cleaned_price == '0.0':
                                    print(f"❌ Empty or zero simple price: '{cleaned_price}'")
                                    last_error = f"Empty or zero simple price: '{cleaned_price}'"
                                    continue
                                price = float(cleaned_price)
                            elif isinstance(raw_price, (int, float)):
                                price = float(raw_price)
                            else:
                                print(f"❌ Unexpected simple price type: {type(raw_price)}")
                                last_error = f"Unexpected simple price type: {type(raw_price)}"
                                continue
                            
                            print(f"📊 Successfully parsed simple price: {price}")
                            
                        except (ValueError, TypeError, AttributeError) as price_error:
                            print(f"❌ SIMPLE PRICE PARSING FAILED: {price_error}")
                            print(f"📊 Raw simple price debug: {repr(raw_price)}")
                            last_error = f"Simple price parsing error: {price_error}"
                            continue

                        # Strict simple price validation
                        if not isinstance(price, (int, float)):
                            print(f"❌ Simple price not numeric: {price} (type: {type(price)})")
                            last_error = f"Simple price not numeric: {price}"
                            continue
                        elif price <= 0:
                            print(f"❌ Simple price is zero or negative: {price}")
                            last_error = f"Invalid simple price (<=0): {price}"
                            continue
                        elif price > 1000000000:
                            print(f"❌ Simple price too high: {price}")
                            last_error = f"Simple price too high: {price}"
                            continue
                        elif str(price) == 'nan' or str(price) == 'inf':
                            print(f"❌ Simple price is NaN/Inf: {price}")
                            last_error = f"Simple price is NaN/Inf: {price}"
                            continue
                        
                        print(f"✅ SIMPLE PRICE VALIDATION PASSED: {symbol} = ${price:,.8f}")

                        result = {
                            'symbol': symbol,
                            'price': price,
                            'change_24h': 0,  # Not available in simple endpoint
                            'high_24h': 0,
                            'low_24h': 0,
                            'volume_24h': 0,
                            'quote_volume_24h': 0,
                            'open_price': 0,
                            'close_price': price,
                            'price_change': 0,
                            'count': 0,
                            'source': 'binance_spot_simple',
                            'api_call_successful': True,
                            'endpoint_used': endpoint_url
                        }

                    # Final validation before returning successful result
                    if not isinstance(price, (int, float)) or price <= 0:
                        print(f"❌ FINAL VALIDATION FAILED: price={price}, type={type(price)}")
                        last_error = f"Final validation failed: invalid price {price}"
                        continue
                    
                    # Successful result with enhanced logging
                    formatted_price = f"${price:,.8f}" if price < 1 else f"${price:,.4f}"
                    print(f"🎯 SUCCESS: {symbol} = {formatted_price} from {endpoint_type}")
                    print(f"📊 Source: {result.get('source')} | Endpoint: {result.get('endpoint_used')}")
                    print(f"🚀 Environment: {'DEPLOYMENT' if is_deployment else 'DEVELOPMENT'}")
                    print(f"✅ USDT Validation: PASSED | Price: {price} | API Call: SUCCESS")
                    
                    # Add deployment-specific metadata
                    result.update({
                        'deployment_mode': is_deployment,
                        'usdt_validated': True,
                        'price_formatted': formatted_price,
                        'validation_passed': True,
                        'price_valid': price > 0,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return result

                except requests.exceptions.Timeout as e:
                    error_msg = f"Timeout ({timeout}s) for {endpoint_type}: {str(e)}"
                    print(f"⏰ {error_msg}")
                    last_error = error_msg
                    continue
                except requests.exceptions.ConnectionError as e:
                    error_msg = f"Connection error for {endpoint_type}: {str(e)}"
                    print(f"🔌 {error_msg}")
                    last_error = error_msg
                    continue
                except requests.exceptions.RequestException as e:
                    error_msg = f"Request error for {endpoint_type}: {str(e)}"
                    print(f"⚠️ {error_msg}")
                    last_error = error_msg
                    continue
                except Exception as e:
                    error_msg = f"Unexpected error for {endpoint_type}: {str(e)}"
                    print(f"❌ {error_msg}")
                    last_error = error_msg
                    continue

            # All Binance endpoints failed - comprehensive error reporting
            final_error = f"🚨 ALL BINANCE ENDPOINTS FAILED for {symbol}"
            print(f"❌ {final_error}")
            print(f"📊 Last error: {last_error}")
            print(f"🌍 Environment: {'DEPLOYMENT' if is_deployment else 'DEVELOPMENT'}")
            print(f"🔍 Endpoints tried: {len(endpoints_to_try)}")
            
            if raw_response_debug:
                print(f"📊 Last raw response sample: {raw_response_debug}")
            
            # In deployment, return structured error without exception
            if is_deployment:
                print(f"🚀 DEPLOYMENT MODE: Returning structured error for {symbol}")
                return {
                    'error': f'Binance APIs failed for {symbol} in deployment',
                    'symbol': symbol,
                    'api_call_successful': False,
                    'error_type': 'deployment_binance_failure',
                    'deployment_mode': True,
                    'usdt_validated': 'USDT' in symbol,
                    'last_error': last_error,
                    'endpoints_tried': len(endpoints_to_try),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise Exception(final_error)

        except Exception as e:
            error_msg = f"🚨 COMPLETE BINANCE API FAILURE for {symbol}: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"🔍 Original symbol: {original_symbol}")
            print(f"🔍 Normalized symbol: {symbol}")
            print(f"🌍 Deployment mode: {is_deployment}")
            
            return {
                'error': error_msg,
                'symbol': symbol,
                'api_call_successful': False,
                'error_type': 'binance_complete_failure',
                'deployment_mode': is_deployment,
                'usdt_validated': 'USDT' in symbol if symbol else False,
                'debug_info': {
                    'original_symbol': original_symbol,
                    'normalized_symbol': symbol,
                    'deployment_mode': is_deployment,
                    'last_error': last_error if 'last_error' in locals() else 'Unknown error',
                    'exception_type': type(e).__name__,
                    'exception_message': str(e)
                },
                'timestamp': datetime.now().isoformat()
            }

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
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Check deployment mode
            is_deployment = (
                os.getenv('REPLIT_DEPLOYMENT') == '1' or 
                os.getenv('REPL_DEPLOYMENT') == '1' or
                bool(os.getenv('REPL_SLUG'))
            )

            print(f"🔄 Fetching Binance Futures price for {symbol} (Deployment: {is_deployment})")

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

            # Check response status
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = f"HTTP {response.status_code}: {error_data.get('msg', 'Unknown error')}"
                except:
                    pass
                print(f"❌ Binance Futures API Error: {error_msg}")
                return {'error': f"Futures API error: {error_msg}"}

            response.raise_for_status()
            data = response.json()

            # Validate response data
            if not data or not isinstance(data, dict):
                print(f"❌ Invalid Binance Futures API response format for {symbol}")
                return {'error': 'Invalid response format'}

            # Validate required fields
            required_fields = ['lastPrice', 'priceChangePercent', 'highPrice', 'lowPrice', 'volume', 'quoteVolume']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing fields in Futures ticker response: {missing_fields}")
                return {'error': f'Missing required fields: {missing_fields}'}

            price = float(data['lastPrice'])
            
            # Validate price is not zero or negative
            if price <= 0:
                print(f"❌ Invalid futures price received from Binance: {price}")
                return {'error': f'Invalid price: {price}'}

            result = {
                'symbol': symbol,
                'price': price,
                'change_24h': float(data['priceChangePercent']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'volume_24h': float(data['volume']),
                'quote_volume_24h': float(data['quoteVolume']),
                'open_price': float(data['openPrice']),
                'weighted_avg_price': float(data['weightedAvgPrice']),
                'price_change': float(data['priceChange']),
                'count': int(data['count']),
                'open_time': data['openTime'],
                'close_time': data['closeTime'],
                'source': 'binance_futures',
                'api_call_successful': True
            }

            print(f"✅ Binance Futures success for {symbol}: ${price:,.4f}")
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

    # === PRICE METHODS (BINANCE ONLY) ===

    def get_price(self, symbol, force_refresh=False):
        """Get price from Binance APIs only"""
        # Check if in deployment mode
        is_deployment = (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
            os.path.exists('/tmp/repl_deployment_flag') or
            bool(os.getenv('REPL_SLUG')) or
            bool(os.getenv('REPL_OWNER'))
        )

        # Always force refresh in deployment
        if is_deployment:
            force_refresh = True

        return self.get_multi_api_price(symbol, force_refresh)

    def get_multi_api_price(self, symbol, force_refresh=False):
        """Get price from Binance APIs only - centralized to Binance with enhanced validation"""
        price_sources = {}
        original_symbol = symbol

        # Enhanced deployment environment check
        is_deployment = (
            os.getenv('REPLIT_DEPLOYMENT') == '1' or 
            os.getenv('REPL_DEPLOYMENT') == '1' or
            os.getenv('REPLIT_ENVIRONMENT') == 'deployment' or
            os.path.exists('/tmp/repl_deployment_flag') or
            bool(os.getenv('REPL_SLUG')) or
            bool(os.getenv('REPL_DB_URL')) or
            bool(os.getenv('REPL_OWNER'))
        )

        # Validate and normalize symbol
        if not symbol or not isinstance(symbol, str):
            return {
                'error': f'Invalid symbol format: {symbol}',
                'symbol': original_symbol,
                'api_call_successful': False
            }

        # Ensure USDT pair
        normalized_symbol = symbol.upper()
        if not normalized_symbol.endswith('USDT'):
            normalized_symbol = normalized_symbol + 'USDT'

        print(f"🔄 Symbol normalization: {original_symbol} -> {normalized_symbol}")

        # ALWAYS force refresh in deployment for real-time data
        if is_deployment:
            force_refresh = True

        # Enhanced logging for deployment mode
        mode = "DEPLOYMENT REAL-TIME" if is_deployment else "STANDARD"
        print(f"🔄 {mode} MODE: Fetching price data for {normalized_symbol} from Binance (Force: {force_refresh})")

        def validate_price_data(data, source_name):
            """Enhanced validation for price data"""
            if not data or not isinstance(data, dict):
                print(f"❌ {source_name} returned invalid data structure")
                return False
                
            if 'error' in data:
                print(f"❌ {source_name} returned error: {data['error']}")
                return False
            
            # Check for required symbol match
            returned_symbol = data.get('symbol', '')
            if returned_symbol and returned_symbol != normalized_symbol:
                print(f"⚠️ {source_name} symbol mismatch: expected {normalized_symbol}, got {returned_symbol}")
                # Don't fail on symbol mismatch, just warn
            
            price = data.get('price', 0)
            
            # Enhanced price validation
            if not isinstance(price, (int, float)):
                print(f"❌ {source_name} price not numeric: {price} (type: {type(price)})")
                return False
                
            if price <= 0:
                print(f"❌ {source_name} price is zero or negative: {price}")
                return False
                
            if price > 1000000000:  # Sanity check for extremely high prices
                print(f"❌ {source_name} price suspiciously high: {price}")
                return False
            
            if not data.get('api_call_successful', True):
                print(f"❌ {source_name} API call marked as unsuccessful")
                return False
                
            print(f"✅ {source_name} validation passed: {normalized_symbol} = ${price:,.6f}")
            return True

        # In deployment mode, prioritize reliability
        if is_deployment:
            print("🚀 DEPLOYMENT MODE: Enhanced reliability mode activated")
            
            # 1. Try Binance Spot API first in deployment (most reliable for basic price)
            try:
                print("📡 DEPLOYMENT: Trying Binance Spot API...")
                binance_data = self.get_binance_price(normalized_symbol, force_refresh=True)
                if validate_price_data(binance_data, "Binance Spot"):
                    price_sources['binance'] = binance_data
                    price_str = f"${binance_data.get('price', 0):,.6f}"
                    print(f"🎯 DEPLOYMENT SUCCESS: {normalized_symbol} = {price_str} ✅ (Binance Spot)")
                    return self._combine_binance_price_data(normalized_symbol, price_sources)
                else:
                    print("❌ Binance Spot validation failed in deployment")
            except Exception as e:
                print(f"💥 Binance Spot API exception in deployment for {normalized_symbol}: {e}")

            # 2. Try Binance Futures API as backup in deployment
            try:
                print("📡 DEPLOYMENT: Trying Binance Futures API...")
                futures_data = self.get_binance_futures_price(normalized_symbol)
                if validate_price_data(futures_data, "Binance Futures"):
                    price_sources['binance_futures'] = futures_data
                    price_str = f"${futures_data.get('price', 0):,.6f}"
                    print(f"🎯 DEPLOYMENT SUCCESS: {normalized_symbol} = {price_str} ✅ (Binance Futures)")
                    return self._combine_binance_price_data(normalized_symbol, price_sources)
                else:
                    print("❌ Binance Futures validation failed in deployment")
            except Exception as e:
                print(f"💥 Binance Futures API exception in deployment for {normalized_symbol}: {e}")

            # In deployment, return detailed error if all Binance APIs fail
            error_msg = f'All Binance APIs failed for {normalized_symbol} in deployment mode'
            print(f"🚨 DEPLOYMENT COMPLETE FAILURE: {error_msg}")
            return {
                'error': error_msg,
                'symbol': normalized_symbol,
                'original_symbol': original_symbol,
                'deployment_mode': True,
                'all_apis_failed': True,
                'api_call_successful': False,
                'debug_info': {
                    'normalized_symbol': normalized_symbol,
                    'environment_vars': {
                        'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT'),
                        'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT'),
                        'REPL_SLUG': bool(os.getenv('REPL_SLUG'))
                    }
                }
            }

        else:
            # Development mode - multiple attempts with patience
            max_attempts = 3
            
            print(f"🔧 DEVELOPMENT MODE: Will try {max_attempts} attempts for {normalized_symbol}")

            for attempt in range(max_attempts):
                if attempt > 0:
                    print(f"🔄 Retry attempt {attempt + 1}/{max_attempts} for {normalized_symbol}")
                    import time
                    time.sleep(2)  # Delay between attempts

                # 1. Try Binance Spot API first in development
                try:
                    print(f"📡 Development attempt {attempt + 1}: Trying Binance Spot API...")
                    binance_data = self.get_binance_price(normalized_symbol, force_refresh=True)
                    if validate_price_data(binance_data, "Binance Spot"):
                        price_sources['binance'] = binance_data
                        price_str = f"${binance_data.get('price', 0):,.6f}"
                        print(f"🎯 DEV SUCCESS: {normalized_symbol} = {price_str} ✅ (Binance Spot)")
                        return self._combine_binance_price_data(normalized_symbol, price_sources)
                except Exception as e:
                    print(f"💥 Binance Spot API exception in dev for {normalized_symbol}: {e}")

                # 2. Try Binance Futures API as backup in development
                try:
                    print(f"📡 Development attempt {attempt + 1}: Trying Binance Futures API...")
                    futures_data = self.get_binance_futures_price(normalized_symbol)
                    if validate_price_data(futures_data, "Binance Futures"):
                        price_sources['binance_futures'] = futures_data
                        price_str = f"${futures_data.get('price', 0):,.6f}"
                        print(f"🎯 DEV SUCCESS: {normalized_symbol} = {price_str} ✅ (Binance Futures)")
                        return self._combine_binance_price_data(normalized_symbol, price_sources)
                except Exception as e:
                    print(f"💥 Binance Futures API exception in dev for {normalized_symbol}: {e}")

            # Development mode fallback
            if price_sources:
                print(f"⚠️ Using partial data from {len(price_sources)} source(s)")
                return self._combine_binance_price_data(normalized_symbol, price_sources)
            else:
                error_msg = f"All Binance APIs failed after {max_attempts} attempts for {normalized_symbol}"
                print(f"🚨 DEVELOPMENT COMPLETE FAILURE: {error_msg}")
                return self._fallback_price(normalized_symbol, error_msg)

    def _combine_binance_price_data(self, symbol, price_sources):
        """Combine price data from Binance sources with enhanced validation"""
        if not price_sources:
            return {
                'error': 'No valid price sources available',
                'symbol': symbol,
                'api_call_successful': False
            }

        combined_data = {
            'symbol': symbol.upper(),
            'sources_used': list(price_sources.keys()),
            'data_quality': 'excellent',  # Binance data quality
            'api_call_successful': True,
            'timestamp': datetime.now().isoformat()
        }

        # Priority: Binance Spot, then Binance Futures
        primary_source = None
        primary_data = None

        if 'binance' in price_sources:
            primary_source = 'binance_spot'
            primary_data = price_sources['binance']
        elif 'binance_futures' in price_sources:
            primary_source = 'binance_futures'
            primary_data = price_sources['binance_futures']

        if primary_data:
            # Validate primary price before combining
            primary_price = primary_data.get('price', 0)
            if primary_price <= 0:
                return {
                    'error': f'Invalid primary price from {primary_source}: {primary_price}',
                    'symbol': symbol,
                    'api_call_successful': False
                }

            # Combine data with safe defaults
            combined_data.update({
                'price': primary_price,
                'change_24h': primary_data.get('change_24h', 0),
                'volume_24h': primary_data.get('volume_24h', 0),
                'high_24h': primary_data.get('high_24h', primary_price),
                'low_24h': primary_data.get('low_24h', primary_price),
                'open_price': primary_data.get('open_price', primary_price),
                'close_price': primary_data.get('close_price', primary_price),
                'price_change': primary_data.get('price_change', 0),
                'quote_volume_24h': primary_data.get('quote_volume_24h', 0),
                'count': primary_data.get('count', 0),
                'primary_source': primary_source,
                'source_endpoint': primary_data.get('endpoint_used', 'unknown')
            })

            # Add source-specific fields
            if primary_source == 'binance_futures':
                combined_data['weighted_avg_price'] = primary_data.get('weighted_avg_price', primary_price)
            
            # Add metadata
            combined_data['source_data'] = {
                'original_response': primary_data.get('source', 'unknown'),
                'endpoint_type': primary_data.get('source', 'unknown')
            }

        # Add cross-validation if both sources available
        if 'binance' in price_sources and 'binance_futures' in price_sources:
            spot_price = price_sources['binance'].get('price', 0)
            futures_price = price_sources['binance_futures'].get('price', 0)
            
            if spot_price > 0 and futures_price > 0:
                spread = abs(spot_price - futures_price)
                spread_percentage = (spread / spot_price) * 100
                
                combined_data.update({
                    'dual_source': True,
                    'spot_price': spot_price,
                    'futures_price': futures_price,
                    'spot_futures_spread': spread,
                    'spread_percentage': spread_percentage,
                    'cross_validation': 'passed' if spread_percentage < 5 else 'warning'
                })

                # Use spot price as primary if spread is reasonable
                if spread_percentage < 1:  # Less than 1% difference
                    combined_data['price'] = spot_price
                    combined_data['primary_source'] = 'binance_spot_validated'

        # Final validation
        final_price = combined_data.get('price', 0)
        if final_price <= 0:
            return {
                'error': f'Final combined price invalid: {final_price}',
                'symbol': symbol,
                'debug_sources': price_sources,
                'api_call_successful': False
            }

        print(f"✅ Combined data for {symbol}: ${final_price:,.6f} from {primary_source}")
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

    def _validate_binance_price_response(self, data, source_name, symbol):
        """Comprehensive price validation helper for Binance responses"""
        try:
            print(f"🔍 Validating {source_name} response for {symbol}...")
            
            # Check data structure
            if not data or not isinstance(data, dict):
                print(f"❌ {source_name}: Invalid data structure")
                return None, f"Invalid data structure from {source_name}"
            
            # Check for API errors
            if 'error' in data:
                print(f"❌ {source_name}: API error - {data['error']}")
                return None, f"API error from {source_name}: {data['error']}"
            
            # Find price field with priority
            price_fields = ['lastPrice', 'price', 'close', 'closePrice']
            price_value = None
            price_field = None
            
            for field in price_fields:
                if field in data and data[field] is not None:
                    price_value = data[field]
                    price_field = field
                    print(f"✅ {source_name}: Found price in '{field}' = {price_value}")
                    break
            
            if price_value is None:
                available = [k for k, v in data.items() if v is not None]
                print(f"❌ {source_name}: No price field found. Available: {available}")
                return None, f"No price field in {source_name} response"
            
            # Parse and validate price
            try:
                if isinstance(price_value, str):
                    cleaned = price_value.strip().replace(',', '')
                    if not cleaned or cleaned in ['0', '0.0', '0.00']:
                        print(f"❌ {source_name}: Zero or empty price string")
                        return None, f"Zero price from {source_name}"
                    price = float(cleaned)
                elif isinstance(price_value, (int, float)):
                    price = float(price_value)
                else:
                    print(f"❌ {source_name}: Unexpected price type {type(price_value)}")
                    return None, f"Invalid price type from {source_name}"
                
                # Final validation
                if not isinstance(price, (int, float)) or price <= 0:
                    print(f"❌ {source_name}: Invalid price value {price}")
                    return None, f"Invalid price value from {source_name}: {price}"
                
                if str(price) in ['nan', 'inf', '-inf']:
                    print(f"❌ {source_name}: Price is NaN/Inf")
                    return None, f"Price NaN/Inf from {source_name}"
                
                if price > 1000000000:  # Sanity check
                    print(f"❌ {source_name}: Price too high {price}")
                    return None, f"Price too high from {source_name}: {price}"
                
                print(f"✅ {source_name}: Price validation PASSED - ${price:,.8f}")
                return price, None
                
            except (ValueError, TypeError, OverflowError) as e:
                print(f"❌ {source_name}: Price parsing failed - {e}")
                return None, f"Price parsing failed from {source_name}: {e}"
                
        except Exception as e:
            print(f"❌ {source_name}: Validation exception - {e}")
            return None, f"Validation exception from {source_name}: {e}"

    def _format_price_display(self, price):
        """Smart price formatting with validation"""
        try:
            if not isinstance(price, (int, float)) or price <= 0:
                return "INVALID"
            
            if price >= 1000:
                return f"${price:,.2f}"
            elif price >= 1:
                return f"${price:.4f}"
            elif price >= 0.01:
                return f"${price:.6f}"
            else:
                return f"${price:.8f}"
        except:
            return "FORMAT_ERROR"

    def _fallback_price(self, symbol, error_msg):
        """Fallback price data when all Binance endpoints fail"""
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
            print(f"❌ DEPLOYMENT: No fallback data for {symbol} - Binance-only mode")
            return {
                'error': f'Binance API unavailable for {symbol} in deployment mode',
                'symbol': symbol.upper(),
                'error_reason': error_msg,
                'deployment_mode': True
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