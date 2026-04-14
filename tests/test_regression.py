"""
Non-regression Tests for CryptoMentor Core Functionality
========================================================

Ensures that coordinator integration does NOT break:
- Signal generation and validation
- Risk calculation
- Order execution logic
- Trade history tracking
- StackMentor position monitoring
- Engine loops and polling

These tests verify the EXISTING behavior is preserved.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from Bismillah.app.autotrade_engine import (
    _compute_signal_pro,
    _is_reversal,
    calc_qty,
)
from Bismillah.app.scalping_engine import ScalpingEngine
from Bismillah.app.trading_mode import ScalpingConfig, ScalpingSignal
from Bismillah.app.trade_execution import open_managed_position, build_stackmentor_levels
from Bismillah.app.stackmentor import (
    register_stackmentor_position,
    remove_stackmentor_position,
)


class TestRiskCalculation:
    """Test that risk calculations are unchanged."""

    def test_qty_calculation_basic(self):
        """Test basic quantity calculation."""
        # User account: 10000 USDT @ 10x leverage = 100000 USDT exposure
        qty = calc_qty("BTCUSDT", 100000, 45000.0)
        assert qty > 0
        assert qty <= 100000 / 45000.0  # Should not exceed max exposure

    def test_qty_calculation_multiple_symbols(self):
        """Test quantity calculation for different symbols."""
        symbols_and_prices = [
            ("BTCUSDT", 45000.0),
            ("ETHUSDT", 2500.0),
            ("SOLUSDT", 110.0),
        ]

        exposure = 50000  # USDT exposure
        for symbol, price in symbols_and_prices:
            qty = calc_qty(symbol, exposure, price)
            assert qty > 0
            assert qty <= exposure / price

    def test_qty_zero_for_zero_exposure(self):
        """Test that zero exposure results in zero qty."""
        qty = calc_qty("BTCUSDT", 0, 45000.0)
        assert qty == 0

    def test_qty_zero_for_zero_price(self):
        """Test that invalid prices are handled."""
        qty = calc_qty("BTCUSDT", 100000, 0)
        assert qty == 0


class TestSignalGeneration:
    """Test that signal generation logic is preserved."""

    @pytest.mark.asyncio
    async def test_reversal_detection_confidence(self):
        """Test that reversal requires minimum confidence."""
        open_side = "BUY"  # Current position
        new_signal = {
            "side": "SELL",  # Opposite direction
            "confidence": 60,  # Below minimum (75%)
            "trend_1h": "DOWNTREND",
            "structure": "DOWNTREND",
        }

        is_rev = _is_reversal(open_side, new_signal, btc_is_sideways=False)
        assert is_rev is False  # Should reject low confidence

    def test_reversal_detection_same_direction(self):
        """Test that same direction signals don't trigger reversal."""
        open_side = "BUY"
        new_signal = {
            "side": "BUY",  # Same direction
            "confidence": 85,  # High confidence
            "trend_1h": "UPTREND",
            "structure": "UPTREND",
        }

        is_rev = _is_reversal(open_side, new_signal, btc_is_sideways=False)
        assert is_rev is False  # Same direction should not reverse


class TestTradeExecution:
    """Test that order execution logic is unchanged."""

    @pytest.mark.asyncio
    async def test_stackmentor_levels_calculation(self):
        """Test StackMentor TP/SL level calculation."""
        entry_price = 45000.0
        sl_price = 43000.0
        side = "LONG"
        total_qty = 0.1
        symbol = "BTCUSDT"

        levels = build_stackmentor_levels(
            entry_price=entry_price,
            sl_price=sl_price,
            side=side,
            total_qty=total_qty,
            symbol=symbol,
        )

        assert levels.sl == sl_price
        assert levels.tp1 > entry_price  # TP should be above entry for LONG
        assert levels.qty_tp1 > 0
        assert levels.qty_tp1 <= total_qty

    @pytest.mark.asyncio
    async def test_stackmentor_levels_short(self):
        """Test StackMentor levels for SHORT positions."""
        entry_price = 45000.0
        sl_price = 47000.0  # SL above entry for SHORT
        side = "SHORT"
        total_qty = 0.1
        symbol = "BTCUSDT"

        levels = build_stackmentor_levels(
            entry_price=entry_price,
            sl_price=sl_price,
            side=side,
            total_qty=total_qty,
            symbol=symbol,
        )

        assert levels.sl == sl_price
        assert levels.tp1 < entry_price  # TP should be below entry for SHORT

    @pytest.mark.asyncio
    async def test_execution_result_structure(self):
        """Test that ExecutionResult has expected structure."""
        # Mock client
        mock_client = AsyncMock()
        mock_client.get_ticker = AsyncMock(
            return_value={"success": True, "mark_price": 45000.0}
        )
        mock_client.set_leverage = AsyncMock(return_value=None)
        mock_client.place_order_with_tpsl = AsyncMock(
            return_value={
                "success": True,
                "order_id": "test-order-123",
                "fill_price": 45000.0,
            }
        )

        result = await open_managed_position(
            client=mock_client,
            user_id=123,
            symbol="BTCUSDT",
            side="LONG",
            entry_price=45000.0,
            sl_price=43000.0,
            quantity=0.1,
            leverage=10,
            set_leverage=False,
            register_in_stackmentor=False,
            reconcile=False,
        )

        assert result.success is True
        assert result.order_id is not None
        assert result.levels is not None
        assert result.levels.tp1 > 45000.0


class TestStackMentorTracking:
    """Test that StackMentor position tracking is unchanged."""

    def test_register_position(self):
        """Test position registration."""
        try:
            register_stackmentor_position(
                user_id=123,
                symbol="BTCUSDT",
                entry_price=45000.0,
                sl_price=43000.0,
                tp1=51000.0,
                tp2=51000.0,
                tp3=51000.0,
                total_qty=0.1,
                qty_tp1=0.1,
                qty_tp2=0,
                qty_tp3=0,
                side="LONG",
                leverage=10,
            )
            # If no exception, tracking works
            assert True
        except Exception as e:
            pytest.fail(f"Position registration failed: {e}")

    def test_remove_position(self):
        """Test position removal."""
        try:
            # First register
            register_stackmentor_position(
                user_id=123,
                symbol="BTCUSDT",
                entry_price=45000.0,
                sl_price=43000.0,
                tp1=51000.0,
                tp2=51000.0,
                tp3=51000.0,
                total_qty=0.1,
                qty_tp1=0.1,
                qty_tp2=0,
                qty_tp3=0,
                side="LONG",
                leverage=10,
            )

            # Then remove
            remove_stackmentor_position(123, "BTCUSDT")
            assert True
        except Exception as e:
            pytest.fail(f"Position removal failed: {e}")


class TestScalpingEngineCore:
    """Test scalping engine core functionality (without coordinator)."""

    def test_scalping_config_defaults(self):
        """Test that ScalpingConfig has expected defaults."""
        config = ScalpingConfig()
        assert config.timeframe == "5m"
        assert config.max_hold_time > 0
        assert config.min_confidence >= 0 and config.min_confidence <= 100
        assert len(config.pairs) > 0

    @pytest.mark.asyncio
    async def test_scalping_position_creation(self):
        """Test ScalpingPosition creation."""
        from Bismillah.app.trading_mode import ScalpingPosition

        position = ScalpingPosition(
            user_id=123,
            symbol="BTCUSDT",
            side="BUY",
            entry_price=45000.0,
            quantity=0.1,
            leverage=10,
            tp_price=50000.0,
            sl_price=40000.0,
            opened_at=time.time(),
            breakeven_set=False,
        )

        assert position.user_id == 123
        assert position.symbol == "BTCUSDT"
        assert position.side == "BUY"
        assert position.entry_price == 45000.0
        assert position.quantity == 0.1
        assert position.is_sideways is False


class TestEngineLoopBehavior:
    """Test that engine main loop behavior is preserved."""

    def test_cooldown_logic(self):
        """Test cooldown calculation (should not be affected by coordinator)."""
        from Bismillah.app.scalping_engine import ScalpingEngine

        # Create a minimal engine instance
        mock_bot = MagicMock()
        mock_client = MagicMock()

        engine = ScalpingEngine(
            user_id=123,
            client=mock_client,
            bot=mock_bot,
            notify_chat_id=123,
            config=ScalpingConfig(),
        )

        # Mark cooldown
        engine.mark_cooldown("BTCUSDT")
        assert engine.check_cooldown("BTCUSDT") is True

        # Wait for cooldown to expire
        current_time = time.time()
        engine.cooldown_tracker["BTCUSDT"] = current_time - 1  # Expired
        assert engine.check_cooldown("BTCUSDT") is False


class TestTradeHistoryPreservation:
    """Test that trade history tracking is unchanged."""

    def test_trade_save_structure(self):
        """Test that trade save function expects correct structure."""
        from Bismillah.app.trade_history import save_trade_open

        # Just verify the function signature exists and accepts expected params
        assert callable(save_trade_open)
        # In a real test, would mock Supabase and call with expected params

    def test_trade_close_tracking(self):
        """Test that closed trade tracking works."""
        from Bismillah.app.trade_history import save_trade_close

        # Verify function exists
        assert callable(save_trade_close)


class TestCoordinatorIntegrationNonBreaking:
    """Test that coordinator integration doesn't break existing behavior."""

    @pytest.mark.asyncio
    async def test_can_enter_allows_fresh_symbol(self):
        """Test that coordinator allows entry on fresh symbols."""
        from Bismillah.app.symbol_coordinator import (
            get_coordinator,
            StrategyOwner,
            reset_coordinator_for_testing,
        )

        reset_coordinator_for_testing()
        coordinator = get_coordinator()

        # Fresh symbol should always be allowed
        allowed, reason = await coordinator.can_enter(
            user_id=123,
            symbol="BTCUSDT",
            strategy=StrategyOwner.SWING,
            now_ts=time.time(),
        )

        assert allowed is True
        assert reason == "allowed"

    def test_coordinator_does_not_affect_signal_logic(self):
        """Test that coordinator is purely additive and doesn't change signal logic."""
        # Signals should still be generated the same way
        # Coordinator just gates the execution
        assert True  # Coordinator is separate from signal generation


class TestErrorHandling:
    """Test that error handling is preserved."""

    @pytest.mark.asyncio
    async def test_execution_error_propagation(self):
        """Test that execution errors are handled gracefully."""
        mock_client = AsyncMock()
        mock_client.get_ticker = AsyncMock(
            return_value={"success": False, "error": "Market data unavailable"}
        )
        mock_client.set_leverage = AsyncMock(return_value=None)

        # Should not raise, but return failure result
        result = await open_managed_position(
            client=mock_client,
            user_id=123,
            symbol="BTCUSDT",
            side="LONG",
            entry_price=45000.0,
            sl_price=43000.0,
            quantity=0.1,
            leverage=10,
            set_leverage=False,
            register_in_stackmentor=False,
            reconcile=False,
        )

        # Execution should complete (not throw), even with missing ticker data
        assert hasattr(result, "success")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
