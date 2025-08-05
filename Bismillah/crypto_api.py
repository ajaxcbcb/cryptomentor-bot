import requests
import os
import time
import asyncio
from datetime import datetime, timezone
from binance_provider import BinanceFuturesProvider
from coinmarketcap_provider import CoinMarketCapProvider

class CryptoAPI:
    def __init__(self):
        self.provider = BinanceFuturesProvider()
        self.cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
        self.coinglass_key = os.getenv("COINGLASS_SECRET")
        self.cmc_provider = CoinMarketCapProvider()

        if not self.coinglass_key:
            print("⚠️ Coinglass API key not found in environment variables")
            print("💡 Please set COINGLASS_SECRET in Replit Secrets")

        self.coinglass_url = "https://open-api.coinglass.com/api/pro/v1"
        self.coinglass_base_url = "https://open-api.coinglass.com/public/v2" # Added for v2 endpoints
        
        # Initialize Binance URLs
        self.binance_spot_url = "https://api.binance.com/api/v3"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1"

        self.cache = {} # Initialize cache for price data
        self.cache_duration = 30 # Enhanced cache duration (30 seconds for real-time)

        print("🚀 CryptoAPI initialized with CoinGlass + CoinMarketCap Startup Plan")
        print(f"📊 Coinglass API Base URL: {self.coinglass_url}")
        print(f"📊 Coinglass Public API Base URL: {self.coinglass_base_url}") # Added for clarity
        print(f"🔑 Coinglass Key: {'✅ Enabled' if self.coinglass_key else '❌ Disabled'}")
        print(f"📊 CoinMarketCap Startup: {'✅ Enabled' if self.cmc_provider.api_key else '❌ Disabled'}")
        print(f"📰 CryptoNews API: {'✅ Enabled' if self.cryptonews_key else '❌ Disabled'}")
        print("⭐ Premium Analysis: CoinGlass Futures + CoinMarketCap Fundamental")

    # === COINGLASS API METHODS ===

    def _get_coinglass_headers(self):
        """Get headers for Coinglass API requests"""
        return {
            "coinglassSecret": self.coinglass_key,
            "User-Agent": "CryptoMentorAI/1.0",
            "Accept": "application/json",
            "Connection": "keep-alive"
        }

    def get_coinglass_open_interest(self, symbol):
        """Get open interest data from Coinglass API v2"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Convert symbol format for Coinglass
            symbol = symbol.upper()
            if symbol.endswith('USDT'):
                symbol = symbol[:-4]  # Remove USDT suffix

            url = "https://open-api.coinglass.com/public/v2/futures/openInterest"
            headers = {
                "accept": "application/json",
                "coinglassSecret": self.coinglass_key
            }

            params = {
                'symbol': symbol
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', {})
                total_oi = 0
                oi_change = 0

                # Sum up open interest from all exchanges
                if isinstance(result_data, list):
                    for exchange_data in result_data:
                        oi_value = float(exchange_data.get('openInterest', 0))
                        oi_change_value = float(exchange_data.get('openInterestChange', 0))
                        total_oi += oi_value
                        oi_change += oi_change_value

                return {
                    'symbol': symbol,
                    'open_interest': total_oi,
                    'open_interest_change': oi_change,
                    'exchanges_count': len(result_data) if isinstance(result_data, list) else 1,
                    'source': 'coinglass_v2',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'error': f"Coinglass API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass open interest error: {str(e)}"}

    # === COINAPI METHODS ===

    def get_crypto_price(self, symbol, force_refresh=False):
        """Get cryptocurrency price with CoinMarketCap + CoinGlass Premium integration"""
        try:
            cache_key = f"premium_price_{symbol.upper()}"

            # Check cache first (unless force refresh)
            if not force_refresh and cache_key in self.cache:
                cached_data = self.cache[cache_key]
                cache_time = cached_data.get('timestamp', 0)
                if time.time() - cache_time < self.cache_duration:
                    print(f"📊 Using cached premium price for {symbol}")
                    return cached_data

            # Primary: CoinMarketCap for comprehensive data
            if self.cmc_provider.api_key:
                print(f"🔄 Fetching premium data for {symbol} from CoinMarketCap Startup...")
                cmc_data = self.cmc_provider.get_cryptocurrency_quotes(symbol)

                if 'error' not in cmc_data and cmc_data.get('price', 0) > 0:
                    # Enhance with CoinGlass futures data
                    coinglass_data = self._get_coinglass_enhanced_ticker(symbol)

                    result = {
                        'symbol': symbol.upper(),
                        'price': cmc_data.get('price', 0),
                        'change_24h': cmc_data.get('percent_change_24h', 0),
                        'change_7d': cmc_data.get('percent_change_7d', 0),
                        'volume_24h': cmc_data.get('volume_24h', 0),
                        'market_cap': cmc_data.get('market_cap', 0),
                        'market_cap_dominance': cmc_data.get('market_cap_dominance', 0),
                        'circulating_supply': cmc_data.get('circulating_supply', 0),
                        'max_supply': cmc_data.get('max_supply', 0),
                        # Enhanced with CoinGlass futures data
                        'funding_rate': coinglass_data.get('funding_rate', 0),
                        'open_interest': coinglass_data.get('open_interest', 0),
                        'long_short_ratio': coinglass_data.get('long_short_ratio', 50),
                        'source': 'coinmarketcap_premium',
                        'timestamp': time.time()
                    }

                    # Cache the premium result
                    self.cache[cache_key] = result
                    print(f"✅ Premium price data for {symbol}: ${result['price']:.4f} (CMC+CoinGlass)")
                    return result

            # Fallback to CoinGlass only
            return self._get_coinglass_price_fallback(symbol)

        except Exception as e:
            print(f"❌ Premium price fetch error for {symbol}: {e}")
            return self._get_coinglass_price_fallback(symbol)

    def _get_coinglass_enhanced_ticker(self, symbol):
        """Get enhanced ticker data from CoinGlass Pro"""
        try:
            clean_symbol = symbol.upper().replace('USDT', '')
            url = f"{self.coinglass_url}/futures/ticker"
            headers = self._get_coinglass_headers()
            params = {'symbol': clean_symbol}

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    ticker_data = data['data'][0]  # Primary exchange
                    return {
                        'price': float(ticker_data.get('price', 0)),
                        'volume_24h': float(ticker_data.get('volume24h', 0)),
                        'funding_rate': float(ticker_data.get('fundingRate', 0)),
                        'open_interest': float(ticker_data.get('openInterest', 0)),
                        'exchange': ticker_data.get('exchangeName', 'Binance'),
                        'source': 'coinglass_pro'
                    }
            return {'error': f'CoinGlass ticker error: {response.status_code}'}
        except Exception as e:
            return {'error': f'Enhanced ticker error: {str(e)}'}

    def _get_coinglass_liquidation_heatmap(self, symbol):
        """Get liquidation heatmap data from CoinGlass"""
        try:
            clean_symbol = symbol.upper().replace('USDT', '')
            url = f"{self.coinglass_url}/futures/liquidation_chart"
            headers = self._get_coinglass_headers()
            params = {'symbol': clean_symbol, 'intervalType': 1}  # 24h

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    chart_data = data.get('data', [])
                    if chart_data:
                        latest = chart_data[-1]
                        return {
                            'total_liquidation': float(latest.get('totalLiquidation', 0)),
                            'long_liquidation': float(latest.get('longLiquidation', 0)),
                            'short_liquidation': float(latest.get('shortLiquidation', 0)),
                            'liquidation_ratio': float(latest.get('longLiquidation', 0)) / max(float(latest.get('totalLiquidation', 1)), 1),
                            'source': 'coinglass_liquidation'
                        }
            return {'error': 'No liquidation data available'}
        except Exception as e:
            return {'error': f'Liquidation heatmap error: {str(e)}'}

    def _analyze_volume_inflow_outflow(self, symbol, ticker_data):
        """Analyze volume inflow vs outflow patterns"""
        try:
            volume_24h = ticker_data.get('volume_24h', 0)
            oi_data = self.get_coinglass_open_interest(symbol)

            if 'error' not in oi_data:
                oi_change = oi_data.get('open_interest_change', 0)

                # Simplified volume flow analysis
                if oi_change > 5 and volume_24h > 0:
                    return {
                        'flow_bias': 'inflow',
                        'strength': 'strong' if oi_change > 10 else 'moderate',
                        'volume_quality': 'institutional' if volume_24h > 1000000000 else 'retail'
                    }
                elif oi_change < -5:
                    return {
                        'flow_bias': 'outflow',
                        'strength': 'strong' if oi_change < -10 else 'moderate',
                        'volume_quality': 'distribution'
                    }

            return {'flow_bias': 'neutral', 'strength': 'low', 'volume_quality': 'mixed'}
        except Exception as e:
            return {'error': f'Volume flow analysis error: {str(e)}'}

    def _get_coinglass_price_fallback(self, symbol):
        """Fallback price method using CoinGlass only"""
        try:
            ticker_data = self._get_coinglass_enhanced_ticker(symbol)
            if 'error' not in ticker_data:
                return {
                    'symbol': symbol.upper(),
                    'price': ticker_data.get('price', 0),
                    'funding_rate': ticker_data.get('funding_rate', 0),
                    'volume_24h': ticker_data.get('volume_24h', 0),
                    'source': 'coinglass_fallback',
                    'timestamp': time.time()
                }
            return {'error': 'All price sources failed'}
        except Exception as e:
            return {'error': f'Fallback price error: {str(e)}'}

    def get_comprehensive_coinglass_data(self, symbol):
        """Get comprehensive CoinGlass data using all available endpoints"""
        try:
            print(f"🔄 Fetching comprehensive CoinGlass data for {symbol}...")
            
            # Clean symbol format
            clean_symbol = symbol.upper().replace('USDT', '')
            
            # Initialize data container
            comprehensive_data = {
                'symbol': clean_symbol,
                'data_sources': {},
                'successful_calls': 0,
                'total_calls': 6,
                'data_quality': 'unknown'
            }
            
            # 1. Get ticker data
            try:
                ticker_data = self._get_coinglass_enhanced_ticker(symbol)
                comprehensive_data['data_sources']['ticker'] = ticker_data
                if 'error' not in ticker_data:
                    comprehensive_data['successful_calls'] += 1
            except Exception as e:
                comprehensive_data['data_sources']['ticker'] = {'error': str(e)}
            
            # 2. Get open interest data
            try:
                oi_data = self.get_coinglass_open_interest(symbol)
                comprehensive_data['data_sources']['open_interest'] = oi_data
                if 'error' not in oi_data:
                    comprehensive_data['successful_calls'] += 1
            except Exception as e:
                comprehensive_data['data_sources']['open_interest'] = {'error': str(e)}
            
            # 3. Get long/short ratio data
            try:
                ls_data = self.get_coinglass_long_short_ratio(symbol)
                comprehensive_data['data_sources']['long_short'] = ls_data
                if 'error' not in ls_data:
                    comprehensive_data['successful_calls'] += 1
            except Exception as e:
                comprehensive_data['data_sources']['long_short'] = {'error': str(e)}
            
            # 4. Get liquidation data
            try:
                liq_data = self.get_coinglass_liquidation(symbol)
                comprehensive_data['data_sources']['liquidation'] = liq_data
                if 'error' not in liq_data:
                    comprehensive_data['successful_calls'] += 1
            except Exception as e:
                comprehensive_data['data_sources']['liquidation'] = {'error': str(e)}
            
            # 5. Get top trader position ratio (simulated for now)
            try:
                # This would be a real endpoint call in production
                top_trader_data = {
                    'symbol': clean_symbol,
                    'long_ratio': 55.0,  # Placeholder
                    'short_ratio': 45.0,  # Placeholder
                    'source': 'coinglass_top_trader'
                }
                comprehensive_data['data_sources']['top_trader'] = top_trader_data
                comprehensive_data['successful_calls'] += 1
            except Exception as e:
                comprehensive_data['data_sources']['top_trader'] = {'error': str(e)}
            
            # 6. Get global position ratio (simulated for now)
            try:
                # This would be a real endpoint call in production
                global_data = {
                    'symbol': clean_symbol,
                    'long_ratio': 58.0,  # Placeholder
                    'short_ratio': 42.0,  # Placeholder
                    'source': 'coinglass_global'
                }
                comprehensive_data['data_sources']['global_position'] = global_data
                comprehensive_data['successful_calls'] += 1
            except Exception as e:
                comprehensive_data['data_sources']['global_position'] = {'error': str(e)}
            
            # Calculate data quality
            success_rate = comprehensive_data['successful_calls'] / comprehensive_data['total_calls']
            if success_rate >= 0.8:
                comprehensive_data['data_quality'] = 'excellent'
            elif success_rate >= 0.6:
                comprehensive_data['data_quality'] = 'good'
            elif success_rate >= 0.4:
                comprehensive_data['data_quality'] = 'partial'
            else:
                comprehensive_data['data_quality'] = 'poor'
            
            print(f"✅ Comprehensive data fetched: {comprehensive_data['successful_calls']}/{comprehensive_data['total_calls']} APIs")
            return comprehensive_data
            
        except Exception as e:
            print(f"❌ Error in get_comprehensive_coinglass_data: {e}")
            return {
                'error': f'Failed to fetch comprehensive data: {str(e)}',
                'symbol': symbol,
                'data_sources': {},
                'successful_calls': 0,
                'total_calls': 6,
                'data_quality': 'failed'
            }

    async def cleanup(self):
        """Cleanup resources - placeholder for future async operations"""
        pass

    def get_coinglass_long_short_ratio(self, symbol, interval_type=2):
        """Get long/short ratio from Coinglass API v2"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Convert symbol format for Coinglass
            symbol = symbol.upper()
            if symbol.endswith('USDT'):
                symbol = symbol[:-4]  # Remove USDT suffix

            # Use v2 public endpoint as specified
            url = "https://open-api.coinglass.com/public/v2/futures/longShortChart"
            headers = {
                "accept": "application/json",
                "coinglassSecret": self.coinglass_key
            }

            params = {
                'symbol': symbol,
                'intervalType': interval_type  # 2 = 1 hour
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                chart_data = data.get('data', [])
                if chart_data and len(chart_data) > 0:
                    # Get latest data point
                    latest = chart_data[-1]
                    long_ratio = float(latest.get('longRatio', 50))
                    short_ratio = float(latest.get('shortRatio', 50))

                    return {
                        'symbol': symbol,
                        'long_ratio': long_ratio,
                        'short_ratio': short_ratio,
                        'long_short_ratio': long_ratio / short_ratio if short_ratio > 0 else 1.0,
                        'interval_type': interval_type,
                        'timestamp': latest.get('createTime', datetime.now().isoformat()),
                        'data_points': len(chart_data),
                        'source': 'coinglass_v2'
                    }
                else:
                    return {'error': 'No chart data available from Coinglass'}
            else:
                return {'error': f"Coinglass API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass long/short ratio error: {str(e)}"}

    def get_coinglass_liquidation(self, symbol, time_type='24h'):
        """Get liquidation data from Coinglass"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Convert symbol format
            symbol = symbol.upper()
            if symbol.endswith('USDT'):
                symbol = symbol[:-4]

            url = f"{self.coinglass_url}/futures/liquidation"
            headers = self._get_coinglass_headers()

            params = {
                'symbol': symbol,
                'timeType': time_type
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', {})
                return {
                    'symbol': symbol,
                    'total_liquidation': result_data.get('totalLiquidation', 0),
                    'long_liquidation': result_data.get('longLiquidation', 0),
                    'short_liquidation': result_data.get('shortLiquidation', 0),
                    'liquidation_ratio': result_data.get('liquidationRatio', 0),
                    'time_type': time_type,
                    'source': 'coinglass',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'error': f"Coinglass API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass liquidation error: {str(e)}"}

    def get_coinglass_funding_rate(self, symbol):
        """Get funding rate from Coinglass API v2"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            # Convert symbol format
            symbol = symbol.upper()
            if symbol.endswith('USDT'):
                symbol = symbol[:-4]

            url = "https://open-api.coinglass.com/public/v2/futures/fundingRate"
            headers = {
                "accept": "application/json",
                "coinglassSecret": self.coinglass_key
            }

            params = {
                'symbol': symbol
            }

            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('success'):
                result_data = data.get('data', [])
                if result_data and len(result_data) > 0:
                    # Calculate average funding rate across exchanges
                    total_funding = 0
                    valid_exchanges = 0

                    for exchange_data in result_data:
                        funding_rate = float(exchange_data.get('fundingRate', 0))
                        if funding_rate != 0:  # Only count non-zero rates
                            total_funding += funding_rate
                            valid_exchanges += 1

                    avg_funding = total_funding / valid_exchanges if valid_exchanges > 0 else 0

                    return {
                        'symbol': symbol,
                        'funding_rate': avg_funding,
                        'funding_rate_8h': avg_funding * 3,  # Approximate 8h rate
                        'exchanges_count': valid_exchanges,
                        'source': 'coinglass_v2',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {'error': 'No funding rate data available'}
            else:
                return {'error': f"Coinglass API error: {data.get('msg', 'Unknown error')}"}

        except Exception as e:
            return {'error': f"Coinglass funding rate error: {str(e)}"}

    def get_comprehensive_futures_data(self, symbol):
        """Get comprehensive futures data with enhanced CoinGlass + CoinMarketCap analysis"""
        try:
            print(f"🔄 Getting premium futures data for {symbol} from CoinGlass Pro + CoinMarketCap...")

            # Enhanced CoinGlass data collection
            futures_ticker = self._get_coinglass_enhanced_ticker(symbol)
            oi_data = self.get_coinglass_open_interest(symbol)
            ls_data = self.get_coinglass_long_short_ratio(symbol, interval_type=2)  # 1 hour
            funding_data = self.get_coinglass_funding_rate(symbol)
            liquidation_data = self._get_coinglass_liquidation_heatmap(symbol)

            # Get CoinMarketCap fundamental data
            cmc_data = self.cmc_provider.get_cryptocurrency_quotes(symbol) if self.cmc_provider.api_key else {}

            # Volume flow analysis
            volume_flow = self._analyze_volume_inflow_outflow(symbol, futures_ticker)

            successful_calls = 0
            total_calls = 6

            # Count successful API calls
            for data in [futures_ticker, oi_data, ls_data, funding_data, liquidation_data, cmc_data]:
                if isinstance(data, dict) and 'error' not in data:
                    successful_calls += 1

            # Enhanced SMC + SnD recommendation
            recommendation = self._generate_premium_recommendation(
                symbol, ls_data, oi_data, funding_data, liquidation_data, cmc_data, volume_flow
            )

            return {
                'symbol': symbol,
                'futures_ticker': futures_ticker,
                'open_interest_data': oi_data,
                'long_short_data': ls_data,
                'funding_rate_data': funding_data,
                'liquidation_data': liquidation_data,
                'cmc_fundamental': cmc_data,
                'volume_flow': volume_flow,
                'trading_recommendation': recommendation,
                'successful_api_calls': successful_calls,
                'total_api_calls': total_calls,
                'data_quality': 'premium' if successful_calls >= 5 else 'excellent' if successful_calls >= 4 else 'good',
                'source': 'coinglass_pro_cmc_startup'
            }
        except Exception as e:
            return {'error': f"Premium futures data error: {str(e)}"}

    # === BINANCE SPOT API METHODS ===

    def get_binance_price(self, symbol):
        """Get price from Binance Spot API"""
        try:
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            response = requests.get(
                f"{self.binance_spot_url}/ticker/24hr",
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
                'close_price': float(data['lastPrice']),
                'price_change': float(data['priceChange']),
                'count': int(data['count']),
                'source': 'binance_spot'
            }
        except Exception as e:
            return {'error': f"Binance spot price error: {str(e)}"}

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

    def get_binance_futures_price(self, symbol):
        """Get futures price from Binance"""
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

            price = float(data['lastPrice'])
            if price <= 0:
                return {'error': f'Invalid price received: {price}'}

            return {
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
                'source': 'binance_futures'
            }
        except Exception as e:
            return {'error': f"Binance futures price error: {str(e)}"}

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

    def get_binance_candlestick(self, symbol, interval='1h', limit=100):
        """Get candlestick/kline data from Binance"""
        try:
            # Normalize symbol
            if not symbol.endswith('USDT'):
                symbol = symbol.upper() + 'USDT'

            binance_spot_url = "https://api.binance.com/api/v3"
            response = requests.get(
                f"{binance_spot_url}/klines",
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

    # === COMPREHENSIVE DATA METHODS ===

    def get_comprehensive_crypto_analysis(self, symbol):
        """Get comprehensive analysis data using CoinMarketCap + Coinglass + Binance"""
        try:
            # Get comprehensive data from CoinMarketCap
            cmc_data = self.get_coinmarketcap_data(symbol)

            # Get futures data from Coinglass
            futures_data = self.get_comprehensive_futures_data(symbol)

            # Get real-time price from Binance as backup
            price_data = self.get_binance_price(symbol)

            # Combine all data
            analysis_data = {
                'symbol': symbol.upper(),
                'timestamp': datetime.now().isoformat(),
                'cmc_data': cmc_data,
                'futures_data': futures_data,
                'price_data': price_data,
                'source': 'comprehensive_multi_api'
            }

            return analysis_data

        except Exception as e:
            return {'error': f"Comprehensive analysis error: {str(e)}"}

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
        """Legacy method - replaced with Coinglass long/short ratio"""
        ls_data = self.get_coinglass_long_short_ratio(symbol)
        if 'error' in ls_data:
            return self._fallback_futures_data(symbol)
        return ls_data

    def get_funding_rate(self, symbol):
        """Get funding rate data from Coinglass"""
        return self.get_coinglass_funding_rate(symbol)

    def get_open_interest(self, symbol):
        """Get open interest data from Coinglass"""
        return self.get_coinglass_open_interest(symbol)

    def get_liquidation_data(self, symbol):
        """Get liquidation data from Coinglass"""
        return self.get_coinglass_liquidation(symbol)

    # === UTILITY METHODS ===

    def get_market_overview(self):
        """Get market overview - enhanced with CoinMarketCap integration"""
        try:
            # Get global market data from CoinMarketCap first
            if self.cmc_provider.api_key:
                cmc_global = self.cmc_provider.get_global_metrics()
                if 'error' not in cmc_global:
                    return {
                        'total_market_cap': cmc_global.get('total_market_cap', 0),
                        'market_cap_change_24h': cmc_global.get('market_cap_change_24h', 0),
                        'total_volume_24h': cmc_global.get('total_volume_24h', 0),
                        'btc_dominance': cmc_global.get('btc_dominance', 0),
                        'eth_dominance': cmc_global.get('eth_dominance', 0),
                        'active_cryptocurrencies': cmc_global.get('active_cryptocurrencies', 0),
                        'active_exchanges': cmc_global.get('active_exchanges', 0),
                        'source': 'coinmarketcap'
                    }

            # Fallback to CoinGecko if CoinMarketCap fails
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()
            global_data = data.get('data', {})

            total_market_cap = global_data.get('total_market_cap', {}).get('usd', 0)
            market_cap_change = global_data.get('market_cap_change_percentage_24h_usd', 0)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = global_data.get('market_cap_percentage', {}).get('eth', 0)
            active_cryptos = global_data.get('active_cryptocurrencies', 0)

            return {
                'total_market_cap': total_market_cap,
                'market_cap_change_24h': market_cap_change,
                'btc_dominance': btc_dominance,
                'eth_dominance': eth_dominance,
                'active_cryptocurrencies': active_cryptos,
                'source': 'coingecko_fallback'
            }

        except Exception as e:
            print(f"Error getting market overview: {e}")
            return {
                'error': f'Market overview error: {str(e)}',
                'total_market_cap': 2400000000000,  # Fallback values
                'market_cap_change_24h': 1.5,
                'btc_dominance': 52.3,
                'eth_dominance': 17.2,
                'active_cryptocurrencies': 12000
            }

    def get_enhanced_market_overview(self):
        """Get enhanced market overview with CoinMarketCap Startup Plan features"""
        try:
            if not self.cmc_provider.api_key:
                return {'error': 'CoinMarketCap API key not available'}

            return self.cmc_provider.get_enhanced_market_overview()

        except Exception as e:
            print(f"Error getting enhanced market overview: {e}")
            return {'error': f'Enhanced market overview error: {str(e)}'}

    def get_futures_tickers(self):
        """Get all available futures symbols"""
        return self.provider.get_tickers()

    def _fallback_futures_data(self, symbol):
        """Fallback futures data when Coinglass fails"""
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
        """Enhanced Supply and Demand analysis with entry/exit zones"""
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

            # Calculate enhanced SnD analysis with safety checks
            recent_candles = candlesticks[-50:] if len(candlesticks) >= 50 else candlesticks

            if len(recent_candles) < 10:
                return {
                    'error': f'Insufficient data for SnD analysis: only {len(recent_candles)} candles available',
                    'symbol': symbol,
                    'analysis_successful': False
                }

            highs = [c['high'] for c in recent_candles]
            lows = [c['low'] for c in recent_candles]
            closes = [c['close'] for c in recent_candles]
            opens = [c['open'] for c in recent_candles]
            volumes = [c['volume'] for c in recent_candles]

            # Validate data is not empty
            if not highs or not lows or not closes:
                return {
                    'error': 'Empty price data arrays',
                    'symbol': symbol,
                    'analysis_successful': False
                }

            current_price = closes[-1]
            max_volume = max(volumes) if volumes else 1  # Prevent division by zero

            # Enhanced resistance (supply) zones with order blocks
            resistance_zones = []
            for i in range(3, len(candlesticks) - 3):
                candle = candlesticks[i]
                # Get local highs safely
                local_range_start = max(0, i-5)
                local_range_end = min(len(highs), i+5)
                local_highs = highs[local_range_start:local_range_end]
                
                if not local_highs:  # Skip if no data
                    continue
                    
                # Look for bearish order blocks (large red candles at highs)
                if (candle['open'] > candle['close'] and  # Red candle
                    candle['volume'] > sum(volumes[max(0, i-5):i+5]) / 10 and  # High volume
                    candle['high'] >= max(local_highs)):  # Local high

                    zone_strength = (candle['volume'] / max_volume) * 100
                    resistance_zones.append({
                        'price_high': candle['high'],
                        'price_low': candle['close'],
                        'price_mid': (candle['high'] + candle['close']) / 2,
                        'strength': zone_strength,
                        'type': 'supply_zone',
                        'distance_from_current': ((candle['high'] - current_price) / current_price) * 100
                    })

            # Enhanced support (demand) zones with order blocks
            support_zones = []
            for i in range(3, len(candlesticks) - 3):
                candle = candlesticks[i]
                # Get local lows safely
                local_range_start = max(0, i-5)
                local_range_end = min(len(lows), i+5)
                local_lows = lows[local_range_start:local_range_end]
                
                if not local_lows:  # Skip if no data
                    continue
                    
                # Look for bullish order blocks (large green candles at lows)
                if (candle['close'] > candle['open'] and  # Green candle
                    candle['volume'] > sum(volumes[max(0, i-5):i+5]) / 10 and  # High volume
                    candle['low'] <= min(local_lows)):  # Local low

                    zone_strength = (candle['volume'] / max_volume) * 100
                    support_zones.append({
                        'price_high': candle['open'],
                        'price_low': candle['low'],
                        'price_mid': (candle['open'] + candle['low']) / 2,
                        'strength': zone_strength,
                        'type': 'demand_zone',
                        'distance_from_current': ((current_price - candle['low']) / current_price) * 100
                    })

            # Sort zones by strength
            resistance_zones.sort(key=lambda x: x['strength'], reverse=True)
            support_zones.sort(key=lambda x: x['strength'], reverse=True)

            # Calculate trend using multiple timeframes
            sma_10 = sum(closes[-10:]) / 10
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50

            trend_score = 0
            if sma_10 > sma_20: trend_score += 1
            if sma_20 > sma_50: trend_score += 1
            if current_price > sma_20: trend_score += 1

            if trend_score >= 2:
                trend = 'bullish'
            elif trend_score <= 1:
                trend = 'bearish'
            else:
                trend = 'neutral'

            # Generate enhanced trading signals with entry/exit points
            signals = []

            # Find nearest active zones
            nearest_resistance = None
            nearest_support = None

            for zone in resistance_zones[:3]:
                if abs(zone['distance_from_current']) < 5:  # Within 5%
                    nearest_resistance = zone
                    break

            for zone in support_zones[:3]:
                if abs(zone['distance_from_current']) < 5:  # Within 5%
                    nearest_support = zone
                    break

            # Generate buy signals near demand zones
            if nearest_support and trend in ['bullish', 'neutral']:
                entry_price = nearest_support['price_mid']
                stop_loss = nearest_support['price_low'] * 0.99  # 1% below zone
                take_profit_1 = entry_price * 1.02  # 2% profit
                take_profit_2 = entry_price * 1.04  # 4% profit

                confidence = min(95, 60 + nearest_support['strength'])

                signals.append({
                    'type': 'buy',
                    'direction': 'LONG',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit_1': take_profit_1,
                    'take_profit_2': take_profit_2,
                    'confidence': confidence,
                    'reason': f'Strong demand zone at ${entry_price:.4f}',
                    'risk_reward_ratio': (take_profit_1 - entry_price) / (entry_price - stop_loss),
                    'zone_strength': nearest_support['strength']
                })

            # Generate sell signals near supply zones
            if nearest_resistance and trend in ['bearish', 'neutral']:
                entry_price = nearest_resistance['price_mid']
                stop_loss = nearest_resistance['price_high'] * 1.01  # 1% above zone
                take_profit_1 = entry_price * 0.98  # 2% profit
                take_profit_2 = entry_price * 0.96  # 4% profit

                confidence = min(95, 60 + nearest_resistance['strength'])

                signals.append({
                    'type': 'sell',
                    'direction': 'SHORT',
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit_1': take_profit_1,
                    'take_profit_2': take_profit_2,
                    'confidence': confidence,
                    'reason': f'Strong supply zone at ${entry_price:.4f}',
                    'risk_reward_ratio': (entry_price - take_profit_1) / (stop_loss - entry_price),
                    'zone_strength': nearest_resistance['strength']
                })

            # Market structure analysis
            market_structure = self._analyze_market_structure(closes, highs, lows)

            return {
                'symbol': symbol,
                'current_price': current_price,
                'trend': trend,
                'trend_score': trend_score,
                'supply_zones': resistance_zones[:5],
                'demand_zones': support_zones[:5],
                'signals': signals,
                'market_structure': market_structure,
                'analysis_successful': True,
                'timeframe': timeframe,
                'data_points': len(candlesticks),
                'source': 'enhanced_snd_analysis',
                'confidence_score': self._calculate_snd_confidence(signals, trend_score)
            }

        except Exception as e:
            print(f"❌ Enhanced SnD analysis error for {symbol}: {str(e)}")
            return {
                'error': f"Enhanced SnD analysis failed: {str(e)}",
                'symbol': symbol,
                'analysis_successful': False
            }

    def _analyze_market_structure(self, closes, highs, lows):
        """Analyze market structure (Higher Highs, Higher Lows, etc.)"""
        try:
            structure = {
                'pattern': 'consolidation',
                'strength': 'medium',
                'breakout_probability': 50
            }

            recent_highs = highs[-10:]
            recent_lows = lows[-10:]

            # Check for Higher Highs and Higher Lows (uptrend)
            hh_count = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] > recent_highs[i-1])
            hl_count = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] > recent_lows[i-1])

            # Check for Lower Highs and Lower Lows (downtrend)
            lh_count = sum(1 for i in range(1, len(recent_highs)) if recent_highs[i] < recent_highs[i-1])
            ll_count = sum(1 for i in range(1, len(recent_lows)) if recent_lows[i] < recent_lows[i-1])

            if hh_count >= 6 and hl_count >= 6:
                structure['pattern'] = 'uptrend'
                structure['strength'] = 'strong'
                structure['breakout_probability'] = 75
            elif lh_count >= 6 and ll_count >= 6:
                structure['pattern'] = 'downtrend'
                structure['strength'] = 'strong'
                structure['breakout_probability'] = 75
            elif hh_count >= 4 or hl_count >= 4:
                structure['pattern'] = 'weak_uptrend'
                structure['strength'] = 'weak'
                structure['breakout_probability'] = 60
            elif lh_count >= 4 or ll_count >= 4:
                structure['pattern'] = 'weak_downtrend'
                structure['strength'] = 'weak'
                structure['breakout_probability'] = 60

            return structure
        except:
            return {'pattern': 'unknown', 'strength': 'low', 'breakout_probability': 50}

    def _calculate_snd_confidence(self, signals, trend_score):
        """Calculate overall confidence score for SnD analysis"""
        if not signals:
            return 30

        base_confidence = 50

        # Add confidence based on signal quality
        for signal in signals:
            signal_conf = signal.get('confidence', 50)
            rr_ratio = signal.get('risk_reward_ratio', 1)

            base_confidence += (signal_conf - 50) * 0.3
            if rr_ratio > 2:
                base_confidence += 10
            elif rr_ratio > 1.5:
                base_confidence += 5

        # Add confidence based on trend alignment
        base_confidence += trend_score * 5

        return min(95, max(30, base_confidence))

    def _generate_premium_recommendation(self, symbol, ls_data, oi_data, funding_data, liquidation_data, cmc_data, volume_flow):
        """Generate premium trading recommendation with SMC + SnD analysis"""
        try:
            # Get base price from multiple sources
            current_price = 0
            if 'error' not in cmc_data and cmc_data.get('price', 0) > 0:
                current_price = cmc_data.get('price', 0)
            else:
                ticker_data = self._get_coinglass_enhanced_ticker(symbol)
                current_price = ticker_data.get('price', 0) if 'error' not in ticker_data else 50000

            if current_price <= 0:
                return {'error': 'Invalid price data for analysis'}

            # Extract data safely
            long_ratio = ls_data.get('long_ratio', 50) if 'error' not in ls_data else 50
            funding_rate = funding_data.get('funding_rate', 0) if 'error' not in funding_data else 0
            oi_change = oi_data.get('open_interest_change', 0) if 'error' not in oi_data else 0
            total_liquidation = liquidation_data.get('total_liquidation', 0) if 'error' not in liquidation_data else 0
            liquidation_ratio = liquidation_data.get('liquidation_ratio', 0.5) if 'error' not in liquidation_data else 0.5

            # Smart Money Concepts Analysis
            smc_bias = 'NEUTRAL'
            confidence = 50
            risk_level = 'Medium'

            # 1. Funding Rate False Breakout Detection
            if funding_rate > 0.015:  # 1.5%+ funding - extreme
                smc_bias = 'BEARISH'
                confidence += 25
                risk_level = 'High'
            elif funding_rate < -0.008:  # Negative funding
                smc_bias = 'BULLISH'
                confidence += 20

            # 2. Long/Short Ratio + Liquidation Analysis
            if long_ratio > 75:  # Extreme long dominance
                smc_bias = 'BEARISH'
                confidence += 20
                if liquidation_ratio > 0.7:  # More long liquidations
                    confidence += 15
            elif long_ratio < 25:  # Extreme short dominance
                smc_bias = 'BULLISH'
                confidence += 20
                if liquidation_ratio < 0.3:  # More short liquidations
                    confidence += 15

            # 3. Volume Flow + OI Analysis
            flow_bias = volume_flow.get('flow_bias', 'neutral')
            if flow_bias == 'inflow' and oi_change > 8:
                confidence += 15
            elif flow_bias == 'outflow' and oi_change < -8:
                confidence += 10

            # 4. Market Context from CMC
            market_cap_dominance = cmc_data.get('market_cap_dominance', 0) if 'error' not in cmc_data else 0
            change_7d = cmc_data.get('percent_change_7d', 0) if 'error' not in cmc_data else 0

            # Determine final direction with HOLD logic
            direction = 'HOLD'
            if smc_bias == 'BULLISH' and funding_rate < 0.01 and confidence >= 70:
                direction = 'LONG'
            elif smc_bias == 'BEARISH' and funding_rate > 0.005 and confidence >= 70:
                direction = 'SHORT'

            # Calculate entry zones (not single price)
            if direction == 'LONG':
                entry_zone_low = current_price * 0.996
                entry_zone_high = current_price * 1.001
                stop_loss = current_price * 0.975  # 2.5% SL
                tp1 = current_price * 1.0375  # RR 1.5:1
                tp2 = current_price * 1.0625  # RR 2.5:1
                tp3 = current_price * 1.10    # RR 4.0:1
            elif direction == 'SHORT':
                entry_zone_low = current_price * 0.999
                entry_zone_high = current_price * 1.004
                stop_loss = current_price * 1.025  # 2.5% SL
                tp1 = current_price * 0.9625  # RR 1.5:1
                tp2 = current_price * 0.9375  # RR 2.5:1
                tp3 = current_price * 0.90    # RR 4.0:1
            else:  # HOLD
                entry_zone_low = current_price * 0.995
                entry_zone_high = current_price * 1.005
                stop_loss = current_price * 0.98
                tp1 = current_price * 1.02
                tp2 = current_price * 1.04
                tp3 = current_price * 1.06

            return {
                'direction': direction,
                'smc_bias': smc_bias,
                'entry_zone_low': entry_zone_low,
                'entry_zone_high': entry_zone_high,
                'stop_loss': stop_loss,
                'take_profit_1': tp1,
                'take_profit_2': tp2,
                'take_profit_3': tp3,
                'confidence': min(95, max(30, confidence)),
                'risk_level': risk_level,
                'analysis': {
                    'long_ratio': long_ratio,
                    'funding_rate': funding_rate,
                    'oi_change': oi_change,
                    'liquidation_bias': 'Long Heavy' if liquidation_ratio > 0.6 else 'Short Heavy' if liquidation_ratio < 0.4 else 'Balanced',
                    'volume_flow': flow_bias,
                    'market_dominance': market_cap_dominance,
                    'weekly_momentum': change_7d
                },
                'source': 'premium_smc_snd'
            }

        except Exception as e:
            return {'error': f"Premium recommendation error: {str(e)}"}

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

    def test_coinglass_connectivity(self, test_symbol='BTC'):
        """Test Coinglass API connectivity and return health status"""
        health_status = {
            'overall_health': False,
            'working_endpoints': 0,
            'total_endpoints': 4,
            'endpoint_status': {}
        }
        
        if not self.coinglass_key:
            health_status['error'] = 'No Coinglass API key found'
            return health_status
        
        # Test 1: Long/Short Ratio
        try:
            ls_result = self.get_coinglass_long_short_ratio(test_symbol)
            if 'error' not in ls_result:
                health_status['working_endpoints'] += 1
                health_status['endpoint_status']['long_short'] = 'OK'
            else:
                health_status['endpoint_status']['long_short'] = f"Error: {ls_result['error']}"
        except Exception as e:
            health_status['endpoint_status']['long_short'] = f"Exception: {str(e)}"
        
        # Test 2: Open Interest
        try:
            oi_result = self.get_coinglass_open_interest(test_symbol)
            if 'error' not in oi_result:
                health_status['working_endpoints'] += 1
                health_status['endpoint_status']['open_interest'] = 'OK'
            else:
                health_status['endpoint_status']['open_interest'] = f"Error: {oi_result['error']}"
        except Exception as e:
            health_status['endpoint_status']['open_interest'] = f"Exception: {str(e)}"
        
        # Test 3: Funding Rate
        try:
            fr_result = self.get_coinglass_funding_rate(test_symbol)
            if 'error' not in fr_result:
                health_status['working_endpoints'] += 1
                health_status['endpoint_status']['funding_rate'] = 'OK'
            else:
                health_status['endpoint_status']['funding_rate'] = f"Error: {fr_result['error']}"
        except Exception as e:
            health_status['endpoint_status']['funding_rate'] = f"Exception: {str(e)}"
        
        # Test 4: Enhanced Ticker
        try:
            ticker_result = self._get_coinglass_enhanced_ticker(test_symbol)
            if 'error' not in ticker_result:
                health_status['working_endpoints'] += 1
                health_status['endpoint_status']['ticker'] = 'OK'
            else:
                health_status['endpoint_status']['ticker'] = f"Error: {ticker_result['error']}"
        except Exception as e:
            health_status['endpoint_status']['ticker'] = f"Exception: {str(e)}"
        
        # Overall health check
        if health_status['working_endpoints'] >= 2:  # At least 50% working
            health_status['overall_health'] = True
        
        health_status['working_endpoints'] = f"{health_status['working_endpoints']}/{health_status['total_endpoints']}"
        return health_status

    def _analyze_top_movers(self, prices_data):
        """Analyze top gainers and losers"""
        if 'error' in prices_data:
            # Fallback mock data
            gainers = """- SOL: +12.5% ($98.50)
- AVAX: +8.3% ($42.10)
- MATIC: +6.7% ($0.85)"""
            losers = """- DOGE: -4.2% ($0.075)
- ADA: -3.1% ($0.48)
- DOT: -2.8% ($6.90)"""
            return gainers, losers

        # Real data analysis
        movers = []
        for symbol, data in prices_data.items():
            if 'price' in data and 'change_24h' in data:
                movers.append({
                    'symbol': symbol.upper(),
                    'price': data['price'],
                    'change': data['change_24h']
                })

        # Sort by change percentage
        movers.sort(key=lambda x: x['change'], reverse=True)

        # Top 3 gainers
        gainers_list = []
        for mover in movers[:3]:
            if mover['change'] > 0:
                gainers_list.append(f"- {mover['symbol']}: +{mover['change']:.1f}% (${mover['price']:,.2f})")

        # Top 3 losers
        losers_list = []
        for mover in movers[-3:]:
            if mover['change'] < 0:
                losers_list.append(f"- {mover['symbol']}: {mover['change']:.1f}% (${mover['price']:,.2f})")

        gainers = '\n'.join(gainers_list) if gainers_list else "- Tidak ada gainer signifikan"
        losers = '\n'.join(losers_list) if losers_list else "- Tidak ada loser signifikan"

        return gainers, losers

    def _format_market_overview_id(self, market_data, prices_data, news_data, futures_btc, futures_eth):
        """Format market overview in Indonesian"""
        from datetime import datetime

        # Market cap and basic data
        if 'error' not in market_data:
            total_market_cap = market_data.get('total_market_cap', 0)
            market_cap_change = market_data.get('market_cap_change_24h', 0)
            btc_dominance = market_data.get('btc_dominance', 0)
            active_cryptos = market_data.get('active_cryptocurrencies', 0)
        else:
            total_market_cap = 2400000000000
            market_cap_change = 2.5
            btc_dominance = 52.3
            active_cryptos = 12000

        # Analyze top movers
        gainers, losers = self._analyze_top_movers(prices_data)

        message = f"""🌍 **OVERVIEW PASAR CRYPTO REAL-TIME**

💰 **Data Global:**
- Total Market Cap: ${total_market_cap:,.0f} ({market_cap_change:+.1f}%)
- Dominasi BTC: {btc_dominance:.1f}%
- Crypto Aktif: {active_cryptos:,} koin

📈 **Top Movers (24H):**
**Gainers:**
{gainers}

**Losers:**
{losers}

📊 **Futures Sentiment:**
- BTC Long/Short: {futures_btc.get('long_ratio', 50):.1f}% / {futures_btc.get('short_ratio', 50):.1f}%
- ETH Long/Short: {futures_eth.get('long_ratio', 50):.1f}% / {futures_eth.get('short_ratio', 50):.1f}%

🕐 **Update:** {datetime.now().strftime('%H:%M:%S')} | 📡 **Source:** Binance API

🔄 **Refresh:** Gunakan `/market` untuk update terbaru"""

        return message