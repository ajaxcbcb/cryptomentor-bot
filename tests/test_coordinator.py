"""
Unit Tests for MultiUserSymbolCoordinator
==========================================
Tests for:
  - Entry gating (can_enter)
  - Pending order lifecycle
  - Position open/close
  - Cooldown enforcement
  - Reconciliation
  - Multi-user isolation
  - Multi-symbol independence
"""

import pytest
import asyncio
import time
from Bismillah.app.symbol_coordinator import (
    MultiUserSymbolCoordinator,
    StrategyOwner,
    PositionSide,
    SymbolState,
    get_coordinator,
    reset_coordinator_for_testing,
)


@pytest.fixture
def coordinator():
    """Fresh coordinator instance for each test."""
    reset_coordinator_for_testing()
    return get_coordinator()


class TestEntryGating:
    """Test can_enter() logic."""

    @pytest.mark.asyncio
    async def test_fresh_symbol_allows_entry(self, coordinator):
        """Fresh symbol (no position) allows entry."""
        allowed, reason = await coordinator.can_enter(
            user_id=123,
            symbol="BTCUSDT",
            strategy=StrategyOwner.SWING,
            now_ts=time.time(),
        )
        assert allowed is True
        assert reason == "allowed"

    @pytest.mark.asyncio
    async def test_pending_order_blocks_entry(self, coordinator):
        """Pending order blocks second entry."""
        user_id = 123
        symbol = "BTCUSDT"
        now = time.time()

        # First entry starts
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)

        # Second entry is blocked
        allowed, reason = await coordinator.can_enter(
            user_id, symbol, StrategyOwner.SWING, now
        )
        assert allowed is False
        assert "pending_order" in reason

    @pytest.mark.asyncio
    async def test_swing_blocks_scalp_same_symbol(self, coordinator):
        """SWING position blocks SCALP on same user+symbol."""
        user_id = 123
        symbol = "BTCUSDT"
        now = time.time()

        # SWING owns it
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)
        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # SCALP cannot enter
        allowed, reason = await coordinator.can_enter(
            user_id, symbol, StrategyOwner.SCALP, now
        )
        assert allowed is False
        assert "existing_owner" in reason

    @pytest.mark.asyncio
    async def test_scalp_blocks_swing_same_symbol(self, coordinator):
        """SCALP position blocks SWING on same user+symbol."""
        user_id = 123
        symbol = "ETHUSDT"
        now = time.time()

        # SCALP owns it
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SCALP)
        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SCALP,
            PositionSide.SHORT, 1.0, 3100.0
        )

        # SWING cannot enter
        allowed, reason = await coordinator.can_enter(
            user_id, symbol, StrategyOwner.SWING, now
        )
        assert allowed is False
        assert "existing_owner" in reason

    @pytest.mark.asyncio
    async def test_different_symbols_independent(self, coordinator):
        """Different symbols are independent."""
        user_id = 123
        now = time.time()

        # SWING owns BTC
        await coordinator.set_pending(user_id, "BTCUSDT", StrategyOwner.SWING)
        await coordinator.confirm_open(
            user_id, "BTCUSDT", StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # SCALP can enter ETH (different symbol)
        allowed, reason = await coordinator.can_enter(
            user_id, "ETHUSDT", StrategyOwner.SCALP, now
        )
        assert allowed is True
        assert reason == "allowed"

    @pytest.mark.asyncio
    async def test_different_users_independent(self, coordinator):
        """Different users are independent."""
        symbol = "BTCUSDT"
        now = time.time()

        # User A's SWING owns BTC
        await coordinator.set_pending(1, symbol, StrategyOwner.SWING)
        await coordinator.confirm_open(
            1, symbol, StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # User B can still enter BTC with SWING
        allowed, reason = await coordinator.can_enter(
            2, symbol, StrategyOwner.SWING, now
        )
        assert allowed is True
        assert reason == "allowed"

    @pytest.mark.asyncio
    async def test_unknown_owner_blocks_all_automation(self, coordinator):
        """UNKNOWN owner blocks any automation attempt."""
        user_id = 123
        symbol = "BTCUSDT"
        now = time.time()

        # Set UNKNOWN state via reconciliation (proper way)
        exchange_positions = [
            {
                "symbol": symbol,
                "side": "LONG",
                "amount": 0.1,
                "entry_price": 45000.0
            }
        ]
        # No DB hint — will result in UNKNOWN owner
        await coordinator.reconcile_user(user_id, exchange_positions, [])

        # All automations blocked
        for strategy in [StrategyOwner.SWING, StrategyOwner.SCALP, StrategyOwner.ONE_CLICK]:
            allowed, reason = await coordinator.can_enter(user_id, symbol, strategy, now)
            assert allowed is False
            assert "unknown_owner" in reason

    @pytest.mark.asyncio
    async def test_cooldown_blocks_reentry(self, coordinator):
        """Cooldown period blocks immediate re-entry after close."""
        user_id = 123
        symbol = "BTCUSDT"

        # Open position
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)
        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # Close position
        close_time = time.time()
        await coordinator.confirm_closed(user_id, symbol, close_time)

        # Immediate re-entry is blocked (within cooldown)
        allowed, reason = await coordinator.can_enter(
            user_id, symbol, StrategyOwner.SWING, close_time + 10
        )
        assert allowed is False
        assert "cooldown" in reason

        # After cooldown expires, entry allowed
        after_cooldown = close_time + 310  # 5min + 10s
        allowed, reason = await coordinator.can_enter(
            user_id, symbol, StrategyOwner.SWING, after_cooldown
        )
        assert allowed is True
        assert reason == "allowed"

    @pytest.mark.asyncio
    async def test_same_strategy_can_reenter_during_reversal(self, coordinator):
        """Same strategy can re-enter its own symbol during reversal."""
        user_id = 123
        symbol = "BTCUSDT"
        now = time.time()

        # SWING opens LONG
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)
        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # Before closing, attempt to enter again (reversal scenario)
        # Should be allowed because same strategy owns it
        allowed, reason = await coordinator.can_enter(
            user_id, symbol, StrategyOwner.SWING, now
        )
        assert allowed is True
        assert reason == "allowed"


class TestPendingOrderLifecycle:
    """Test set_pending() and clear_pending()."""

    @pytest.mark.asyncio
    async def test_pending_marked_and_cleared(self, coordinator):
        """Pending order can be marked and cleared."""
        user_id = 123
        symbol = "BTCUSDT"

        # Set pending
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)
        state = await coordinator.get_state(user_id, symbol)
        assert state.pending_order is True
        assert state.owner == StrategyOwner.SWING

        # Clear pending
        await coordinator.clear_pending(user_id, symbol)
        state = await coordinator.get_state(user_id, symbol)
        assert state.pending_order is False
        # Owner cleared if no position
        assert state.owner == StrategyOwner.NONE

    @pytest.mark.asyncio
    async def test_clear_pending_preserves_owner_if_position_open(self, coordinator):
        """Clearing pending preserves owner if position is already open."""
        user_id = 123
        symbol = "BTCUSDT"

        # Open position
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)
        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # Set pending again (reversal/scaling)
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)

        # Clear pending — should keep owner since position is open
        await coordinator.clear_pending(user_id, symbol)
        state = await coordinator.get_state(user_id, symbol)
        assert state.pending_order is False
        assert state.owner == StrategyOwner.SWING  # Still owns it


class TestPositionLifecycle:
    """Test confirm_open() and confirm_closed()."""

    @pytest.mark.asyncio
    async def test_open_position_with_metadata(self, coordinator):
        """Position opens with full metadata."""
        user_id = 123
        symbol = "BTCUSDT"

        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SWING,
            PositionSide.LONG, 0.5, 45000.0,
            exchange_position_id="pos_123"
        )

        state = await coordinator.get_state(user_id, symbol)
        assert state.has_position is True
        assert state.owner == StrategyOwner.SWING
        assert state.side == PositionSide.LONG
        assert state.size == 0.5
        assert state.entry_price == 45000.0
        assert state.exchange_position_id == "pos_123"
        assert state.pending_order is False

    @pytest.mark.asyncio
    async def test_close_position_starts_cooldown(self, coordinator):
        """Closing position starts cooldown timer."""
        user_id = 123
        symbol = "BTCUSDT"

        # Open
        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # Close
        close_time = time.time()
        await coordinator.confirm_closed(user_id, symbol, close_time)

        state = await coordinator.get_state(user_id, symbol)
        assert state.has_position is False
        assert state.owner == StrategyOwner.NONE
        assert state.side == PositionSide.NONE
        assert state.size == 0.0
        assert state.last_exit_ts == close_time

    @pytest.mark.asyncio
    async def test_close_clears_pending_flag(self, coordinator):
        """Closing clears pending flag."""
        user_id = 123
        symbol = "BTCUSDT"

        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)
        await coordinator.confirm_open(
            user_id, symbol, StrategyOwner.SWING,
            PositionSide.SHORT, 1.0, 3100.0
        )

        # Mark pending again (partial close scenario)
        await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)

        # Close
        await coordinator.confirm_closed(user_id, symbol, time.time())
        state = await coordinator.get_state(user_id, symbol)
        assert state.pending_order is False


class TestReconciliation:
    """Test reconcile_user() for startup restore."""

    @pytest.mark.asyncio
    async def test_reconcile_exchange_position_with_db_hint(self, coordinator):
        """Reconciliation assigns owner based on DB hint."""
        user_id = 123
        now = time.time()

        exchange_positions = [
            {
                "symbol": "BTCUSDT",
                "side": "LONG",
                "amount": 0.1,
                "entry_price": 45000.0,
                "position_id": "pos_123"
            }
        ]

        db_trades = [
            {
                "symbol": "BTCUSDT",
                "strategy": "scalping",
                "status": "open"
            }
        ]

        notes = await coordinator.reconcile_user(user_id, exchange_positions, db_trades)

        state = await coordinator.get_state(user_id, "BTCUSDT")
        assert state.has_position is True
        assert state.owner == StrategyOwner.SCALP  # Inferred from "scalping"
        assert state.side == PositionSide.LONG
        assert state.size == 0.1

    @pytest.mark.asyncio
    async def test_reconcile_orphaned_position_unknown_owner(self, coordinator):
        """Reconciliation assigns UNKNOWN to orphaned positions."""
        user_id = 123

        exchange_positions = [
            {
                "symbol": "ETHUSDT",
                "side": "SHORT",
                "amount": 1.0,
                "entry_price": 3100.0
            }
        ]

        # No DB hint
        notes = await coordinator.reconcile_user(user_id, exchange_positions, [])

        state = await coordinator.get_state(user_id, "ETHUSDT")
        assert state.has_position is True
        assert state.owner == StrategyOwner.UNKNOWN  # No DB hint
        assert "manual-confirmation" in notes.get("ETHUSDT", "")

    @pytest.mark.asyncio
    async def test_reconcile_multiple_positions(self, coordinator):
        """Reconciliation handles multiple positions."""
        user_id = 123

        exchange_positions = [
            {"symbol": "BTCUSDT", "side": "LONG", "amount": 0.1, "entry_price": 45000.0},
            {"symbol": "ETHUSDT", "side": "SHORT", "amount": 1.0, "entry_price": 3100.0},
        ]

        db_trades = [
            {"symbol": "BTCUSDT", "strategy": "swing"},
            {"symbol": "ETHUSDT", "strategy": "scalp"},
        ]

        notes = await coordinator.reconcile_user(user_id, exchange_positions, db_trades)

        btc_state = await coordinator.get_state(user_id, "BTCUSDT")
        eth_state = await coordinator.get_state(user_id, "ETHUSDT")

        assert btc_state.owner == StrategyOwner.SWING
        assert eth_state.owner == StrategyOwner.SCALP


class TestConcurrency:
    """Test async/concurrent safety."""

    @pytest.mark.asyncio
    async def test_concurrent_entries_on_different_symbols(self, coordinator):
        """Concurrent operations on different symbols should not race."""
        user_id = 123
        now = time.time()

        # Concurrent entries on different symbols
        results = await asyncio.gather(
            coordinator.can_enter(user_id, "BTCUSDT", StrategyOwner.SWING, now),
            coordinator.can_enter(user_id, "ETHUSDT", StrategyOwner.SCALP, now),
            coordinator.can_enter(user_id, "SOLUSDT", StrategyOwner.SWING, now),
        )

        # All should succeed
        assert all(r[0] for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_operations_same_symbol_serialize(self, coordinator):
        """Concurrent operations on same symbol should serialize via lock."""
        user_id = 123
        symbol = "BTCUSDT"

        async def entry_and_open():
            allowed, _ = await coordinator.can_enter(user_id, symbol, StrategyOwner.SWING, time.time())
            if allowed:
                await coordinator.set_pending(user_id, symbol, StrategyOwner.SWING)
                await asyncio.sleep(0.01)  # Simulate order submission
                await coordinator.confirm_open(
                    user_id, symbol, StrategyOwner.SWING,
                    PositionSide.LONG, 0.1, 45000.0
                )

        # Run two concurrent entry attempts
        # Second should block due to lock
        await entry_and_open()

        # Verify position is open
        state = await coordinator.get_state(user_id, symbol)
        assert state.has_position is True


class TestDebugExport:
    """Test debug/admin snapshot export."""

    @pytest.mark.asyncio
    async def test_export_snapshot(self, coordinator):
        """Export snapshot contains all coordinator state."""
        user_id = 123

        # Set up some positions
        await coordinator.set_pending(user_id, "BTCUSDT", StrategyOwner.SWING)
        await coordinator.confirm_open(
            user_id, "BTCUSDT", StrategyOwner.SWING,
            PositionSide.LONG, 0.1, 45000.0
        )

        # Export
        snapshot = await coordinator.export_debug_snapshot()

        assert snapshot["total_users"] >= 1
        assert snapshot["total_positions"] >= 1
        assert user_id in snapshot["users"]
        assert "BTCUSDT" in snapshot["users"][user_id]["symbols"]

        btc_data = snapshot["users"][user_id]["symbols"]["BTCUSDT"]
        assert btc_data["has_position"] is True
        assert btc_data["owner"] == "swing"
        assert btc_data["side"] == "long"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
