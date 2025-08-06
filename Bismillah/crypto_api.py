

import requests
import os
import time
from datetime import datetime
from binance_provider import BinanceFuturesProvider
from coinmarketcap_provider import CoinMarketCapProvider

class CryptoAPI:
    def __init__(self):
        self.provider = BinanceFuturesProvider()
        self.cryptonews_key = os.getenv("CRYPTONEWS_API_KEY")
        self.coinglass_key = os.getenv("COINGLASS_API_KEY")
        self.cmc_provider = CoinMarketCapProvider()

        if not self.coinglass_key:
            print("⚠️ Coinglass API key not found in environment variables")
            print("💡 Please set COINGLASS_API_KEY in Replit Secrets")

        # Coinglass V4 Official API
        self.coinglass_base_url = "https://api.coinglass.dev/v4"
        
        # Initialize Binance URLs for fallback
        self.binance_spot_url = "https://api.binance.com/api/v3"
        self.binance_futures_url = "https://fapi.binance.com/fapi/v1"

        self.cache = {}
        self.cache_duration = 60  # Increased cache duration for better performance

        print("🚀 CryptoAPI initialized with Coinglass V4 + CoinMarketCap")
        print(f"📊 Coinglass V4 API: {self.coinglass_base_url}")
        print(f"🔑 Coinglass Key: {'✅ Enabled' if self.coinglass_key else '❌ Disabled'}")
        print(f"📊 CoinMarketCap: {'✅ Enabled' if self.cmc_provider.api_key else '❌ Disabled'}")
        print(f"📰 CryptoNews API: {'✅ Enabled' if self.cryptonews_key else '❌ Disabled'}")
        print("⭐ Data Sources: Coinglass V4 Startup Plan + CoinMarketCap")

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
                return {'error': 'Coinglass API key not found'}

            clean_symbol = symbol.upper().replace('USDT', '')
            url = f"{self.coinglass_base_url}/open_interest"
            headers = self._get_coinglass_headers()
            params = {'symbol': clean_symbol}

            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    oi_data = data['data']
                    
                    total_oi = 0
                    oi_change = 0
                    exchanges_count = 0
                    
                    if isinstance(oi_data, list):
                        for exchange_data in oi_data:
                            oi_value = float(exchange_data.get('openInterest', 0))
                            oi_change_value = float(exchange_data.get('openInterestChange24h', 0))
                            total_oi += oi_value
                            oi_change += oi_change_value
                            exchanges_count += 1
                    else:
                        total_oi = float(oi_data.get('openInterest', 0))
                        oi_change = float(oi_data.get('openInterestChange24h', 0))
                        exchanges_count = 1

                    return {
                        'symbol': clean_symbol,
                        'open_interest': total_oi,
                        'open_interest_change': oi_change,
                        'exchanges_count': exchanges_count,
                        'source': 'coinglass_v4',
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {'error': f'Coinglass V4 OI error: {response.status_code}'}
        except Exception as e:
            return {'error': f'Coinglass V4 OI error: {str(e)}'}

    def get_funding_rate(self, symbol):
        """Get funding rate from Coinglass V4"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            clean_symbol = symbol.upper().replace('USDT', '')
            url = f"{self.coinglass_base_url}/funding_rate"
            headers = self._get_coinglass_headers()
            params = {'symbol': clean_symbol}

            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    funding_data = data['data']
                    
                    total_funding = 0
                    valid_exchanges = 0
                    
                    if isinstance(funding_data, list):
                        for exchange_data in funding_data:
                            funding_rate = float(exchange_data.get('fundingRate', 0))
                            if funding_rate != 0:
                                total_funding += funding_rate
                                valid_exchanges += 1
                    else:
                        funding_rate = float(funding_data.get('fundingRate', 0))
                        if funding_rate != 0:
                            total_funding = funding_rate
                            valid_exchanges = 1

                    avg_funding = total_funding / valid_exchanges if valid_exchanges > 0 else 0

                    return {
                        'symbol': clean_symbol,
                        'funding_rate': avg_funding,
                        'funding_rate_8h': avg_funding * 3,
                        'exchanges_count': valid_exchanges,
                        'source': 'coinglass_v4',
                        'timestamp': datetime.now().isoformat()
                    }
            
            return {'error': f'Coinglass V4 funding error: {response.status_code}'}
        except Exception as e:
            return {'error': f'Coinglass V4 funding error: {str(e)}'}

    def get_long_short_ratio(self, symbol):
        """Get long/short ratio from Coinglass V4"""
        try:
            if not self.coinglass_key:
                return {'error': 'Coinglass API key not found'}

            clean_symbol = symbol.upper().replace('USDT', '')
            url = f"{self.coinglass_base_url}/long_short_ratio"
            headers = self._get_coinglass_headers()
            params = {'symbol': clean_symbol}

            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    ls_data = data['data']
                    
                    if isinstance(ls_data, list) and len(ls_data) > 0:
                        latest = ls_data[-1]
                    else:
                        latest = ls_data
                    
                    long_ratio = float(latest.get('longRatio', 50))
                    short_ratio = float(latest.get('shortRatio', 50))

                    return {
                        'symbol': clean_symbol,
                        'long_ratio': long_ratio,
                        'short_ratio': short_ratio,
                        'long_short_ratio': long_ratio / short_ratio if short_ratio > 0 else 1.0,
                        'timestamp': latest.get('timestamp', datetime.now().isoformat()),
                        'source': 'coinglass_v4'
                    }
            
            return {'error': f'Coinglass V4 L/S error: {response.status_code}'}
        except Exception as e:
            return {'error': f'Coinglass V4 L/S error: {str(e)}'}

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

            # Get all data from V4 endpoints
            price_data = self.get_futures_price(symbol)
            oi_data = self.get_open_interest(symbol)
            funding_data = self.get_funding_rate(symbol)
            ls_data = self.get_long_short_ratio(symbol)
            liquidation_data = self.get_liquidation_price_range(symbol)

            successful_calls = 0
            total_calls = 5

            # Count successful API calls
            for data in [price_data, oi_data, funding_data, ls_data, liquidation_data]:
                if isinstance(data, dict) and 'error' not in data:
                    successful_calls += 1

            return {
                'symbol': symbol,
                'price_data': price_data,
                'open_interest_data': oi_data,
                'funding_rate_data': funding_data,
                'long_short_data': ls_data,
                'liquidation_data': liquidation_data,
                'successful_api_calls': successful_calls,
                'total_api_calls': total_calls,
                'data_quality': 'excellent' if successful_calls >= 4 else 'good' if successful_calls >= 3 else 'fair',
                'source': 'coinglass_v4_comprehensive'
            }
        except Exception as e:
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

                if 'error' not in cmc_data and cmc_data.get('price', 0) > 0:
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

    async def cleanup(self):
        """Cleanup resources"""
        pass

