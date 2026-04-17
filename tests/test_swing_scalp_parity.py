import importlib
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.auto_mode_switcher import AutoModeSwitcher  # type: ignore
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

    monkeypatch.setattr(TradingModeManager, "get_mode", lambda _uid: TradingMode.SWING)
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
