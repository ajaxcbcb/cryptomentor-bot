import os
import sys
from datetime import datetime, timezone

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    from Bismillah.app import win_playbook
except ImportError:
    from app import win_playbook  # type: ignore


def _mk_trade(status: str, pnl: float, entry_reasons=None):
    return {
        "status": status,
        "close_reason": status,
        "pnl_usdt": pnl,
        "entry_reasons": entry_reasons or [],
        "closed_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture(autouse=True)
def _reset_state():
    with win_playbook._state_lock:
        win_playbook._state.clear()
    yield
    with win_playbook._state_lock:
        win_playbook._state.clear()


def test_tag_activation_filters_noise_and_positive_lift(monkeypatch):
    trades = []
    trades.extend([
        _mk_trade("closed_tp", 2.0, ["📊 Volume confirmation 1.8x", "BTC aligned"]),
        _mk_trade("closed_tp", 1.8, ["Volume spike 2.1x", "SMC BOS"]),
        _mk_trade("closed_tp", 1.1, ["Volume confirmation 1.6x"]),
        _mk_trade("closed_tp", 1.5, ["Volume confirmation 1.4x"]),
        _mk_trade("closed_tp", 1.2, ["Volume spike", "✅"]),
        _mk_trade("closed_tp", 1.0, ["Volume confirmation", "Error: Insufficient data"]),
    ])
    trades.extend([
        _mk_trade("closed_sl", -1.0, ["RSI overbought"]),
        _mk_trade("closed_sl", -1.2, ["RSI overbought"]),
        _mk_trade("closed_sl", -0.7, ["Conflicting timeframes"]),
        _mk_trade("closed_sl", -0.5, ["🚫"]),
    ])
    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=2500: trades)

    snapshot = win_playbook.refresh_global_win_playbook_state()
    active_names = snapshot.get("active_tag_names", [])
    assert "volume_confirmation" in active_names
    assert all(tag != "reason:error_insufficient_data" for tag in active_names)


def test_match_score_is_deterministic(monkeypatch):
    trades = [
        _mk_trade("closed_tp", 1.0, ["Volume confirmation 1.8x", "BTC aligned"]),
        _mk_trade("closed_tp", 1.0, ["Volume spike", "BTC bias aligned"]),
        _mk_trade("closed_tp", 1.0, ["Volume confirmation", "BTC aligned"]),
        _mk_trade("closed_tp", 1.0, ["Volume confirmation", "BTC aligned"]),
        _mk_trade("closed_tp", 1.0, ["Volume confirmation", "BTC aligned"]),
        _mk_trade("closed_tp", 1.0, ["Volume confirmation", "BTC aligned"]),
        _mk_trade("closed_sl", -1.0, ["RSI overbought"]),
        _mk_trade("closed_sl", -1.0, ["RSI overbought"]),
        _mk_trade("closed_sl", -1.0, ["RSI oversold"]),
        _mk_trade("closed_sl", -1.0, ["RSI oversold"]),
    ]
    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=2500: trades)
    snapshot = win_playbook.refresh_global_win_playbook_state()

    r1 = win_playbook.compute_playbook_match_from_reasons(
        ["Volume confirmation 1.6x", "BTC aligned"], snapshot=snapshot
    )
    r2 = win_playbook.compute_playbook_match_from_reasons(
        ["Volume confirmation 1.6x", "BTC aligned"], snapshot=snapshot
    )
    assert r1["playbook_match_score"] == r2["playbook_match_score"]
    assert r1["matched_tags"] == r2["matched_tags"]


def test_risk_controller_ramps_and_brakes_with_cap(monkeypatch):
    with win_playbook._state_lock:
        win_playbook._state.update({
            "active_tags": [{"tag": "volume_confirmation", "weight": 1.0}],
            "active_tag_names": ["volume_confirmation"],
            "risk_overlay_pct": 0.0,
            "last_overlay_update_ts": 0.0,
            "guardrails_healthy": True,
            "rolling_win_rate": 0.8,
            "rolling_expectancy": 0.2,
            "sample_size": 120,
        })

    now = {"ts": 1_000_000.0}
    monkeypatch.setattr(win_playbook.time, "time", lambda: now["ts"])

    for _ in range(30):
        res = win_playbook.evaluate_signal_risk(5.0, ["Volume confirmation 2.0x"])
        now["ts"] += 121.0
    assert res["risk_overlay_pct"] <= 5.0
    assert res["effective_risk_pct"] <= 10.0

    with win_playbook._state_lock:
        win_playbook._state["guardrails_healthy"] = False
    before = res["risk_overlay_pct"]
    res2 = win_playbook.evaluate_signal_risk(5.0, ["Volume confirmation 2.0x"])
    now["ts"] += 121.0
    res3 = win_playbook.evaluate_signal_risk(5.0, ["Volume confirmation 2.0x"])
    assert res2["risk_overlay_pct"] <= before
    assert res3["risk_overlay_pct"] <= res2["risk_overlay_pct"]
