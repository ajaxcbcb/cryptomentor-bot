import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    from Bismillah.app.trade_history import (
        build_win_reasoning,
        _should_enforce_win_reasoning,
        _normalized_win_tags,
    )
except ImportError:
    from app.trade_history import (  # type: ignore
        build_win_reasoning,
        _should_enforce_win_reasoning,
        _normalized_win_tags,
    )


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


def test_should_enforce_win_reasoning_status_policy():
    assert _should_enforce_win_reasoning("closed_tp", -0.20) is True
    assert _should_enforce_win_reasoning("closed_tp3", -1.00) is True
    assert _should_enforce_win_reasoning("closed_sl", 0.50) is True
    assert _should_enforce_win_reasoning("closed_flip", 0.01) is True
    assert _should_enforce_win_reasoning("closed_flip", -0.01) is False


def test_normalized_win_tags_fallback_non_empty():
    assert _normalized_win_tags([], "closed_tp") == ["win_close", "closed_tp"]
    assert _normalized_win_tags(None, "closed_tp3") == ["win_close", "closed_tp3"]
    assert _normalized_win_tags(["tag_a"], "closed_tp") == ["tag_a"]
