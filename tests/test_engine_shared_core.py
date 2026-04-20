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
import app.autotrade_engine as autotrade_engine  # type: ignore
import app.trade_history as trade_history  # type: ignore
from app.autotrade_engine import _scalping_engines, get_engine, get_scalping_engine  # type: ignore
from app.engine_execution_shared import build_cumulative_close_update_payload  # type: ignore
from app.providers.alternative_klines_provider import AlternativeKlinesProvider  # type: ignore


def test_get_scalping_engine_alias_delegates_runtime_instance(monkeypatch):
    uid = 91001
    sentinel = object()
    monkeypatch.setitem(_scalping_engines, uid, sentinel)
    assert get_engine(uid) is sentinel
    assert get_scalping_engine(uid) is sentinel


def test_is_running_mixed_requires_both_component_tasks(monkeypatch):
    uid = 91002

    class _FakeTask:
        def __init__(self, done_state: bool):
            self._done_state = bool(done_state)

        def done(self):
            return self._done_state

    monkeypatch.setitem(autotrade_engine._running_tasks, uid, _FakeTask(False))
    monkeypatch.setitem(
        autotrade_engine._mixed_component_tasks,
        uid,
        {"swing": _FakeTask(False), "scalp": _FakeTask(True)},
    )
    assert autotrade_engine.is_running(uid) is False

    monkeypatch.setitem(
        autotrade_engine._mixed_component_tasks,
        uid,
        {"swing": _FakeTask(False), "scalp": _FakeTask(False)},
    )
    assert autotrade_engine.is_running(uid) is True


def test_should_notify_blocked_pending_honors_ttl():
    cache = {}
    assert runtime_shared.should_notify_blocked_pending(cache, key="BTCUSDT", ttl_sec=600, now_ts=1000.0) is True
    assert runtime_shared.should_notify_blocked_pending(cache, key="BTCUSDT", ttl_sec=600, now_ts=1200.0) is False
    assert runtime_shared.should_notify_blocked_pending(cache, key="BTCUSDT", ttl_sec=600, now_ts=1601.0) is True


def test_normalize_pending_lock_context_exposes_diagnostics():
    ctx = runtime_shared.normalize_pending_lock_context(
        {
            "pending_order": True,
            "pending_owner": "swing",
            "pending_age_seconds": 45.25,
            "pending_ttl_seconds": 90.0,
            "has_position": False,
            "owner": "swing",
            "last_pending_clear_reason": "",
        }
    )
    assert ctx["pending_order"] is True
    assert ctx["pending_owner"] == "swing"
    assert ctx["pending_age_seconds"] == pytest.approx(45.25)
    assert ctx["pending_ttl_seconds"] == pytest.approx(90.0)
    assert ctx["has_position"] is False
    assert ctx["owner"] == "swing"
    assert ctx["stale_candidate"] is False


def test_normalize_pending_lock_context_marks_stale_candidate_without_position():
    ctx = runtime_shared.normalize_pending_lock_context(
        {
            "pending_order": True,
            "pending_owner": "scalp",
            "pending_age_seconds": 120.0,
            "pending_ttl_seconds": 90.0,
            "has_position": False,
            "owner": "scalp",
            "last_pending_clear_reason": "startup_sanitize",
        }
    )
    assert ctx["stale_candidate"] is True
    assert runtime_shared.pending_lock_age_label(ctx["pending_age_seconds"]) == "120.0s"
    assert runtime_shared.pending_lock_age_label(None) == "n/a"


def test_stale_cooldown_helpers_set_and_expire():
    cache = {}
    expiry = runtime_shared.set_ttl_cooldown(cache, key="ETHUSDT", ttl_sec=120, now_ts=1000.0)
    assert expiry == pytest.approx(1120.0)
    assert runtime_shared.is_ttl_cooldown_active(cache, key="ETHUSDT", now_ts=1119.9) is True
    assert runtime_shared.is_ttl_cooldown_active(cache, key="ETHUSDT", now_ts=1120.0) is False
    assert "ETHUSDT" not in cache


def test_swing_queue_age_gate_does_not_drop_inflight_symbol():
    uid = 77701
    autotrade_engine._signal_queues[uid] = [{"symbol": "ETHUSDT", "_queued_at_ts": 10.0}]
    autotrade_engine._signals_being_processed[uid] = {"ETHUSDT"}
    try:
        expired = autotrade_engine._drop_expired_signal_queue_entries(
            uid,
            max_age_sec=90.0,
            now_ts=1000.0,
        )
        assert expired == []
        assert [s["symbol"] for s in autotrade_engine._signal_queues[uid]] == ["ETHUSDT"]
    finally:
        autotrade_engine._signal_queues.pop(uid, None)
        autotrade_engine._signals_being_processed.pop(uid, None)


def test_swing_signal_mark_proxy_uses_cache_within_ttl():
    symbol = "ETHUSDT"
    autotrade_engine._SIGNAL_MARK_PROXY_CACHE[symbol] = (2450.5, 100.0)
    try:
        px = autotrade_engine._resolve_signal_mark_price(symbol, now_ts=104.0)
        assert px == pytest.approx(2450.5)
    finally:
        autotrade_engine._SIGNAL_MARK_PROXY_CACHE.pop(symbol, None)


def test_klines_freshness_gate_accepts_recent_candle():
    provider = AlternativeKlinesProvider()
    now_ts = 1_700_000_000.0
    recent_ts_ms = int((now_ts - 45.0) * 1000.0)
    klines = [[recent_ts_ms, "1", "2", "1", "1.5", "100", recent_ts_ms + 60000, "0", 0, "0", "0", "0"]]
    assert provider._is_klines_fresh(klines, interval="1m", now_ts=now_ts) is True


def test_klines_freshness_gate_rejects_stale_candle():
    provider = AlternativeKlinesProvider()
    now_ts = 1_700_000_000.0
    stale_ts_ms = int((now_ts - 500.0) * 1000.0)
    klines = [[stale_ts_ms, "1", "2", "1", "1.5", "100", stale_ts_ms + 60000, "0", 0, "0", "0", "0"]]
    assert provider._is_klines_fresh(klines, interval="1m", now_ts=now_ts) is False


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


def test_build_cumulative_close_update_payload_enforces_win_tags_when_manual_reasoning_provided():
    open_row = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 100.0,
        "entry_reasons": ["volume_confirmation"],
        "confidence": 80.0,
        "rr_ratio": 2.0,
    }
    position = SimpleNamespace(symbol="BTCUSDT", side="BUY", entry_price=100.0, entry_reasons=["volume_confirmation"])
    win_meta = {
        "win_reasoning": "manual winner context",
        # Intentionally omit win_reason_tags to verify fallback enforcement.
    }

    payload, _, _ = build_cumulative_close_update_payload(
        open_row=open_row,
        position=position,
        close_price=102.0,
        pnl=2.0,
        close_reason="closed_tp",
        win_metadata=win_meta,
        playbook_snapshot=None,
    )
    assert payload["win_reasoning"] == "manual winner context"
    assert payload.get("win_reason_tags"), "Winning close paths must keep non-empty win_reason_tags"


def test_build_cumulative_close_update_payload_enforces_win_reasoning_for_closed_tp_even_if_net_negative():
    open_row = {
        "symbol": "BTCUSDT",
        "side": "LONG",
        "entry_price": 100.0,
        "entry_reasons": ["tp_breakout", "trend_align"],
        "confidence": 78.0,
        "rr_ratio": 1.5,
    }
    position = SimpleNamespace(symbol="BTCUSDT", side="BUY", entry_price=100.0, entry_reasons=["tp_breakout"])

    payload, cumulative_pnl, _ = build_cumulative_close_update_payload(
        open_row=open_row,
        position=position,
        close_price=99.95,
        pnl=-0.05,
        close_reason="closed_tp",
    )
    assert cumulative_pnl == pytest.approx(-0.05)
    assert payload["close_reason"] == "closed_tp"
    assert payload.get("win_reasoning"), "closed_tp close paths must persist win_reasoning"
    assert payload.get("win_reason_tags"), "closed_tp close paths must persist non-empty win_reason_tags"
    assert "loss_reasoning" not in payload


def test_build_cumulative_close_update_payload_preserves_qty_fields_for_audit_integrity():
    open_row = {
        "symbol": "SOLUSDT",
        "side": "LONG",
        "entry_price": 150.0,
        "entry_reasons": ["trend_align"],
        "confidence": 72.0,
        "rr_ratio": 2.0,
        "qty": 0.42,
        "quantity": 0.42,
        "original_quantity": 0.42,
    }
    position = SimpleNamespace(symbol="SOLUSDT", side="BUY", entry_price=150.0, entry_reasons=["trend_align"])

    payload, cumulative_pnl, _ = build_cumulative_close_update_payload(
        open_row=open_row,
        position=position,
        close_price=149.0,
        pnl=-1.0,
        close_reason="closed_sl",
    )

    assert cumulative_pnl == pytest.approx(-1.0)
    assert "qty" not in payload
    assert "quantity" not in payload
    assert payload["remaining_quantity"] == pytest.approx(0.0)


def test_save_trade_open_derives_rr_from_executed_levels(monkeypatch):
    captured = {}

    class _FakeInsert:
        def __init__(self, row):
            self._row = row

        def execute(self):
            captured["row"] = self._row
            return SimpleNamespace(data=[{"id": 999}])

    class _FakeTable:
        def insert(self, row):
            return _FakeInsert(row)

    class _FakeDB:
        def table(self, name):
            assert name == "autotrade_trades"
            return _FakeTable()

    monkeypatch.setattr(trade_history, "_db", lambda: _FakeDB())

    trade_id = trade_history.save_trade_open(
        telegram_id=1,
        symbol="ETHUSDT",
        side="LONG",
        entry_price=100.0,
        qty=1.0,
        leverage=10,
        tp_price=120.0,
        sl_price=90.0,
        signal={"rr_ratio": 2.0, "confidence": 75, "reasons": []},
        tp1_price=130.0,
        strategy="stackmentor",
    )

    assert trade_id == 999
    assert captured["row"]["rr_ratio"] == pytest.approx(3.0)
