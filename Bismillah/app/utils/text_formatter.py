
"""
Text formatting utilities for CryptoMentor AI bot.
Ensures compatibility with Telegram MarkdownV2 and HTML modes.
"""

import html
import re
from typing import List

# --- Basic text formatters ---
def bold(text: str) -> str:
    """Return text in bold (MarkdownV2 safe)."""
    return f"*{escape_md(text)}*"

def italic(text: str) -> str:
    """Return text in italic (MarkdownV2 safe)."""
    return f"_{escape_md(text)}_"

def code(text: str) -> str:
    """Return text as inline code."""
    return f"`{escape_md(text)}`"

def pre(text: str, lang: str = "") -> str:
    """Return text as code block, optional language hint."""
    if lang:
        return f"```{lang}\n{escape_md(text)}\n```"
    return f"```\n{escape_md(text)}\n```"

def bullet(items: List[str], emoji: str = "•") -> str:
    """Return bullet list from items."""
    return "\n".join(f"{emoji} {escape_md(str(i))}" for i in items)

# --- Escape helpers ---
def escape_md(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.
    """
    if text is None:
        return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', str(text))

def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(str(text)) if text else ""

# --- Sentiment emoji helper ---
def sentiment_emoji(score: float) -> str:
    """
    Return emoji based on sentiment score (0-100 scale or -1..1 normalized).
    """
    if score is None:
        return "😐"
    if score > 0.7 or score >= 70:
        return "🟢"
    elif score < 0.3 or score <= 30:
        return "🔴"
    else:
        return "😐"

# --- Special format for key-value pairs ---
def format_kv(title: str, value: str, bold_key: bool = True) -> str:
    """Format 'Key: Value' with bold key if desired."""
    if bold_key:
        return f"{bold(title)}: {escape_md(value)}"
    return f"{escape_md(title)}: {escape_md(value)}"

# --- Join sections with spacing ---
def join_sections(sections: List[str], spacer: str = "\n\n") -> str:
    """Join text sections with a spacer."""
    return spacer.join(s for s in sections if s and s.strip())

# --- Title formatter ---
def title(text: str, emoji: str = "🌍") -> str:
    """Format a section title with emoji."""
    return f"{emoji} {bold(text)}"

# --- Price formatter ---
def format_price(price: float, symbol: str = "$") -> str:
    """Format price with proper comma separation."""
    try:
        return f"{symbol}{float(price):,.2f}"
    except (ValueError, TypeError):
        return str(price)

# --- Percentage formatter ---
def format_percentage(pct: float, show_sign: bool = True) -> str:
    """Format percentage with optional sign."""
    try:
        v = float(pct)
        sign = "+" if v > 0 and show_sign else ""
        return f"{sign}{v:.2f}%"
    except (ValueError, TypeError):
        return str(pct)

# --- Money formatter with short notation ---
def format_money(amount: float, short: bool = False, symbol: str = "$") -> str:
    """Format money with optional short notation (1.2T, 45.6B, etc)."""
    try:
        v = float(amount)
        if not short:
            return f"{symbol}{v:,.2f}"
        
        # Short notation
        if v >= 1_000_000_000_000:  # Trillion
            return f"{symbol}{v/1_000_000_000_000:.1f}T"
        elif v >= 1_000_000_000:  # Billion
            return f"{symbol}{v/1_000_000_000:.1f}B"
        elif v >= 1_000_000:  # Million
            return f"{symbol}{v/1_000_000:.1f}M"
        elif v >= 1_000:  # Thousand
            return f"{symbol}{v/1_000:.1f}K"
        else:
            return f"{symbol}{v:.2f}"
    except (ValueError, TypeError):
        return str(amount)

# --- Risk/Reward ratio formatter ---
def format_rr_ratio(ratio: float) -> str:
    """Format risk/reward ratio."""
    try:
        return f"{float(ratio):.1f}:1"
    except (ValueError, TypeError):
        return str(ratio)

# --- Futures signals response formatter ---
def format_futures_signals_response(signals: List[Dict[str, Any]], scan_time: str = "", threshold: float = 75.0) -> str:
    """
    Format futures signals response for Telegram.
    Compatible with both legacy and modern signal formats.
    """
    if not signals:
        return f"""🚨 {bold("FUTURES SIGNALS – SUPPLY & DEMAND ANALYSIS")}

🕐 {bold("Scan Time")}: {escape_md(scan_time)}
📊 {bold("Signals Found")}: 0 (Confidence ≥ {threshold:.2f}%)

❌ Tidak ada sinyal memenuhi syarat

💡 Kemungkinan Penyebab:
• Market dalam kondisi consolidation  
• Volatilitas rendah saat ini
• Menunggu momentum yang lebih jelas

🔄 Alternatif:
• Coba /futures btc untuk analisis spesifik
• Gunakan /analyze eth untuk analisis fundamental  
• Monitor kondisi market dengan /market"""

    lines = [
        f"🚨 {bold('FUTURES SIGNALS – SUPPLY & DEMAND ANALYSIS')}",
        "",
        f"🕐 {bold('Scan Time')}: {escape_md(scan_time)}",
        f"📊 {bold('Signals Found')}: {len(signals)} (Confidence ≥ {threshold:.2f}%)",
        ""
    ]

    for i, signal in enumerate(signals, 1):
        coin = signal.get('coin', signal.get('symbol', 'Unknown'))
        trend = signal.get('trend', '').lower()
        direction = signal.get('direction', 'NEUTRAL')
        
        # Determine emoji and direction
        if trend == 'up' or direction in ['LONG', 'BUY']:
            emoji = "🟢"
            dir_text = "LONG"
        elif trend == 'down' or direction in ['SHORT', 'SELL']:
            emoji = "🔴"
            dir_text = "SHORT"
        else:
            emoji = "🟡"
            dir_text = "NEUTRAL"

        lines.append(f"{bold(f'{i}. {coin} {emoji} {dir_text}')}")
        
        if 'confidence' in signal:
            lines.append(f"⭐️ Confidence: {float(signal['confidence']):.2f}%")
        
        if signal.get('entry'):
            lines.append(f"💰 Entry: {format_price(signal['entry'])}")
        
        if signal.get('stop') or signal.get('sl'):
            stop_price = signal.get('stop') or signal.get('sl')
            lines.append(f"🛑 Stop Loss: {format_price(stop_price)}")
        
        if signal.get('tp1'):
            lines.append(f"🎯 TP1: {format_price(signal['tp1'])}")
        
        if signal.get('tp2'):
            lines.append(f"🎯 TP2: {format_price(signal['tp2'])}")
        
        if signal.get('rr') or signal.get('rr_ratio'):
            rr = signal.get('rr') or signal.get('rr_ratio')
            if isinstance(rr, str) and ':' in rr:
                lines.append(f"📊 R/R Ratio: {escape_md(rr)}")
            else:
                lines.append(f"📊 R/R Ratio: {float(rr):.1f}:1")
        
        if signal.get('structure'):
            lines.append(f"⚡️ Structure: {escape_md(signal['structure'])}")
        
        if signal.get('reason'):
            lines.append(f"🧠 Reason: {escape_md(signal['reason'])}")
        
        if signal.get('change_24h') is not None:
            change = float(signal['change_24h'])
            lines.append(f"📈 24h Change: {format_percentage(change)}")
        
        lines.append("")  # Space between signals

    return "\n".join(lines)

# --- Example usage ---
if __name__ == "__main__":
    print(title("COMPREHENSIVE MARKET ANALYSIS"))
    print(format_kv("Total Market Cap", "$4.02T"))
    print(bullet(["BTC: $60k", "ETH: $3k"], emoji="📊"))
