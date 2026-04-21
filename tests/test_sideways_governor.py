import os
import sys
from datetime import datetime, timedelta, timezone

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    from Bismillah.app.sideways_governor import (
        default_sideways_governor_state,
        compute_next_sideways_governor_state,
        resolve_dynamic_max_hold_seconds,
        build_sideways_metrics,
    )
except ImportError:
    from app.sideways_governor import (  # type: ignore
        default_sideways_governor_state,
        compute_next_sideways_governor_state,
        resolve_dynamic_max_hold_seconds,
        build_sideways_metrics,
    )


def test_governor_moves_to_strict_on_negative_expectancy():
    prev = default_sideways_governor_state()
    now = datetime.now(timezone.utc)
    metrics = {
        "sample_size_24h": 24,
        "non_sideways_sample_size_24h": 80,
        "sideways_expectancy_24h": -0.001,
        "non_sideways_expectancy_24h": 0.02,
        "sideways_timeout_exit_count_24h": 12,
        "sideways_timeout_loss_count_24h": 5,
        "sideways_timeout_loss_rate_24h": 5 / 12,
        "fallback_sample_size_14d": 24,
        "sideways_expectancy_14d": -0.001,
        "sideways_timeout_exit_count_14d": 12,
        "sideways_timeout_loss_count_14d": 5,
        "sideways_timeout_loss_rate_14d": 5 / 12,
        "symbol_sideways_stats": {},
        "symbol_non_sideways_stats": {},
    }
    nxt = compute_next_sideways_governor_state(prev, metrics, now_utc=now)
    assert nxt["mode"] == "strict"
    assert nxt["allow_sideways_fallback"] is False
    assert nxt["sideways_confirmations_required"] >= 1
    assert float(nxt["sideways_min_rr_override"]) >= 1.1


def test_governor_moves_to_pause_for_severe_degradation():
    prev = default_sideways_governor_state()
    now = datetime.now(timezone.utc)
    metrics = {
        "sample_size_24h": 35,
        "non_sideways_sample_size_24h": 120,
        "sideways_expectancy_24h": -0.01,
        "non_sideways_expectancy_24h": 0.01,
        "sideways_timeout_exit_count_24h": 20,
        "sideways_timeout_loss_count_24h": 15,
        "sideways_timeout_loss_rate_24h": 0.75,
        "fallback_sample_size_14d": 35,
        "sideways_expectancy_14d": -0.01,
        "sideways_timeout_exit_count_14d": 20,
        "sideways_timeout_loss_count_14d": 15,
        "sideways_timeout_loss_rate_14d": 0.75,
        "symbol_sideways_stats": {},
        "symbol_non_sideways_stats": {},
    }
    nxt = compute_next_sideways_governor_state(prev, metrics, now_utc=now)
    assert nxt["mode"] == "pause"
    assert nxt["allow_sideways_entries"] is False
    assert float(nxt["pause_until_ts"]) > now.timestamp()


def test_governor_recovers_to_normal_after_two_good_windows():
    now = datetime.now(timezone.utc)
    prev = default_sideways_governor_state()
    prev["mode"] = "strict"
    prev["consecutive_recovery_windows"] = 0
    prev["fallback_recovery_windows"] = 0

    good_metrics = {
        "sample_size_24h": 30,
        "non_sideways_sample_size_24h": 140,
        "sideways_expectancy_24h": 0.002,
        "non_sideways_expectancy_24h": 0.03,
        "sideways_timeout_exit_count_24h": 18,
        "sideways_timeout_loss_count_24h": 7,
        "sideways_timeout_loss_rate_24h": 7 / 18,
        "fallback_sample_size_14d": 30,
        "sideways_expectancy_14d": 0.002,
        "sideways_timeout_exit_count_14d": 18,
        "sideways_timeout_loss_count_14d": 7,
        "sideways_timeout_loss_rate_14d": 7 / 18,
        "symbol_sideways_stats": {},
        "symbol_non_sideways_stats": {},
    }
    mid = compute_next_sideways_governor_state(prev, good_metrics, now_utc=now)
    assert mid["mode"] == "strict"
    assert mid["consecutive_recovery_windows"] == 1
    assert mid["fallback_recovery_windows"] == 1
    assert mid["allow_sideways_fallback"] is False

    nxt = compute_next_sideways_governor_state(mid, good_metrics, now_utc=now + timedelta(minutes=10))
    assert nxt["mode"] == "normal"
    assert nxt["consecutive_recovery_windows"] == 0
    assert nxt["allow_sideways_fallback"] is True


def test_governor_uses_14d_fallback_basis_when_24h_sample_sparse():
    prev = default_sideways_governor_state()
    now = datetime.now(timezone.utc)
    metrics = {
        "sample_size_24h": 0,
        "non_sideways_sample_size_24h": 40,
        "sideways_expectancy_24h": 0.0,
        "non_sideways_expectancy_24h": 0.01,
        "sideways_timeout_exit_count_24h": 0,
        "sideways_timeout_loss_count_24h": 0,
        "sideways_timeout_loss_rate_24h": 0.0,
        "fallback_sample_size_14d": 28,
        "sideways_expectancy_14d": -0.02,
        "sideways_timeout_exit_count_14d": 24,
        "sideways_timeout_loss_count_14d": 18,
        "sideways_timeout_loss_rate_14d": 0.75,
        "symbol_sideways_stats": {},
        "symbol_non_sideways_stats": {},
    }

    nxt = compute_next_sideways_governor_state(prev, metrics, now_utc=now)
    assert nxt["mode"] == "strict"
    assert nxt["sample_basis_window"] == "14d_fallback"
    assert nxt["sample_size_basis"] == 28
    assert nxt["sideways_expectancy_basis"] == -0.02
    assert nxt["allow_sideways_fallback"] is False


def test_governor_does_not_pause_on_fallback_only_degradation():
    prev = default_sideways_governor_state()
    now = datetime.now(timezone.utc)
    metrics = {
        "sample_size_24h": 0,
        "non_sideways_sample_size_24h": 80,
        "sideways_expectancy_24h": 0.0,
        "non_sideways_expectancy_24h": 0.01,
        "sideways_timeout_exit_count_24h": 0,
        "sideways_timeout_loss_count_24h": 0,
        "sideways_timeout_loss_rate_24h": 0.0,
        "fallback_sample_size_14d": 40,
        "sideways_expectancy_14d": -0.02,
        "sideways_timeout_exit_count_14d": 30,
        "sideways_timeout_loss_count_14d": 24,
        "sideways_timeout_loss_rate_14d": 0.80,
        "symbol_sideways_stats": {},
        "symbol_non_sideways_stats": {},
    }

    nxt = compute_next_sideways_governor_state(prev, metrics, now_utc=now)
    assert nxt["mode"] == "strict"
    assert nxt["decision_reason"] != "pause_sideways_60m"


def test_dynamic_max_hold_respects_symbol_overrides_and_bounds():
    snapshot = default_sideways_governor_state()
    snapshot["dynamic_hold_sideways_seconds"] = 120
    snapshot["dynamic_hold_non_sideways_seconds"] = 1800
    snapshot["symbol_sideways_hold_seconds"] = {"XRPUSDT": 150}
    snapshot["symbol_non_sideways_hold_seconds"] = {"BTCUSDT": 2400}

    assert resolve_dynamic_max_hold_seconds("XRPUSDT", True, snapshot=snapshot) == 150
    assert resolve_dynamic_max_hold_seconds("ETHUSDT", True, snapshot=snapshot) == 120
    assert resolve_dynamic_max_hold_seconds("BTCUSDT", False, snapshot=snapshot) == 2400
    assert resolve_dynamic_max_hold_seconds("ETHUSDT", False, snapshot=snapshot) == 1800


def test_build_sideways_metrics_computes_timeout_loss_rate():
    now = datetime.now(timezone.utc)
    rows = [
        {
            "symbol": "XRPUSDT",
            "status": "sideways_max_hold_exceeded",
            "close_reason": "sideways_max_hold_exceeded",
            "pnl_usdt": -0.03,
            "trade_subtype": "sideways_scalp",
            "closed_at": (now - timedelta(hours=1)).isoformat(),
        },
        {
            "symbol": "XRPUSDT",
            "status": "sideways_max_hold_exceeded",
            "close_reason": "sideways_max_hold_exceeded",
            "pnl_usdt": 0.01,
            "trade_subtype": "sideways_scalp",
            "closed_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "symbol": "BTCUSDT",
            "status": "max_hold_time_exceeded",
            "close_reason": "max_hold_time_exceeded",
            "pnl_usdt": 0.2,
            "trade_subtype": None,
            "closed_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "symbol": "XRPUSDT",
            "status": "sideways_max_hold_exceeded",
            "close_reason": "sideways_max_hold_exceeded",
            "pnl_usdt": -0.02,
            "trade_subtype": "sideways_scalp",
            "closed_at": (now - timedelta(days=5)).isoformat(),
        },
    ]
    m = build_sideways_metrics(rows, now_utc=now)
    assert m["sample_size_24h"] == 2
    assert m["sideways_timeout_exit_count_24h"] == 2
    assert m["sideways_timeout_loss_count_24h"] == 1
    assert abs(float(m["sideways_timeout_loss_rate_24h"]) - 0.5) < 1e-9
    assert m["fallback_sample_size_14d"] == 3
    assert m["sideways_timeout_exit_count_14d"] == 3
