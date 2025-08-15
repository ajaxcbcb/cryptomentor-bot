
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
    Return emoji based on sentiment score (0–100 scale or -1..1 normalized).
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

# --- Example usage ---
if __name__ == "__main__":
    print(title("COMPREHENSIVE MARKET ANALYSIS"))
    print(format_kv("Total Market Cap", "$4.02T"))
    print(bullet(["BTC: $60k", "ETH: $3k"], emoji="📊"))
