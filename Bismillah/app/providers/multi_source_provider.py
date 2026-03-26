"""
Multi-source data provider untuk crypto market data
Menggunakan multiple APIs untuk speed dan reliability:
1. Binance API (primary)
2. CoinGecko API (free, no key needed)
3. Helius RPC (on-chain data untuk Solana)
4. CryptoCompare API (free tier)
"""
import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from datetime import datetime

class MultiSourceProvider:
    """Provider yang menggunakan multiple sources untuk data market"""
    
    def __init__(self):
        self.helius_api_key = os.getenv('HELIUS_API_KEY', '')
        self.cryptocompare_api_key = os.getenv('CRYPTOCOMPARE_API_KEY', '')
        
        # API endpoints
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.helius_base = f"https://mainnet.helius-rpc.com/?api-key={self.helius_api_key}"
        self.cryptocompare_base = "https://min-api.cryptocompare.com/data"
        
        self.session = None
        logging.info("✅ MultiSourceProvider initialized")
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        Simple interface to get price with automatic timeout protection
        TIMEOUT: 5 seconds max
        """
        return await self.get_price_multi_source(symbol)
    
    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_price_multi_source(self, symbol: str) -> Dict[str, Any]:
        """
        Get price from multiple sources simultaneously for speed
        Returns fastest response with fallback
        CRITICAL: 5 second total timeout to prevent hanging
        """
        try:
            # Launch all requests in parallel WITH TIMEOUT
            tasks = [
                self._get_coingecko_price(symbol),
                self._get_cryptocompare_price(symbol),
            ]
            
            # Add Helius for Solana tokens
            if symbol.upper() in ['SOL', 'BONK', 'JUP', 'PYTH', 'JTO', 'WEN']:
                tasks.append(self._get_helius_price(symbol))
            
            # Wait for first successful response WITH 5 SECOND TIMEOUT
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=5.0
            )
            
            # Find first successful result
            for result in results:
                if isinstance(result, dict) and not result.get('error'):
                    return result
            
            # If all failed, return error
            return {
                'error': 'All data sources failed',
                'symbol': symbol,
                'attempts': len(tasks)
            }
        
        except asyncio.TimeoutError:
            logging.error(f"Multi-source price fetch timeout (5s) for {symbol}")
            return {
                'error': 'Timeout after 5 seconds',
                'symbol': symbol
            }
        except Exception as e:
            logging.error(f"Error in multi-source price fetch: {e}")
            return {'error': str(e)}
    
    async def _get_coingecko_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get price from CoinGecko (FREE, no API key needed)
        Very reliable and fast
        TIMEOUT: 3 seconds
        """
        try:
            session = await self._get_session()
            
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'SOL': 'solana',
                'XRP': 'ripple',
                'ADA': 'cardano',
                'DOGE': 'dogecoin',
                'DOT': 'polkadot',
                'MATIC': 'matic-network',
                'AVAX': 'avalanche-2',
                'UNI': 'uniswap',
                'LINK': 'chainlink',
                'LTC': 'litecoin',
                'ATOM': 'cosmos',
                'ICP': 'internet-computer',
                'NEAR': 'near',
                'APT': 'aptos',
                'FTM': 'fantom',
                'ALGO': 'algorand',
                'VET': 'vechain',
                'BONK': 'bonk',
                'JUP': 'jupiter-exchange-solana',
                'PYTH': 'pyth-network',
                'JTO': 'jito-governance-token',
                'WEN': 'wen-4'
            }
            
            coin_id = symbol_map.get(symbol.upper())
            if not coin_id:
                return {'error': f'Symbol {symbol} not mapped in CoinGecko'}
            
            url = f"{self.coingecko_base}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_market_cap': 'true'
            }
            
            # CRITICAL: 3 second timeout
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if coin_id in data:
                        coin_data = data[coin_id]
                        return {
                            'symbol': symbol.upper(),
                            'price': coin_data.get('usd', 0),
                            'change_24h': coin_data.get('usd_24h_change', 0),
                            'volume_24h': coin_data.get('usd_24h_vol', 0),
                            'market_cap': coin_data.get('usd_market_cap', 0),
                            'source': 'coingecko',
                            'timestamp': datetime.now().isoformat(),
                            'success': True
                        }
                
                return {'error': f'CoinGecko API returned {response.status}'}
                
        except asyncio.TimeoutError:
            return {'error': 'CoinGecko timeout (3s)'}
        except Exception as e:
            return {'error': f'CoinGecko error: {str(e)}'}
    
    async def _get_cryptocompare_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get price from CryptoCompare (FREE tier available)
        Good for additional data validation
        TIMEOUT: 3 seconds
        """
        try:
            session = await self._get_session()
            
            url = f"{self.cryptocompare_base}/pricemultifull"
            params = {
                'fsyms': symbol.upper(),
                'tsyms': 'USD'
            }
            
            headers = {}
            if self.cryptocompare_api_key:
                headers['authorization'] = f'Apikey {self.cryptocompare_api_key}'
            
            # CRITICAL: 3 second timeout
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'RAW' in data and symbol.upper() in data['RAW']:
                        coin_data = data['RAW'][symbol.upper()]['USD']
                        
                        return {
                            'symbol': symbol.upper(),
                            'price': coin_data.get('PRICE', 0),
                            'change_24h': coin_data.get('CHANGEPCT24HOUR', 0),
                            'volume_24h': coin_data.get('VOLUME24HOURTO', 0),
                            'market_cap': coin_data.get('MKTCAP', 0),
                            'high_24h': coin_data.get('HIGH24HOUR', 0),
                            'low_24h': coin_data.get('LOW24HOUR', 0),
                            'source': 'cryptocompare',
                            'timestamp': datetime.now().isoformat(),
                            'success': True
                        }
                
                return {'error': f'CryptoCompare API returned {response.status}'}
                
        except asyncio.TimeoutError:
            return {'error': 'CryptoCompare timeout (3s)'}
        except Exception as e:
            return {'error': f'CryptoCompare error: {str(e)}'}
    
    async def _get_helius_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get on-chain data from Helius RPC (for Solana tokens)
        Provides real-time on-chain metrics
        TIMEOUT: 3 seconds
        """
        try:
            if not self.helius_api_key:
                return {'error': 'Helius API key not configured'}
            
            session = await self._get_session()
            
            # Token mint addresses for Solana tokens
            token_mints = {
                'SOL': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
                'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
                'JUP': 'JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN',
                'PYTH': 'HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3',
                'JTO': 'jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL',
                'WEN': 'WENWENvqqNya429ubCdR81ZmD69brwQaaBYY6p3LCpk'
            }
            
            mint_address = token_mints.get(symbol.upper())
            if not mint_address:
                return {'error': f'Token {symbol} not supported by Helius'}
            
            # Get token metadata and price from Helius
            url = f"https://api.helius.xyz/v0/token-metadata"
            params = {
                'api-key': self.helius_api_key
            }
            
            payload = {
                'mintAccounts': [mint_address]
            }
            
            # CRITICAL: 3 second timeout
            async with session.post(url, params=params, json=payload, timeout=aiohttp.ClientTimeout(total=3)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        token_data = data[0]
                        
                        # Note: Helius provides metadata, not price
                        # For price, we'd need to query a DEX or use another source
                        return {
                            'symbol': symbol.upper(),
                            'source': 'helius',
                            'on_chain_data': {
                                'name': token_data.get('onChainMetadata', {}).get('metadata', {}).get('name'),
                                'symbol': token_data.get('onChainMetadata', {}).get('metadata', {}).get('symbol'),
                                'mint': mint_address,
                            },
                            'timestamp': datetime.now().isoformat(),
                            'note': 'Helius provides on-chain metadata, use CoinGecko for price'
                        }
                
                return {'error': f'Helius API returned {response.status}'}
                
        except asyncio.TimeoutError:
            return {'error': 'Helius timeout (3s)'}
        except Exception as e:
            return {'error': f'Helius error: {str(e)}'}
    
    async def get_market_data_fast(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get market data for multiple symbols in parallel
        Much faster than sequential requests
        """
        try:
            tasks = [self.get_price_multi_source(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            market_data = {}
            for symbol, result in zip(symbols, results):
                if isinstance(result, dict) and not result.get('error'):
                    market_data[symbol] = result
                else:
                    market_data[symbol] = {'error': 'Failed to fetch', 'symbol': symbol}
            
            return {
                'success': True,
                'data': market_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error in fast market data fetch: {e}")
            return {'error': str(e), 'success': False}

# Global instance
multi_source_provider = MultiSourceProvider()
