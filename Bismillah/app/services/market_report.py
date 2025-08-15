from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime
from app.providers import cmc as cmc_p
from app.providers import coingecko as cg_p
from app.providers.binance import get_24h

SYMBOLS_DEFAULT = ["BTC", "ETH", "BNB", "SOL", "XRP"]

def _now_wib(): 
    return datetime.now().strftime("%H:%M:%S WIB")

def _sentiment_from_change(ch: float) -> tuple[str, int]:
    # Heuristik confidence sederhana dari % perubahan market cap 24h
    conf = max(0, min(100, 60 + ch * 8))  # sekitar 60% di netral, geser ±
    if ch > 0.5: 
        return "📈 BULLISH", int(conf)
    if ch < -0.5: 
        return "📉 BEARISH", int(conf)
    return "😐 NEUTRAL", int(conf)

async def _global_primary() -> Dict[str, Any]:
    d = await cmc_p.get_global_metrics()
    g, q = d["data"], d["data"]["quote"]["USD"]
    return {
        "market_cap": float(q["total_market_cap"]),
        "market_cap_change_pct_24h": float(g.get("quote", {}).get("USD", {}).get("total_market_cap_yesterday_percentage_change", 0.0) or 0.0),
        "total_volume_24h": float(q["total_volume_24h"]),
        "active_cryptocurrencies": int(g.get("active_cryptocurrencies", 0) or 0),
        "btc_dominance": float(g.get("btc_dominance", 0.0) or 0.0),
        "eth_dominance": float(g.get("eth_dominance", 0.0) or 0.0),
    }

async def _global_fallback() -> Dict[str, Any]:
    d = await cg_p.get_global()
    g = d.get("data", {})
    return {
        "market_cap": float(g.get("total_market_cap", {}).get("usd", 0.0)),
        "market_cap_change_pct_24h": float(g.get("market_cap_change_percentage_24h_usd", 0.0)),
        "total_volume_24h": float(g.get("total_volume", {}).get("usd", 0.0)),
        "active_cryptocurrencies": int(g.get("active_cryptocurrencies", 0) or 0),
        "btc_dominance": float(g.get("market_cap_percentage", {}).get("btc", 0.0)),
        "eth_dominance": float(g.get("market_cap_percentage", {}).get("eth", 0.0)),
    }

async def _top_block(symbols: List[str]) -> List[Dict[str, Any]]:
    # Coba CMC; fallback Binance per simbol
    out = []
    try:
        q = await cmc_p.get_quotes(symbols)
        data = q["data"]
        for s in symbols:
            row = data.get(s.upper())
            row = row[0] if isinstance(row, list) else row
            usd = row["quote"]["USD"]
            ch = float(usd["percent_change_24h"])
            price = float(usd["price"])
            trend_word = "Bullish" if ch > 0 else ("Bearish" if ch < 0 else "Neutral")
            trend_emoji = "📈" if ch > 0 else ("📉" if ch < 0 else "😐")
            out.append({
                "symbol": s.upper(),
                "price": price,
                "change_pct_24h": ch,
                "trend_word": trend_word,
                "trend_emoji": trend_emoji
            })
        return out
    except Exception:
        for s in symbols:
            try:
                t = await get_24h(f"{s.upper()}USDT")
                ch = float(t.get("priceChangePercent", 0.0))
                price = float(t.get("lastPrice", 0.0))
            except Exception:
                ch, price = 0.0, 0.0
            trend_word = "Bullish" if ch > 0 else ("Bearish" if ch < 0 else "Neutral")
            trend_emoji = "📈" if ch > 0 else ("📉" if ch < 0 else "😐")
            out.append({
                "symbol": s.upper(),
                "price": price,
                "change_pct_24h": ch,
                "trend_word": trend_word,
                "trend_emoji": trend_emoji
            })
        return out

def _structure_block(btc_dom: float, mc_ch: float) -> Dict[str, str]:
    # Turunan struktur sederhana dari dominasi & perubahan MC
    if abs(mc_ch) < 0.5:
        return {
            "trend": "Sideways Consolidation",
            "structure": "BTC Dominance Phase",
            "reason": "Bitcoin consolidating market share, alts underperforming",
            "fear_greed": "😐 Neutral (45/100)"
        }
    if mc_ch >= 0.5:
        return {
            "trend": "Bullish Momentum",
            "structure": "Bitcoin-Led Bull Market" if btc_dom >= 50 else "Rotation to Alts",
            "reason": "Market growth driven primarily by Bitcoin strength" if btc_dom >= 50 else "Capital rotation toward alt sectors",
            "fear_greed": "😤 Greed (65/100)"
        }
    return {
        "trend": "Bearish Pressure",
        "structure": "Risk-off / Flight to Quality",
        "reason": "Liquidity contraction; majors outperform",
        "fear_greed": "🥶 Fear (35/100)"
    }

async def build_market_report(symbols: List[str] | None = None) -> Dict[str, Any]:
    # 1) Global
    try:
        g = await _global_primary()
    except Exception:
        g = await _global_fallback()

    # 2) Sentiment + confidence
    ch = float(g.get("market_cap_change_pct_24h", 0.0))
    sentiment, confidence = _sentiment_from_change(ch)

    # 3) Structure
    s = _structure_block(float(g.get("btc_dominance", 0.0)), ch)

    # 4) Top performance (urutkan sesuai input)
    syms = [s.upper() for s in (symbols or ["BTC", "ETH", "BNB", "SOL", "XRP"])]
    top = await _top_block(syms)

    return {
        "time": _now_wib(),
        "sentiment": sentiment,
        "confidence": confidence,
        "global": g,
        "structure": s,
        "top": top
    }