
import requests
import os
import time
from datetime import datetime

class CoinMarketCapProvider:
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
            print("✅ CoinMarketCap API initialized with Startup plan")

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

    def get_cryptocurrency_info(self, symbol):
        """Get cryptocurrency info using /v1/cryptocurrency/info"""
        try:
            if not self.api_key:
                return {'error': 'CMC API key not found'}

            # First get ID from symbol
            map_url = f"{self.base_url}/v1/cryptocurrency/map"
            map_params = {'symbol': symbol.upper()}
            
            map_response = requests.get(map_url, headers=self.headers, params=map_params, timeout=10)
            map_response.raise_for_status()
            map_data = map_response.json()
            
            if not map_data.get('data') or len(map_data['data']) == 0:
                return {'error': f'Cryptocurrency {symbol} not found'}
                
            crypto_id = map_data['data'][0]['id']
            
            # Get detailed info
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
                crypto_data = data.get('data', {}).get(symbol.upper(), {})
                quote_data = crypto_data.get('quote', {}).get('USD', {})
                
                return {
                    'id': crypto_data.get('id', 0),
                    'name': crypto_data.get('name', ''),
                    'symbol': crypto_data.get('symbol', ''),
                    'cmc_rank': crypto_data.get('cmc_rank', 0),
                    'circulating_supply': crypto_data.get('circulating_supply', 0),
                    'total_supply': crypto_data.get('total_supply', 0),
                    'max_supply': crypto_data.get('max_supply', 0),
                    'price': quote_data.get('price', 0),
                    'volume_24h': quote_data.get('volume_24h', 0),
                    'volume_change_24h': quote_data.get('volume_change_24h', 0),
                    'percent_change_1h': quote_data.get('percent_change_1h', 0),
                    'percent_change_24h': quote_data.get('percent_change_24h', 0),
                    'percent_change_7d': quote_data.get('percent_change_7d', 0),
                    'percent_change_30d': quote_data.get('percent_change_30d', 0),
                    'market_cap': quote_data.get('market_cap', 0),
                    'market_cap_dominance': quote_data.get('market_cap_dominance', 0),
                    'fully_diluted_market_cap': quote_data.get('fully_diluted_market_cap', 0),
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

    def get_comprehensive_data(self, symbol):
        """Get both info and quotes data combined"""
        try:
            info_data = self.get_cryptocurrency_info(symbol)
            quotes_data = self.get_cryptocurrency_quotes(symbol)
            
            if 'error' in info_data and 'error' in quotes_data:
                return {'error': f'Failed to get data for {symbol}'}
            
            # Combine data
            combined_data = {
                'symbol': symbol.upper(),
                'source': 'coinmarketcap_comprehensive'
            }
            
            if 'error' not in info_data:
                combined_data.update(info_data)
                
            if 'error' not in quotes_data:
                combined_data.update(quotes_data)
                
            return combined_data
            
        except Exception as e:
            return {'error': f'CMC comprehensive data error: {str(e)}'}

    def check_api_status(self):
        """Check CoinMarketCap API status"""
        try:
            if not self.api_key:
                return {
                    'api_key_present': False,
                    'global_metrics_test': False,
                    'quotes_test': False,
                    'info_test': False,
                    'overall_health': False,
                    'plan': 'startup'
                }

            # Test global metrics
            global_test = self.get_global_metrics()
            global_ok = 'error' not in global_test

            # Test quotes (BTC)
            quotes_test = self.get_cryptocurrency_quotes('BTC')
            quotes_ok = 'error' not in quotes_test

            # Test info (BTC)
            info_test = self.get_cryptocurrency_info('BTC')
            info_ok = 'error' not in info_test

            working_endpoints = sum([global_ok, quotes_ok, info_ok])
            overall_health = working_endpoints >= 2

            return {
                'api_key_present': True,
                'global_metrics_test': global_ok,
                'quotes_test': quotes_ok,
                'info_test': info_ok,
                'working_endpoints': f"{working_endpoints}/3",
                'overall_health': overall_health,
                'plan': 'startup',
                'btc_price': quotes_test.get('price', 0) if quotes_ok else 0
            }

        except Exception as e:
            return {
                'api_key_present': bool(self.api_key),
                'global_metrics_test': False,
                'quotes_test': False,
                'info_test': False,
                'overall_health': False,
                'plan': 'startup',
                'error': str(e)
            }
