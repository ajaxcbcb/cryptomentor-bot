
import time
import httpx
from typing import List, Dict, Any

BINANCE_URL = "https://api.binance.com"

async def get_klines(symbol="BNBUSDT", interval="5m", limit=300, timeout=10):
    """Get klines data from Binance"""
    url = f"{BINANCE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    
    rows = []
    for k in data:
        rows.append({
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(k[6]//1000)),
            "open": float(k[1]),
            "high": float(k[2]),
            "low":  float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    return rows

async def get_top_usdt_coins(limit: int = 30, timeout=12):
    """
    Ambil top USDT pairs by 24h quoteVolume dari Binance (spot),
    lalu kembalikan list coin tanpa suffix USDT. Contoh: ['BTC','ETH',...]
    """
    url = f"{BINANCE_URL}/api/v3/ticker/24hr"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
    
    items = []
    for it in data:
        sym = it.get("symbol", "")
        if (sym.endswith("USDT") and 
            "UPUSDT" not in sym and 
            "DOWNUSDT" not in sym and 
            "BULLUSDT" not in sym and 
            "BEARUSDT" not in sym and
            "LEVERAGEUSDT" not in sym):
            try:
                qv = float(it.get("quoteVolume", 0.0))
            except Exception:
                qv = 0.0
            items.append((sym, qv))
    
    items.sort(key=lambda x: x[1], reverse=True)
    top = [s[:-4] for s, _ in items[:limit]]  # buang "USDT"
    return top
