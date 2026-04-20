"""
Shared helpers for user-facing trade close alerts.
"""
from html import escape
from typing import Any


_CLOSE_REASON_LABELS = {
    "closed_tp": "TP Hit",
    "closed_tp1": "TP1 Hit",
    "closed_tp2": "TP2 Hit",
    "closed_tp3": "TP3 Hit",
    "closed_sl": "SL Hit",
    "closed_flip": "Flip Close",
    "max_hold_time_exceeded": "Max Hold Timeout",
    "sideways_max_hold_exceeded": "Sideways Max Hold Timeout",
    "stale_reconcile": "Exchange Reconcile Close",
}


def _fmt_price(value: Any) -> str:
    try:
        v = float(value)
    except Exception:
        v = 0.0
    s = f"{v:,.6f}"
    return s.rstrip("0").rstrip(".")


def _fmt_pnl(value: Any) -> str:
    try:
        pnl = float(value)
    except Exception:
        pnl = 0.0
    if abs(pnl) < 0.01:
        return f"{pnl:+.4f}"
    return f"{pnl:+.2f}"


def normalize_trade_side(side: Any) -> str:
    raw = str(side or "").strip().upper()
    if raw in {"BUY", "LONG"}:
        return "LONG"
    if raw in {"SELL", "SHORT"}:
        return "SHORT"
    return raw or "UNKNOWN"


def close_reason_label(close_reason: Any) -> str:
    key = str(close_reason or "").strip().lower()
    if not key:
        return "Unknown Close"
    return _CLOSE_REASON_LABELS.get(key, key.replace("_", " ").title())


def format_trade_close_alert(
    *,
    symbol: Any,
    side: Any,
    close_reason: Any,
    entry_price: Any,
    exit_price: Any,
    pnl_usdt: Any,
    header: str = "🔔 <b>Trade Closed</b>",
) -> str:
    reason = close_reason_label(close_reason)
    reason_raw = str(close_reason or "").strip().lower() or "unknown"
    symbol_txt = escape(str(symbol or "").strip().upper() or "-")
    side_txt = escape(normalize_trade_side(side))
    reason_txt = escape(reason)
    reason_code_txt = escape(reason_raw)
    return (
        f"{header}\n\n"
        f"Symbol: <b>{symbol_txt}</b>\n"
        f"Side: <b>{side_txt}</b>\n"
        f"Close Reason: <b>{reason_txt}</b> (<code>{reason_code_txt}</code>)\n"
        f"Entry: <code>{_fmt_price(entry_price)}</code>\n"
        f"Exit: <code>{_fmt_price(exit_price)}</code>\n"
        f"PnL: <b>{_fmt_pnl(pnl_usdt)} USDT</b>"
    )
