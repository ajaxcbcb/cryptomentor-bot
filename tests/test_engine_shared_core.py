import os
import sys
from types import SimpleNamespace

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.engine_runtime_shared as runtime_shared  # type: ignore
from app.autotrade_engine import _scalping_engines, get_engine, get_scalping_engine  # type: ignore
from app.engine_execution_shared import build_cumulative_close_update_payload  # type: ignore


def test_get_scalping_engine_alias_delegates_runtime_instance(monkeypatch):
    uid = 91001
    sentinel = object()
    monkeypatch.setitem(_scalping_engines, uid, sentinel)
    assert get_engine(uid) is sentinel
    assert get_scalping_engine(uid) is sentinel


def test_should_notify_blocked_pending_honors_ttl():
    cache = {}
    assert runtime_shared.should_notify_blocked_pending(cache, key="BTCUSDT", ttl_sec=600, now_ts=1000.0) is True
    assert runtime_shared.should_notify_blocked_pending(cache, key="BTCUSDT", ttl_sec=600, now_ts=1200.0) is False
    assert runtime_shared.should_notify_blocked_pending(cache, key="BTCUSDT", ttl_sec=600, now_ts=1601.0) is True


@pytest.mark.asyncio
async def test_refresh_runtime_snapshot_respects_next_refresh():
    calls = {"refresh": 0}

    def _refresh():
        calls["refresh"] += 1

    def _snapshot():
        return {"state": "new"}

    next_ts, snap, refreshed, err = await runtime_shared.refresh_runtime_snapshot(
        now_ts=100.0,
        next_refresh_ts=200.0,
        refresh_fn=_refresh,
        snapshot_fn=_snapshot,
        current_snapshot={"state": "old"},
        interval_sec=600.0,
    )
    assert next_ts == 200.0
    assert snap == {"state": "old"}
    assert refreshed is False
    assert err is None
    assert calls["refresh"] == 0


@pytest.mark.asyncio
async def test_refresh_runtime_snapshot_refreshes_on_cadence():
    calls = {"refresh": 0}

    def _refresh():
        calls["refresh"] += 1

    def _snapshot():
        return {"state": "fresh"}

    next_ts, snap, refreshed, err = await runtime_shared.refresh_runtime_snapshot(
        now_ts=200.0,
        next_refresh_ts=200.0,
        refresh_fn=_refresh,
        snapshot_fn=_snapshot,
        current_snapshot={"state": "old"},
        interval_sec=30.0,
    )
    assert next_ts == 230.0
    assert snap == {"state": "fresh"}
    assert refreshed is True
    assert err is None
    assert calls["refresh"] == 1


@pytest.mark.asyncio
async def test_should_stop_engine_reads_db_control_row(monkeypatch):
    async def _fake_fetch(_user_id: int):
        return {"status": "stopped", "engine_active": False}

    monkeypatch.setattr(runtime_shared, "fetch_engine_control_row", _fake_fetch)
    assert await runtime_shared.should_stop_engine(1234) is True


@pytest.mark.asyncio
async def test_should_stop_engine_returns_false_on_poll_error(monkeypatch):
    async def _fake_fetch(_user_id: int):
        raise RuntimeError("db timeout")

    monkeypatch.setattr(runtime_shared, "fetch_engine_control_row", _fake_fetch)
    assert await runtime_shared.should_stop_engine(1234) is False


def test_build_cumulative_close_update_payload_uses_cumulative_pnl_and_win_reasoning():
    open_row = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 100.0,
        "entry_reasons": ["smc_break", "volume_expand"],
        "confidence": 79.0,
        "rr_ratio": 2.3,
        "profit_tp1": 7.5,
        "profit_tp2": 0.0,
        "profit_tp3": 0.0,
        "playbook_match_score": 0.35,
        "effective_risk_pct": 1.25,
        "risk_overlay_pct": 0.25,
    }
    position = SimpleNamespace(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=100.0,
        entry_reasons=["smc_break", "volume_expand"],
        playbook_match_score=0.0,
        effective_risk_pct=1.25,
        risk_overlay_pct=0.25,
    )

    payload, cumulative_pnl, partial_realized = build_cumulative_close_update_payload(
        open_row=open_row,
        position=position,
        close_price=101.0,
        pnl=-2.0,
        close_reason="closed_sl",
        playbook_snapshot=None,
    )
    assert partial_realized == pytest.approx(7.5)
    assert cumulative_pnl == pytest.approx(5.5)
    assert payload["pnl_usdt"] == pytest.approx(5.5)
    assert payload["close_reason"] == "closed_sl"
    assert payload["status"] == "closed_sl"
    assert payload.get("win_reasoning"), "Positive cumulative exits must persist win_reasoning"
    assert "loss_reasoning" not in payload


def test_build_cumulative_close_update_payload_sets_auto_loss_reasoning_on_losses():
    open_row = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 100.0,
        "entry_reasons": ["smc_break"],
        "confidence": 70.0,
        "rr_ratio": 2.0,
    }
    position = SimpleNamespace(symbol="BTCUSDT", side="BUY", entry_price=100.0, entry_reasons=["smc_break"])

    payload, cumulative_pnl, partial_realized = build_cumulative_close_update_payload(
        open_row=open_row,
        position=position,
        close_price=98.0,
        pnl=-2.5,
        close_reason="closed_sl",
    )
    assert partial_realized == pytest.approx(0.0)
    assert cumulative_pnl == pytest.approx(-2.5)
    assert payload["pnl_usdt"] == pytest.approx(-2.5)
    assert payload["loss_reasoning"].startswith("auto_loss_reason: close_reason=closed_sl; pnl=")


def test_build_cumulative_close_update_payload_applies_win_metadata_overrides():
    open_row = {
        "symbol": "ETHUSDT",
        "side": "SHORT",
        "entry_price": 2500.0,
        "entry_reasons": ["mean_revert"],
        "confidence": 82.0,
        "rr_ratio": 2.1,
    }
    position = SimpleNamespace(symbol="ETHUSDT", side="SELL", entry_price=2500.0, entry_reasons=["mean_revert"])
    win_meta = {
        "playbook_match_score": 0.91,
        "effective_risk_pct": 2.4,
        "risk_overlay_pct": 0.8,
        "win_reason_tags": ["tag_a", "tag_b"],
        "win_reasoning": "manual override winner",
    }

    payload, cumulative_pnl, _ = build_cumulative_close_update_payload(
        open_row=open_row,
        position=position,
        close_price=2475.0,
        pnl=3.0,
        close_reason="closed_tp",
        win_metadata=win_meta,
        playbook_snapshot=None,
    )
    assert cumulative_pnl == pytest.approx(3.0)
    assert payload["playbook_match_score"] == pytest.approx(0.91)
    assert payload["effective_risk_pct"] == pytest.approx(2.4)
    assert payload["risk_overlay_pct"] == pytest.approx(0.8)
    assert payload["win_reason_tags"] == ["tag_a", "tag_b"]
    assert payload["win_reasoning"] == "manual override winner"
