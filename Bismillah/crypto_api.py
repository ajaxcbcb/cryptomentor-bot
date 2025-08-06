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
        """Get open interest from Coinglass V4 - REAL DATA with proper symbol format"""
        try:
            if not self.coinglass_key:
                print(f"❌ CoinGlass API key not found for {symbol}")
                return {'error': 'Coinglass API key not found'}

            # Use proper symbol format for CoinGlass V4 (BTCUSDT, ETHUSDT, etc.)
            clean_symbol = self.coinglass_provider._clean_symbol(symbol)
            print(f"🔄 Getting REAL open interest for {clean_symbol} from CoinGlass V4...")

            # Use the coinglass_provider for real API calls
            result = self.coinglass_provider.get_open_interest_chart(clean_symbol)
            
            if result and 'error' not in result:
                oi_value = result.get('open_interest', 0)
                oi_change = result.get('oi_change_percent', 0)
                print(f"✅ Real OI data: ${oi_value/1000000:.1f}M ({oi_change:+.1f}%)")
                
                return {
                    'symbol': clean_symbol,
                    'open_interest': oi_value,
                    'oi_change_percent': oi_change,
                    'timestamp': result.get('timestamp', int(time.time() * 1000)),
                    'source': 'coinglass_v4_realtime'
                }
            else:
                error_msg = result.get('error', 'Unknown error') if result else f'No open interest data for {clean_symbol}'
                print(f"❌ CoinGlass V4 open interest error: {error_msg}")
                return {'error': error_msg}

        except Exception as e:
            print(f"❌ Open interest error for {symbol}: {e}")
            return {'error': f'Open interest error: {str(e)}'}

    def get_funding_rate(self, symbol):
        """Get funding rate from Coinglass V4 - REAL DATA"""
        try:
            if not self.coinglass_key:
                print(f"❌ CoinGlass API key not found for {symbol}")
                return {'error': 'Coinglass API key not found'}

            # Clean symbol to basic format (BTC, ETH, etc.)
            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')
            print(f"🔄 Getting REAL funding rate for {clean_symbol} from CoinGlass V4...")

            # Use the coinglass_provider for real API calls
            result = self.coinglass_provider.get_funding_rate_chart(clean_symbol)
            
            if result and 'error' not in result:
                return {
                    'symbol': clean_symbol,
                    'funding_rate': result.get('funding_rate', 0),
                    'funding_rate_percent': result.get('funding_rate_percent', 0),
                    'timestamp': result.get('timestamp', int(time.time() * 1000)),
                    'source': 'coinglass_v4_realtime'
                }
            else:
                print(f"❌ CoinGlass V4 funding rate error: {result.get('error', 'Unknown error')}")
                return result if result else {'error': f'No funding rate data for {clean_symbol}'}

        except Exception as e:
            print(f"❌ Funding rate error for {symbol}: {e}")
            return {'error': f'Funding rate error: {str(e)}'}

    def get_long_short_ratio(self, symbol):
        """Get long/short ratio from Coinglass V4 - REAL DATA"""
        try:
            if not self.coinglass_key:
                print(f"❌ CoinGlass API key not found for {symbol}")
                return {'error': 'Coinglass API key not found'}

            # Clean symbol to basic format (BTC, ETH, etc.)
            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')
            print(f"🔄 Getting REAL long/short ratio for {clean_symbol} from CoinGlass V4...")

            # Use the coinglass_provider for real API calls
            result = self.coinglass_provider.get_long_short_ratio(clean_symbol)
            
            if result and 'error' not in result:
                return {
                    'symbol': clean_symbol,
                    'long_ratio': result.get('long_ratio', 50),
                    'short_ratio': result.get('short_ratio', 50),
                    'timestamp': result.get('timestamp', int(time.time() * 1000)),
                    'source': 'coinglass_v4_realtime'
                }
            else:
                print(f"❌ CoinGlass V4 long/short error: {result.get('error', 'Unknown error')}")
                return result if result else {'error': f'No long/short ratio data for {clean_symbol}'}

        except Exception as e:
            print(f"❌ Long/short ratio error for {symbol}: {e}")
            return {'error': f'Long/short ratio error: {str(e)}'}

    def get_liquidation_price_range(self, symbol):
        """Get liquidation price ranges from Coinglass V4 - REAL DATA"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')
            print(f"🔄 Getting REAL liquidation zones for {clean_symbol} from CoinGlass V4...")

            # Use the coinglass_provider for real API calls
            result = self.coinglass_provider.get_liquidation_map(clean_symbol)
            
            if result and 'error' not in result:
                return {
                    'symbol': clean_symbol,
                    'total_liquidation': result.get('total_liquidation', 0),
                    'long_liquidation': result.get('long_liquidation', 0),
                    'short_liquidation': result.get('short_liquidation', 0),
                    'long_percentage': result.get('long_percentage', 50),
                    'short_percentage': result.get('short_percentage', 50),
                    'dominant_side': result.get('dominant_side', 'Balanced'),
                    'zones': result.get('zones', []),
                    'source': 'coinglass_v4_realtime'
                }
            else:
                print(f"❌ CoinGlass V4 liquidation error: {result.get('error', 'Unknown error')}")
                return result if result else {'error': f'No liquidation data for {clean_symbol}'}

        except Exception as e:
            print(f"❌ Liquidation zones error for {symbol}: {e}")
            return {'error': f'Coinglass V4 liquidation error: {str(e)}'}

    def get_comprehensive_futures_data(self, symbol):
        """Get comprehensive futures data from Coinglass V4 - REAL DATA"""
        try:
            print(f"🔄 Getting REAL comprehensive futures data for {symbol} from CoinGlass V4...")

            # Clean symbol for consistency
            clean_symbol = symbol.upper().replace('USDT', '').replace('BINANCE_', '').replace('USD', '')

            # Use coinglass_provider directly for real data
            result = self.coinglass_provider.get_comprehensive_futures_data(clean_symbol)
            
            if result and 'error' not in result:
                successful_calls = result.get('successful_calls', 0)
                total_calls = result.get('total_calls', 4)
                
                print(f"✅ CoinGlass V4 comprehensive data: {successful_calls}/{total_calls} endpoints successful")
                
                return {
                    'symbol': clean_symbol,
                    'long_short_data': result.get('long_short_data', {}),
                    'open_interest_data': result.get('open_interest_data', {}),
                    'funding_rate_data': result.get('funding_rate_data', {}),
                    'liquidation_data': result.get('liquidation_data', {}),
                    'successful_api_calls': successful_calls,
                    'total_api_calls': total_calls,
                    'data_quality': result.get('data_quality', 'poor'),
                    'source': 'coinglass_v4_realtime_comprehensive',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"❌ CoinGlass V4 comprehensive data error: {result.get('error', 'Unknown error') if result else 'No data'}")
                return result if result else {'error': f'No comprehensive data for {clean_symbol}'}
                
        except Exception as e:
            print(f"❌ Comprehensive futures data error: {e}")
            return {'error': f"CoinGlass V4 comprehensive data error: {str(e)}"}

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
        """Analyze supply and demand zones using real CoinGlass V4 and price data"""
        try:
            print(f"🔄 Analyzing supply/demand for {symbol} using real data...")
            
            # Get comprehensive futures data from CoinGlass V4
            futures_data = self.get_comprehensive_futures_data(symbol)
            
            if 'error' in futures_data:
                print(f"⚠️ CoinGlass data unavailable, using price data only")
                # Fallback to price-only analysis
                price_data = self.get_crypto_price(symbol)
                if 'error' in price_data:
                    return {'error': f'Failed to get any data: {price_data["error"]}'}
                
                current_price = price_data.get('price', 0)
                price_change_24h = price_data.get('change_24h', 0)
                
                # Basic analysis without futures data
                if price_change_24h > 2:
                    trend = 'BULLISH'
                    signal = 'LONG'
                    confidence = 60
                elif price_change_24h < -2:
                    trend = 'BEARISH'
                    signal = 'SHORT'
                    confidence = 60
                else:
                    trend = 'SIDEWAYS'
                    signal = 'HOLD'
                    confidence = 40
                
                return {
                    'symbol': symbol.upper(),
                    'current_price': current_price,
                    'trend': trend,
                    'signal': signal,
                    'confidence': confidence,
                    'support_level': current_price * 0.97,
                    'resistance_level': current_price * 1.03,
                    'price_change_24h': price_change_24h,
                    'timeframe': timeframe,
                    'source': 'basic_price_analysis',
                    'timestamp': time.time()
                }
            
            # Extract real data from CoinGlass V4
            ticker_data = futures_data.get('ticker_data', {})
            ls_data = futures_data.get('long_short_data', {})
            oi_data = futures_data.get('open_interest_data', {})
            funding_data = futures_data.get('funding_rate_data', {})
            liq_data = futures_data.get('liquidation_data', {})
            
            # Get current price from ticker or fallback
            current_price = 0
            price_change_24h = 0
            
            if 'error' not in ticker_data:
                current_price = ticker_data.get('price', 0)
                price_change_24h = ticker_data.get('price_change_24h', 0)
            else:
                # Fallback to price API
                price_data = self.get_crypto_price(symbol)
                if 'error' not in price_data:
                    current_price = price_data.get('price', 0)
                    price_change_24h = price_data.get('change_24h', 0)
            
            if current_price <= 0:
                return {'error': 'Unable to get valid price data'}
            
            # Advanced supply/demand analysis using real futures data
            confidence = 50
            trend = 'SIDEWAYS'
            signal = 'HOLD'
            analysis_factors = []
            
            # 1. Long/Short Ratio Analysis
            if 'error' not in ls_data:
                long_ratio = ls_data.get('long_ratio', 50)
                if long_ratio > 70:
                    # High long ratio = potential distribution/supply zone
                    confidence += 15
                    trend = 'BEARISH'
                    signal = 'SHORT'
                    analysis_factors.append(f"High long ratio ({long_ratio:.1f}%) indicates supply pressure")
                elif long_ratio < 30:
                    # Low long ratio = potential accumulation/demand zone
                    confidence += 15
                    trend = 'BULLISH'
                    signal = 'LONG'
                    analysis_factors.append(f"Low long ratio ({long_ratio:.1f}%) indicates demand building")
                else:
                    analysis_factors.append(f"Balanced long/short ratio ({long_ratio:.1f}%)")
            
            # 2. Open Interest Analysis
            if 'error' not in oi_data:
                oi_change = oi_data.get('oi_change_percent', 0)
                if oi_change > 5:
                    confidence += 10
                    analysis_factors.append(f"Rising OI ({oi_change:+.1f}%) confirms trend strength")
                elif oi_change < -5:
                    confidence -= 5
                    analysis_factors.append(f"Falling OI ({oi_change:+.1f}%) suggests weakening")
            
            # 3. Funding Rate Analysis
            if 'error' not in funding_data:
                funding_rate = funding_data.get('funding_rate', 0)
                if funding_rate > 0.01:  # High positive funding
                    confidence += 10
                    if trend != 'BULLISH':
                        trend = 'BEARISH'
                        signal = 'SHORT'
                    analysis_factors.append(f"High funding rate ({funding_rate*100:.3f}%) = overheated longs")
                elif funding_rate < -0.005:  # Negative funding
                    confidence += 10
                    if trend != 'BEARISH':
                        trend = 'BULLISH'
                        signal = 'LONG'
                    analysis_factors.append(f"Negative funding ({funding_rate*100:.3f}%) = oversold")
            
            # 4. Liquidation Analysis
            if 'error' not in liq_data:
                dominant_side = liq_data.get('dominant_side', 'Balanced')
                total_liq = liq_data.get('total_liquidation', 0)
                if total_liq > 10000000:  # $10M+ liquidations
                    confidence += 8
                    analysis_factors.append(f"High liquidations (${total_liq/1000000:.1f}M) - {dominant_side} heavy")
            
            # 5. Price momentum confirmation
            if price_change_24h > 3:
                if trend == 'BULLISH':
                    confidence += 10
                analysis_factors.append(f"Strong price momentum (+{price_change_24h:.1f}%)")
            elif price_change_24h < -3:
                if trend == 'BEARISH':
                    confidence += 10
                analysis_factors.append(f"Strong bearish momentum ({price_change_24h:.1f}%)")
            
            # Calculate support/resistance based on liquidation zones
            support_level = current_price * 0.95
            resistance_level = current_price * 1.05
            
            if 'error' not in liq_data and liq_data.get('zones'):
                zones = liq_data['zones']
                for zone in zones[:3]:  # Check top 3 zones
                    zone_price = zone.get('price', 0)
                    if zone_price > 0:
                        if zone_price < current_price:
                            support_level = max(support_level, zone_price)
                        else:
                            resistance_level = min(resistance_level, zone_price)
            
            # Final confidence adjustment
            confidence = min(95, max(30, confidence))
            
            # Override signal if confidence too low
            if confidence < 60:
                signal = 'HOLD'
                trend = 'SIDEWAYS'
            
            successful_endpoints = futures_data.get('successful_calls', 0)
            data_quality = futures_data.get('data_quality', 'poor')
            
            print(f"✅ Supply/Demand analysis: {signal} ({confidence}%) using {successful_endpoints}/5 real endpoints")
            
            return {
                'symbol': symbol.upper(),
                'current_price': current_price,
                'trend': trend,
                'signal': signal,
                'confidence': confidence,
                'support_level': support_level,
                'resistance_level': resistance_level,
                'price_change_24h': price_change_24h,
                'analysis_factors': analysis_factors,
                'data_quality': data_quality,
                'successful_endpoints': successful_endpoints,
                'timeframe': timeframe,
                'source': 'advanced_snd_analysis_coinglass_v4',
                'timestamp': time.time()
            }

        except Exception as e:
            print(f"❌ Supply/demand analysis error: {e}")
            return {'error': f'Supply/demand analysis failed: {str(e)}'}

    # === BACKWARD COMPATIBILITY METHODS ===

    def get_binance_long_short_ratio(self, symbol):
        """Backward compatibility: redirect to get_long_short_ratio with real CoinGlass V4 data"""
        print(f"✅ get_binance_long_short_ratio called for {symbol}, using CoinGlass V4 REAL data...")
        result = self.get_long_short_ratio(symbol)
        
        # Add extra logging for debugging
        if 'error' not in result:
            long_ratio = result.get('long_ratio', 50)
            print(f"🎯 Real L/S Ratio: {long_ratio:.1f}% Long / {100-long_ratio:.1f}% Short")
        else:
            print(f"❌ L/S Ratio error: {result['error']}")
        
        return result

    def get_binance_open_interest(self, symbol):
        """Backward compatibility: redirect to get_open_interest"""
        print(f"✅ get_binance_open_interest called for {symbol}, using CoinGlass V4 REAL data...")
        return self.get_open_interest(symbol)

    def get_binance_funding_rate(self, symbol):
        """Backward compatibility: redirect to get_funding_rate"""
        print(f"✅ get_binance_funding_rate called for {symbol}, using CoinGlass V4 REAL data...")
        return self.get_funding_rate(symbol)

    def get_liquidation_zones(self, symbol, interval='15m', limit=100):
        """Get liquidation zones - redirect to liquidation price range"""
        print(f"✅ get_liquidation_zones called for {symbol}, using CoinGlass V4 REAL data...")
        return self.get_liquidation_price_range(symbol)

    def get_binance_oi(self, symbol):
        """Backward compatibility: redirect to get_open_interest"""  
        print(f"✅ get_binance_oi called for {symbol}, using CoinGlass V4 REAL data...")
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