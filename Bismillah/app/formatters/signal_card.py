
from __future__ import annotations
from typing import Dict, Any, List

def _fmt_price(x) -> str:
    try:
        v = float(x)
        s = f"{v:,.2f}"
        return f"${s}"
    except Exception:
        return str(x)

def _fmt_pct(x) -> str:
    try:
        v = float(x)
        sign = "+" if v > 0 else ""
        return f"{sign}{v:.2f}%"
    except Exception:
        return str(x)

def _fmt_conf(x) -> str:
    try:
        return f"{float(x):.2f}%"
    except Exception:
        return str(x)

def _rr_text(rr) -> str:
    try:
        v = float(rr)
        txt = f"{v:.1f}".rstrip("0").rstrip(".")
        return f"{txt}:1"
    except Exception:
        return str(rr)

def format_signal_card(item: Dict[str, Any], *, include_entry: bool = True) -> str:
    """
    Format 1 sinyal seperti contoh:
    **1. APT 🟢 LONG**
    ⭐️ Confidence: 82.00%
    💰 Entry: $4.94
    🛑 Stop Loss: $4.80
    🎯 TP1: $5.04
    🎯 TP2: $5.10
    📊 R/R Ratio: 2.0:1
    🔄 Trend: Bullish
    ⚡️ Structure: LONG Bias
    🧠 Reason: Trend continuation setup
    📈 24h Change: +9.16%
    """
    coin = item.get("coin", "?")
    trend = (item.get("trend") or "").lower()
    trend_word = "Bullish" if trend == "up" else ("Bearish" if trend == "down" else "Sideways")
    dir_emoji = "🟢" if trend == "up" else ("🔴" if trend == "down" else "🟡")
    dir_word = "LONG" if trend == "up" else ("SHORT" if trend == "down" else "NEUTRAL")

    lines = [f"**{coin} {dir_emoji} {dir_word}**"]

    if "confidence" in item and item["confidence"] is not None:
        lines.append(f"⭐️ Confidence: {_fmt_conf(item['confidence'])}")

    if include_entry and item.get("entry") is not None:
        lines.append(f"💰 Entry: {_fmt_price(item['entry'])}")

    if item.get("stop") is not None:
        lines.append(f"🛑 Stop Loss: {_fmt_price(item['stop'])}")

    if item.get("tp1") is not None:
        lines.append(f"🎯 TP1: {_fmt_price(item['tp1'])}")
    if item.get("tp2") is not None:
        lines.append(f"🎯 TP2: {_fmt_price(item['tp2'])}")

    if item.get("rr") is not None:
        lines.append(f"📊 R/R Ratio: {_rr_text(item['rr'])}")

    lines.append(f"🔄 Trend: {trend_word}")

    if item.get("structure"):
        lines.append(f"⚡️ Structure: {item['structure']}")

    if item.get("reason"):
        lines.append(f"🧠 Reason: {item['reason']}")

    if "change_24h" in item and item["change_24h"] is not None:
        lines.append(f"📈 24h Change: {_fmt_pct(item['change_24h'])}")

    return "\n".join(lines)

def format_signal_list(items: List[Dict[str, Any]], *, include_entry: bool = True, title: str | None = None) -> str:
    out = []
    if title:
        out.append(title)
    if not items:
        out.append("❌ Tidak ada sinyal.")
        return "\n".join(out)
    for idx, it in enumerate(items, 1):
        card = format_signal_card(it, include_entry=include_entry)
        out.append(f"**{idx}.** " + card[2:] if card.startswith("**") else card)  # prefiks nomor
    return "\n".join(out)
