
import os
import asyncio
import aiohttp
import time
from datetime import datetime
from typing import Dict, Any, Optional

class CoinAPIHelper:
    """Helper class untuk menangani CoinAPI operations"""
    
    def __init__(self):
        self.coinapi_key = os.getenv('COINAPI_KEY')
        self.base_url = "https://rest.coinapi.io/v1"
        self.session = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                'X-CoinAPI-Key': self.coinapi_key,
                'Accept': 'application/json',
                'User-Agent': 'CryptoMentorAI/1.0'
            }
            timeout = aiohttp.ClientTimeout(total=15.0)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_coinapi_price(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch real-time price from CoinAPI
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            force_refresh: Force fresh API call
            
        Returns:
            Dict with price data or error
        """
        try:
            if not self.coinapi_key:
                return {'error': 'CoinAPI key not found'}
            
            # Normalize symbol
            clean_symbol = symbol.upper().replace('USDT', '')
            
            session = await self._get_session()
            url = f"{self.base_url}/exchangerate/{clean_symbol}/USD"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    price = data.get('rate', 0)
                    if price <= 0:
                        return {'error': f'Invalid price received: {price}'}
                    
                    return {
                        'symbol': clean_symbol,
                        'price': price,
                        'time': data.get('time', ''),
                        'source': 'coinapi',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    return {'error': f'CoinAPI HTTP {response.status}: {error_text}'}
                    
        except asyncio.TimeoutError:
            return {'error': 'CoinAPI request timeout'}
        except Exception as e:
            return {'error': f'CoinAPI error: {str(e)}'}
    
    async def get_multiple_prices(self, symbols: list) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple prices concurrently
        
        Args:
            symbols: List of crypto symbols
            
        Returns:
            Dict mapping symbols to price data
        """
        tasks = []
        for symbol in symbols:
            task = self.get_coinapi_price(symbol)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        price_data = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, dict) and 'error' not in result:
                price_data[symbol] = result
            else:
                price_data[symbol] = {'error': str(result)}
        
        return price_data
    
    async def get_coinapi_historical(self, symbol: str, period: str = "1HRS", limit: int = 100) -> Dict[str, Any]:
        """
        Get historical OHLCV data from CoinAPI
        
        Args:
            symbol: Crypto symbol
            period: Time period (1HRS, 1DAY, etc.)
            limit: Number of data points
            
        Returns:
            Dict with historical data or error
        """
        try:
            if not self.coinapi_key:
                return {'error': 'CoinAPI key not found'}
            
            clean_symbol = symbol.upper().replace('USDT', '')
            
            session = await self._get_session()
            url = f"{self.base_url}/ohlcv/{clean_symbol}/USD/history"
            
            params = {
                'period_id': period,
                'limit': limit
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data:
                        return {'error': 'No historical data available'}
                    
                    return {
                        'symbol': clean_symbol,
                        'period': period,
                        'data': data,
                        'count': len(data),
                        'source': 'coinapi_historical',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    return {'error': f'CoinAPI historical HTTP {response.status}: {error_text}'}
                    
        except asyncio.TimeoutError:
            return {'error': 'CoinAPI historical request timeout'}
        except Exception as e:
            return {'error': f'CoinAPI historical error: {str(e)}'}
    
    def format_price(self, price: float) -> str:
        """Format price with appropriate decimal places"""
        if price < 1:
            return f"${price:.8f}"
        elif price < 100:
            return f"${price:.6f}"
        else:
            return f"${price:,.4f}"
    
    def calculate_price_change(self, current: float, previous: float) -> float:
        """Calculate percentage price change"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
