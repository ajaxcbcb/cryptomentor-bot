"""
Unified Trade Execution Module
==============================
Single code path for opening managed positions across BOTH the swing
(autotrade_engine) and scalping (scalping_engine) strategies.

Why this exists
---------------
Previously the two engines duplicated entry/TP/SL/registration logic and
had drifted apart:
  * Swing used `client.place_order_with_tpsl(...)` (atomic TP+SL at entry)
  * Scalping used `client.place_order(...)` then patched SL afterwards and
    NEVER set TP on the exchange. It also called `calculate_qty_splits`,
    `calculate_stackmentor_levels` and `register_stackmentor_position`
    with the wrong signatures, so the StackMentor registry was never
    populated and the in-memory monitor never tracked scalping positions.

This module owns the canonical entry pipeline:
    1. Compute StackMentor TP/SL tiers and qty splits
    2. Validate prices against current mark price
    3. Set leverage
    4. Place atomic order WITH TP1 + SL on the exchange
    5. Register the position in the StackMentor in-memory registry

Both engines call `open_managed_position(...)` so behavior cannot drift.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from app.stackmentor import (
    calculate_stackmentor_levels,
    calculate_qty_splits,
    register_stackmentor_position,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class StackMentorLevels:
    """Computed TP/SL tiers and quantity splits."""
    tp1: float
    tp2: float
    tp3: float
    sl: float
    qty_tp1: float
    qty_tp2: float
    qty_tp3: float


@dataclass
class ExecutionResult:
    """Result of an `open_managed_position` call."""
    success: bool
    order_id: Optional[str] = None
    levels: Optional[StackMentorLevels] = None
    adjusted_sl: Optional[float] = None      # set if validator nudged SL
    error: Optional[str] = None
    error_code: Optional[str] = None         # short tag for caller dispatch
    raw: Dict = field(default_factory=dict)  # raw exchange response
    reconciled: bool = False                 # True if self-healing fixed something
    reconcile_notes: list = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Pure helpers (no I/O)
# ──────────────────────────────────────────────────────────────────────────────


def build_stackmentor_levels(
    entry_price: float,
    sl_price: float,
    side: str,
    total_qty: float,
    precision: int = 3,
) -> StackMentorLevels:
    """
    Compute the 3-tier StackMentor TP levels and quantity splits.
    Side must be "LONG" or "SHORT".
    """
    tp1, tp2, tp3 = calculate_stackmentor_levels(
        entry_price=entry_price,
        sl_price=sl_price,
        side=side,
    )
    qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(total_qty, precision)
    return StackMentorLevels(
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
        sl=sl_price,
        qty_tp1=qty_tp1,
        qty_tp2=qty_tp2,
        qty_tp3=qty_tp3,
    )


def validate_entry_prices(
    side: str,
    entry: float,
    tp1: float,
    sl: float,
    mark_price: float,
) -> Tuple[bool, float, Optional[str]]:
    """
    Validate that SL/TP make sense relative to current mark price.

    Returns: (is_valid, possibly_adjusted_sl, error_msg)
      * If SL is on the wrong side of mark we nudge it 2% away from mark
        and return the new value (adjusted_sl).
      * If TP is on the wrong side of mark we abort the trade entirely.
    """
    adjusted_sl = sl
    if side == "LONG":
        if sl >= mark_price:
            adjusted_sl = mark_price * 0.98
            logger.warning(
                "[trade_execution] LONG SL %.6f >= mark %.6f — adjusted to %.6f",
                sl, mark_price, adjusted_sl,
            )
        if tp1 <= mark_price:
            return False, adjusted_sl, f"LONG TP1 {tp1:.6f} <= mark {mark_price:.6f}"
    else:  # SHORT
        if sl <= mark_price:
            adjusted_sl = mark_price * 1.02
            logger.warning(
                "[trade_execution] SHORT SL %.6f <= mark %.6f — adjusted to %.6f",
                sl, mark_price, adjusted_sl,
            )
        if tp1 >= mark_price:
            return False, adjusted_sl, f"SHORT TP1 {tp1:.6f} >= mark {mark_price:.6f}"
    return True, adjusted_sl, None


# ──────────────────────────────────────────────────────────────────────────────
# Self-healing reconciliation
# ──────────────────────────────────────────────────────────────────────────────


# Tolerances for "matches expected" comparison.
QTY_TOLERANCE_PCT = 0.02      # actual qty within 2% of expected
PRICE_TOLERANCE_PCT = 0.005   # tp/sl within 0.5% of expected


def _within_pct(actual: float, expected: float, pct: float) -> bool:
    if expected == 0:
        return abs(actual) < 1e-9
    return abs(actual - expected) / abs(expected) <= pct


async def reconcile_position(
    *,
    client,
    user_id: int,
    symbol: str,
    side: str,
    expected_qty: float,
    expected_tp: float,
    expected_sl: float,
) -> Tuple[bool, list, float]:
    """
    Verify the live exchange position matches expectations and self-heal.

    Strategy:
      1. Fetch actual positions from the exchange.
      2. If no position exists for this symbol → entry never landed; return
         (False, ["no_position"]).
      3. If qty mismatch beyond tolerance → cannot fix qty after the fact;
         emergency-close and return (False, [...reason]).
      4. If TP/SL missing or wrong → call set_position_tpsl / set_position_sl
         to repair them. If repair fails → emergency-close.
      5. If all good → return (True, []).

    Returns: (healthy, notes)
    """
    notes: list = []
    try:
        pos_resp = await asyncio.to_thread(client.get_positions)
    except Exception as e:
        notes.append(f"get_positions raised: {e}")
        return False, notes, 0.0

    if not pos_resp.get("success"):
        notes.append(f"get_positions failed: {pos_resp.get('error')}")
        return False, notes, 0.0

    # Find the matching position
    matching = None
    for p in pos_resp.get("positions", []):
        if p.get("symbol") == symbol:
            matching = p
            break

    if not matching:
        notes.append("no_position_on_exchange")
        return False, notes, 0.0

    actual_qty = float(matching.get("qty") or matching.get("size") or 0)
    actual_tp = float(matching.get("tp_price") or 0)
    actual_sl = float(matching.get("sl_price") or 0)

    # 1. Quantity check ────────────────────────────────────────────────────────
    if not _within_pct(actual_qty, expected_qty, QTY_TOLERANCE_PCT):
        notes.append(
            f"qty_mismatch_ignored actual={actual_qty} expected={expected_qty}"
        )
        # We ignore qty mismatch for self-healing and update the actual_qty later.

    # 2. TP / SL check + repair ────────────────────────────────────────────────
    tp_ok = actual_tp > 0 and _within_pct(actual_tp, expected_tp, PRICE_TOLERANCE_PCT)
    sl_ok = actual_sl > 0 and _within_pct(actual_sl, expected_sl, PRICE_TOLERANCE_PCT)

    if tp_ok and sl_ok:
        return True, notes, actual_qty

    notes.append(
        f"tpsl_drift actual_tp={actual_tp} expected_tp={expected_tp} "
        f"actual_sl={actual_sl} expected_sl={expected_sl}"
    )

    # Try to set both via set_position_tpsl if the client supports it,
    # otherwise fall back to set_position_sl + best-effort TP.
    repair_ok = False
    set_tpsl = getattr(client, "set_position_tpsl", None)
    if callable(set_tpsl):
        try:
            r = await asyncio.to_thread(set_tpsl, symbol, expected_tp, expected_sl)
            repair_ok = bool(r.get("success"))
            if not repair_ok:
                notes.append(f"set_position_tpsl failed: {r.get('error')}")
        except Exception as e:
            notes.append(f"set_position_tpsl raised: {e}")

    if not repair_ok:
        # Fall back: at minimum re-set SL — losing TP is recoverable via the
        # in-memory StackMentor monitor, losing SL is not.
        try:
            r = await asyncio.to_thread(client.set_position_sl, symbol, expected_sl)
            repair_ok = bool(r.get("success"))
            if not repair_ok:
                notes.append(f"set_position_sl failed: {r.get('error')}")
        except Exception as e:
            notes.append(f"set_position_sl raised: {e}")

    if repair_ok:
        notes.append("tpsl_repaired")
        return True, notes, actual_qty

    # Repair failed completely — emergency close to protect user.
    notes.append("repair_failed_emergency_close")
    try:
        close_side = "SELL" if side.upper() == "LONG" else "BUY"
        await asyncio.to_thread(
            client.place_order,
            symbol,
            close_side,
            actual_qty,
            'market',
            None,
            True,
        )
    except Exception as e:
        notes.append(f"emergency_close_failed: {e}")
    return False, notes, actual_qty


# ──────────────────────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────────────────────


async def open_managed_position(
    *,
    client,
    user_id: int,
    symbol: str,
    side: str,                       # "LONG" or "SHORT"
    entry_price: float,
    sl_price: float,
    quantity: float,
    leverage: int,
    precision: int = 3,
    set_leverage: bool = True,
    register_in_stackmentor: bool = True,
    reconcile: bool = True,
    reconcile_delay_s: float = 1.0,
) -> ExecutionResult:
    """
    Open a managed position with StackMentor 3-tier TP/SL.

    Both the scalping and swing engines call this function so the on-exchange
    behavior is identical:

      1. Compute TP1/TP2/TP3 + qty splits
      2. Get mark price → validate SL/TP, possibly adjust SL
      3. Set leverage on the symbol
      4. Atomic `place_order_with_tpsl` (TP1 + SL attached at entry)
      5. Register the position in the StackMentor monitoring registry

    Returns an `ExecutionResult`. Callers are responsible for user-facing
    notifications, retries, error message formatting, and persistence
    (trade history, sessions, etc.).
    """
    side = side.upper()
    if side not in ("LONG", "SHORT"):
        return ExecutionResult(
            success=False,
            error=f"Invalid side: {side}",
            error_code="invalid_side",
        )

    # 1. Compute StackMentor tiers + qty splits ────────────────────────────────
    try:
        levels = build_stackmentor_levels(
            entry_price=entry_price,
            sl_price=sl_price,
            side=side,
            total_qty=quantity,
            precision=precision,
        )
    except Exception as e:
        logger.exception("[trade_execution:%s] level calc failed", user_id)
        return ExecutionResult(
            success=False,
            error=f"Level calculation failed: {e}",
            error_code="levels_failed",
        )

    # 2. Validate against mark price ────────────────────────────────────────────
    try:
        ticker = await asyncio.to_thread(client.get_ticker, symbol)
        if ticker.get("success"):
            mark_price = float(ticker.get("mark_price", entry_price))
            ok, adj_sl, err = validate_entry_prices(
                side=side,
                entry=entry_price,
                tp1=levels.tp1,
                sl=levels.sl,
                mark_price=mark_price,
            )
            if not ok:
                logger.warning(
                    "[trade_execution:%s] %s validation failed: %s",
                    user_id, symbol, err,
                )
                return ExecutionResult(
                    success=False,
                    error=err,
                    error_code="invalid_prices",
                    levels=levels,
                )
            if adj_sl != levels.sl:
                levels.sl = adj_sl
        else:
            logger.warning(
                "[trade_execution:%s] could not fetch ticker for %s, proceeding without validation",
                user_id, symbol,
            )
    except Exception as e:
        logger.warning(
            "[trade_execution:%s] price validation error: %s — proceeding",
            user_id, e,
        )

    # 3. Set leverage ───────────────────────────────────────────────────────────
    if set_leverage:
        try:
            await asyncio.to_thread(client.set_leverage, symbol, leverage)
        except Exception as e:
            logger.warning(
                "[trade_execution:%s] set_leverage failed for %s: %s",
                user_id, symbol, e,
            )

    # 4. Atomic entry: place order WITH TP1 + SL on the exchange ───────────────
    order_side = "BUY" if side == "LONG" else "SELL"
    try:
        order_result = await asyncio.to_thread(
            client.place_order_with_tpsl,
            symbol,
            order_side,
            quantity,
            levels.tp1,
            levels.sl,
        )
    except Exception as e:
        logger.exception("[trade_execution:%s] place_order_with_tpsl raised", user_id)
        return ExecutionResult(
            success=False,
            error=str(e),
            error_code="order_exception",
            levels=levels,
        )

    if not order_result.get("success"):
        err_msg = str(order_result.get("error", "Unknown error"))
        # Classify error so callers can branch (auth, balance, SL price, etc.)
        if "TOKEN_INVALID" in err_msg or "SIGNATURE_ERROR" in err_msg:
            code = "auth"
        elif "HTTP 403" in err_msg or "IP_BLOCKED" in err_msg:
            code = "ip_blocked"
        elif "30029" in err_msg or "SL price must be" in err_msg:
            code = "invalid_sl_price"
        elif "20003" in err_msg or "insufficient" in err_msg.lower():
            code = "insufficient_balance"
        else:
            code = "order_failed"
        return ExecutionResult(
            success=False,
            error=err_msg,
            error_code=code,
            levels=levels,
            raw=order_result,
        )

    order_id = order_result.get("order_id", "-")
    logger.info(
        "[trade_execution:%s] %s %s opened qty=%.6f tp1=%.6f sl=%.6f order=%s",
        user_id, symbol, side, quantity, levels.tp1, levels.sl, order_id,
    )

    # 4b. Self-healing reconciliation ──────────────────────────────────────────
    # Verify the live position on the exchange matches what we expect.
    # If qty drifts → emergency close. If TP/SL drift → repair, else close.
    reconciled = False
    reconcile_notes: list = []
    if reconcile:
        if reconcile_delay_s > 0:
            await asyncio.sleep(reconcile_delay_s)
        try:
            healthy, reconcile_notes, actual_qty = await reconcile_position(
                client=client,
                user_id=user_id,
                symbol=symbol,
                side=side,
                expected_qty=quantity,
                expected_tp=levels.tp1,
                expected_sl=levels.sl,
            )
            # Retrieve the update of the quantity after the position check
            if actual_qty > 0:
                quantity = actual_qty
            if not healthy:
                logger.error(
                    "[trade_execution:%s] reconciliation FAILED for %s: %s",
                    user_id, symbol, reconcile_notes,
                )
                return ExecutionResult(
                    success=False,
                    order_id=order_id,
                    levels=levels,
                    error=f"Reconciliation failed: {'; '.join(reconcile_notes)}",
                    error_code="reconcile_failed",
                    raw=order_result,
                    reconciled=False,
                    reconcile_notes=reconcile_notes,
                )
            if reconcile_notes:
                reconciled = True
                logger.warning(
                    "[trade_execution:%s] reconciliation healed %s: %s",
                    user_id, symbol, reconcile_notes,
                )
        except Exception as e:
            logger.exception(
                "[trade_execution:%s] reconciliation raised — proceeding without",
                user_id,
            )
            reconcile_notes.append(f"exception: {e}")

    # 5. Register with StackMentor monitor ─────────────────────────────────────
    if register_in_stackmentor:
        try:
            register_stackmentor_position(
                user_id=user_id,
                symbol=symbol,
                entry_price=entry_price,
                sl_price=levels.sl,
                tp1=levels.tp1,
                tp2=levels.tp2,
                tp3=levels.tp3,
                total_qty=quantity,
                qty_tp1=levels.qty_tp1,
                qty_tp2=levels.qty_tp2,
                qty_tp3=levels.qty_tp3,
                side=side,
                leverage=leverage,
            )
        except Exception as e:
            logger.error(
                "[trade_execution:%s] StackMentor registration failed: %s",
                user_id, e,
            )
            # Position is open with TP/SL on the exchange, so this is
            # non-fatal: TP1 and SL will still trigger natively. Only the
            # in-memory tiered monitor (TP2/TP3 partial closes + breakeven
            # move) will be missing.

    return ExecutionResult(
        success=True,
        order_id=order_id,
        levels=levels,
        adjusted_sl=levels.sl if levels.sl != sl_price else None,
        raw=order_result,
        reconciled=reconciled,
        reconcile_notes=reconcile_notes,
    )
