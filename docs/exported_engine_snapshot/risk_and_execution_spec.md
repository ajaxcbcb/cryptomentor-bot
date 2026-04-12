# Risk and Execution Spec (Current Code Snapshot)

## Scope

- Swing engine: `Bismillah/app/autotrade_engine.py`
- Scalping engine: `Bismillah/app/scalping_engine.py`
- Unified execution helper: `Bismillah/app/trade_execution.py`
- TP monitor: `Bismillah/app/stackmentor.py`
- Exchange adapter: `Bismillah/app/bitunix_autotrade_client.py`
- Web 1-click execution: `website-backend/app/routes/signals.py`, `website-backend/app/services/bitunix.py`

---

## 1) Position Sizing

### 1.1 Swing/autotrade sizing (`autotrade_engine._trade_loop -> calc_qty_with_risk`)

Confirmed from code:
- Uses live account equity model from `client.get_account_info()`:
  - `balance = available + frozen`
  - `equity = balance + total_unrealized_pnl`
- Risk amount: `risk_amount = equity * (risk_pct/100)`.
- Quantity: `position_size = risk_amount / abs(entry - sl)` then rounded by `QTY_PRECISION`.
- Margin guard: `margin_required <= balance * 0.95`, otherwise fails risk sizing.
- Fallback path: if risk sizing fails, uses fixed-margin legacy sizing `calc_qty(symbol, amount * leverage, entry)`.

Risk bounds:
- Runtime normalization in `autotrade_engine.py`:
  - `RISK_MIN_PCT=0.25`, `RISK_MAX_PCT=5.0`
  - `_normalize_risk_pct(...)` clamps to `[0.25, 5.0]`.

### 1.2 Scalping sizing (`ScalpingEngine.calculate_position_size_pro`)

Confirmed from code:
- Reads risk from DB (`supabase_repo.get_risk_per_trade`).
- Caps risk at 5% for scalping path.
- Caps leverage at 10x for scalping path.
- Uses `position_sizing.calculate_position_size(...)` for primary sizing.
- Additional safety cap: position value limited to <= 50% of balance (then reduced to 90% of cap).
- Fallback if risk sizing fails: "ultra-safe" 2% risk method + 20% capital cap.

### 1.3 Web 1-click sizing (`routes/signals.execute_signal`)

Confirmed from code:
- Uses account equity model for risk base:
  - `equity = available + total_unrealized_pnl` (as implemented there).
- Risk clamped to `[0.25, 5.0]`.
- Qty formula: `qty = (equity * risk_pct) / sl_distance / entry_price` (via position value route).
- Rejects `sl_distance_pct < 0.1%` or `> 15%`.
- Margin cap: required margin <= `balance * 0.95`.
- Adds UI risk zone:
  - `risk_zone="amber_red"` when `risk_pct > 1.0`.

---

## 2) Stops and Take Profit

## 2.1 On-entry TP/SL placement

Confirmed from code:
- Both swing and scalping use Bitunix market order with attached TP/SL through:
  - `BitunixAutoTradeClient.place_order_with_tpsl(...)`
  - fields `tpStopType="MARK_PRICE"`, `slStopType="MARK_PRICE"`.

## 2.2 Swing TP/SL construction

Confirmed from code:
- Confluence path (`_generate_confluence_signal`):
  - LONG: `sl = support - 0.5*ATR`, TP tiers scaled by ATR multiplier.
  - SHORT mirrored from resistance.
- Fallback `_compute_signal_pro` path:
  - `sl_dist = atr_1h * atr_sl_multiplier`
  - `tp1_dist = atr_1h * atr_tp1_multiplier`
  - `tp2_dist = atr_1h * atr_tp2_multiplier`.

## 2.3 Scalping TP/SL

Confirmed from code:
- Sideways path (`_try_sideways_signal`):
  - TP near 70% toward opposite range bound.
  - SL buffered by `0.75*ATR` (fallback 0.35% of price).
- Trending async fallback (`autosignal_async.compute_signal_scalping_async`):
  - `sl_distance = atr_5m * 1.5`
  - `tp_distance = sl_distance * 1.5`.

## 2.4 StackMentor behavior

Confirmed from code (`stackmentor.py`):
- Effective mode is unified single target:
  - config sets `tp1_pct=1.00`, `tp2_pct=0.00`, `tp3_pct=0.00`, target RR 1:3.
  - `calculate_qty_splits` returns all qty in TP1.
- Monitor checks TP1/TP2/TP3 functions still exist for compatibility, but TP2/TP3 qty is zero in unified mode.

---

## 3) Risk Gates and Vetoes

Confirmed from code:
- Signal confidence minimums (static + dynamic profile by risk in some branches).
- R:R minimum checks:
  - swing: minimum `ENGINE_CONFIG["min_rr_ratio"]` in fallback path.
  - sideways scalping: requires RR >= 1.0.
  - scalping general validation: `signal.rr_ratio >= config.min_rr`.
- Volatility filters:
  - ATR bounds in swing fallback and scalping validation.
- BTC market-leader filter (swing): altcoin skip when BTC bias strength too low.
- Position limits:
  - swing max concurrent from `ENGINE_CONFIG["max_concurrent"]`.
  - scalping max concurrent from `ScalpingConfig.max_concurrent_positions`.
- Cooldowns and anti-flip controls (scalping + swing reversal cooldowns).
- Sideway-specific forced max hold in scalping (2 minutes).
- General max hold in scalping (30 minutes).

Risk logic can veto valid signals:
- Confirmed yes. Even if a signal exists, validation/risk checks can reject before execution.

Position management can override fresh signals:
- Confirmed yes. Existing positions can force hold/close/flip logic paths before new entries.

---

## 4) Execution Decision Logic

## 4.1 Swing/autotrade

Confirmed from code:
1. Build candidate list from symbol scans.
2. Sort by `(confidence, rr_ratio)` descending.
3. Queue candidates and sync queue status to DB.
4. Pick next non-processing symbol.
5. Compute qty with risk sizing.
6. Validate SL/TP against current mark price.
7. Place order with TP/SL.
8. Persist, register monitor, notify, start WS PnL tracker.

## 4.2 Scalping

Confirmed from code:
1. Scan symbols concurrently.
2. Generate and validate signal.
3. Apply anti-flip gates.
4. Size position with capped-risk model.
5. Reject if qty below pair min qty.
6. Execute via `trade_execution.open_managed_position`.
7. Handle non-retryable vs retryable errors.

## 4.3 Web 1-click

Confirmed from code:
1. Verify signal freshness window.
2. Fetch live account and session risk/leverage.
3. Recompute live signal (`_live_signal` using ticker momentum builder).
4. Compute risk-based qty.
5. Place market with TP/SL through service wrapper.

---

## 5) Order Types and API Calls

Confirmed from code:
- Entry: market order via `/api/v1/futures/trade/place_order`.
- Attached TP/SL: same call with `tpPrice`/`slPrice` and mark-price stop type.
- Close/partial close: market reduce-only orders via `close_partial(...)`.
- TP/SL amendment: `/api/v1/futures/tpsl/position/modify_order`.

---

## 6) Slippage / Spread / Liquidity Protections

Confirmed from code:
- Mark-price-side validation before entry (SL/TP relation checks).
- SL auto-adjust by ±2% from mark if invalid side.
- Explicit small-sl/large-sl distance rejection in web 1-click execution.
- Scalping has helper `calculate_scalping_tp_sl` with slippage/spread buffer comments and math, but this helper is not the main live execution path.

Unclear from code:
- No explicit order-book liquidity depth filter in active execution path.
- No explicit spread cap gate in swing execution path.

---

## 7) Kill Switches / Circuit Breakers / Defensive Paths

Confirmed from code:
- Swing daily-loss tracker exists but comments indicate circuit breaker is disabled (monitoring only).
- Scalping has `_circuit_breaker_triggered` check against daily loss limit from DB/session model.
- Auth/IP blocked retry branches in swing execution (`TOKEN_INVALID`, `IP_BLOCKED`, 403 handling).
- Reconciliation-based defensive close in `trade_execution.reconcile_position` when live position cannot be repaired.

---

## 8) Flash Crash / Dislocation / Mark-vs-Last

Confirmed from code:
- Mark price is used for:
  - stop/TP validation,
  - trigger type on TP/SL,
  - many close/monitor checks.
- Last price appears as fallback in ticker response mapping.

Unclear from code:
- Dedicated "flash crash detector" is not found in core runtime path.
- Dedicated "dislocation detector" is not found in core runtime path.
- Dedicated "liquidity filter" is not found in core runtime path.
