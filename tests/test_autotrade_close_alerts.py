import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.autotrade_engine as autotrade_engine  # type: ignore
from app.close_alerts import format_trade_close_alert, close_reason_label  # type: ignore


def test_partial_close_symbol_diff_is_detectable():
    prev_live = {"BTCUSDT", "ETHUSDT"}
    now_live = autotrade_engine._extract_live_symbols(
        [
            {"symbol": "BTCUSDT", "qty": 0.25},
            {"symbol": "ETHUSDT", "qty": 0},
        ]
    )
    closed_symbols = prev_live - now_live
    assert closed_symbols == {"ETHUSDT"}


def test_format_trade_close_alert_contains_detailed_fields():
    msg = format_trade_close_alert(
        symbol="BTCUSDT",
        side="BUY",
        close_reason="closed_tp3",
        entry_price=100.0,
        exit_price=110.5,
        pnl_usdt=10.5,
    )
    assert "Trade Closed" in msg
    assert "BTCUSDT" in msg
    assert "LONG" in msg
    assert "TP3 Hit" in msg
    assert "Entry:" in msg
    assert "Exit:" in msg
    assert "PnL:" in msg


def test_close_reason_label_handles_timeout_and_reconcile_reasons():
    assert close_reason_label("max_hold_time_exceeded") == "Max Hold Timeout"
    assert close_reason_label("stale_reconcile") == "Exchange Reconcile Close"
