
from typing import Dict, Any, List
import asyncio
import pandas as pd
import numpy as np
from app.utils.async_tools import gather_safe
from app.providers.coinapi import get_ohlcv, get_price_spot
from app.providers.binance import get_top_usdt_coins
from app.services.indicators import to_df, ema, rsi, macd, atr

def _trend_label(df: pd.DataFrame) -> str:
    """Determine trend based on EMAs"""
    e50 = ema(df["close"], 50)
    e200 = ema(df["close"], 200)
    if e50.iloc[-1] > e200.iloc[-1]: 
        return "up"
    if e50.iloc[-1] < e200.iloc[-1]: 
        return "down"
    return "sideways"

def _single_entry_point(df: pd.DataFrame) -> float:
    """Calculate single entry point based on trend"""
    last_close = float(df["close"].iloc[-1])
    e50 = ema(df["close"], 50).iloc[-1]
    a14 = atr(df, 14).iloc[-1]
    trend = _trend_label(df)
    
    if trend == "up":
        return float(min(e50, last_close - 0.5 * a14))
    elif trend == "down":
        return float(max(e50, last_close + 0.5 * a14))
    else:
        return float(last_close - 0.2 * a14)

def _confidence(trend: str, rsi_last: float, macd_hist_last: float, atr_last: float, price_last: float) -> float:
    """
    Calculate confidence score 0-100:
      +30 if trend 'up', +15 if 'down' (we prefer long signals)
      +0..30 from MACD hist (sigmoid scale)
      +0..30 from RSI proximity to healthy zone (55 for long, 45 for short)
      +0..10 bonus for healthy volatility (ATR/price in 0.5%..3%)
    """
    score = 0.0
    
    # Trend scoring
    if trend == "up":   
        score += 30
    elif trend == "down": 
        score += 15
    else: 
        score += 5

    # MACD histogram -> 0..30 (using sigmoid for smooth scaling)
    macd_scaled = 1/(1+np.exp(-macd_hist_last*4))  # 0..1
    score += 30 * macd_scaled

    # RSI fit: target 55 (long) vs 45 (short)
    target = 55 if trend == "up" else (45 if trend == "down" else 50)
    rsi_penalty = min(abs(rsi_last - target), 25)  # large deviation penalized
    score += max(0.0, 30 - (rsi_penalty * 1.2))

    # Volatility sweet spot
    vol = (atr_last / max(price_last, 1e-9)) * 100  # %
    if 0.5 <= vol <= 3.0:
        score += 10.0 * (1 - abs((vol-1.75)/1.75))  # peak at ~1.75%

    return float(max(0.0, min(100.0, score)))

async def analyze_coin_futures(coin: str) -> Dict[str, Any]:
    """Analyze single coin for futures trading"""
    try:
        ohlcv = await get_ohlcv(coin, period="5MIN", limit=300, market="perp")
        df = to_df(ohlcv).dropna()
        
        if len(df) < 200:
            return {"coin": coin.upper(), "error": "Insufficient data"}
        
        trend = _trend_label(df)
        r = rsi(df["close"])
        m, s, h = macd(df["close"])
        a = atr(df, 14)

        price = float(df["close"].iloc[-1])
        res: Dict[str, Any] = {
            "coin": coin.upper(),
            "price": price,
            "trend": trend,
            "rsi": float(r.iloc[-1]),
            "macd_hist": float(h.iloc[-1]),
            "atr": float(a.iloc[-1]),
            "entry": _single_entry_point(df),
        }
        
        res["confidence"] = _confidence(res["trend"], res["rsi"], res["macd_hist"], res["atr"], price)
        res["ok"] = res["confidence"] >= 75.0
        return res
        
    except Exception as e:
        return {"coin": coin.upper(), "error": str(e)}

async def futures_signals(coins: List[str] = None, crypto_api=None, threshold: float = 75.0) -> List[Dict[str, Any]]:
    """
    Scan coins for futures signals with confidence >= threshold
    If no coins specified, get Top 30 by volume
    """
    try:
        # If no coins specified → get Top 30 by volume
        if not coins:
            coins = await get_top_usdt_coins(limit=30)
        
        coins_up = [c.upper() for c in coins]

        tasks = [analyze_coin_futures(c) for c in coins_up]
        results = await gather_safe(tasks)

        out: List[Dict[str, Any]] = []
        for c, r in zip(coins_up, results):
            if isinstance(r, Exception):
                out.append({"coin": c, "error": str(r)})
            else:
                if r.get("confidence", 0.0) >= threshold:
                    out.append(r)
        
        # Sort by confidence (highest first)
        valid_signals = [x for x in out if 'error' not in x]
        valid_signals.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
        
        return valid_signals[:10]  # Return top 10 signals max
        
    except Exception as e:
        print(f"Error in futures_signals: {e}")
        return []
