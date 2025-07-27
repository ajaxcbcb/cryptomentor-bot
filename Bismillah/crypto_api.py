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