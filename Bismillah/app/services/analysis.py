
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from app.providers.coinapi import ohlcv as ca_ohlcv, spot_rate
from app.providers.binance import get_24h
from app.services.indicators import to_df, ema, rsi, macd, atr
import asyncio

def _trend(df: pd.DataFrame) -> str:
    e50 = ema(df["close"], 50).iloc[-1]
    e200 = ema(df["close"], 200).iloc[-1]
    return "up" if e50 > e200 else ("down" if e50 < e200 else "sideways")

def _single_entry(df: pd.DataFrame) -> float:
    last = float(df["close"].iloc[-1])
    e50 = ema(df["close"], 50).iloc[-1]
    a14 = atr(df, 14).iloc[-1]
    t = _trend(df)
    return float(min(e50, last - 0.5 * a14) if t == "up" else max(e50, last + 0.5 * a14) if t == "down" else last - 0.2 * a14)

def _structure_label(t: str) -> str:
    return "LONG Bias" if t == "up" else ("SHORT Bias" if t == "down" else "Neutral")

def _reason(t: str, macd_hist: float) -> str:
    if t == "up" and macd_hist > 0:
        return "Trend continuation setup"
    if t == "down" and macd_hist < 0:
        return "Trend continuation setup"
    return "Range/await momentum"

def _confidence(t: str, rsi_last: float, macd_hist: float, atr_last: float, price: float) -> float:
    score = 0.0
    score += 30 if t == "up" else 15 if t == "down" else 5
    score += 30 * (1 / (1 + np.exp(-macd_hist * 4)))
    target = 55 if t == "up" else 45 if t == "down" else 50
    score += max(0.0, 30 - min(abs(rsi_last - target), 25) * 1.2)
    vol = (atr_last / max(price, 1e-9)) * 100
    if 0.5 <= vol <= 3.0:
        score += 10 * (1 - abs((vol - 1.75) / 1.75))
    return float(max(0, min(100, score)))

async def _enrich_change24(coin: str) -> float:
    try:
        t = await get_24h(f"{coin.upper()}USDT")
        return float(t.get("priceChangePercent", 0.0))
    except Exception:
        return 0.0

async def analyze_coin(coin: str) -> Dict[str, Any]:
    # SPOT analysis (NO entry in output)
    data = await ca_ohlcv(coin, period="5MIN", limit=300, kind="spot")
    df = to_df(data).dropna()
    t = _trend(df)
    r = rsi(df["close"])
    m, s, h = macd(df["close"])
    a = atr(df, 14)
    change = await _enrich_change24(coin)
    
    res = {
        "coin": coin.upper(),
        "price": float(df["close"].iloc[-1]),
        "trend": t,
        "rsi": float(r.iloc[-1]),
        "macd_hist": float(h.iloc[-1]),
        "atr": float(a.iloc[-1]),
        "structure": _structure_label(t),
        "reason": _reason(t, float(h.iloc[-1])),
        "change_24h": change
    }
    # NO entry here by design
    return res

async def analyze_coin_futures(coin: str) -> Dict[str, Any]:
    # PERP analysis (ONE entry)
    data = await ca_ohlcv(coin, period="5MIN", limit=300, kind="perp")
    df = to_df(data).dropna()
    t = _trend(df)
    r = rsi(df["close"])
    m, s, h = macd(df["close"])
    a = atr(df, 14)
    price = float(df["close"].iloc[-1])
    entry = _single_entry(df)
    
    # simple SL/TP: SL at entry-1*ATR (long) or entry+1*ATR (short); TP1/TP2 = R/R ~2
    A = float(a.iloc[-1])
    if t == "up":
        stop = entry - 1 * A
        tp1 = entry + 1 * A
        tp2 = entry + 2 * A
    elif t == "down":
        stop = entry + 1 * A
        tp1 = entry - 1 * A
        tp2 = entry - 2 * A
    else:
        stop = entry - 1.2 * A
        tp1 = entry + 1 * A
        tp2 = entry + 1.6 * A
    
    rr = 2.0
    change = await _enrich_change24(coin)
    conf = _confidence(t, float(r.iloc[-1]), float(h.iloc[-1]), A, price)
    
    return {
        "coin": coin.upper(),
        "price": price,
        "trend": t,
        "rsi": float(r.iloc[-1]),
        "macd_hist": float(h.iloc[-1]),
        "atr": A,
        "entry": float(entry),
        "stop": float(stop),
        "tp1": float(tp1),
        "tp2": float(tp2),
        "rr": rr,
        "structure": _structure_label(t),
        "reason": _reason(t, float(h.iloc[-1])),
        "confidence": conf,
        "change_24h": change
    }

async def futures_signals(coins: List[str], threshold: float = 75.0) -> List[Dict[str, Any]]:
    tasks = [analyze_coin_futures(c) for c in [x.upper() for x in coins]]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out = []
    for c, r in zip(coins, results):
        if isinstance(r, Exception):
            continue
        if float(r.get("confidence", 0.0)) >= threshold:
            out.append(r)
    out.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
    return out

async def futures_entry(coin: str) -> Dict[str, Any]:
    r = await analyze_coin_futures(coin)
    return {
        "coin": r["coin"],
        "price": r["price"],
        "entry": r["entry"],
        "trend": r["trend"]
    }

# Legacy compatibility
async def analyze_coin_crypto(symbol):
    """Legacy compatibility wrapper"""
    return await analyze_coin(symbol)
