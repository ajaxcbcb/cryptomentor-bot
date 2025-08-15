
from typing import Dict, Any, List
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.providers.coinapi import get_price_spot, get_ohlcv
from app.services.indicators import to_df, ema, rsi, macd, atr

def _trend_label(df: pd.DataFrame) -> str:
    e50 = ema(df["close"], 50)
    e200 = ema(df["close"], 200)
    if e50.iloc[-1] > e200.iloc[-1]: return "up"
    if e50.iloc[-1] < e200.iloc[-1]: return "down"
    return "sideways"

def _single_entry_point(df: pd.DataFrame) -> float:
    """
    Syarat user: satu titik entry saja.
    Logika:
      - Trend up  -> entry di 'pullback' ke EMA50 (dibatasi di atas support low N)
      - Trend down-> entry di 'retrace' ke EMA50 (dibatasi di bawah resistance high N)
      - Sideways  -> entry di mid (Close -/+ 0.5*ATR)
    """
    last_close = float(df["close"].iloc[-1])
    e50 = ema(df["close"], 50).iloc[-1]
    a14 = atr(df, 14).iloc[-1]
    trend = _trend_label(df)

    if trend == "up":
        # entry = min(EMA50, last_close - 0.5*ATR) → jaga risk
        return float(min(e50, last_close - 0.5 * a14))
    elif trend == "down":
        # entry = max(EMA50, last_close + 0.5*ATR) → sell the rip / short
        return float(max(e50, last_close + 0.5 * a14))
    else:
        # sideways → harga tengah band ATR
        return float(last_close - 0.2 * a14)

async def analyze_coin(coin: str) -> Dict[str, Any]:
    ohlcv = await get_ohlcv(coin, period="5MIN", limit=300)
    df = to_df(ohlcv)
    df = df.dropna()
    trend = _trend_label(df)
    r = rsi(df["close"])
    m, s, h = macd(df["close"])
    a = atr(df, 14)

    info = {
        "coin": coin.upper(),
        "price": float(df["close"].iloc[-1]),
        "trend": trend,
        "rsi": float(r.iloc[-1]),
        "macd_hist": float(h.iloc[-1]),
        "atr": float(a.iloc[-1]),
    }
    info["entry_one"] = _single_entry_point(df)
    return info

async def futures_entry(coin: str) -> Dict[str, Any]:
    # gunakan analyze_coin; enforce single entry point
    res = await analyze_coin(coin)
    return {
        "coin": res["coin"],
        "price": res["price"],
        "entry": res["entry_one"],  # SATU TITIK
        "trend": res["trend"],
    }

async def futures_signals(coin_list: List[str]) -> List[Dict[str, Any]]:
    out = []
    for c in coin_list:
        try:
            ana = await analyze_coin(c)
            # sinyal sederhana: tren up + macd hist > 0 + 40 < rsi < 70
            good = (ana["trend"]=="up") and (ana["macd_hist"]>0) and (40 < ana["rsi"] < 70)
            out.append({
                "coin": ana["coin"],
                "ok": bool(good),
                "entry": ana["entry_one"],
                "rsi": ana["rsi"],
                "macd_hist": ana["macd_hist"],
                "trend": ana["trend"],
                "price": ana["price"],
            })
        except Exception as e:
            out.append({"coin": c.upper(), "error": str(e)})
    return out

async def market_overview(top: List[str] = ["BTC","ETH"]) -> Dict[str, Any]:
    data = {}
    for c in top:
        try:
            p = await get_price_spot(c)
            data[c.upper()] = {"price": float(p)}
        except Exception as e:
            data[c.upper()] = {"error": str(e)}
    return {"coins": data}
