import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.auto_mode_switcher as auto_mode_switcher  # type: ignore
from app.auto_mode_switcher import AutoModeSwitcher  # type: ignore
from app.trading_mode_manager import TradingMode, TradingModeManager  # type: ignore


@pytest.mark.asyncio
async def test_check_and_switch_skips_when_confidence_below_threshold(monkeypatch):
    switcher = AutoModeSwitcher(bot=Mock())
    switcher.min_confidence = 80

    monkeypatch.setattr(
        auto_mode_switcher,
        "detect_market_condition",
        lambda _symbol: {
            "condition": "SIDEWAYS",
            "confidence": 60,
            "recommended_mode": "scalping",
            "reason": "weak sideways",
        },
    )
    monkeypatch.setattr(switcher, "_get_auto_mode_users", lambda: [1001, 1002])
    switch_user_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(switcher, "_switch_user_mode", switch_user_mock)

    await switcher._check_and_switch()
    switch_user_mock.assert_not_called()


@pytest.mark.asyncio
async def test_hysteresis_requires_repeated_recommendation(monkeypatch):
    switcher = AutoModeSwitcher(bot=Mock())
    switcher.required_confirmations = 2
    switcher.switch_cooldown_seconds = 0

    monkeypatch.setattr(TradingModeManager, "get_mode", lambda _uid: TradingMode.SWING)
    monkeypatch.setattr(TradingModeManager, "is_manual_override_active", lambda _uid: False)
    switch_mode_mock = AsyncMock(return_value={"success": True, "message": "ok"})
    monkeypatch.setattr(TradingModeManager, "switch_mode", switch_mode_mock)
    monkeypatch.setattr(switcher, "_notify_user", AsyncMock(return_value=None))

    switched_first = await switcher._switch_user_mode(
        user_id=2001,
        recommended_mode="scalping",
        market_result={"condition": "SIDEWAYS", "confidence": 82, "reason": "range"},
    )
    switched_second = await switcher._switch_user_mode(
        user_id=2001,
        recommended_mode="scalping",
        market_result={"condition": "SIDEWAYS", "confidence": 83, "reason": "range"},
    )

    assert switched_first is False
    assert switched_second is True
    switch_mode_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_cooldown_blocks_repeated_auto_switches(monkeypatch):
    switcher = AutoModeSwitcher(bot=Mock())
    switcher.required_confirmations = 1
    switcher.switch_cooldown_seconds = 3600

    monkeypatch.setattr(TradingModeManager, "get_mode", lambda _uid: TradingMode.SWING)
    monkeypatch.setattr(TradingModeManager, "is_manual_override_active", lambda _uid: False)
    switch_mode_mock = AsyncMock(return_value={"success": True, "message": "ok"})
    monkeypatch.setattr(TradingModeManager, "switch_mode", switch_mode_mock)
    monkeypatch.setattr(switcher, "_notify_user", AsyncMock(return_value=None))

    switched_first = await switcher._switch_user_mode(
        user_id=3001,
        recommended_mode="scalping",
        market_result={"condition": "SIDEWAYS", "confidence": 88, "reason": "range"},
    )
    switched_second = await switcher._switch_user_mode(
        user_id=3001,
        recommended_mode="scalping",
        market_result={"condition": "SIDEWAYS", "confidence": 89, "reason": "range"},
    )

    assert switched_first is True
    assert switched_second is False
    switch_mode_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_override_blocks_auto_switch(monkeypatch):
    switcher = AutoModeSwitcher(bot=Mock())
    switcher.required_confirmations = 1
    switcher.switch_cooldown_seconds = 0

    monkeypatch.setattr(TradingModeManager, "is_manual_override_active", lambda _uid: True)
    switch_mode_mock = AsyncMock(return_value={"success": True, "message": "ok"})
    monkeypatch.setattr(TradingModeManager, "switch_mode", switch_mode_mock)

    switched = await switcher._switch_user_mode(
        user_id=4001,
        recommended_mode="scalping",
        market_result={"condition": "SIDEWAYS", "confidence": 91, "reason": "range"},
    )

    assert switched is False
    switch_mode_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_mixed_mode_blocks_legacy_auto_switch(monkeypatch):
    switcher = AutoModeSwitcher(bot=Mock())
    switcher.required_confirmations = 1
    switcher.switch_cooldown_seconds = 0

    monkeypatch.setattr(TradingModeManager, "is_manual_override_active", lambda _uid: False)
    monkeypatch.setattr(TradingModeManager, "get_mode", lambda _uid: TradingMode.MIXED)
    switch_mode_mock = AsyncMock(return_value={"success": True, "message": "ok"})
    monkeypatch.setattr(TradingModeManager, "switch_mode", switch_mode_mock)

    switched = await switcher._switch_user_mode(
        user_id=4501,
        recommended_mode="swing",
        market_result={"condition": "TRENDING", "confidence": 91, "reason": "trend"},
    )

    assert switched is False
    switch_mode_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_background_check_no_users_no_switch(monkeypatch):
    switcher = AutoModeSwitcher(bot=Mock())

    monkeypatch.setattr(
        auto_mode_switcher,
        "detect_market_condition",
        lambda _symbol: {
            "condition": "TRENDING",
            "confidence": 90,
            "recommended_mode": "swing",
            "reason": "trend",
        },
    )
    monkeypatch.setattr(switcher, "_get_auto_mode_users", lambda: [])
    switch_user_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(switcher, "_switch_user_mode", switch_user_mock)

    await switcher._check_and_switch()
    switch_user_mock.assert_not_called()
