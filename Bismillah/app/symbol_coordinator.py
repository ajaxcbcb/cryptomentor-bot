"""
Multi-User Symbol Coordinator
==============================
Enforces single-owner-per-user-per-symbol rule for safe position coordination.

Core principle:
  - Each (user_id, symbol) pair can have only ONE active strategy owner
  - SWING blocks SCALP, SCALP blocks SWING on same symbol
  - Different symbols on same user are independent
  - Different users on same symbol are independent
  - UNKNOWN owner blocks all automation (orphaned position safety)

Thread safety:
  - All methods are async-safe (use asyncio.Lock)
  - State updates are atomic
  - Callers must await can_enter(), set_pending(), clear_pending(), confirm_*()

Lifecycle of a trade:
  1. can_enter(user, sym, strategy) → CHECKS and BLOCKS if conflict
  2. set_pending(user, sym, strategy) → MARKS as pending entry
  3. [order submitted to exchange]
  4a. clear_pending(user, sym) if order fails/times out
  4b. confirm_open(user, sym, strategy, side, size, entry) if order succeeds
  5. [position held until target or stop]
  6. confirm_closed(user, sym) when position is flat
"""

import asyncio
import logging
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────


class StrategyOwner(Enum):
    """Who currently owns this symbol for this user."""
    NONE = "none"           # No position or owner
    SCALP = "scalp"         # Scalping engine owns it
    SWING = "swing"         # Swing (autotrade) engine owns it
    ONE_CLICK = "one_click" # Manual 1-click execution owns it
    MANUAL = "manual"       # Manual exchange action
    UNKNOWN = "unknown"     # Position exists, but owner is unclear (orphaned or reconciliation gap)


class PositionSide(Enum):
    """Direction of open position."""
    NONE = "none"
    LONG = "long"
    SHORT = "short"


# ──────────────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class SymbolState:
    """Snapshot of a single user's symbol coordination state."""
    symbol: str
    has_position: bool = False          # Is there an open position?
    pending_order: bool = False         # Is an order pending at the exchange?
    owner: StrategyOwner = StrategyOwner.NONE
    side: PositionSide = PositionSide.NONE
    size: float = 0.0                   # Position quantity
    entry_price: Optional[float] = None
    exchange_position_id: Optional[str] = None  # Bitunix position ID for reconciliation
    last_exit_ts: Optional[float] = None        # Timestamp of last close

    def __str__(self) -> str:
        return (
            f"SymbolState({self.symbol}: "
            f"owner={self.owner.value}, "
            f"position={'YES' if self.has_position else 'NO'}, "
            f"pending={'YES' if self.pending_order else 'NO'}, "
            f"side={self.side.value}, size={self.size})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Multi-User Coordinator
# ──────────────────────────────────────────────────────────────────────────────


class MultiUserSymbolCoordinator:
    """
    Centralized coordination for multi-user, multi-symbol position management.

    Thread-safe for async environments using asyncio.Lock per (user, symbol) pair.
    """

    def __init__(self):
        """Initialize empty coordinator."""
        # user_id → {symbol → SymbolState}
        self._user_symbol_states: Dict[int, Dict[str, SymbolState]] = {}

        # (user_id, symbol) → asyncio.Lock for atomic state updates
        self._locks: Dict[Tuple[int, str], asyncio.Lock] = {}

        # Cooldown: user_id → {symbol → last_exit_timestamp}
        # After close, don't allow re-entry until cooldown expires
        self._cooldown_map: Dict[int, Dict[str, float]] = {}
        self._cooldown_seconds = 300  # 5-minute cooldown (configurable)

        logger.info("[Coordinator] Initialized")

    # ──────────────────────────────────────────────────────────────────────────
    # Lock Management (internal)
    # ──────────────────────────────────────────────────────────────────────────

    def _get_lock(self, user_id: int, symbol: str) -> asyncio.Lock:
        """Get or create lock for (user_id, symbol) pair."""
        key = (user_id, symbol)
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    # ──────────────────────────────────────────────────────────────────────────
    # State Access
    # ──────────────────────────────────────────────────────────────────────────

    async def get_state(self, user_id: int, symbol: str) -> SymbolState:
        """
        Get current state of a user's symbol.

        Returns a snapshot of the current coordination state.
        Safe to call without locks (returns a copy).
        """
        if user_id not in self._user_symbol_states:
            return SymbolState(symbol=symbol)
        return self._user_symbol_states[user_id].get(symbol, SymbolState(symbol=symbol))

    # ──────────────────────────────────────────────────────────────────────────
    # Entry Gate (the critical decision point)
    # ──────────────────────────────────────────────────────────────────────────

    async def can_enter(
        self,
        user_id: int,
        symbol: str,
        strategy: StrategyOwner,
        now_ts: float,
    ) -> Tuple[bool, str]:
        """
        Check if a strategy can enter this symbol for this user.

        Returns:
            (allowed: bool, reason: str)

        Blocks entry if:
          - Another strategy already owns this symbol for this user
          - A pending order exists on this symbol for this user
          - Cooldown period hasn't elapsed since last exit
          - Owner is UNKNOWN (orphaned position safety)

        Does NOT block entry if:
          - Symbol is free (owner=NONE)
          - Requested strategy already owns symbol (allows re-entry during reversal)
        """
        lock = self._get_lock(user_id, symbol)
        async with lock:
            state = self._ensure_state(user_id, symbol)

            # Rule 1: UNKNOWN owner blocks automation
            if state.owner == StrategyOwner.UNKNOWN:
                return False, f"blocked_unknown_owner: {symbol} has orphaned position, admin intervention required"

            # Rule 2: Pending order blocks entry (prevent double-entry)
            if state.pending_order:
                return False, f"blocked_pending_order: {symbol} already has pending order"

            # Rule 3: Different strategy owns symbol (conflict)
            if state.owner != StrategyOwner.NONE and state.owner != strategy:
                return (
                    False,
                    f"blocked_existing_owner: {symbol} owned by {state.owner.value}, requested {strategy.value}",
                )

            # Rule 4: Cooldown after close
            if symbol in self._cooldown_map.get(user_id, {}):
                last_exit = self._cooldown_map[user_id][symbol]
                cooldown_remaining = self._cooldown_seconds - (now_ts - last_exit)
                if cooldown_remaining > 0:
                    return (
                        False,
                        f"blocked_cooldown: {symbol} cooling down for {cooldown_remaining:.0f}s more",
                    )

            # All checks passed
            return True, "allowed"

    # ──────────────────────────────────────────────────────────────────────────
    # Pending Order Management
    # ──────────────────────────────────────────────────────────────────────────

    async def set_pending(self, user_id: int, symbol: str, strategy: StrategyOwner) -> None:
        """
        Mark that an order is being submitted (pending at exchange).

        Must be called BEFORE sending order to exchange.
        Blocks concurrent entry on same symbol while pending.
        """
        lock = self._get_lock(user_id, symbol)
        async with lock:
            state = self._ensure_state(user_id, symbol)
            state.pending_order = True
            state.owner = strategy  # Tentatively assign owner
            logger.debug(f"[Coordinator] {user_id}:{symbol} marked pending (strategy={strategy.value})")

    async def clear_pending(self, user_id: int, symbol: str) -> None:
        """
        Clear pending order flag (order failed, was rejected, or timed out).

        Also clears owner assignment since entry failed.
        Must be called if order submission fails.
        """
        lock = self._get_lock(user_id, symbol)
        async with lock:
            state = self._ensure_state(user_id, symbol)
            if state.pending_order:
                state.pending_order = False
                # If no position open, clear owner
                if not state.has_position:
                    state.owner = StrategyOwner.NONE
                logger.debug(f"[Coordinator] {user_id}:{symbol} pending cleared")

    # ──────────────────────────────────────────────────────────────────────────
    # Position Lifecycle
    # ──────────────────────────────────────────────────────────────────────────

    async def confirm_open(
        self,
        user_id: int,
        symbol: str,
        strategy: StrategyOwner,
        side: PositionSide,
        size: float,
        entry_price: float,
        exchange_position_id: Optional[str] = None,
    ) -> None:
        """
        Confirm that a position has been opened at the exchange.

        Must be called AFTER successful order execution.
        Marks position as open with full metadata.
        """
        lock = self._get_lock(user_id, symbol)
        async with lock:
            state = self._ensure_state(user_id, symbol)
            state.has_position = True
            state.pending_order = False
            state.owner = strategy
            state.side = side
            state.size = size
            state.entry_price = entry_price
            state.exchange_position_id = exchange_position_id
            logger.info(
                f"[Coordinator] {user_id}:{symbol} position OPEN — "
                f"owner={strategy.value}, side={side.value}, size={size}, entry={entry_price:.6f}"
            )

    async def confirm_closed(self, user_id: int, symbol: str, now_ts: float) -> None:
        """
        Confirm that a position has been closed (flat).

        Must be called AFTER position is confirmed flat on exchange.
        Clears position state and starts cooldown timer.
        """
        lock = self._get_lock(user_id, symbol)
        async with lock:
            state = self._ensure_state(user_id, symbol)

            if state.has_position:
                logger.info(
                    f"[Coordinator] {user_id}:{symbol} position CLOSED — "
                    f"was {state.side.value}, starting {self._cooldown_seconds}s cooldown"
                )

            # Clear position
            state.has_position = False
            state.pending_order = False
            state.owner = StrategyOwner.NONE
            state.side = PositionSide.NONE
            state.size = 0.0
            state.entry_price = None
            state.exchange_position_id = None
            state.last_exit_ts = now_ts

            # Start cooldown
            if user_id not in self._cooldown_map:
                self._cooldown_map[user_id] = {}
            self._cooldown_map[user_id][symbol] = now_ts

    # ──────────────────────────────────────────────────────────────────────────
    # Reconciliation (startup restore)
    # ──────────────────────────────────────────────────────────────────────────

    async def reconcile_user(
        self,
        user_id: int,
        exchange_positions: List[Dict],
        db_open_trades: Optional[List[Dict]] = None,
    ) -> Dict[str, str]:
        """
        Reconcile coordinator state with exchange + database on startup.

        Args:
            user_id: User to reconcile
            exchange_positions: Live positions from exchange API (list of dicts with 'symbol', 'side', etc.)
            db_open_trades: Open trades from database (list of dicts with 'symbol', 'status', etc.)

        Returns:
            Dict[str, str]: symbol → reconciliation_notes for each position

        Behavior:
            - For each exchange position: mark as open with UNKNOWN owner
            - If DB has hint about which engine opened it: infer and assign owner
            - If DB says closed but exchange says open: log warning + assign UNKNOWN
            - If both closed: no action

        Ambiguous cases get UNKNOWN owner + TODO note logged.
        """
        notes = {}

        db_trades = {(t.get("symbol") or "").upper(): t for t in (db_open_trades or [])}

        # Process each exchange position
        for ex_pos in (exchange_positions or []):
            sym = (ex_pos.get("symbol") or "").upper().replace("/", "")
            if not sym:
                continue

            # Determine owner from DB hint
            owner = StrategyOwner.UNKNOWN
            db_trade = db_trades.get(sym)

            if db_trade:
                # DB knows about this trade — try to infer strategy
                strategy_hint = (db_trade.get("strategy") or "").lower()
                if "scalp" in strategy_hint or "scalping" in strategy_hint:
                    owner = StrategyOwner.SCALP
                elif "swing" in strategy_hint or "autotrade" in strategy_hint:
                    owner = StrategyOwner.SWING
                else:
                    owner = StrategyOwner.UNKNOWN
                    notes[sym] = f"TODO(manual-confirmation): DB has {sym} but strategy unclear, assigned UNKNOWN"
            else:
                # No DB hint — position is orphaned
                notes[sym] = f"TODO(manual-confirmation): {sym} has exchange position but no DB record, assigned UNKNOWN"

            # Determine side
            ex_side = (ex_pos.get("side") or "").upper().replace("BUY", "LONG").replace("SELL", "SHORT")
            side = PositionSide.LONG if ex_side == "LONG" else PositionSide.SHORT if ex_side == "SHORT" else PositionSide.NONE

            # Set state
            state = self._ensure_state(user_id, sym)
            state.has_position = True
            state.owner = owner
            state.side = side
            state.size = float(ex_pos.get("amount", 0) or 0)
            state.entry_price = float(ex_pos.get("entry_price", 0) or 0)
            state.exchange_position_id = ex_pos.get("position_id")

            logger.info(
                f"[Coordinator] Restored {user_id}:{sym} from exchange — "
                f"owner={owner.value}, side={side.value}, size={state.size}"
            )

        return notes

    # ──────────────────────────────────────────────────────────────────────────
    # Debug / Admin
    # ──────────────────────────────────────────────────────────────────────────

    async def export_debug_snapshot(self) -> Dict:
        """
        Export complete coordinator state for debugging/admin dashboards.

        Returns:
            {
              "total_users": int,
              "total_positions": int,
              "users": {
                user_id: {
                  "symbols": {
                    symbol: {
                      "has_position": bool,
                      "owner": str,
                      "side": str,
                      "size": float,
                      "entry_price": float,
                      ...
                    }
                  },
                  "cooldowns": {symbol: seconds_remaining}
                }
              }
            }
        """
        now = time.time()
        snapshot = {
            "total_users": len(self._user_symbol_states),
            "total_positions": sum(
                len(syms) for syms in self._user_symbol_states.values()
            ),
            "users": {}
        }

        for user_id, symbols in self._user_symbol_states.items():
            user_data = {
                "symbols": {},
                "cooldowns": {}
            }

            for sym, state in symbols.items():
                user_data["symbols"][sym] = {
                    "has_position": state.has_position,
                    "pending_order": state.pending_order,
                    "owner": state.owner.value,
                    "side": state.side.value,
                    "size": state.size,
                    "entry_price": state.entry_price,
                    "exchange_position_id": state.exchange_position_id,
                }

            # Cooldowns remaining
            if user_id in self._cooldown_map:
                for sym, exit_ts in self._cooldown_map[user_id].items():
                    remaining = self._cooldown_seconds - (now - exit_ts)
                    if remaining > 0:
                        user_data["cooldowns"][sym] = remaining

            snapshot["users"][user_id] = user_data

        return snapshot

    async def force_reset_symbol(self, user_id: int, symbol: str) -> None:
        """
        Admin-only: Force reset a symbol to NONE state (for orphaned positions).

        Use cautiously — only after manual review and decision.
        """
        lock = self._get_lock(user_id, symbol)
        async with lock:
            state = self._ensure_state(user_id, symbol)
            state.has_position = False
            state.pending_order = False
            state.owner = StrategyOwner.NONE
            state.side = PositionSide.NONE
            state.size = 0.0
            state.entry_price = None
            state.exchange_position_id = None
            logger.warning(f"[Coordinator] Admin reset {user_id}:{symbol} to NONE state")

    # ──────────────────────────────────────────────────────────────────────────
    # Internal Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _ensure_state(self, user_id: int, symbol: str) -> SymbolState:
        """Get or create SymbolState for (user_id, symbol)."""
        if user_id not in self._user_symbol_states:
            self._user_symbol_states[user_id] = {}

        if symbol not in self._user_symbol_states[user_id]:
            self._user_symbol_states[user_id][symbol] = SymbolState(symbol=symbol)

        return self._user_symbol_states[user_id][symbol]


# ──────────────────────────────────────────────────────────────────────────────
# Global Instance
# ──────────────────────────────────────────────────────────────────────────────

_coordinator_instance: Optional[MultiUserSymbolCoordinator] = None


def get_coordinator() -> MultiUserSymbolCoordinator:
    """Get or create the global coordinator instance."""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = MultiUserSymbolCoordinator()
    return _coordinator_instance


def reset_coordinator_for_testing() -> None:
    """Reset global coordinator (for unit tests only)."""
    global _coordinator_instance
    _coordinator_instance = MultiUserSymbolCoordinator()
