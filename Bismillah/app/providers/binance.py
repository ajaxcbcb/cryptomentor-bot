from typing import List, Dict, Any
from app.providers.http import fetch_json

BINANCE_URL = "https://api.binance.com"

async def get_top_usdt_coins(limit: int = 30) -> List[str]:
    """Get top USDT pairs by volume"""
    url = f"{BINANCE_URL}/api/v3/ticker/24hr"
    data = await fetch_json(url, cache_key="binance:24hr", cache_ttl=300)
    
    # Filter USDT pairs and sort by volume
    usdt_pairs = [item for item in data if item['symbol'].endswith('USDT')]
    usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
    
    # Extract coin symbols (remove USDT suffix)
    coins = []
    for pair in usdt_pairs[:limit]:
        symbol = pair['symbol'].replace('USDT', '')
        if symbol not in ['USDC', 'USDT', 'BUSD', 'TUSD', 'DAI']:  # Skip stablecoins
            coins.append(symbol)
    
    return coins[:limit]

async def get_24h(symbol: str) -> Dict[str, Any]:
    """Get 24h ticker for a symbol"""
    url = f"{BINANCE_URL}/api/v3/ticker/24hr"
    params = {"symbol": f"{symbol.upper()}USDT"}
    return await fetch_json(url, params=params, cache_key=f"binance:ticker:{symbol}", cache_ttl=60)