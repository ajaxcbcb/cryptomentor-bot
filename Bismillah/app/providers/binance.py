from typing import List, Dict, Any
from app.providers.http import fetch_json

BASE = "https://api.binance.com"

async def klines(symbol="BTCUSDT", interval="5m", limit=300):
    data = await fetch_json(f"{BASE}/api/v3/klines", params={"symbol": symbol, "interval": interval, "limit": limit},
                            cache_key=f"bn:kl:{symbol}:{interval}:{limit}", cache_ttl=20)
    rows = [{"time": k[6], "open": float(k[1]), "high": float(k[2]), "low": float(k[3]),
             "close": float(k[4]), "volume": float(k[5])} for k in data]
    return rows

async def get_24h(symbol):
    return await fetch_json(f"{BASE}/api/v3/ticker/24hr", params={"symbol": symbol},
                            cache_key=f"bn:24:{symbol}", cache_ttl=30)