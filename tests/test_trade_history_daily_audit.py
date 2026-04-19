import os
import sys
from datetime import datetime, timezone

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.trade_history as trade_history  # type: ignore


def test_daily_rr_integrity_audit_summarizes_per_mode(monkeypatch):
    window = {
        "utc_start": datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc),
        "utc_end": datetime(2026, 4, 19, 0, 0, tzinfo=timezone.utc),
        "local_start": datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc),
        "local_end": datetime(2026, 4, 19, 8, 0, tzinfo=timezone.utc),
    }
    monkeypatch.setattr(trade_history, "_resolve_day_window_utc", lambda **_kwargs: window)

    opened_rows = [
        {
            "trade_type": "scalping",
            "timeframe": "5m",
            "strategy": "stackmentor",
            "rr_ratio": 1.5,
            "entry_price": 100.0,
            "sl_price": 98.0,
            "tp_price": 103.0,
        },
        {
            "trade_type": "",
            "timeframe": "",
            "strategy": "stackmentor",
            "rr_ratio": 3.0,
            "entry_price": 50.0,
            "sl_price": 49.0,
            "tp1_price": 53.0,
        },
    ]
    closed_rows = [
        {
            "trade_type": "scalping",
            "timeframe": "5m",
            "strategy": "stackmentor",
            "status": "max_hold_time_exceeded",
            "close_reason": "max_hold_time_exceeded",
            "pnl_usdt": 1.0,
            "entry_price": 100.0,
            "sl_price": 98.0,
            "qty": 1.0,
        },
        {
            "trade_type": "",
            "timeframe": "",
            "strategy": "stackmentor",
            "status": "closed_sl",
            "close_reason": "closed_sl",
            "pnl_usdt": -1.0,
            "entry_price": 50.0,
            "sl_price": 49.0,
            "qty": 1.0,
        },
    ]

    def _fake_fetch(*, time_column, **_kwargs):
        return opened_rows if time_column == "opened_at" else closed_rows

    monkeypatch.setattr(trade_history, "_fetch_trades_for_window", _fake_fetch)

    report = trade_history.get_daily_rr_integrity_audit(include_runtime_snapshots=False)
    assert report["totals"]["opened_count"] == 2
    assert report["totals"]["closed_count"] == 2
    assert report["per_mode"]["scalping"]["configured_rr_median"] == 1.5
    assert report["per_mode"]["swing"]["configured_rr_median"] == 3.0
    assert report["per_mode"]["scalping"]["realized_r_median"] == 0.5
    assert report["per_mode"]["swing"]["realized_r_median"] == -1.0
    assert report["per_mode"]["scalping"]["close_reason_mix"]["max_hold_time_exceeded"] == 1
    assert report["explainability"]["losing_close_count"] == 1
    assert report["explainability"]["loss_reasoning_coverage_pct"] == 0.0
    assert report["explainability"]["missing_loss_reasoning_by_close_reason"]["closed_sl"] == 1


def test_daily_rr_integrity_audit_runtime_snapshots_include_reason_metadata(monkeypatch):
    window = {
        "utc_start": datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc),
        "utc_end": datetime(2026, 4, 19, 0, 0, tzinfo=timezone.utc),
        "local_start": datetime(2026, 4, 18, 8, 0, tzinfo=timezone.utc),
        "local_end": datetime(2026, 4, 19, 8, 0, tzinfo=timezone.utc),
    }
    monkeypatch.setattr(trade_history, "_resolve_day_window_utc", lambda **_kwargs: window)
    monkeypatch.setattr(
        trade_history,
        "_fetch_trades_for_window",
        lambda **_kwargs: [],
    )

    import app.adaptive_confluence as adaptive_confluence  # type: ignore
    import app.sideways_governor as sideways_governor  # type: ignore
    import app.win_playbook as win_playbook  # type: ignore

    monkeypatch.setattr(
        adaptive_confluence,
        "get_adaptive_overrides",
        lambda: {
            "updated_at": "2026-04-18T12:00:00+00:00",
            "decision_reason": "rate_limited",
            "conf_delta": 0,
            "volume_min_ratio_delta": 0.0,
        },
    )
    monkeypatch.setattr(sideways_governor, "refresh_sideways_governor_state", lambda: {})
    monkeypatch.setattr(
        sideways_governor,
        "get_sideways_governor_snapshot",
        lambda: {
            "updated_at": "2026-04-18T12:01:00+00:00",
            "mode": "normal",
            "decision_reason": "normal_hold",
            "sample_size_24h": 0,
        },
    )
    monkeypatch.setattr(win_playbook, "refresh_global_win_playbook_state", lambda: {})
    monkeypatch.setattr(
        win_playbook,
        "get_win_playbook_snapshot",
        lambda: {
            "updated_at": "2026-04-18T12:02:00+00:00",
            "guardrails_healthy": False,
            "rolling_expectancy": -0.1,
            "rolling_win_rate": 0.8,
            "sample_size": 300,
            "risk_overlay_pct": 0.0,
            "active_tags": [],
        },
    )

    report = trade_history.get_daily_rr_integrity_audit(include_runtime_snapshots=True)
    assert report["runtime_snapshots"]["adaptive"]["decision_reason"] == "rate_limited"
    assert report["runtime_snapshots"]["adaptive"]["sample_size"] == 0
    assert report["runtime_snapshots"]["sideways_governor"]["mode"] == "NORMAL"
    assert report["runtime_snapshots"]["win_playbook"]["guardrails_healthy"] is False
    assert report["runtime_snapshots"]["win_playbook"]["decision_reason"] == "hold"
    assert "top_tags" in report["runtime_snapshots"]["win_playbook"]
    assert "runtime_snapshot_quality" in report["explainability"]
    assert report["explainability"]["runtime_snapshot_quality"]["runtime_snapshots_ok"] is True
