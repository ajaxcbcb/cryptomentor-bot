import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    from Bismillah.app.trade_history import build_win_reasoning
except ImportError:
    from app.trade_history import build_win_reasoning  # type: ignore


def test_build_win_reasoning_includes_playbook_and_alignment():
    trade = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 64000.0,
        "exit_price": 64600.0,
        "close_reason": "closed_tp",
        "pnl_usdt": 12.5,
        "confidence": 84,
        "rr_ratio": 2.1,
        "trend_1h": "uptrend",
        "market_structure": "uptrend",
        "entry_reasons": ["Volume confirmation 1.8x", "Bullish OB", "BTC bias aligned"],
    }

    txt = build_win_reasoning(
        trade,
        playbook_tags=["volume_confirmation", "ob_fvg"],
        playbook_score=0.812,
    )
    assert "Playbook tags matched" in txt
    assert "Alignment factors" in txt
    assert "Realized positive expectancy" in txt
