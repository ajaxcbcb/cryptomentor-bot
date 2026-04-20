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


def _mk_trade(
    status: str,
    pnl: float,
    entry_reasons=None,
    *,
    trade_type: str = "swing",
    timeframe: str = "15m",
    include_r_fields: bool = True,
):
    row = {
        "status": status,
        "close_reason": status,
        "pnl_usdt": pnl,
        "entry_reasons": entry_reasons or [],
        "closed_at": datetime.now(timezone.utc).isoformat(),
        "trade_type": trade_type,
        "timeframe": timeframe,
    }
    if include_r_fields:
        row["entry_price"] = 100.0
        row["sl_price"] = 99.0
        row["qty"] = 1.0
    return row


@pytest.fixture(autouse=True)
def _reset_state():
    with win_playbook._state_lock:
        win_playbook._state.clear()
    yield
    with win_playbook._state_lock:
        win_playbook._state.clear()


def test_mode_specific_patterns_use_mode_scoped_weights(monkeypatch):
    trades = []
    for _ in range(50):
        trades.append(_mk_trade("closed_tp", 1.2, ["Order block retest", "FVG reclaim"], trade_type="swing"))
    for _ in range(10):
        trades.append(_mk_trade("closed_sl", -0.8, ["Volume confirmation"], trade_type="swing"))

    for _ in range(50):
        trades.append(_mk_trade("closed_tp", 1.1, ["Volume confirmation 1.8x"], trade_type="scalping", timeframe="5m"))
    for _ in range(10):
        trades.append(_mk_trade("closed_sl", -0.7, ["Order block touch"], trade_type="scalping", timeframe="5m"))

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: trades)
    snapshot = win_playbook.refresh_global_win_playbook_state()

    swing_match = win_playbook.compute_playbook_match_from_reasons(
        ["Order block retest", "FVG reclaim"],
        snapshot=snapshot,
        trade_type="swing",
    )
    scalp_match = win_playbook.compute_playbook_match_from_reasons(
        ["Order block retest", "FVG reclaim"],
        snapshot=snapshot,
        trade_type="scalping",
        timeframe="5m",
    )

    assert swing_match["score_source"] == "swing"
    assert scalp_match["score_source"] == "scalping"
    assert swing_match["playbook_match_score"] > scalp_match["playbook_match_score"]


def test_pair_activation_requires_support_and_positive_lift(monkeypatch):
    trades = []
    for _ in range(15):
        trades.append(_mk_trade("closed_tp", 1.0, ["Order block", "Volume confirmation"]))
    for _ in range(20):
        trades.append(_mk_trade("closed_sl", -0.8, ["Order block"]))
    for _ in range(20):
        trades.append(_mk_trade("closed_sl", -0.8, ["Volume confirmation"]))
    # Below absolute pair threshold (8 < 10) even with strong wins.
    for _ in range(8):
        trades.append(_mk_trade("closed_tp", 0.9, ["BTC aligned", "EMA cross"]))
    for _ in range(20):
        trades.append(_mk_trade("closed_sl", -0.6, ["RSI overbought"]))

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: trades)
    snapshot = win_playbook.refresh_global_win_playbook_state()
    active_pair_keys = list(snapshot.get("active_pair_keys", []))

    assert "ob_fvg+volume_confirmation" in active_pair_keys
    assert "btc_alignment+ema_alignment" not in active_pair_keys


def test_pair_pattern_can_drive_strong_match_without_single_match(monkeypatch):
    trades = []
    for _ in range(18):
        trades.append(_mk_trade("closed_tp", 1.0, ["Order block", "Volume confirmation"]))
    for _ in range(30):
        trades.append(_mk_trade("closed_sl", -0.7, ["Order block"]))
    for _ in range(30):
        trades.append(_mk_trade("closed_sl", -0.7, ["Volume confirmation"]))
    for _ in range(22):
        trades.append(_mk_trade("closed_sl", -0.6, ["RSI overbought"]))

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: trades)
    snapshot = win_playbook.refresh_global_win_playbook_state()
    match = win_playbook.compute_playbook_match_from_reasons(
        ["Order block", "Volume confirmation"],
        snapshot=snapshot,
    )

    assert "ob_fvg+volume_confirmation" in match["matched_pair_tags"]
    assert any(tag.startswith("pair:ob_fvg+volume_confirmation") for tag in match["matched_tags"])
    assert match["strong_match"] is True


def test_guardrails_use_expectancy_r_for_ramp_and_brake(monkeypatch):
    positive_r = []
    for _ in range(45):
        positive_r.append(_mk_trade("closed_tp", 1.2, ["Volume confirmation"]))
    for _ in range(15):
        positive_r.append(_mk_trade("closed_sl", -0.4, ["RSI overbought"]))

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: positive_r)
    monkeypatch.setattr(win_playbook.time, "time", lambda: 1_000_000.0)
    snapshot = win_playbook.refresh_global_win_playbook_state()
    assert snapshot["guardrails_healthy"] is True
    assert snapshot["rolling_expectancy_r"] > 0

    ramped = win_playbook.evaluate_signal_risk(5.0, ["Volume confirmation 2.0x"])
    assert ramped["overlay_action"] == "ramp_up"
    assert ramped["risk_overlay_pct"] > 0

    negative_r = []
    for _ in range(50):
        negative_r.append(_mk_trade("closed_tp", 0.1, ["Volume confirmation"]))
    for _ in range(10):
        negative_r.append(_mk_trade("closed_sl", -5.0, ["RSI overbought"]))

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: negative_r)
    with win_playbook._state_lock:
        win_playbook._state.update({
            "risk_overlay_pct": 1.0,
            "last_overlay_update_ts": 0.0,
            "last_overlay_action": "ramp_up",
        })
    snapshot2 = win_playbook.refresh_global_win_playbook_state()
    assert snapshot2["guardrails_healthy"] is False
    assert snapshot2["rolling_expectancy_r"] <= 0
    assert snapshot2["risk_overlay_pct"] == pytest.approx(0.5)
    assert snapshot2["last_overlay_action"] == "brake_down"


def test_insufficient_valid_r_sample_stays_conservative(monkeypatch):
    no_r_rows = []
    for _ in range(50):
        no_r_rows.append(
            _mk_trade("closed_tp", 1.0, ["Volume confirmation"], include_r_fields=False)
        )
    for _ in range(10):
        no_r_rows.append(
            _mk_trade("closed_sl", -0.2, ["RSI overbought"], include_r_fields=False)
        )

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: no_r_rows)
    monkeypatch.setattr(win_playbook.time, "time", lambda: 1_000_000.0)
    snapshot = win_playbook.refresh_global_win_playbook_state()
    assert snapshot["valid_r_sample_size"] == 0
    assert snapshot["guardrails_healthy"] is False

    res = win_playbook.evaluate_signal_risk(5.0, ["Volume confirmation"])
    assert res["guardrails_healthy"] is False
    assert res["risk_overlay_pct"] == pytest.approx(0.0)
    assert res["overlay_action"] in {"brake_down", "hold", "hold_rate_limited"}


def test_snapshot_keeps_backward_keys_and_new_observability_fields(monkeypatch):
    trades = []
    for _ in range(40):
        trades.append(_mk_trade("closed_tp", 1.0, ["Volume confirmation"], trade_type="swing"))
    for _ in range(10):
        trades.append(_mk_trade("closed_sl", -0.4, ["RSI overbought"], trade_type="swing"))

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: trades)
    snapshot = win_playbook.refresh_global_win_playbook_state()

    assert "rolling_expectancy" in snapshot
    assert "rolling_expectancy_pnl" in snapshot
    assert "rolling_expectancy_r" in snapshot
    assert "active_pairs" in snapshot
    assert "mode_stats" in snapshot
    assert "historical_vocab_tags" in snapshot
    assert "swing" in snapshot["mode_stats"]
    assert "scalping" in snapshot["mode_stats"]


def test_risk_eval_honors_signal_mode_context(monkeypatch):
    trades = []
    for _ in range(45):
        trades.append(_mk_trade("closed_tp", 1.2, ["Order block"], trade_type="swing"))
    for _ in range(15):
        trades.append(_mk_trade("closed_sl", -0.4, ["RSI overbought"], trade_type="swing"))
    for _ in range(45):
        trades.append(_mk_trade("closed_tp", 1.2, ["Volume confirmation"], trade_type="scalping", timeframe="5m"))
    for _ in range(15):
        trades.append(_mk_trade("closed_sl", -0.4, ["Order block"], trade_type="scalping", timeframe="5m"))

    monkeypatch.setattr(win_playbook, "fetch_closed_trades", lambda limit=win_playbook.MAX_PLAYBOOK_FETCH_ROWS: trades)
    monkeypatch.setattr(win_playbook.time, "time", lambda: 1_000_000.0)
    win_playbook.refresh_global_win_playbook_state()

    swing_eval = win_playbook.evaluate_signal_risk(
        2.0,
        ["Order block"],
        trade_type="swing",
        timeframe="15m",
    )
    scalp_eval = win_playbook.evaluate_signal_risk(
        2.0,
        ["Order block"],
        trade_type="scalping",
        timeframe="5m",
    )

    assert swing_eval["playbook_score_source"] == "swing"
    assert scalp_eval["playbook_score_source"] == "scalping"
    assert swing_eval["playbook_match_score"] > scalp_eval["playbook_match_score"]
