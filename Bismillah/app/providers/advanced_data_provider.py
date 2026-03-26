"""
Advanced Data Provider
Integrates Helius (Solana on-chain) and CryptoCompare (market data)
"""

import os
import requests
from typing import Dict, Optional
import asyncio
import aiohttp

class AdvancedDataProvider:
    """Provide advanced market data from multiple sources"""
    
    def __init__(self):
        self.helius_api_key = os.getenv('HELIUS_API_KEY')
        self.cryptocompare_api_key = os.getenv('CRYPTOCOMPARE_API_KEY')
        
        self.helius_available = bool(self.helius_api_key)
        self.cryptocompare_available = bool(self.cryptocompare_api_key)
        
        if self.helius_available:
            print("✅ Helius API initialized")
        if self.cryptocompare_available:
            print("✅ CryptoCompare API initialized")
    
    async def get_cryptocompare_data(self, symbol: str) -> Optional[Dict]:
        """
        Get advanced market data from CryptoCompare
        - Social stats
        - News sentiment
        - Historical data
        """
        if not self.cryptocompare_available:
            return None
        
        try:
            # Remove USDT suffix if present
            clean_symbol = symbol.replace('USDT', '').replace('USD', '')
            
            async with aiohttp.ClientSession() as session:
                # Get social stats
                url = f"https://min-api.cryptocompare.com/data/social/coin/latest"
                params = {
                    'coinId': clean_symbol,
                    'api_key': self.cryptocompare_api_key
                }
                
                async with session.get(url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('Response') == 'Success':
                            social_data = data.get('Data', {})
                            
                            return {
                                'social_score': social_data.get('General', {}).get('Points', 0),
                                'twitter_followers': social_data.get('Twitter', {}).get('followers', 0),
                                'reddit_subscribers': social_data.get('Reddit', {}).get('subscribers', 0),
                                'sentiment': self._calculate_sentiment(social_data)
                            }
            
            return None
            
        except Exception as e:
            print(f"Error fetching CryptoCompare data: {e}")
            return None
    
    async def get_helius_solana_data(self, token_address: str) -> Optional[Dict]:
        """
        Get Solana on-chain data from Helius
        - Token holders
        - Transaction volume
        - Liquidity
        """
        if not self.helius_available:
            return None
        
        try:
            url = f"https://api.helius.xyz/v0/token-metadata"
            params = {
                'api-key': self.helius_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url}?api-key={self.helius_api_key}",
                    timeout=5
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'holders': data.get('holders', 0),
                            'liquidity': data.get('liquidity', 0),
                            'volume_24h': data.get('volume24h', 0)
                        }
            
            return None
            
        except Exception as e:
            print(f"Error fetching Helius data: {e}")
            return None
    
    def _calculate_sentiment(self, social_data: Dict) -> str:
        """Calculate overall sentiment from social data"""
        try:
            points = social_data.get('General', {}).get('Points', 0)
            
            if points > 1000000:
                return "Very Bullish 🚀"
            elif points > 500000:
                return "Bullish 📈"
            elif points > 100000:
                return "Neutral ↔️"
            elif points > 50000:
                return "Bearish 📉"
            else:
                return "Very Bearish 🔻"
        except:
            return "Unknown"
    
    async def get_enhanced_market_context(self, symbol: str) -> Dict:
        """
        Get enhanced market context combining multiple sources
        """
        context = {
            'social_data': None,
            'onchain_data': None
        }
        
        # Fetch data in parallel
        tasks = []
        
        # CryptoCompare social data
        if self.cryptocompare_available:
            tasks.append(self.get_cryptocompare_data(symbol))
        
        # Helius data (only for Solana tokens)
        if self.helius_available and symbol.upper() in ['SOL', 'SOLUSDT']:
            tasks.append(self.get_helius_solana_data(symbol))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            if len(results) > 0 and not isinstance(results[0], Exception):
                context['social_data'] = results[0]
            
            if len(results) > 1 and not isinstance(results[1], Exception):
                context['onchain_data'] = results[1]
        
        return context
    
    def format_enhanced_context(self, context: Dict) -> str:
        """Format enhanced context for AI prompt"""
        text = ""
        
        # Social data
        if context.get('social_data'):
            social = context['social_data']
            text += f"\n\n📱 Social Metrics:"
            text += f"\n- Sentiment: {social.get('sentiment', 'Unknown')}"
            text += f"\n- Social Score: {social.get('social_score', 0):,.0f}"
            
            if social.get('twitter_followers'):
                text += f"\n- Twitter Followers: {social['twitter_followers']:,.0f}"
            
            if social.get('reddit_subscribers'):
                text += f"\n- Reddit Subscribers: {social['reddit_subscribers']:,.0f}"
        
        # On-chain data
        if context.get('onchain_data'):
            onchain = context['onchain_data']
            text += f"\n\n⛓️ On-Chain Metrics:"
            text += f"\n- Token Holders: {onchain.get('holders', 0):,.0f}"
            text += f"\n- Liquidity: ${onchain.get('liquidity', 0):,.0f}"
            text += f"\n- Volume 24h: ${onchain.get('volume_24h', 0):,.0f}"
        
        return text if text else ""


# Global instance
advanced_data_provider = AdvancedDataProvider()
