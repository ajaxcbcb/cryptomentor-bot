import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.auto_mode_switcher import AutoModeSwitcher  # type: ignore
import app.autotrade_engine as autotrade_engine  # type: ignore
from app.scalping_engine import ScalpingEngine  # type: ignore
from app.trade_execution import open_managed_position  # type: ignore
from app.trading_mode_manager import TradingMode, TradingModeManager  # type: ignore


class _InvalidPriceClient:
    def __init__(self):
        self.order_calls = 0
        self.leverage_calls = 0

    def get_ticker(self, symbol: str):
        return {"success": True, "mark_price": 100.0}

    def set_leverage(self, symbol: str, leverage: int):
        self.leverage_calls += 1
        return {"success": True}

    def place_order_with_tpsl(self, symbol, side, quantity, tp_price, sl_price):
        self.order_calls += 1
        return {"success": True, "order_id": "should-not-happen"}


@pytest.mark.asyncio
async def test_open_managed_position_rejects_invalid_sl_without_order():
    client = _InvalidPriceClient()
    result = await open_managed_position(
        client=client,
        user_id=101,
        symbol="BTCUSDT",
        side="LONG",
        entry_price=100.0,
        sl_price=101.0,  # invalid for LONG vs mark=100
        tp_price=110.0,
        quantity=0.01,
        leverage=10,
        register_in_stackmentor=False,
        reconcile=False,
    )
    assert result.success is False
    assert result.error_code == "invalid_prices"
    assert client.order_calls == 0
    assert client.leverage_calls == 0


class _UnsupportedSymbolClient:
    def __init__(self):
        self.order_calls = 0

    def get_ticker(self, symbol: str):
        return {"success": True, "mark_price": 100.0}

    def set_leverage(self, symbol: str, leverage: int):
        return {"success": True}

    def place_order_with_tpsl(self, symbol, side, quantity, tp_price, sl_price):
        self.order_calls += 1
        return {
            "success": False,
            "error": "API error 710002: This trading pair does not currently support trading via OpenAPI.",
        }


@pytest.mark.asyncio
async def test_open_managed_position_classifies_unsupported_symbol_api_error():
    client = _UnsupportedSymbolClient()
    result = await open_managed_position(
        client=client,
        user_id=102,
        symbol="RAVEUSDT",
        side="LONG",
        entry_price=100.0,
        sl_price=95.0,
        tp_price=110.0,
        quantity=0.01,
        leverage=10,
        register_in_stackmentor=False,
        reconcile=False,
    )
    assert result.success is False
    assert result.error_code == "unsupported_symbol_api"
    assert client.order_calls == 1


class _SizingClient:
    def get_account_info(self):
        return {
            "success": True,
            "available": 1000.0,
            "frozen": 0.0,
            "total_unrealized_pnl": 0.0,
        }


def test_scalping_position_size_uses_requested_symbol(monkeypatch):
    import app.position_sizing as position_sizing  # type: ignore
    import app.supabase_repo as supabase_repo  # type: ignore

    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine.user_id = 999
    engine.client = _SizingClient()

    monkeypatch.setattr(supabase_repo, "get_risk_per_trade", lambda _uid: 1.0)

    captured = {}

    def _fake_calculate_position_size(*, balance, risk_pct, entry_price, sl_price, leverage, symbol):
        captured["symbol"] = symbol
        return {
            "valid": True,
            "qty": 0.1,
            "sl_distance_pct": 4.0,
            "position_size_usdt": 250.0,
            "margin_required": 25.0,
            "risk_amount": 10.0,
        }

    monkeypatch.setattr(position_sizing, "calculate_position_size", _fake_calculate_position_size)

    qty, used_risk = engine.calculate_position_size_pro(
        symbol="ETHUSDT",
        entry_price=2500.0,
        sl_price=2400.0,
        capital=1000.0,
        leverage=10,
    )
    assert used_risk is True
    assert qty > 0
    assert captured["symbol"] == "ETHUSDT"


def test_scalping_stale_cooldown_not_overridden_by_generic_failure():
    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine.cooldown_tracker = {}
    engine._stale_price_cooldown_ts = {}

    expiry = engine._mark_stale_price_cooldown("ETHUSDT", ttl_sec=120.0, now_ts=1000.0)
    assert expiry == pytest.approx(1120.0)
    assert engine.cooldown_tracker["ETHUSDT"] == pytest.approx(1120.0)

    applied = engine._apply_generic_failure_cooldown("ETHUSDT", ttl_sec=300.0, now_ts=1010.0)
    assert applied is False
    assert engine.cooldown_tracker["ETHUSDT"] == pytest.approx(1120.0)


def test_scalping_v2_rejection_cooldown_uses_symbol_side_setup_signature():
    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine._v2_rejection_cooldown_ts = {}
    engine._v2_rejection_reason_by_signature = {}

    signal = {"symbol": "XAGUSDT", "side": "SHORT", "trade_subtype": "trend_scalp"}
    expiry = engine._mark_v2_rejection_cooldown(
        signal,
        "tradeability_below_threshold",
        ttl_sec=180.0,
        now_ts=1000.0,
    )
    assert expiry == pytest.approx(1180.0)

    active, reason, remaining = engine._get_v2_rejection_cooldown_state(signal, now_ts=1010.0)
    assert active is True
    assert reason == "tradeability_below_threshold"
    assert remaining == 170

    other_setup_signal = {"symbol": "XAGUSDT", "side": "SHORT", "trade_subtype": "breakout_scalp"}
    active_other, reason_other, remaining_other = engine._get_v2_rejection_cooldown_state(other_setup_signal, now_ts=1010.0)
    assert active_other is False
    assert reason_other == ""
    assert remaining_other == 0


def test_scalping_v2_rejection_cooldown_clears_after_expiry():
    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine._v2_rejection_cooldown_ts = {}
    engine._v2_rejection_reason_by_signature = {}

    signal = {"symbol": "XAGUSDT", "side": "SHORT", "trade_subtype": "trend_scalp"}
    engine._mark_v2_rejection_cooldown(
        signal,
        "tradeability_below_threshold",
        ttl_sec=60.0,
        now_ts=1000.0,
    )

    active, reason, remaining = engine._get_v2_rejection_cooldown_state(signal, now_ts=1061.0)
    assert active is False
    assert reason == ""
    assert remaining == 0
    assert engine._v2_rejection_reason_by_signature == {}


def test_swing_queue_upsert_refreshes_symbol_and_respects_inflight():
    uid = 4242
    autotrade_engine._signal_queues[uid] = []
    autotrade_engine._signals_being_processed[uid] = set()
    first = {"symbol": "ETHUSDT", "side": "SHORT", "entry_price": 2500.0, "tp1": 2450.0, "tp2": 2400.0, "tp3": 2350.0, "sl": 2550.0, "confidence": 72, "rr_ratio": 2.0}
    second = {"symbol": "ETHUSDT", "side": "SHORT", "entry_price": 2490.0, "tp1": 2440.0, "tp2": 2390.0, "tp3": 2340.0, "sl": 2540.0, "confidence": 78, "rr_ratio": 2.2}
    third = {"symbol": "ETHUSDT", "side": "SHORT", "entry_price": 2480.0, "tp1": 2430.0, "tp2": 2380.0, "tp3": 2330.0, "sl": 2530.0, "confidence": 80, "rr_ratio": 2.3}
    try:
        action1 = autotrade_engine._upsert_signal_queue_entry(uid, first, now_ts=1000.0)
        assert action1 == "inserted"
        action2 = autotrade_engine._upsert_signal_queue_entry(uid, second, now_ts=1010.0)
        assert action2 == "updated"
        assert len(autotrade_engine._signal_queues[uid]) == 1
        queued = autotrade_engine._signal_queues[uid][0]
        assert queued["entry_price"] == pytest.approx(2490.0)
        assert queued["_queued_at_ts"] == pytest.approx(1010.0)

        autotrade_engine._signals_being_processed[uid].add("ETHUSDT")
        action3 = autotrade_engine._upsert_signal_queue_entry(uid, third, now_ts=1020.0)
        assert action3 == "skipped_inflight"
        assert autotrade_engine._signal_queues[uid][0]["entry_price"] == pytest.approx(2490.0)
    finally:
        autotrade_engine._signal_queues.pop(uid, None)
        autotrade_engine._signals_being_processed.pop(uid, None)


def test_swing_queue_age_gate_drops_expired_entries():
    uid = 4243
    autotrade_engine._signal_queues[uid] = [
        {"symbol": "BTCUSDT", "_queued_at_ts": 100.0},
        {"symbol": "ETHUSDT", "_queued_at_ts": 130.5},
    ]
    autotrade_engine._signals_being_processed[uid] = set()
    try:
        expired = autotrade_engine._drop_expired_signal_queue_entries(
            uid,
            max_age_sec=90.0,
            now_ts=220.0,
        )
        assert expired == ["BTCUSDT"]
        assert [s["symbol"] for s in autotrade_engine._signal_queues[uid]] == ["ETHUSDT"]
    finally:
        autotrade_engine._signal_queues.pop(uid, None)
        autotrade_engine._signals_being_processed.pop(uid, None)


def test_swing_queue_remaining_symbols_excludes_active_index_and_symbol():
    queue = [
        {"symbol": "SOLUSDT"},
        {"symbol": "ETHUSDT"},
        {"symbol": "XRPUSDT"},
        {"symbol": "ETHUSDT"},
    ]
    remaining = autotrade_engine._build_queued_remaining_symbols(
        queue,
        active_idx=1,
        active_symbol="ETHUSDT",
    )
    assert remaining == ["SOLUSDT", "XRPUSDT"]


def test_swing_loop_error_cleanup_clears_inflight_marker(monkeypatch):
    uid = 4244
    autotrade_engine._signals_being_processed[uid] = {"ETHUSDT"}
    calls = []

    def _fake_cleanup(user_id, symbol, success=True):
        calls.append((user_id, symbol, success))
        autotrade_engine._signals_being_processed[user_id].discard(symbol)

    monkeypatch.setattr(autotrade_engine, "_cleanup_signal_queue", _fake_cleanup)
    cleaned = autotrade_engine._cleanup_inflight_signal_marker(uid, "ETHUSDT")
    assert cleaned is True
    assert calls == [(uid, "ETHUSDT", False)]
    assert "ETHUSDT" not in autotrade_engine._signals_being_processed[uid]
    autotrade_engine._signals_being_processed.pop(uid, None)


def test_swing_preflight_live_mark_rejects_stale_short_levels(monkeypatch):
    cooldown_calls = []

    monkeypatch.setattr(autotrade_engine, "_resolve_signal_mark_price", lambda _symbol, now_ts=None: 2451.0)
    monkeypatch.setattr(
        autotrade_engine,
        "_mark_stale_price_cooldown",
        lambda user_id, symbol, ttl_sec=120.0: cooldown_calls.append((user_id, symbol, ttl_sec)) or 1120.0,
    )
    ok = autotrade_engine._signal_prices_pass_live_mark(
        symbol="ETHUSDT",
        side="SHORT",
        entry_price=2513.9210,
        tp1_price=2479.448857,
        sl_price=2525.4117,
        stale_cooldown_user_id=4242,
    )
    assert ok is False
    assert len(cooldown_calls) == 1
    assert cooldown_calls[0][0] == 4242
    assert cooldown_calls[0][1] == "ETHUSDT"
    assert cooldown_calls[0][2] == pytest.approx(120.0)


def test_swing_preflight_live_mark_accepts_valid_short_levels(monkeypatch):
    monkeypatch.setattr(autotrade_engine, "_resolve_signal_mark_price", lambda _symbol, now_ts=None: 2500.0)
    ok = autotrade_engine._signal_prices_pass_live_mark(
        symbol="ETHUSDT",
        side="SHORT",
        entry_price=2513.9210,
        tp1_price=2479.448857,
        sl_price=2525.4117,
    )
    assert ok is True


def test_swing_preflight_live_mark_allows_when_mark_unavailable(monkeypatch):
    monkeypatch.setattr(autotrade_engine, "_resolve_signal_mark_price", lambda _symbol, now_ts=None: None)
    ok = autotrade_engine._signal_prices_pass_live_mark(
        symbol="ETHUSDT",
        side="SHORT",
        entry_price=2513.9210,
        tp1_price=2479.448857,
        sl_price=2525.4117,
    )
    assert ok is True


def test_swing_queue_pre_exec_stale_guard_present():
    source = Path(_ROOT, "Bismillah", "app", "autotrade_engine.py").read_text(encoding="utf-8")
    assert "Queue pre-exec stale reject" in source
    assert "selected_idx=" in source
    assert "queue_age=" in source


def test_swing_final_pre_open_stale_guard_present():
    source = Path(_ROOT, "Bismillah", "app", "autotrade_engine.py").read_text(encoding="utf-8")
    assert "Final pre-open stale reject" in source


def test_swing_queue_status_mentions_volume_priority():
    source = Path(_ROOT, "Bismillah", "app", "autotrade_engine.py").read_text(encoding="utf-8")
    assert "Higher volume priority signals execute first (confidence breaks ties)" in source
    assert "Higher confidence signals execute first" not in source


def test_swing_pending_signal_sync_falls_back_tp3_when_missing(monkeypatch):
    import app.supabase_repo as supabase_repo  # type: ignore

    captured = {}

    class _FakeTable:
        def __init__(self):
            self._op = None
            self._payload = None

        def select(self, *_args, **_kwargs):
            self._op = "select"
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def update(self, payload):
            self._op = "update"
            self._payload = payload
            return self

        def insert(self, payload):
            self._op = "insert"
            self._payload = payload
            return self

        def execute(self):
            if self._op == "select":
                return SimpleNamespace(data=[])
            if self._op in {"insert", "update"}:
                captured[self._op] = self._payload
                return SimpleNamespace(data=[{"id": 1}])
            return SimpleNamespace(data=[])

    class _FakeClient:
        def table(self, _name):
            return _FakeTable()

    monkeypatch.setattr(supabase_repo, "_client", lambda: _FakeClient())
    autotrade_engine._sync_pending_signal_queue_row(
        321,
        {
            "symbol": "ETHUSDT",
            "side": "SHORT",
            "confidence": 70,
            "entry_price": 2500.0,
            "tp1": 2470.0,
            "tp2": 2450.0,
            "tp3": None,
            "sl": 2520.0,
            "reason": "test",
        },
    )

    assert "insert" in captured
    assert captured["insert"]["tp3"] == pytest.approx(2450.0)


def test_swing_timeout_alias_env_compat(monkeypatch):
    import app.trading_mode as trading_mode  # type: ignore

    monkeypatch.delenv("SWING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED", raising=False)
    monkeypatch.setenv("SWING_TIMEOUT_PROTECTION_ENABLED", "true")
    trading_mode = importlib.reload(trading_mode)
    cfg = trading_mode.SwingAdaptiveConfig()
    assert cfg.adaptive_timeout_protection_enabled is True

    monkeypatch.setenv("SWING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED", "false")
    monkeypatch.setenv("SWING_TIMEOUT_PROTECTION_ENABLED", "true")
    trading_mode = importlib.reload(trading_mode)
    cfg = trading_mode.SwingAdaptiveConfig()
    assert cfg.adaptive_timeout_protection_enabled is False


@pytest.mark.asyncio
async def test_auto_mode_switcher_uses_full_switch_mode(monkeypatch):
    switcher = AutoModeSwitcher(bot=Mock())
    switcher.required_confirmations = 1
    switcher.switch_cooldown_seconds = 0

    monkeypatch.setattr(TradingModeManager, "get_mode", lambda _uid: TradingMode.SWING)
    monkeypatch.setattr(TradingModeManager, "is_manual_override_active", lambda _uid: False)
    monkeypatch.setattr(
        TradingModeManager,
        "set_mode",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("set_mode should not be called directly")),
    )
    switch_mode_mock = AsyncMock(return_value={"success": True, "message": "ok"})
    monkeypatch.setattr(TradingModeManager, "switch_mode", switch_mode_mock)
    monkeypatch.setattr(switcher, "_notify_user", AsyncMock(return_value=None))

    switched = await switcher._switch_user_mode(
        user_id=12345,
        recommended_mode="scalping",
        market_result={"condition": "SIDEWAYS", "confidence": 80, "reason": "range"},
    )
    assert switched is True
    switch_mode_mock.assert_awaited_once()


def test_swing_engine_no_direct_place_order_with_tpsl_calls():
    source = Path(_ROOT, "Bismillah", "app", "autotrade_engine.py").read_text(encoding="utf-8")
    assert "client.place_order_with_tpsl" not in source
    assert "open_managed_position(" in source
