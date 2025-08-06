
import requests
import os
import time
from datetime import datetime

class CoinMarketCapProvider:
    """CoinMarketCap API Provider"""
    
    def __init__(self):
        self.api_key = os.getenv("CMC_API_KEY")
        self.base_url = "https://pro-api.coinmarketcap.com"
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json',
            'Accept-Encoding': 'deflate, gzip'
        }

        if not self.api_key:
            print("⚠️ CMC_API_KEY not found in environment variables")
            print("💡 Please set CMC_API_KEY in Replit Secrets")
        else:
            print("✅ CoinMarketCap API initialized")

    def get_cryptocurrency_quotes(self, symbol):
        """Get cryptocurrency quotes using /v1/cryptocurrency/quotes/latest"""
        try:
            if not self.api_key:
                return {'error': 'CMC API key not found'}

            url = f"{self.base_url}/v1/cryptocurrency/quotes/latest"
            params = {'symbol': symbol.upper()}

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                crypto_data = data.get('data', {})
                
                symbol_upper = symbol.upper()
                if symbol_upper not in crypto_data:
                    return {'error': f'Cryptocurrency {symbol} data not found in response'}

                current_crypto_data = crypto_data[symbol_upper]
                quote_data = current_crypto_data.get('quote', {}).get('USD', {})

                price = quote_data.get('price')
                if price is None:
                    price = 0
                
                return {
                    'id': current_crypto_data.get('id', 0),
                    'name': current_crypto_data.get('name', ''),
                    'symbol': current_crypto_data.get('symbol', ''),
                    'cmc_rank': int(current_crypto_data.get('cmc_rank', 0) or 0),
                    'circulating_supply': float(current_crypto_data.get('circulating_supply', 0) or 0),
                    'total_supply': float(current_crypto_data.get('total_supply', 0) or 0),
                    'max_supply': float(current_crypto_data.get('max_supply', 0) or 0) if current_crypto_data.get('max_supply') else None,
                    'price': float(price) if price else 0,
                    'volume_24h': float(quote_data.get('volume_24h', 0) or 0),
                    'volume_change_24h': float(quote_data.get('volume_change_24h', 0) or 0),
                    'percent_change_1h': float(quote_data.get('percent_change_1h', 0) or 0),
                    'percent_change_24h': float(quote_data.get('percent_change_24h', 0) or 0),
                    'percent_change_7d': float(quote_data.get('percent_change_7d', 0) or 0),
                    'percent_change_30d': float(quote_data.get('percent_change_30d', 0) or 0),
                    'market_cap': float(quote_data.get('market_cap', 0) or 0),
                    'market_cap_dominance': float(quote_data.get('market_cap_dominance', 0) or 0),
                    'fully_diluted_market_cap': float(quote_data.get('fully_diluted_market_cap', 0) or 0),
                    'last_updated': quote_data.get('last_updated', ''),
                    'source': 'coinmarketcap_quotes'
                }
            else:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                return {'error': f'CMC quotes API error: {error_msg}'}

        except requests.exceptions.RequestException as e:
            return {'error': f'CMC quotes request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'CMC quotes error: {str(e)}'}

    def get_cryptocurrency_info(self, symbol):
        """Get cryptocurrency info using /v1/cryptocurrency/info"""
        try:
            if not self.api_key:
                return {'error': 'CMC API key not found'}

            map_url = f"{self.base_url}/v1/cryptocurrency/map"
            map_params = {'symbol': symbol.upper()}

            map_response = requests.get(map_url, headers=self.headers, params=map_params, timeout=10)
            map_response.raise_for_status()
            map_data = map_response.json()

            if not map_data.get('data') or len(map_data['data']) == 0:
                return {'error': f'Cryptocurrency {symbol} not found'}

            crypto_id = map_data['data'][0]['id']

            info_url = f"{self.base_url}/v1/cryptocurrency/info"
            info_params = {'id': crypto_id}

            info_response = requests.get(info_url, headers=self.headers, params=info_params, timeout=10)
            info_response.raise_for_status()
            info_data = info_response.json()

            if info_data.get('status', {}).get('error_code') == 0:
                crypto_info = info_data.get('data', {}).get(str(crypto_id), {})

                return {
                    'id': crypto_id,
                    'name': crypto_info.get('name', ''),
                    'symbol': crypto_info.get('symbol', ''),
                    'description': crypto_info.get('description', ''),
                    'logo': crypto_info.get('logo', ''),
                    'website': crypto_info.get('urls', {}).get('website', []),
                    'explorer': crypto_info.get('urls', {}).get('explorer', []),
                    'reddit': crypto_info.get('urls', {}).get('reddit', []),
                    'twitter': crypto_info.get('urls', {}).get('twitter', []),
                    'category': crypto_info.get('category', ''),
                    'tags': crypto_info.get('tags', []),
                    'date_added': crypto_info.get('date_added', ''),
                    'source': 'coinmarketcap_info'
                }
            else:
                error_msg = info_data.get('status', {}).get('error_message', 'Unknown error')
                return {'error': f'CMC info API error: {error_msg}'}

        except requests.exceptions.RequestException as e:
            return {'error': f'CMC info request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'CMC info error: {str(e)}'}

    def get_global_metrics(self):
        """Get global market metrics using /v1/global-metrics/quotes/latest"""
        try:
            if not self.api_key:
                return {'error': 'CMC API key not found'}

            url = f"{self.base_url}/v1/global-metrics/quotes/latest"

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                quote_data = data.get('data', {}).get('quote', {}).get('USD', {})

                return {
                    'total_market_cap': quote_data.get('total_market_cap', 0),
                    'total_volume_24h': quote_data.get('total_volume_24h', 0),
                    'market_cap_change_24h': quote_data.get('total_market_cap_yesterday_percentage_change', 0),
                    'btc_dominance': data.get('data', {}).get('btc_dominance', 0),
                    'eth_dominance': data.get('data', {}).get('eth_dominance', 0),
                    'active_cryptocurrencies': data.get('data', {}).get('active_cryptocurrencies', 0),
                    'active_exchanges': data.get('data', {}).get('active_exchanges', 0),
                    'active_market_pairs': data.get('data', {}).get('active_market_pairs', 0),
                    'last_updated': data.get('data', {}).get('last_updated', ''),
                    'source': 'coinmarketcap_global'
                }
            else:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                return {'error': f'CMC API error: {error_msg}'}

        except requests.exceptions.RequestException as e:
            return {'error': f'CMC API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'CMC global metrics error: {str(e)}'}

    def get_top_cryptocurrencies(self, limit=5):
        """Get top cryptocurrencies by market cap using /v1/cryptocurrency/listings/latest"""
        try:
            if not self.api_key:
                return {'error': 'CMC API key not found'}

            url = f"{self.base_url}/v1/cryptocurrency/listings/latest"
            params = {
                'limit': limit,
                'sort': 'market_cap',
                'convert': 'USD'
            }

            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('error_code') == 0:
                cryptocurrencies = []
                for crypto in data.get('data', []):
                    quote = crypto.get('quote', {}).get('USD', {})
                    cryptocurrencies.append({
                        'name': crypto.get('name', ''),
                        'symbol': crypto.get('symbol', ''),
                        'cmc_rank': crypto.get('cmc_rank', 0),
                        'price': quote.get('price', 0),
                        'percent_change_24h': quote.get('percent_change_24h', 0),
                        'market_cap': quote.get('market_cap', 0),
                        'volume_24h': quote.get('volume_24h', 0)
                    })

                return {
                    'data': cryptocurrencies,
                    'source': 'coinmarketcap_listings'
                }
            else:
                error_msg = data.get('status', {}).get('error_message', 'Unknown error')
                return {'error': f'CMC listings API error: {error_msg}'}

        except requests.exceptions.RequestException as e:
            return {'error': f'CMC listings request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'CMC listings error: {str(e)}'}

    def get_fear_greed_index(self):
        """Get Fear & Greed Index from alternative.me API (free alternative)"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                fng_data = data['data'][0]
                return {
                    'value': int(fng_data.get('value', 50)),
                    'value_classification': fng_data.get('value_classification', 'Neutral'),
                    'timestamp': fng_data.get('timestamp', ''),
                    'source': 'alternative.me'
                }
            else:
                return {'error': 'No Fear & Greed data available'}

        except Exception as e:
            return {
                'value': 50,
                'value_classification': 'Neutral',
                'timestamp': str(int(time.time())),
                'source': 'estimated',
                'error': f'FNG API failed: {str(e)}'
            }

    def get_enhanced_market_overview(self):
        """Get enhanced market overview combining multiple CMC endpoints"""
        try:
            if not self.api_key:
                return {'error': 'CMC API key not found'}

            # Get global metrics
            global_data = self.get_global_metrics()
            if 'error' in global_data:
                return global_data

            # Get top cryptos
            top_cryptos = self.get_top_cryptocurrencies(10)
            if 'error' in top_cryptos:
                top_cryptos = {'data': []}

            # Get fear & greed index
            fng_data = self.get_fear_greed_index()

            return {
                'global_metrics': global_data,
                'top_cryptocurrencies': top_cryptos.get('data', []),
                'fear_greed_index': fng_data,
                'source': 'coinmarketcap_enhanced'
            }

        except Exception as e:
            return {'error': f'Enhanced market overview error: {str(e)}'}

print("✅ CoinMarketCapProvider loaded successfully")
