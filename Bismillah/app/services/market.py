
from __future__ import annotations
from typing import Dict, Any, List, Tuple
import math
from datetime import datetime
import requests
import asyncio

BINANCE_URL = "https://api.binance.com"

async def _get_24h_all() -> List[Dict[str, Any]]:
    """Get all 24h ticker data from Binance"""
    try:
        url = f"{BINANCE_URL}/api/v3/ticker/24hr"
        response = requests.get(url, timeout=12)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error fetching 24h data: {e}")
        return []

async def get_top_usdt_coins(limit: int = 20) -> List[str]:
    """Get top USDT pairs by volume"""
    try:
        url = f"{BINANCE_URL}/api/v3/ticker/24hr"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            usdt_pairs = [item for item in data if item['symbol'].endswith('USDT')]
            usdt_pairs.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
            return [pair['symbol'].replace('USDT', '') for pair in usdt_pairs[:limit]]
        return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT'][:limit]
    except Exception as e:
        print(f"Error getting top coins: {e}")
        return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'MATIC', 'DOT'][:limit]

def _classify_sentiment(breadth_pct: float) -> str:
    """Classify market sentiment based on breadth percentage"""
    if breadth_pct >= 60:
        return "Bullish"
    if breadth_pct <= 40:
        return "Bearish"
    return "Neutral"

async def get_market_sentiment(top_n: int = 20) -> Dict[str, Any]:
    """
    Get market sentiment based on top USDT pairs breadth analysis
    """
    try:
        top = await get_top_usdt_coins(limit=top_n)
        all24 = await _get_24h_all()

        by_symbol = {d.get("symbol"): d for d in all24}
        scanned: List[Dict[str, Any]] = []
        green = 0
        total = 0

        for coin in top:
            sym = f"{coin}USDT"
            d = by_symbol.get(sym)
            if not d:
                continue
            total += 1
            try:
                change_pct = float(d.get("priceChangePercent", 0.0))
                last_price = float(d.get("lastPrice", 0.0))
                qv = float(d.get("quoteVolume", 0.0))
            except Exception:
                change_pct, last_price, qv = 0.0, 0.0, 0.0
            
            if change_pct > 0:
                green += 1
            
            scanned.append({
                "coin": coin,
                "price": last_price,
                "change_24h": change_pct,
                "quote_volume": qv,
            })

        breadth_pct = (green / total * 100.0) if total else 0.0
        sentiment = _classify_sentiment(breadth_pct)

        # Sort by absolute change (biggest movers first)
        scanned.sort(key=lambda x: abs(x.get("change_24h", 0.0)), reverse=True)

        return {
            "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB"),
            "universe": f"Top {top_n} USDT by 24h volume",
            "breadth_pct": breadth_pct,
            "sentiment": sentiment,
            "coins": scanned,
            "counts": {"green": green, "red": total - green, "total": total},
            "success": True
        }

    except Exception as e:
        print(f"Error in get_market_sentiment: {e}")
        return {
            "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S WIB"),
            "universe": f"Top {top_n} USDT by 24h volume",
            "breadth_pct": 50.0,
            "sentiment": "Neutral",
            "coins": [],
            "counts": {"green": 0, "red": 0, "total": 0},
            "success": False,
            "error": str(e)
        }
