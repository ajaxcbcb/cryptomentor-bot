
from __future__ import annotations
from typing import Dict, Any, List

def _money(x: float) -> str:
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return str(x)

def _money_short(x: float) -> str:
    try:
        n = float(x)
        units = ["", "K", "M", "B", "T"]
        i = 0
        while abs(n) >= 1000 and i < len(units) - 1:
            n /= 1000
            i += 1
        return f"${n:,.2f}{units[i]}"
    except Exception:
        return str(x)

def _pct(x: float) -> str:
    try:
        v = float(x)
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.2f}%"
    except Exception:
        return str(x)

def format_market_report(rep: Dict[str, Any]) -> str:
    g, s, top = rep["global"], rep["structure"], rep["top"]
    lines = []
    
    lines.append("🌍 <b>COMPREHENSIVE MARKET ANALYSIS</b>")
    lines.append("")
    lines.append(f"🕐 <b>Analysis Time:</b> {rep['time']}")
    lines.append(f"📊 <b>Global Sentiment:</b> {rep['sentiment']}")
    lines.append(f"⭐️ <b>Confidence:</b> {rep['confidence']:.0f}%")
    lines.append("")
    
    lines.append("💰 <b>GLOBAL METRICS:</b>")
    lines.append(f"• Total Market Cap: {_money_short(g['market_cap'])}")
    lines.append(f"• 24h Market Change: {_pct(g.get('market_cap_change_pct_24h', 0.0))}")
    lines.append(f"• Total Volume 24h: {_money_short(g['total_volume_24h'])}")
    lines.append(f"• Active Cryptocurrencies: {int(g.get('active_cryptocurrencies', 0)):,}")
    lines.append(f"• BTC Dominance: {float(g.get('btc_dominance', 0.0)):.1f}%")
    lines.append(f"• ETH Dominance: {float(g.get('eth_dominance', 0.0)):.1f}%")
    lines.append("")
    
    lines.append("🔬 <b>MARKET STRUCTURE ANALYSIS:</b>")
    lines.append(f"🔄 Trend: {s['trend']}")
    lines.append(f"⚡️ Structure: {s['structure']}")
    lines.append(f"🧠 Reasoning: {s['reason']}")
    if s.get("fear_greed"):
        lines.append(f"📊 Fear &amp; Greed: {s['fear_greed']}")
    lines.append("")
    
    lines.append("📈 <b>TOP CRYPTOCURRENCIES PERFORMANCE:</b>")
    for idx, c in enumerate(top, 1):
        lines.append(f"{idx}. {c['symbol']} {c['trend_emoji']} {_money(c['price'])} ({_pct(c['change_pct_24h'])}) - {c['trend_word']}")
    lines.append("")
    
    lines.append("💡 <b>TRADING IMPLICATIONS:</b>")
    if "BULLISH" in rep["sentiment"]:
        lines += [
            "• 📈 Bullish momentum confirmed - Look for LONG opportunities",
            "• ⚡️ Scalping and swing trades favorable",
            "• 🟠 BTC leading market - Trade major pairs (BTC, ETH)",
            "• ⚠️ Altcoins may underperform - Be selective",
        ]
    elif "NEUTRAL" in rep["sentiment"]:
        lines += [
            "• 😐 Neutral market - Range trading strategies optimal",
            "• 🎯 Focus on support/resistance levels",
            "• 🟠 BTC leading market - Trade major pairs (BTC, ETH)",
            "• ⚠️ Altcoins may underperform - Be selective",
        ]
    else:
        lines += [
            "• 📉 Bearish momentum - Prefer defensive or hedge",
            "• 🛡️ Reduce leverage & protect capital",
            "• 🟠 Focus on high-liquidity majors",
            "• ⚠️ Avoid weak alts during drawdowns",
        ]
    lines.append("")
    
    lines.append("🎯 <b>MARKET OPPORTUNITIES:</b>")
    lines += [
        "• 🏃 Range trading between key support/resistance",
        "• ⚡️ Scalping opportunities in high-volume pairs",
        "• 🟠 Bitcoin maximalist strategy - Focus on BTC/ETH",
        "• 🔄 Cross-exchange arbitrage opportunities",
        "• 📈 Futures vs spot price discrepancies",
    ]
    lines.append("")
    
    lines.append("⚠️ <b>RISK ASSESSMENT:</b>")
    lines += [
        "• 😴 LOW VOLATILITY - May increase position sizes slightly",
        "• 📊 Wider stops acceptable (5-7%)",
        "• 🔍 Uncertain market conditions - Wait for clarity",
        "• 💡 Paper trade strategies before live execution",
        "• 📱 Monitor news and regulatory developments",
        "• ⏰ Set alerts for key support/resistance breaks",
    ]
    lines.append("")
    
    # Key levels heuristik: ±2% dom & ±5% MC
    btc_dom = float(g.get("btc_dominance", 0.0))
    mc = float(g.get("market_cap", 0.0))
    sup = max(0.0, btc_dom - 2.0)
    res = min(100.0, btc_dom + 2.0)
    lines.append("🚨 <b>KEY LEVELS TO WATCH:</b>")
    lines.append(f"• BTC Dominance Support: {sup:.1f}%")
    lines.append(f"• BTC Dominance Resistance: {res:.1f}%")
    lines.append(f"• Market Cap Key Level: {_money_short(mc * 0.95)} - {_money_short(mc * 1.05)}")
    lines.append("")
    
    lines.append("📡 Data Sources: CoinMarketCap Global Metrics + Multi-API Analysis")
    lines.append("⏰ Next Update: Setiap 15 menit untuk data real-time")
    lines.append("")
    lines.append("👑 Admin Access - Unlimited")
    
    return "\n".join(lines)
