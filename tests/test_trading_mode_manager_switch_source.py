import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.trading_mode_manager import TradingMode, TradingModeManager  # type: ignore


@pytest.mark.asyncio
async def test_manual_switch_marks_manual_override(monkeypatch):
    user_id = 51001
    TradingModeManager.clear_manual_override(user_id)

    monkeypatch.setattr(TradingModeManager, "get_mode", lambda _uid: TradingMode.SWING)
    monkeypatch.setattr(TradingModeManager, "set_mode", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        TradingModeManager,
        "_restart_engine_with_mode",
        AsyncMock(return_value=None),
    )

    fake_engine_mod = SimpleNamespace(
        stop_engine_async=AsyncMock(return_value=None),
        get_scalping_engine=lambda _uid: None,
    )
    monkeypatch.setitem(sys.modules, "app.autotrade_engine", fake_engine_mod)

    result = await TradingModeManager.switch_mode(
        user_id=user_id,
        new_mode=TradingMode.SCALPING,
        bot=Mock(),
        context=None,
        switch_source="manual",
    )

    assert result["success"] is True
    assert TradingModeManager.is_manual_override_active(user_id) is True


@pytest.mark.asyncio
async def test_auto_switch_does_not_mark_manual_override(monkeypatch):
    user_id = 51002
    TradingModeManager.clear_manual_override(user_id)

    monkeypatch.setattr(TradingModeManager, "get_mode", lambda _uid: TradingMode.SWING)
    monkeypatch.setattr(TradingModeManager, "set_mode", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        TradingModeManager,
        "_restart_engine_with_mode",
        AsyncMock(return_value=None),
    )

    fake_engine_mod = SimpleNamespace(
        stop_engine_async=AsyncMock(return_value=None),
        get_scalping_engine=lambda _uid: None,
    )
    monkeypatch.setitem(sys.modules, "app.autotrade_engine", fake_engine_mod)

    result = await TradingModeManager.switch_mode(
        user_id=user_id,
        new_mode=TradingMode.SCALPING,
        bot=Mock(),
        context=None,
        switch_source="auto",
    )

    assert result["success"] is True
    assert TradingModeManager.is_manual_override_active(user_id) is False
