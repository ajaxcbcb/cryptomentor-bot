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
        """Get real-time price from Binance Spot API"""
        try:
            # Normalize symbol format
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            # Enhanced headers for real-time data
            headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'User-Agent': 'CryptoMentorAI/1.0'
            }

            # Add timestamp parameter to prevent caching in deployment
            params = {'symbol': symbol}
            if force_refresh:
                import time
                params['_t'] = int(time.time() * 1000)  # Cache buster

            # Multiple endpoint attempts for better reliability
            endpoints_to_try = [
                f"{self.binance_spot_url}/ticker/24hr",
                f"{self.binance_spot_url}/ticker/price"
            ]

            for endpoint in endpoints_to_try:
                try:
                    response = requests.get(
                        endpoint,
                        params=params,
                        timeout=10,
                        headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Handle different endpoint responses
                    if endpoint.endswith('/ticker/24hr'):
                        return {
                            'symbol': symbol,
                            'price': float(data['lastPrice']),
                            'change_24h': float(data['priceChangePercent']),
                            'high_24h': float(data['highPrice']),
                            'low_24h': float(data['lowPrice']),
                            'volume_24h': float(data['volume']),
                            'quote_volume_24h': float(data['quoteVolume']),
                            'open_price': float(data['openPrice']),
                            'close_price': float(data['lastPrice']),
                            'price_change': float(data['priceChange']),
                            'count': int(data['count']),
                            'first_id': data['firstId'],
                            'last_id': data['lastId'],
                            'open_time': data['openTime'],
                            'close_time': data['closeTime'],
                            'source': 'binance_spot'
                        }
                    else:  # ticker/price endpoint
                        return {
                            'symbol': symbol,
                            'price': float(data['price']),
                            'change_24h': 0,  # Not available in price endpoint
                            'volume_24h': 0,
                            'source': 'binance_spot_simple'
                        }
                        
                except requests.exceptions.RequestException as e:
                    print(f"⚠️ Binance endpoint {endpoint} failed: {e}")
                    continue
                    
            # If all endpoints failed
            raise Exception("All Binance Spot endpoints failed")
            
        except Exception as e:
            print(f"❌ Binance Spot API completely failed for {symbol}: {e}")
            return {'error': f"Binance API error: {str(e)}"}

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
        """Get futures price ticker from Binance Futures"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_futures_url}/ticker/24hr",
                params={'symbol': symbol},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return {
                'symbol': symbol,
                'price': float(data['lastPrice']),
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
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Futures price error: {str(e)}"}

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

    # === BINANCE-ONLY INTEGRATION METHODS ===

    def get_multi_api_price(self, symbol, force_refresh=False):
        """Get price from Binance APIs only - centralized to Binance"""
        price_sources = {}

        # Enhanced deployment environment check
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

        # Multiple attempts for real-time data in deployment
        max_attempts = 3 if is_deployment else 1
        
        for attempt in range(max_attempts):
            if attempt > 0:
                print(f"🔄 Binance retry attempt {attempt + 1}/{max_attempts} for {symbol}")
                import time
                time.sleep(1)  # Brief delay between attempts
            
            # 1. Try Binance Spot API first (most reliable for real-time)
            try:
                binance_data = self.get_binance_price(symbol, force_refresh=True)
                if 'error' not in binance_data and binance_data.get('price', 0) > 0:
                    price_sources['binance'] = binance_data
                    price_str = f"${binance_data.get('price', 0):,.4f}"
                    print(f"🚀 BINANCE REAL-TIME: {symbol} = {price_str} ✅ (Binance Spot)")
                    return self._combine_binance_price_data(symbol, price_sources)
            except Exception as e:
                print(f"⚠️ Binance Spot API error for {symbol}: {e}")
            
            # 2. Try Binance Futures API as backup
            try:
                futures_data = self.get_binance_futures_price(symbol)
                if 'error' not in futures_data and futures_data.get('price', 0) > 0:
                    price_sources['binance_futures'] = futures_data
                    price_str = f"${futures_data.get('price', 0):,.4f}"
                    print(f"🚀 BINANCE REAL-TIME: {symbol} = {price_str} ✅ (Binance Futures)")
                    return self._combine_binance_price_data(symbol, price_sources)
            except Exception as e:
                print(f"⚠️ Binance Futures API error for {symbol}: {e}")

        # Only use fallback if ALL Binance attempts failed AND not in deployment
        if price_sources:
            return self._combine_binance_price_data(symbol, price_sources)
        elif is_deployment:
            # In deployment, return error instead of mock data
            print(f"❌ DEPLOYMENT: All Binance APIs failed for {symbol} - returning error")
            return {'error': f'Binance real-time data unavailable for {symbol} in deployment mode'}
        else:
            return self._fallback_price(symbol, "All Binance APIs unavailable")

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

    def get_price(self, symbol, force_refresh=False):
        """Get price with multi-API integration"""
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

    def get_advanced_futures_analytics(self, symbol):
        """Get advanced futures analytics using multiple Binance endpoints"""
        try:
            # Get comprehensive data
            analytics = {}
            
            # 1. Get price and volume metrics
            price_data = self.get_binance_futures_price(symbol)
            analytics['price_metrics'] = price_data
            
            # 2. Get funding rate trends
            funding_data = self.get_binance_funding_rate(symbol, limit=50)
            analytics['funding_trends'] = funding_data
            
            # 3. Get open interest analytics
            oi_data = self.get_binance_open_interest(symbol)
            analytics['open_interest'] = oi_data
            
            # 4. Get long/short sentiment over time
            ls_data = self.get_binance_long_short_ratio(symbol, period='1h', limit=24)
            analytics['sentiment_trends'] = ls_data
            
            # 5. Get recent liquidation patterns
            liq_data = self.get_binance_liquidation_orders(symbol, limit=200)
            analytics['liquidation_patterns'] = liq_data
            
            # 6. Calculate advanced metrics
            analytics['advanced_metrics'] = self._calculate_advanced_metrics(
                price_data, funding_data, oi_data, ls_data, liq_data
            )
            
            return {
                'symbol': symbol,
                'analytics': analytics,
                'timestamp': datetime.now().isoformat(),
                'source': 'binance_advanced_analytics'
            }
            
        except Exception as e:
            return {'error': f"Advanced analytics error: {str(e)}"}

    def _calculate_advanced_metrics(self, price_data, funding_data, oi_data, ls_data, liq_data):
        """Calculate advanced trading metrics"""
        try:
            metrics = {}
            
            # Price momentum score
            if 'error' not in price_data:
                change_24h = price_data.get('change_24h', 0)
                volume_24h = price_data.get('volume_24h', 0)
                
                momentum_score = abs(change_24h) * (volume_24h / 1000000000)  # Weighted by volume
                metrics['momentum_score'] = min(momentum_score, 100)  # Cap at 100
            
            # Funding rate pressure
            if 'error' not in funding_data:
                avg_funding = funding_data.get('average_funding_rate', 0)
                last_funding = funding_data.get('last_funding_rate', 0)
                
                funding_pressure = abs(last_funding) * 1000  # Convert to basis points
                metrics['funding_pressure'] = funding_pressure
            
            # Open interest health
            if 'error' not in oi_data:
                oi_value = oi_data.get('open_interest', 0)
                # Normalize OI (this is simplified)
                oi_health = min(oi_value / 100000000, 10)  # Scale factor
                metrics['oi_health'] = oi_health
            
            # Sentiment extremes
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                sentiment_extreme = abs(long_ratio - 50)  # Distance from neutral
                metrics['sentiment_extreme'] = sentiment_extreme
            
            # Liquidation risk
            if 'error' not in liq_data:
                total_liq = liq_data.get('total_liquidation', 0)
                liq_risk = min(total_liq / 1000000000, 10)  # Scale factor
                metrics['liquidation_risk'] = liq_risk
            
            return metrics
            
        except Exception as e:
            return {'error': f"Metrics calculation error: {str(e)}"}

    def analyze_supply_demand(self, symbol):
        """Analyze supply and demand levels for entry recommendations"""
        try:
            # Get comprehensive market data
            price_data = self.get_binance_price(symbol)
            futures_data = self.get_comprehensive_futures_data(symbol)
            candlestick_data = self.get_binance_candlestick(symbol, '1h', 24)
            
            if 'error' in price_data:
                return {'error': 'Failed to get price data for supply/demand analysis'}
            
            current_price = price_data.get('price', 0)
            volume_24h = price_data.get('volume_24h', 0)
            change_24h = price_data.get('change_24h', 0)
            
            # 1. Volume Analysis (Supply/Demand Pressure)
            volume_pressure = self._analyze_volume_pressure(volume_24h, change_24h)
            
            # 2. Order Book Imbalance (using available data)
            order_imbalance = self._analyze_order_imbalance(futures_data)
            
            # 3. Support/Resistance as Supply/Demand Zones
            supply_demand_zones = self._identify_supply_demand_zones(candlestick_data, current_price)
            
            # 4. Market Structure Analysis
            market_structure = self._analyze_market_structure(candlestick_data)
            
            # 5. Open Interest Flow Analysis
            oi_flow = self._analyze_oi_flow(futures_data)
            
            # 6. Generate Supply/Demand Score
            sd_score = self._calculate_supply_demand_score(
                volume_pressure, order_imbalance, supply_demand_zones, 
                market_structure, oi_flow
            )
            
            # 7. Generate Entry Recommendations
            entry_recommendation = self._generate_supply_demand_entry(
                current_price, sd_score, supply_demand_zones, market_structure
            )
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'volume_pressure': volume_pressure,
                'order_imbalance': order_imbalance,
                'supply_demand_zones': supply_demand_zones,
                'market_structure': market_structure,
                'oi_flow': oi_flow,
                'supply_demand_score': sd_score,
                'entry_recommendation': entry_recommendation,
                'timestamp': datetime.now().isoformat(),
                'source': 'binance_supply_demand_analysis'
            }
            
        except Exception as e:
            return {'error': f"Supply/Demand analysis error: {str(e)}"}

    def _analyze_volume_pressure(self, volume_24h, change_24h):
        """Analyze volume pressure to determine buying/selling pressure"""
        try:
            # Calculate volume-price relationship
            if volume_24h == 0:
                return {
                    'pressure_type': 'neutral',
                    'pressure_strength': 0,
                    'analysis': 'Insufficient volume data'
                }
            
            # High volume + positive change = Strong buying pressure (Demand)
            # High volume + negative change = Strong selling pressure (Supply)
            # Low volume + any change = Weak pressure
            
            volume_threshold_high = 100000000  # 100M USDT
            volume_threshold_medium = 50000000  # 50M USDT
            
            if volume_24h > volume_threshold_high:
                volume_level = 'high'
                volume_multiplier = 3
            elif volume_24h > volume_threshold_medium:
                volume_level = 'medium'
                volume_multiplier = 2
            else:
                volume_level = 'low'
                volume_multiplier = 1
            
            # Determine pressure direction and strength
            if change_24h > 2:
                pressure_type = 'strong_demand'
                pressure_strength = min(abs(change_24h) * volume_multiplier, 100)
                analysis = f"Strong buying pressure - High demand with {volume_level} volume"
            elif change_24h > 0:
                pressure_type = 'moderate_demand'
                pressure_strength = min(abs(change_24h) * volume_multiplier * 0.7, 100)
                analysis = f"Moderate buying pressure - Some demand with {volume_level} volume"
            elif change_24h < -2:
                pressure_type = 'strong_supply'
                pressure_strength = min(abs(change_24h) * volume_multiplier, 100)
                analysis = f"Strong selling pressure - High supply with {volume_level} volume"
            elif change_24h < 0:
                pressure_type = 'moderate_supply'
                pressure_strength = min(abs(change_24h) * volume_multiplier * 0.7, 100)
                analysis = f"Moderate selling pressure - Some supply with {volume_level} volume"
            else:
                pressure_type = 'equilibrium'
                pressure_strength = 0
                analysis = f"Balanced supply/demand - No clear pressure with {volume_level} volume"
            
            return {
                'pressure_type': pressure_type,
                'pressure_strength': pressure_strength,
                'volume_level': volume_level,
                'volume_24h': volume_24h,
                'price_change_24h': change_24h,
                'analysis': analysis
            }
            
        except Exception as e:
            return {'error': f"Volume pressure analysis error: {str(e)}"}

    def _analyze_order_imbalance(self, futures_data):
        """Analyze order imbalance using long/short ratio as proxy"""
        try:
            if 'error' in futures_data:
                return {
                    'imbalance_type': 'unknown',
                    'imbalance_strength': 0,
                    'analysis': 'Futures data unavailable'
                }
            
            ls_data = futures_data.get('long_short_ratio_data', {})
            if 'error' in ls_data:
                return {
                    'imbalance_type': 'unknown',
                    'imbalance_strength': 0,
                    'analysis': 'Long/short ratio data unavailable'
                }
            
            long_ratio = ls_data.get('long_ratio', 50)
            short_ratio = ls_data.get('short_ratio', 50)
            
            # Calculate imbalance (contrarian approach)
            if long_ratio > 75:
                imbalance_type = 'oversupplied_longs'  # Too many longs = potential supply
                imbalance_strength = min((long_ratio - 50) * 2, 100)
                analysis = f"Extreme long bias ({long_ratio:.1f}%) - Risk of long liquidations creating supply"
            elif long_ratio > 65:
                imbalance_type = 'high_long_bias'
                imbalance_strength = min((long_ratio - 50) * 1.5, 100)
                analysis = f"High long bias ({long_ratio:.1f}%) - Potential supply pressure from overleverage"
            elif short_ratio > 75:
                imbalance_type = 'oversupplied_shorts'  # Too many shorts = potential demand
                imbalance_strength = min((short_ratio - 50) * 2, 100)
                analysis = f"Extreme short bias ({short_ratio:.1f}%) - Risk of short squeeze creating demand"
            elif short_ratio > 65:
                imbalance_type = 'high_short_bias'
                imbalance_strength = min((short_ratio - 50) * 1.5, 100)
                analysis = f"High short bias ({short_ratio:.1f}%) - Potential demand from short covering"
            else:
                imbalance_type = 'balanced'
                imbalance_strength = 0
                analysis = f"Balanced positioning ({long_ratio:.1f}%/{short_ratio:.1f}%) - No significant imbalance"
            
            return {
                'imbalance_type': imbalance_type,
                'imbalance_strength': imbalance_strength,
                'long_ratio': long_ratio,
                'short_ratio': short_ratio,
                'analysis': analysis
            }
            
        except Exception as e:
            return {'error': f"Order imbalance analysis error: {str(e)}"}

    def _identify_supply_demand_zones(self, candlestick_data, current_price):
        """Identify key supply and demand zones from price action"""
        try:
            if 'error' in candlestick_data:
                return {
                    'demand_zones': [],
                    'supply_zones': [],
                    'analysis': 'Candlestick data unavailable'
                }
            
            candlesticks = candlestick_data.get('candlesticks', [])
            if len(candlesticks) < 10:
                return {
                    'demand_zones': [],
                    'supply_zones': [],
                    'analysis': 'Insufficient price history'
                }
            
            demand_zones = []
            supply_zones = []
            
            # Look for strong reactions (supply/demand zones)
            for i in range(2, len(candlesticks) - 2):
                candle = candlesticks[i]
                prev_candle = candlesticks[i-1]
                next_candle = candlesticks[i+1]
                
                high = float(candle['high'])
                low = float(candle['low'])
                close = float(candle['close'])
                open_price = float(candle['open'])
                volume = float(candle['volume'])
                
                # Identify demand zones (strong buying reactions from low)
                if (low < float(prev_candle['low']) and 
                    close > open_price and  # Bullish candle
                    float(next_candle['close']) > close):  # Follow-through
                    
                    zone_strength = self._calculate_zone_strength(volume, close - open_price, current_price, low)
                    demand_zones.append({
                        'price_level': low,
                        'zone_high': min(open_price, close),
                        'zone_low': low,
                        'strength': zone_strength,
                        'distance_from_current': abs(current_price - low) / current_price * 100,
                        'type': 'demand'
                    })
                
                # Identify supply zones (strong selling reactions from high)
                if (high > float(prev_candle['high']) and 
                    close < open_price and  # Bearish candle
                    float(next_candle['close']) < close):  # Follow-through
                    
                    zone_strength = self._calculate_zone_strength(volume, open_price - close, current_price, high)
                    supply_zones.append({
                        'price_level': high,
                        'zone_high': high,
                        'zone_low': max(open_price, close),
                        'strength': zone_strength,
                        'distance_from_current': abs(current_price - high) / current_price * 100,
                        'type': 'supply'
                    })
            
            # Sort by strength and proximity
            demand_zones = sorted(demand_zones, key=lambda x: (x['strength'], -x['distance_from_current']), reverse=True)[:3]
            supply_zones = sorted(supply_zones, key=lambda x: (x['strength'], -x['distance_from_current']), reverse=True)[:3]
            
            return {
                'demand_zones': demand_zones,
                'supply_zones': supply_zones,
                'nearest_demand': demand_zones[0] if demand_zones else None,
                'nearest_supply': supply_zones[0] if supply_zones else None,
                'analysis': f"Found {len(demand_zones)} demand zones and {len(supply_zones)} supply zones"
            }
            
        except Exception as e:
            return {'error': f"Supply/Demand zones error: {str(e)}"}

    def _calculate_zone_strength(self, volume, body_size, current_price, zone_price):
        """Calculate the strength of a supply/demand zone"""
        try:
            # Factors: Volume, reaction size, freshness (proximity to current price)
            volume_score = min(volume / 1000000, 10)  # Normalize volume
            reaction_score = min(abs(body_size) / current_price * 100 * 10, 10)  # Reaction percentage
            freshness_score = max(10 - abs(current_price - zone_price) / current_price * 100, 1)  # Proximity bonus
            
            # Weighted combination
            strength = (volume_score * 0.4 + reaction_score * 0.4 + freshness_score * 0.2)
            return min(strength, 10)
            
        except Exception as e:
            return 5  # Default moderate strength

    def _analyze_market_structure(self, candlestick_data):
        """Analyze market structure for supply/demand context"""
        try:
            if 'error' in candlestick_data:
                return {
                    'structure': 'unknown',
                    'trend': 'unknown',
                    'analysis': 'Candlestick data unavailable'
                }
            
            candlesticks = candlestick_data.get('candlesticks', [])
            if len(candlesticks) < 10:
                return {
                    'structure': 'unknown',
                    'trend': 'unknown',
                    'analysis': 'Insufficient data for structure analysis'
                }
            
            # Analyze recent price action for structure
            recent_closes = [float(c['close']) for c in candlesticks[-10:]]
            recent_highs = [float(c['high']) for c in candlesticks[-10:]]
            recent_lows = [float(c['low']) for c in candlesticks[-10:]]
            
            # Higher highs and higher lows = Uptrend (Demand controlling)
            # Lower highs and lower lows = Downtrend (Supply controlling)
            # Mixed = Sideways (Balanced supply/demand)
            
            hh_count = 0  # Higher highs
            hl_count = 0  # Higher lows
            lh_count = 0  # Lower highs
            ll_count = 0  # Lower lows
            
            for i in range(1, len(recent_closes)):
                if recent_highs[i] > recent_highs[i-1]:
                    hh_count += 1
                elif recent_highs[i] < recent_highs[i-1]:
                    lh_count += 1
                    
                if recent_lows[i] > recent_lows[i-1]:
                    hl_count += 1
                elif recent_lows[i] < recent_lows[i-1]:
                    ll_count += 1
            
            # Determine structure
            if hh_count >= 3 and hl_count >= 2:
                structure = 'uptrend'
                trend = 'bullish'
                analysis = "Higher highs and higher lows - Demand in control, look for demand zone entries"
            elif lh_count >= 3 and ll_count >= 2:
                structure = 'downtrend'
                trend = 'bearish'
                analysis = "Lower highs and lower lows - Supply in control, look for supply zone entries"
            else:
                structure = 'sideways'
                trend = 'neutral'
                analysis = "Mixed structure - Supply and demand balanced, range-bound market"
            
            return {
                'structure': structure,
                'trend': trend,
                'higher_highs': hh_count,
                'higher_lows': hl_count,
                'lower_highs': lh_count,
                'lower_lows': ll_count,
                'analysis': analysis
            }
            
        except Exception as e:
            return {'error': f"Market structure analysis error: {str(e)}"}

    def _analyze_oi_flow(self, futures_data):
        """Analyze open interest flow for supply/demand insights"""
        try:
            if 'error' in futures_data:
                return {
                    'oi_trend': 'unknown',
                    'flow_direction': 'unknown',
                    'analysis': 'Futures data unavailable'
                }
            
            oi_data = futures_data.get('open_interest_data', {})
            if 'error' in oi_data:
                return {
                    'oi_trend': 'unknown',
                    'flow_direction': 'unknown',
                    'analysis': 'Open interest data unavailable'
                }
            
            current_oi = oi_data.get('open_interest', 0)
            
            # Get funding rate for context
            funding_data = futures_data.get('funding_rate_data', {})
            current_funding = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0
            
            # Analyze OI with funding rate context
            if current_oi > 1000000:  # High OI
                if current_funding > 0.01:  # Positive funding = longs paying shorts
                    flow_direction = 'long_pressure'
                    analysis = "High OI with positive funding - Long demand but expensive to hold"
                elif current_funding < -0.01:  # Negative funding = shorts paying longs
                    flow_direction = 'short_pressure'
                    analysis = "High OI with negative funding - Short pressure but expensive to maintain"
                else:
                    flow_direction = 'balanced'
                    analysis = "High OI with neutral funding - Balanced supply/demand"
            else:
                flow_direction = 'low_interest'
                analysis = "Low open interest - Limited futures activity"
            
            oi_trend = 'increasing' if current_oi > 500000 else 'decreasing'
            
            return {
                'oi_trend': oi_trend,
                'flow_direction': flow_direction,
                'current_oi': current_oi,
                'funding_rate': current_funding,
                'analysis': analysis
            }
            
        except Exception as e:
            return {'error': f"OI flow analysis error: {str(e)}"}

    def _calculate_supply_demand_score(self, volume_pressure, order_imbalance, supply_demand_zones, market_structure, oi_flow):
        """Calculate overall supply/demand score for trading recommendation"""
        try:
            score = 50  # Start neutral (50/100)
            factors = []
            
            # Volume pressure analysis (30% weight)
            if volume_pressure.get('pressure_type') == 'strong_demand':
                score += 15
                factors.append("Strong volume demand pressure (+15)")
            elif volume_pressure.get('pressure_type') == 'moderate_demand':
                score += 8
                factors.append("Moderate volume demand pressure (+8)")
            elif volume_pressure.get('pressure_type') == 'strong_supply':
                score -= 15
                factors.append("Strong volume supply pressure (-15)")
            elif volume_pressure.get('pressure_type') == 'moderate_supply':
                score -= 8
                factors.append("Moderate volume supply pressure (-8)")
            
            # Order imbalance analysis (25% weight)
            imbalance_type = order_imbalance.get('imbalance_type')
            if imbalance_type == 'oversupplied_shorts':
                score += 12
                factors.append("Oversupplied shorts - demand potential (+12)")
            elif imbalance_type == 'high_short_bias':
                score += 6
                factors.append("High short bias - some demand potential (+6)")
            elif imbalance_type == 'oversupplied_longs':
                score -= 12
                factors.append("Oversupplied longs - supply risk (-12)")
            elif imbalance_type == 'high_long_bias':
                score -= 6
                factors.append("High long bias - some supply risk (-6)")
            
            # Market structure analysis (25% weight)
            structure = market_structure.get('structure')
            if structure == 'uptrend':
                score += 10
                factors.append("Uptrend structure - demand favored (+10)")
            elif structure == 'downtrend':
                score -= 10
                factors.append("Downtrend structure - supply favored (-10)")
            
            # Supply/demand zones proximity (20% weight)
            nearest_demand = supply_demand_zones.get('nearest_demand')
            nearest_supply = supply_demand_zones.get('nearest_supply')
            
            if nearest_demand and nearest_demand.get('distance_from_current', 100) < 5:
                score += 8
                factors.append("Near strong demand zone (+8)")
            if nearest_supply and nearest_supply.get('distance_from_current', 100) < 5:
                score -= 8
                factors.append("Near strong supply zone (-8)")
            
            # Ensure score stays within bounds
            score = max(0, min(100, score))
            
            # Determine overall bias
            if score >= 70:
                bias = "Strong Demand"
                recommendation = "LONG"
            elif score >= 60:
                bias = "Moderate Demand"
                recommendation = "WEAK LONG"
            elif score <= 30:
                bias = "Strong Supply"
                recommendation = "SHORT"
            elif score <= 40:
                bias = "Moderate Supply"
                recommendation = "WEAK SHORT"
            else:
                bias = "Balanced"
                recommendation = "HOLD"
            
            return {
                'score': score,
                'bias': bias,
                'recommendation': recommendation,
                'factors': factors,
                'confidence': 'High' if abs(score - 50) >= 20 else 'Medium' if abs(score - 50) >= 10 else 'Low'
            }
            
        except Exception as e:
            return {'error': f"Score calculation error: {str(e)}"}

    def _generate_supply_demand_entry(self, current_price, sd_score, supply_demand_zones, market_structure):
        """Generate specific entry recommendations based on supply/demand analysis"""
        try:
            recommendations = []
            
            score = sd_score.get('score', 50)
            bias = sd_score.get('bias', 'Balanced')
            
            # Get zones
            demand_zones = supply_demand_zones.get('demand_zones', [])
            supply_zones = supply_demand_zones.get('supply_zones', [])
            
            if score >= 60:  # Demand favored
                # Look for demand zone entries
                if demand_zones:
                    best_demand = demand_zones[0]
                    entry_price = best_demand['zone_high']
                    stop_loss = best_demand['zone_low'] * 0.998  # Just below demand zone
                    take_profit = current_price * 1.02  # 2% target
                    
                    recommendations.append({
                        'direction': 'LONG',
                        'entry_type': 'Demand Zone Entry',
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': abs(take_profit - entry_price) / abs(entry_price - stop_loss),
                        'confidence': sd_score.get('confidence', 'Medium'),
                        'logic': f"Enter long at demand zone ${entry_price:,.4f} with SL below zone"
                    })
                else:
                    # Market entry with tight SL
                    entry_price = current_price
                    stop_loss = current_price * 0.98
                    take_profit = current_price * 1.03
                    
                    recommendations.append({
                        'direction': 'LONG',
                        'entry_type': 'Market Entry',
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': abs(take_profit - entry_price) / abs(entry_price - stop_loss),
                        'confidence': sd_score.get('confidence', 'Medium'),
                        'logic': f"Market long entry with demand bias"
                    })
            
            elif score <= 40:  # Supply favored
                # Look for supply zone entries
                if supply_zones:
                    best_supply = supply_zones[0]
                    entry_price = best_supply['zone_low']
                    stop_loss = best_supply['zone_high'] * 1.002  # Just above supply zone
                    take_profit = current_price * 0.98  # 2% target
                    
                    recommendations.append({
                        'direction': 'SHORT',
                        'entry_type': 'Supply Zone Entry',
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': abs(entry_price - take_profit) / abs(stop_loss - entry_price),
                        'confidence': sd_score.get('confidence', 'Medium'),
                        'logic': f"Enter short at supply zone ${entry_price:,.4f} with SL above zone"
                    })
                else:
                    # Market entry with tight SL
                    entry_price = current_price
                    stop_loss = current_price * 1.02
                    take_profit = current_price * 0.97
                    
                    recommendations.append({
                        'direction': 'SHORT',
                        'entry_type': 'Market Entry',
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'risk_reward': abs(entry_price - take_profit) / abs(stop_loss - entry_price),
                        'confidence': sd_score.get('confidence', 'Medium'),
                        'logic': f"Market short entry with supply bias"
                    })
            
            else:  # Balanced market
                recommendations.append({
                    'direction': 'HOLD',
                    'entry_type': 'Wait for Clear Signal',
                    'entry_price': current_price,
                    'stop_loss': None,
                    'take_profit': None,
                    'risk_reward': 0,
                    'confidence': 'Low',
                    'logic': "Balanced supply/demand - wait for clearer directional bias"
                })
            
            return {
                'primary_recommendation': recommendations[0] if recommendations else None,
                'alternative_setups': recommendations[1:] if len(recommendations) > 1 else [],
                'market_bias': bias,
                'entry_timing': 'Immediate' if score >= 70 or score <= 30 else 'Wait for confirmation'
            }
            
        except Exception as e:
            return {'error': f"Entry recommendation error: {str(e)}"}

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

    def get_timeframe_analysis(self, symbol, timeframe='1h'):
        """Get comprehensive timeframe analysis using Binance API"""
        try:
            # Get candlestick data for the timeframe
            candles_data = self.get_binance_candlestick(symbol, timeframe, 50)
            if 'error' in candles_data:
                return {'error': f"Failed to get candlestick data: {candles_data.get('error')}"}

            # Get current price and futures data
            price_data = self.get_binance_futures_price(symbol)
            mark_data = self.get_binance_mark_price(symbol)
            funding_data = self.get_binance_funding_rate(symbol)
            oi_data = self.get_binance_open_interest(symbol)
            ls_data = self.get_binance_long_short_ratio(symbol)
            liq_data = self.get_binance_liquidation_orders(symbol)

            # Analyze candlestick patterns and trends
            candlesticks = candles_data.get('candlesticks', [])
            trend_analysis = self._analyze_trend_from_candles(candlesticks, timeframe)
            support_resistance = self._calculate_support_resistance(candlesticks)
            volatility = self._calculate_volatility(candlesticks)

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'price_data': price_data,
                'mark_data': mark_data,
                'funding_data': funding_data,
                'open_interest_data': oi_data,
                'long_short_data': ls_data,
                'liquidation_data': liq_data,
                'candlesticks': candlesticks[-20:],  # Last 20 candles
                'trend_analysis': trend_analysis,
                'support_resistance': support_resistance,
                'volatility': volatility,
                'source': 'binance_timeframe_analysis'
            }
        except Exception as e:
            return {'error': f"Timeframe analysis error: {str(e)}"}

    def _analyze_trend_from_candles(self, candlesticks, timeframe):
        """Analyze trend from candlestick data"""
        if not candlesticks or len(candlesticks) < 10:
            return {'trend': 'unknown', 'strength': 'weak', 'direction': 'neutral'}

        # Calculate trend using moving averages
        closes = [float(candle['close']) for candle in candlesticks[-20:]]
        
        # Simple moving averages
        sma_5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1]
        sma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else closes[-1]
        sma_20 = sum(closes) / len(closes)

        # Trend direction
        if sma_5 > sma_10 > sma_20:
            direction = 'bullish'
            strength = 'strong' if (sma_5 - sma_20) / sma_20 > 0.02 else 'moderate'
        elif sma_5 < sma_10 < sma_20:
            direction = 'bearish'
            strength = 'strong' if (sma_20 - sma_5) / sma_20 > 0.02 else 'moderate'
        else:
            direction = 'sideways'
            strength = 'weak'

        # Calculate momentum
        price_change = (closes[-1] - closes[0]) / closes[0] * 100
        
        return {
            'trend': direction,
            'strength': strength,
            'direction': direction,
            'price_change_pct': price_change,
            'sma_5': sma_5,
            'sma_10': sma_10,
            'sma_20': sma_20,
            'timeframe': timeframe
        }

    def _calculate_support_resistance(self, candlesticks):
        """Calculate support and resistance levels"""
        if not candlesticks or len(candlesticks) < 10:
            return {'support': 0, 'resistance': 0, 'levels': []}

        highs = [float(candle['high']) for candle in candlesticks[-20:]]
        lows = [float(candle['low']) for candle in candlesticks[-20:]]

        # Simple support/resistance calculation
        resistance = max(highs)
        support = min(lows)
        
        # Current price
        current_price = float(candlesticks[-1]['close'])
        
        # Calculate key levels
        levels = []
        for i in range(1, len(candlesticks) - 1):
            high = float(candlesticks[i]['high'])
            low = float(candlesticks[i]['low'])
            
            # Check for local highs (resistance)
            if (high > float(candlesticks[i-1]['high']) and 
                high > float(candlesticks[i+1]['high'])):
                levels.append({'type': 'resistance', 'price': high})
            
            # Check for local lows (support)
            if (low < float(candlesticks[i-1]['low']) and 
                low < float(candlesticks[i+1]['low'])):
                levels.append({'type': 'support', 'price': low})

        return {
            'support': support,
            'resistance': resistance,
            'current_price': current_price,
            'distance_to_support': (current_price - support) / current_price * 100,
            'distance_to_resistance': (resistance - current_price) / current_price * 100,
            'key_levels': levels[-5:]  # Last 5 key levels
        }

    def _calculate_volatility(self, candlesticks):
        """Calculate volatility metrics"""
        if not candlesticks or len(candlesticks) < 10:
            return {'volatility': 'low', 'atr': 0, 'price_range': 0}

        # Calculate Average True Range (ATR)
        atr_values = []
        for i in range(1, len(candlesticks)):
            high = float(candlesticks[i]['high'])
            low = float(candlesticks[i]['low'])
            prev_close = float(candlesticks[i-1]['close'])
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            atr_values.append(tr)

        atr = sum(atr_values[-14:]) / min(14, len(atr_values))  # 14-period ATR
        
        # Calculate price range
        recent_highs = [float(c['high']) for c in candlesticks[-10:]]
        recent_lows = [float(c['low']) for c in candlesticks[-10:]]
        price_range = (max(recent_highs) - min(recent_lows)) / min(recent_lows) * 100

        # Volatility classification
        if price_range > 10:
            volatility = 'very_high'
        elif price_range > 5:
            volatility = 'high'
        elif price_range > 2:
            volatility = 'moderate'
        else:
            volatility = 'low'

        return {
            'volatility': volatility,
            'atr': atr,
            'price_range': price_range,
            'classification': volatility
        }

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

    def get_binance_global_data(self):
        """Get global market data using Binance APIs exclusively"""
        try:
            # Get data from top cryptocurrencies via Binance
            major_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'DOT', 'AVAX', 'LINK', 'LTC', 'UNI', 'ATOM']
            prices_data = self.get_multiple_binance_prices(major_symbols)
            
            if 'error' not in prices_data and len(prices_data) > 0:
                # Calculate market metrics from Binance data
                btc_data = prices_data.get('BTC', {})
                eth_data = prices_data.get('ETH', {})
                
                # Calculate total volume and market metrics
                total_volume = sum(data.get('volume_24h', 0) for data in prices_data.values())
                btc_volume = btc_data.get('volume_24h', 0)
                eth_volume = eth_data.get('volume_24h', 0)
                
                # Estimate market cap and dominance
                btc_price = btc_data.get('price', 0)
                eth_price = eth_data.get('price', 0)
                
                # Rough market cap estimates based on known supply
                btc_market_cap = btc_price * 19700000  # ~19.7M BTC in circulation
                eth_market_cap = eth_price * 120000000  # ~120M ETH in circulation
                
                # Estimate total market cap (BTC dominance typically 40-50%)
                estimated_total_market_cap = btc_market_cap / 0.45  # Assume 45% dominance
                
                btc_dominance = (btc_market_cap / estimated_total_market_cap * 100) if estimated_total_market_cap > 0 else 45.0
                eth_dominance = (eth_market_cap / estimated_total_market_cap * 100) if estimated_total_market_cap > 0 else 18.0
                
                # Calculate weighted average market change
                changes = []
                volumes = []
                for data in prices_data.values():
                    if 'change_24h' in data and 'volume_24h' in data:
                        changes.append(data['change_24h'])
                        volumes.append(data['volume_24h'])
                
                weighted_change = sum(c * v for c, v in zip(changes, volumes)) / sum(volumes) if volumes else 0
                
                return {
                    'total_market_cap': estimated_total_market_cap,
                    'total_volume': total_volume,
                    'market_cap_percentage': {
                        'btc': btc_dominance,
                        'eth': eth_dominance,
                        'others': 100 - btc_dominance - eth_dominance
                    },
                    'market_cap_change_percentage_24h_usd': weighted_change,
                    'active_cryptocurrencies': len(prices_data),
                    'markets': 1,  # Binance
                    'updated_at': int(datetime.now().timestamp()),
                    'source': 'binance_global_estimate'
                }
            else:
                return {'error': 'Binance market data unavailable for global calculation'}
        except Exception as e:
            return {'error': f"Binance global data error: {str(e)}"}

    def get_market_overview(self):
        """Get market overview data using Binance data exclusively"""
        try:
            # Get global data using Binance
            global_data = self.get_binance_global_data()
            
            # Get data from top cryptocurrencies via Binance
            major_symbols = ['BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'XRP', 'DOGE', 'MATIC', 'DOT', 'AVAX']
            prices_data = self.get_multiple_binance_prices(major_symbols)
            
            if 'error' not in prices_data and len(prices_data) > 0:
                # Get individual coin data
                btc_data = prices_data.get('BTC', {})
                eth_data = prices_data.get('ETH', {})
                bnb_data = prices_data.get('BNB', {})
                
                # Get BTC futures data for additional insights
                btc_futures = self.get_comprehensive_futures_data('BTC')
                funding_rate = 0
                open_interest = 0
                if 'error' not in btc_futures:
                    funding_data = btc_futures.get('funding_rate_data', {})
                    oi_data = btc_futures.get('open_interest_data', {})
                    funding_rate = funding_data.get('last_funding_rate', 0) if 'error' not in funding_data else 0
                    open_interest = oi_data.get('open_interest', 0) if 'error' not in oi_data else 0
                
                # Combine global and specific data
                return {
                    'total_market_cap': global_data.get('total_market_cap', 0),
                    'market_cap_change_24h': global_data.get('market_cap_change_percentage_24h_usd', 0),
                    'btc_dominance': global_data.get('market_cap_percentage', {}).get('btc', 45.0),
                    'eth_dominance': global_data.get('market_cap_percentage', {}).get('eth', 18.0),
                    'btc_price': btc_data.get('price', 0),
                    'eth_price': eth_data.get('price', 0),
                    'bnb_price': bnb_data.get('price', 0),
                    'btc_change_24h': btc_data.get('change_24h', 0),
                    'eth_change_24h': eth_data.get('change_24h', 0),
                    'bnb_change_24h': bnb_data.get('change_24h', 0),
                    'total_volume_24h': global_data.get('total_volume', 0),
                    'active_cryptocurrencies': len(prices_data),
                    'btc_funding_rate': funding_rate,
                    'btc_open_interest': open_interest,
                    'source': 'binance_exclusive',
                    'last_updated': datetime.now().isoformat()
                }
            else:
                return {'error': 'Binance market data unavailable'}
        except Exception as e:
            return {'error': f"Market overview error: {str(e)}"}