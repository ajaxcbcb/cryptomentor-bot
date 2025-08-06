import requests
import os
import time
import asyncio
from datetime import datetime, timezone
from binance_provider import BinanceFuturesProvider
from coinmarketcap_provider import CoinMarketCapProvider
from coinglass_provider import CoinGlassProvider

class CryptoAPI:
    def __init__(self):
        self.provider = BinanceFuturesProvider()
        self.cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
        self.cmc_provider = CoinMarketCapProvider()
        from coinglass_provider import CoinGlassProvider
        self.coinglass_provider = CoinGlassProvider()

        # Initialize Binance URLs for fallback
        self.binance_spot_url = "https://api.binance.com/api/v3"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1"

        self.cache = {}
        self.cache_duration = 30

        print("🚀 CryptoAPI initialized with CoinGlass V4 + CoinMarketCap")
        self.coinglass_key = self.coinglass_provider.api_key
        self.coinglass_base_url = self.coinglass_provider.base_url
        print(f"📊 CoinGlass V4 API: {self.coinglass_base_url}")
        print(f"🔑 CoinGlass Key: {'✅ Enabled' if self.coinglass_key else '❌ Disabled'}")
        print(f"📊 CoinMarketCap: {'✅ Enabled' if self.cmc_provider.api_key else '❌ Disabled'}")
        print(f"📰 CryptoNews API: {'✅ Enabled' if self.cryptonews_key else '❌ Disabled'}")
        print("⭐ Data Sources: CoinGlass V4 Startup Plan + CoinMarketCap")

        # Verify and patch missing methods
        self._verify_and_patch_methods()

    # === COINGLASS V4 API METHODS ===

    def _get_coinglass_headers(self):
        """Get headers for Coinglass V4 API requests"""
        return {
            "accept": "application/json",
            "X-API-KEY": self.coinglass_key
        }

    def get_futures_price(self, symbol):
        """Get futures price from Coinglass V4"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            clean_symbol = symbol.upper().replace('USDT', '')
            url = f"{self.coinglass_base_url}/futures/ticker"
            headers = self._get_coinglass_headers()
            params = {'symbol': clean_symbol}

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    ticker_data = data['data']
                    if isinstance(ticker_data, list) and len(ticker_data) > 0:
                        primary_data = ticker_data[0]
                    else:
                        primary_data = ticker_data

                    return {
                        'symbol': clean_symbol,
                        'price': float(primary_data.get('price', 0)),
                        'volume_24h': float(primary_data.get('volume24h', 0)),
                        'price_change_24h': float(primary_data.get('priceChangePercent', 0)),
                        'exchange': primary_data.get('exchangeName', 'Binance'),
                        'source': 'coinglass_v4'
                    }

            return {'error': f'Coinglass V4 ticker error: {response.status_code}'}
        except Exception as e:
            return {'error': f'Coinglass V4 ticker error: {str(e)}'}

    def get_open_interest(self, symbol):
        """Get open interest from Coinglass V4"""
        try:
            if not self.coinglass_key:
                print(f"❌ CoinGlass API key not found for {symbol}")
                return {'error': 'Coinglass API key not found'}

            # Clean symbol to basic format (BTC, ETH, etc.)
            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')
            print(f"🔄 Getting open interest for {clean_symbol} from CoinGlass V4...")

            # Use the coinglass_provider for consistent API calls
            result = self.coinglass_provider.get_open_interest_chart(clean_symbol)
            if result and 'error' not in result:
                return {
                    'symbol': clean_symbol,
                    'data': result,
                    'source': 'coinglass_v4_openinterest',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return result if result else {'error': f'No open interest data for {clean_symbol}'}

        except Exception as e:
            print(f"❌ Open interest error for {symbol}: {e}")
            return {'error': f'Open interest error: {str(e)}'}

    def get_funding_rate(self, symbol):
        """Get funding rate from Coinglass V4"""
        try:
            if not self.coinglass_key:
                print(f"❌ CoinGlass API key not found for {symbol}")
                return {'error': 'Coinglass API key not found'}

            # Clean symbol to basic format (BTC, ETH, etc.)
            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')
            print(f"🔄 Getting funding rate for {clean_symbol} from CoinGlass V4...")

            # Use the coinglass_provider for consistent API calls
            result = self.coinglass_provider.get_funding_rate_chart(clean_symbol)
            if result and 'error' not in result:
                return {
                    'symbol': clean_symbol,
                    'data': result,
                    'source': 'coinglass_v4_fundingrate',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return result if result else {'error': f'No funding rate data for {clean_symbol}'}

        except Exception as e:
            print(f"❌ Funding rate error for {symbol}: {e}")
            return {'error': f'Funding rate error: {str(e)}'}

    def get_long_short_ratio(self, symbol):
        """Get long/short ratio from Coinglass V4"""
        try:
            if not self.coinglass_key:
                print(f"❌ CoinGlass API key not found for {symbol}")
                return {'error': 'Coinglass API key not found'}

            # Clean symbol to basic format (BTC, ETH, etc.)
            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')
            print(f"🔄 Getting long/short ratio for {clean_symbol} from CoinGlass V4...")

            # Use the coinglass_provider for consistent API calls
            result = self.coinglass_provider.get_long_short_ratio(clean_symbol)
            if result and 'error' not in result:
                return {
                    'symbol': clean_symbol,
                    'data': result,
                    'source': 'coinglass_v4_longshortratio',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return result if result else {'error': f'No long/short ratio data for {clean_symbol}'}

        except Exception as e:
            print(f"❌ Long/short ratio error for {symbol}: {e}")
            return {'error': f'Long/short ratio error: {str(e)}'}

    def get_liquidation_price_range(self, symbol):
        """Get liquidation price ranges from Coinglass V4"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            clean_symbol = symbol.upper().replace('USDT', '')
            url = f"{self.coinglass_base_url}/liquidation_map"
            headers = self._get_coinglass_headers()
            params = {'symbol': clean_symbol}

            response = requests.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    liq_data = data['data']

                    if isinstance(liq_data, list) and len(liq_data) > 0:
                        latest = liq_data[-1]
                    else:
                        latest = liq_data

                    total_liquidation = float(latest.get('totalLiquidation', 0))
                    long_liquidation = float(latest.get('longLiquidation', 0))
                    short_liquidation = float(latest.get('shortLiquidation', 0))

                    return {
                        'symbol': clean_symbol,
                        'total_liquidation': total_liquidation,
                        'long_liquidation': long_liquidation,
                        'short_liquidation': short_liquidation,
                        'liquidation_ratio': long_liquidation / max(total_liquidation, 1),
                        'dominant_side': 'Long Heavy' if long_liquidation > short_liquidation * 1.5 else 'Short Heavy' if short_liquidation > long_liquidation * 1.5 else 'Balanced',
                        'price_ranges': latest.get('priceRanges', []),
                        'source': 'coinglass_v4'
                    }

            return {'error': f'Coinglass V4 liquidation error: {response.status_code}'}
        except Exception as e:
            return {'error': f'Coinglass V4 liquidation error: {str(e)}'}

    def get_comprehensive_futures_data(self, symbol):
        """Get comprehensive futures data from Coinglass V4"""
        try:
            print(f"🔄 Getting comprehensive futures data for {symbol} from Coinglass V4...")

            # Clean symbol for consistency
            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')

            # Get all data from V4 endpoints using coinglass_provider
            price_data = self.get_futures_price(clean_symbol)
            oi_data = self.get_open_interest(clean_symbol)
            funding_data = self.get_funding_rate(clean_symbol)
            ls_data = self.get_long_short_ratio(clean_symbol)
            liquidation_data = self.get_liquidation_price_range(clean_symbol)

            successful_calls = 0
            total_calls = 5

            # Count successful API calls
            for data in [price_data, oi_data, funding_data, ls_data, liquidation_data]:
                if isinstance(data, dict) and 'error' not in data:
                    successful_calls += 1

            # Determine data quality based on success rate
            if successful_calls >= 4:
                data_quality = 'excellent'
            elif successful_calls >= 2:
                data_quality = 'good'
            elif successful_calls >= 1:
                data_quality = 'fair'
            else:
                data_quality = 'poor'

            return {
                'symbol': clean_symbol,
                'price_data': price_data,
                'open_interest_data': oi_data,
                'funding_rate_data': funding_data,
                'long_short_data': ls_data,
                'liquidation_data': liquidation_data,
                'successful_api_calls': successful_calls,
                'total_api_calls': total_calls,
                'data_quality': data_quality,
                'source': 'coinglass_v4_comprehensive',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Comprehensive futures data error: {e}")
            return {'error': f"Coinglass V4 comprehensive data error: {str(e)}"}

    # === COINMARKETCAP API METHODS ===

    def get_coinmarketcap_summary(self, symbol):
        """Get comprehensive crypto summary from CoinMarketCap"""
        try:
            if not self.cmc_provider.api_key:
                return {'error': 'CoinMarketCap API key not found'}

            # Get quotes data
            quotes_data = self.cmc_provider.get_cryptocurrency_quotes(symbol)
            if 'error' in quotes_data:
                return quotes_data

            # Get info data
            info_data = self.cmc_provider.get_cryptocurrency_info(symbol)

            # Combine data
            result = {
                'symbol': symbol.upper(),
                'price': quotes_data.get('price', 0),
                'market_cap': quotes_data.get('market_cap', 0),
                'volume_24h': quotes_data.get('volume_24h', 0),
                'percent_change_24h': quotes_data.get('percent_change_24h', 0),
                'percent_change_7d': quotes_data.get('percent_change_7d', 0),
                'cmc_rank': quotes_data.get('cmc_rank', 0),
                'circulating_supply': quotes_data.get('circulating_supply', 0),
                'max_supply': quotes_data.get('max_supply', 0),
                'market_cap_dominance': quotes_data.get('market_cap_dominance', 0),
                'source': 'coinmarketcap'
            }

            # Add info data if available
            if 'error' not in info_data:
                result.update({
                    'name': info_data.get('name', ''),
                    'description': info_data.get('description', ''),
                    'website': info_data.get('website', []),
                    'tags': info_data.get('tags', []),
                    'category': info_data.get('category', '')
                })

            return result

        except Exception as e:
            return {'error': f"CoinMarketCap summary error: {str(e)}"}

    def get_coinmarketcap_global_market_data(self):
        """Get global market data from CoinMarketCap"""
        try:
            if not self.cmc_provider.api_key:
                return {'error': 'CoinMarketCap API key not found'}

            global_data = self.cmc_provider.get_global_metrics()
            if 'error' in global_data:
                return global_data

            # Get top cryptocurrencies
            top_cryptos = self.cmc_provider.get_top_cryptocurrencies(5)

            # Get Fear & Greed Index
            fng_data = self.cmc_provider.get_fear_greed_index()

            return {
                'total_market_cap': global_data.get('total_market_cap', 0),
                'market_cap_change_24h': global_data.get('market_cap_change_24h', 0),
                'total_volume_24h': global_data.get('total_volume_24h', 0),
                'btc_dominance': global_data.get('btc_dominance', 0),
                'eth_dominance': global_data.get('eth_dominance', 0),
                'active_cryptocurrencies': global_data.get('active_cryptocurrencies', 0),
                'active_exchanges': global_data.get('active_exchanges', 0),
                'top_cryptocurrencies': top_cryptos.get('data', []) if 'error' not in top_cryptos else [],
                'fear_greed_index': fng_data.get('value', 50) if 'error' not in fng_data else 50,
                'fear_greed_classification': fng_data.get('value_classification', 'Neutral') if 'error' not in fng_data else 'Neutral',
                'source': 'coinmarketcap_global'
            }

        except Exception as e:
            return {'error': f"CoinMarketCap global data error: {str(e)}"}

    # === MAIN API METHODS ===

    def get_crypto_price(self, symbol, force_refresh=False):
        """Get cryptocurrency price with CoinMarketCap integration"""
        try:
            cache_key = f"price_{symbol.upper()}"

            # Check cache first
            if not force_refresh and cache_key in self.cache:
                cached_data = self.cache[cache_key]
                cache_time = cached_data.get('timestamp', 0)
                if time.time() - cache_time < self.cache_duration:
                    print(f"📊 Using cached price for {symbol}")
                    return cached_data

            # Primary: CoinMarketCap for price data
            if self.cmc_provider.api_key:
                print(f"🔄 Fetching price for {symbol} from CoinMarketCap...")
                cmc_data = self.cmc_provider.get_cryptocurrency_quotes(symbol)

                price_value = cmc_data.get('price', 0)
                if 'error' not in cmc_data and price_value is not None and price_value > 0:
                    result = {
                        'symbol': symbol.upper(),
                        'price': cmc_data.get('price', 0),
                        'change_24h': cmc_data.get('percent_change_24h', 0),
                        'change_7d': cmc_data.get('percent_change_7d', 0),
                        'volume_24h': cmc_data.get('volume_24h', 0),
                        'market_cap': cmc_data.get('market_cap', 0),
                        'source': 'coinmarketcap',
                        'timestamp': time.time()
                    }

                    # Cache the result
                    self.cache[cache_key] = result
                    print(f"✅ Price data for {symbol}: ${result['price']:.4f} (CoinMarketCap)")
                    return result

            # Fallback to Binance
            return self._get_binance_price_fallback(symbol)

        except Exception as e:
            print(f"❌ Price fetch error for {symbol}: {e}")
            return self._get_binance_price_fallback(symbol)

    def _get_binance_price_fallback(self, symbol):
        """Fallback price method using Binance"""
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
                'volume_24h': float(data['quoteVolume']),
                'source': 'binance_fallback',
                'timestamp': time.time()
            }
        except Exception as e:
            return {'error': f'All price sources failed: {str(e)}'}

    def get_market_overview(self):
        """Get market overview from CoinMarketCap"""
        try:
            if self.cmc_provider.api_key:
                return self.get_coinmarketcap_global_market_data()
            else:
                return {'error': 'CoinMarketCap API key not available'}
        except Exception as e:
            return {'error': f'Market overview error: {str(e)}'}

    # === CRYPTO NEWS ===

    def get_crypto_news(self, limit=5):
        """Get crypto news"""
        try:
            if not self.cryptonews_key:
                return self._get_fallback_news(limit)

            url = "https://cryptonews-api.com/api/v1/category"
            params = {
                'section': 'general',
                'items': limit,
                'page': 1,
                'token': self.cryptonews_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'success':
                news_items = []
                for item in data.get('data', []):
                    news_items.append({
                        'title': item.get('title', 'No title'),
                        'text': item.get('text', 'No description'),
                        'url': item.get('news_url', ''),
                        'date': item.get('date', ''),
                        'source_name': item.get('source_name', 'CryptoNews'),
                        'source': 'cryptonews_api'
                    })
                return news_items
            else:
                return self._get_fallback_news(limit)

        except Exception as e:
            print(f"News API error: {e}")
            return self._get_fallback_news(limit)

    def _get_fallback_news(self, limit):
        """Fallback news when API fails"""
        fallback_news = [
            {
                'title': 'Bitcoin Continues Strong Market Performance',
                'text': 'Bitcoin maintains its position as the leading cryptocurrency with strong institutional adoption.',
                'url': 'https://example.com',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source_name': 'CryptoMentor AI',
                'source': 'fallback'
            },
            {
                'title': 'Ethereum Network Upgrades Show Promise',
                'text': 'Ethereum continues to improve its scalability and efficiency with ongoing network upgrades.',
                'url': 'https://example.com',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source_name': 'CryptoMentor AI',
                'source': 'fallback'
            }
        ]
        return fallback_news[:limit]

    def analyze_supply_demand(self, symbol, timeframe="15m"):
        """Analyze supply and demand zones for a cryptocurrency"""
        try:
            # Get price data from CoinMarketCap or Binance
            price_data = self.get_crypto_price(symbol)

            if 'error' in price_data:
                return {'error': f'Failed to get price data: {price_data["error"]}'}

            current_price = price_data.get('price', 0)

            if current_price <= 0:
                return {'error': 'Invalid price data'}

            # Simple supply/demand analysis based on price action
            # This is a basic implementation - in production you'd use more sophisticated algorithms
            price_change_24h = price_data.get('change_24h', 0)

            # Determine trend and zones
            if price_change_24h > 2:
                trend = 'BULLISH'
                signal = 'LONG'
                confidence = min(70 + abs(price_change_24h) * 2, 95)
            elif price_change_24h < -2:
                trend = 'BEARISH' 
                signal = 'SHORT'
                confidence = min(70 + abs(price_change_24h) * 2, 95)
            else:
                trend = 'SIDEWAYS'
                signal = 'HOLD'
                confidence = 50

            # Calculate basic support/resistance levels
            support_level = current_price * 0.97  # 3% below current price
            resistance_level = current_price * 1.03  # 3% above current price

            return {
                'symbol': symbol.upper(),
                'current_price': current_price,
                'trend': trend,
                'signal': signal,
                'confidence': confidence,
                'support_level': support_level,
                'resistance_level': resistance_level,
                'price_change_24h': price_change_24h,
                'timeframe': timeframe,
                'timestamp': time.time(),
                'source': 'supply_demand_analysis'
            }

        except Exception as e:
            return {'error': f'Supply/demand analysis failed: {str(e)}'}

    # === BACKWARD COMPATIBILITY METHODS ===

    def get_binance_long_short_ratio(self, symbol):
        """Backward compatibility: redirect to get_long_short_ratio"""
        print(f"🔄 get_binance_long_short_ratio called for {symbol}, redirecting to CoinGlass V4...")
        return self.get_long_short_ratio(symbol)

    def get_binance_open_interest(self, symbol):
        """Backward compatibility: redirect to get_open_interest"""
        print(f"🔄 get_binance_open_interest called for {symbol}, redirecting to CoinGlass V4...")
        return self.get_open_interest(symbol)

    def get_binance_funding_rate(self, symbol):
        """Backward compatibility: redirect to get_funding_rate"""
        print(f"🔄 get_binance_funding_rate called for {symbol}, redirecting to CoinGlass V4...")
        return self.get_funding_rate(symbol)

    def get_liquidation_zones(self, symbol, interval='15m', limit=100):
        """Get liquidation zones - redirect to liquidation price range"""
        print(f"🔄 get_liquidation_zones called for {symbol}, redirecting to CoinGlass V4...")
        return self.get_liquidation_price_range(symbol)

    def get_binance_oi(self, symbol):
        """Backward compatibility: redirect to get_open_interest"""
        print(f"🔄 get_binance_oi called for {symbol}, redirecting to CoinGlass V4...")
        return self.get_open_interest(symbol)

    def get_coinglass_futures_data(self, symbol):
        """Get comprehensive Coinglass futures data"""
        return self.get_comprehensive_futures_data(symbol)

    def get_candlestick_data(self, symbol, timeframe='1h', limit=100):
        """Get candlestick data for technical analysis"""
        try:
            # For compatibility, return simulated candlestick data based on current price
            price_data = self.get_crypto_price(symbol)
            if 'error' in price_data:
                return {'error': price_data['error']}

            current_price = price_data.get('price', 0)
            if current_price <= 0:
                return {'error': 'Invalid price data'}

            # Generate simulated OHLCV data for analysis
            candlesticks = []
            for i in range(limit):
                # Simple simulation with some price variance
                variance = 0.02  # 2% variance
                high = current_price * (1 + (i % 3) * variance / 3)
                low = current_price * (1 - (i % 3) * variance / 3)
                open_price = current_price * (1 + ((i % 5) - 2) * variance / 5)
                close_price = current_price * (1 + ((i % 4) - 1.5) * variance / 4)
                volume = 1000000 * (1 + (i % 7) * 0.1)  # Simulated volume

                candlesticks.append([
                    int(time.time() - (limit - i) * 3600),  # timestamp
                    open_price,   # open
                    high,         # high
                    low,          # low
                    close_price,  # close
                    volume        # volume
                ])

            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'data': candlesticks,
                'source': 'simulated_candlesticks'
            }

        except Exception as e:
            return {'error': f'Candlestick data error: {str(e)}'}

    def _verify_and_patch_methods(self):
        """Verify all required methods exist and patch missing ones"""
        required_methods = [
            'get_binance_long_short_ratio',
            'get_binance_open_interest', 
            'get_binance_funding_rate',
            'get_binance_oi',
            'get_liquidation_zones',
            'analyze_supply_demand'
        ]

        patched_methods = []

        for method_name in required_methods:
            if not hasattr(self, method_name):
                print(f"🔧 Patching missing method: {method_name}")
                patched_methods.append(method_name)
                self._patch_method(method_name)

        if patched_methods:
            print(f"✅ Patched methods: {', '.join(patched_methods)}")
        else:
            print("✅ All required methods are present")

        return patched_methods

    def _patch_method(self, method_name):
        """Dynamically patch a missing method"""
        if method_name == 'get_binance_long_short_ratio':
            setattr(self, method_name, self.get_long_short_ratio)
        elif method_name == 'get_binance_open_interest':
            setattr(self, method_name, self.get_open_interest)
        elif method_name == 'get_binance_funding_rate':
            setattr(self, method_name, self.get_funding_rate)
        elif method_name == 'get_binance_oi':
            setattr(self, method_name, self.get_open_interest)
        elif method_name == 'get_liquidation_zones':
            setattr(self, method_name, self.get_liquidation_price_range)
        elif method_name == 'analyze_supply_demand':
            if not hasattr(self, 'analyze_supply_demand'):
                setattr(self, method_name, self.analyze_supply_demand)

    async def cleanup(self):
        """Cleanup resources"""
        pass