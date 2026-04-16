# Changelog

## [2.2.15] — 2026-04-17 — Timeout Flag Env Alias Hotfix

### 🩹 Runtime Flag Compatibility Fix
- Updated `Bismillah/app/trading_mode.py` timeout feature-flag loading to accept both:
  - `SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED` (primary), and
  - `SCALPING_TIMEOUT_PROTECTION_ENABLED` (legacy/ops alias fallback).
- This fixes cases where timeout protection remained disabled even after enabling the flag in `.env` under the legacy name.

## [2.2.14] — 2026-04-17 — Timeout-Loss Reduction (Dynamic Pre-Timeout Protection, Flagged)

### ⏱️ Timeout Protection Layer (Scalping)
- Added runtime-flagged timeout protection policy in `Bismillah/app/scalping_engine.py`:
  - phase checkpoints: `early` / `mid` / `late` based on time-in-trade,
  - mid/late breakeven promotion when unrealized move exceeds trigger,
  - soft trailing SL before forced timeout exits,
  - extra late-phase tightening for sideways positions.
- Added structured observability markers:
  - `timeout_protection_applied`
  - `timeout_exit_with_protection`
  - `timeout_exit_without_protection`
- Timeout close handlers now persist timeout-loss reasoning tags to DB (`loss_reasoning`) for KPI tracking.

### ⚙️ New Runtime Config Keys (Default Safe/Off)
- Added internal config knobs in `Bismillah/app/trading_mode.py`:
  - `adaptive_timeout_protection_enabled` (default `false`)
  - `timeout_be_trigger_pct`
  - `timeout_trailing_trigger_pct`
  - `timeout_late_tighten_multiplier`
  - `timeout_protection_min_update_seconds`
  - `timeout_near_flat_usdt_threshold`

### 📊 Daily Report KPI Expansion
- Updated `Bismillah/app/admin_daily_report.py` with timeout-specific metrics:
  - timeout loss count/rate,
  - timeout loss PnL + avg timeout loss,
  - timeout protection effectiveness (% near-flat among protected timeout exits).

### ✅ Tests
- Added `tests/test_timeout_protection_policy.py`:
  - timeout phase boundary checks,
  - breakeven/trailing SL activation in mid-phase favorable scenario.

## [2.2.13] — 2026-04-17 — Global Win Playbook + Runtime Risk Overlay (v4.0)

### 🏆 Win Playbook Subsystem (Global)
- Added `Bismillah/app/win_playbook.py`:
  - builds global playbook from recent strategy outcomes (same learning horizon pattern as adaptive controller),
  - normalizes/filters noisy reasons and computes tag support, win-rate, and lift,
  - activates positive-lift tags with minimum support,
  - computes deterministic `playbook_match_score` and matched tags for candidate signals.
- Refresh cadence integrated at 10 minutes in both Swing and Scalping loops.

### 📈 Runtime Risk Overlay (All Users, Runtime-Only)
- Added global runtime overlay logic:
  - `risk_overlay_pct` runtime state in `[0, +5]`,
  - `effective_risk_pct = min(10, base_risk_pct + risk_overlay_pct)`.
- Ramp-up only on strong playbook match with healthy guardrails:
  - rolling win rate >= 75%,
  - rolling expectancy > 0.
- Gradual brake-down when guardrails weaken (stepwise, not instant reset).
- Overlay applies to position sizing only; signal-quality gates remain unchanged.

### ⚙️ Engine Integration (Swing + Scalping)
- `Bismillah/app/autotrade_engine.py`:
  - candidate scoring now includes playbook match snapshot,
  - execution path computes runtime effective risk and feeds it into risk-based qty sizing,
  - profitable close paths now persist win metadata (`win_reasoning`, tags, playbook score, risk snapshot),
  - flip path now uses the same runtime risk overlay sizing pipeline.
- `Bismillah/app/scalping_engine.py`:
  - open-trade rows now always persist `entry_reasons`,
  - playbook + overlay evaluation applied before qty sizing,
  - sizing helper now accepts explicit `effective_risk_pct_override`,
  - close pipeline now writes consistent close reason + win reasoning/tags for profitable TP closures.

### 🧾 Durable Win Reason Tracking
- `Bismillah/app/trade_history.py`:
  - added `build_win_reasoning(...)` (parallel to existing loss reasoning),
  - extended `save_trade_close(...)` with optional win metadata payload and auto-win-reason generation for profitable TP/flip closes,
  - extended `save_trade_open(...)` to store execution metadata snapshot.
- `Bismillah/app/stackmentor.py`:
  - TP/TP3 close updates now set `close_reason` consistently,
  - TP/TP3 close updates now persist win reasoning + matched playbook tags + risk snapshot fields.

### 🗄️ Schema
- Added migration `db/add_win_playbook_fields.sql` for `autotrade_trades`:
  - `win_reasoning text`
  - `win_reason_tags jsonb default '[]'`
  - `playbook_match_score numeric(6,3)`
  - `effective_risk_pct numeric(6,3)`
  - `risk_overlay_pct numeric(6,3)`
- Updated base schema definition in `db/autotrade_trades.sql` with the same fields.

### 👀 Admin Visibility
- `Bismillah/app/admin_daily_report.py` now includes Win Playbook section:
  - active playbook tags (top contributors),
  - current runtime overlay and effective risk bounds,
  - win-reason coverage on winners,
  - playbook-matched wins vs non-matched wins KPI.

### ✅ Tests
- Added `tests/test_win_playbook.py`:
  - tag activation + noise filtering,
  - match-score determinism,
  - risk ramp/brake behavior and cap enforcement.
- Added `tests/test_trade_history_win_reasoning.py` for win reasoning composition.

## [2.2.12] — 2026-04-16 — Unified Auto Max-Safe Leverage Compliance

### ⚙️ Canonical Leverage Policy
- Added `Bismillah/app/leverage_policy.py` with canonical function:
  - `get_auto_max_safe_leverage(symbol, entry_price=None, sl_price=None, baseline_leverage=None) -> int`
- `Bismillah/app/position_sizing.py` now delegates leverage selection to canonical policy.

### 🤖 Engine Alignment (Production + Whitelabel + SMC)
- `Bismillah/app/autotrade_engine.py`:
  - swing flip/reversal path now uses auto max-safe leverage for qty sizing + `set_leverage` + trade history + notifications.
  - standardized leverage observability log markers (`leverage_mode=auto_max_safe`).
- `Bismillah/app/scalping_engine.py`:
  - entry path now uses canonical policy with standardized leverage observability logs.
- `Whitelabel #1/app/autotrade_engine.py`:
  - regular entries and flip/reversal entries now use canonical auto max-safe leverage end-to-end.
- `smc_trading_engine/app/services/trade_service.py`:
  - order requests now use canonical auto max-safe leverage instead of direct `default_leverage`.

### 🌐 One-Click Web Alignment
- `website-backend/app/routes/signals.py`:
  - removed local leverage map drift.
  - one-click execution now derives leverage from canonical policy while preserving existing response fields:
    - `leverage`, `leverage_mode`, `baseline_leverage`.

### ✅ Tests
- Added `tests/test_leverage_policy.py`:
  - known-symbol max-safe mapping
  - unknown-symbol fallback
  - baseline metadata does not override effective policy

## [2.2.11] — 2026-04-16 — Scalping Runtime Compatibility Guard (`tp_price`)

### 🛠️ Fix
- Updated `Bismillah/app/scalping_engine.py` to harden unified entry call against mixed runtime signatures:
  - Added `_open_managed_position_safe(...)` wrapper.
  - If runtime raises `TypeError: unexpected keyword argument 'tp_price'`, engine now retries `open_managed_position(...)` without `tp_price` and logs a compatibility warning.
- This prevents repeated entry-path failures that could cascade into persistent `blocked_pending_order` skips during version skew or stale runtime code windows.

### ✅ Verification
- Compile/syntax pass:
  - `python -m py_compile Bismillah/app/scalping_engine.py Bismillah/app/symbol_coordinator.py Bismillah/app/autotrade_engine.py`

## [2.2.10] — 2026-04-16 — Pending-Lock Self-Healing + Restart Serialization

### 🛡️ Coordinator Hardening (`blocked_pending_order`)
- Updated `Bismillah/app/symbol_coordinator.py` with stale-pending metadata and self-healing:
  - `pending_since_ts`, `pending_owner`, `pending_set_by_task_id`, `last_pending_clear_reason`
  - `can_enter()` now auto-clears pending locks older than 90s when no position exists
  - added user-scoped cleanup helpers for restart/startup sanitization:
    - `clear_stale_pending_for_user(...)`
    - `clear_pending_if_no_position(...)`
    - `clear_all_pending_without_position_for_user(...)`
- Added structured coordinator logs:
  - `blocked_pending_order_active`
  - `blocked_pending_order_stale_cleared`

### 🔄 Engine Lifecycle Race Fix
- `Bismillah/app/autotrade_engine.py`:
  - added serialized async lifecycle with per-user locks:
    - `start_engine_async(...)`
    - `stop_engine_async(...)`
  - stop path now cancels + awaits old task, then clears pending-only locks before restart.
  - preserved sync wrappers (`start_engine`, `stop_engine`) for compatibility.
- Restart callpaths now use serialized async start/stop:
  - `Bismillah/app/scheduler.py`
  - `Bismillah/app/handlers_autotrade.py`
  - `Bismillah/app/trading_mode_manager.py`
  - `Bismillah/app/engine_restore.py`

### 🚦 Startup Sanitization + UX Dedupe
- Startup pending cleanup added before scanning in:
  - swing loop (`autotrade_engine`)
  - scalping loop (`scalping_engine`)
- Repeated `blocked_pending_order` user alerts are now deduped per symbol for 10 minutes (logs remain complete).

### ✅ Tests
- Extended `tests/test_coordinator.py`:
  - stale-pending auto-expiry (>90s) behavior
  - no auto-expiry when position is open
  - restart cleanup clears only pending-without-position symbols

## [2.2.9] — 2026-04-16 — Dynamic Top-10 Volume Routing + Equity Messaging Alignment

### 📈 Dynamic Pair Universe (Bitunix `quoteVol`)
- Added `Bismillah/app/volume_pair_selector.py`:
  - Pulls futures tickers from `GET /api/v1/futures/market/tickers`
  - Filters tradable `*USDT` pairs
  - Sorts by `quoteVol` (descending)
  - Returns top-10 ranked symbols (highest volume first)
- Selector includes safe runtime controls:
  - 5-minute refresh TTL cache
  - fallback priority: last-good cache → bootstrap list
  - structured refresh/fallback logs with source + error

### ⚙️ Engine Integration
- `Bismillah/app/autotrade_engine.py`
  - Swing scan universe now uses live top-10 volume pairs at runtime.
  - Candidate queue priority updated: `volume_rank` first, then confidence, then RR.
  - Queue ordering and processing now follow highest-volume-first focus.
- `Bismillah/app/scalping_engine.py`
  - Scan universe now uses the same shared top-10 volume selector.
  - Startup + scan logs now reflect top-volume dynamic pair routing.
  - Allowed-symbol validation follows current active top-volume set.

### 💬 Equity Wording / Startup Messaging
- Replaced user-facing “Capital” semantics with “Equity” across autotrade startup/status/risk text where account-value semantics are intended.
- `Bismillah/app/scheduler.py` startup/restart notifications now show:
  - `Equity` sourced from live exchange account data (`available + frozen + unrealized`)
  - trading universe label: `Top 10 by volume`
- Updated mode switch copy in `Bismillah/app/handlers_autotrade.py` from fixed `Top 15` to dynamic `Top 10 by volume`.

### ✅ Tests
- Added `tests/test_volume_pair_selector.py`:
  - descending sort correctness on `quoteVol`
  - cache fallback behavior on API failure
  - bootstrap fallback behavior when cache is unavailable

## [2.2.8] — 2026-04-16 — Adaptive Confluence v1 (Global Controller + Outcome Taxonomy)

### 🧠 Adaptive Confluence Controller (Global, Balanced Objective)
- Added `Bismillah/app/adaptive_confluence.py`:
  - Normalizes trade outcomes into: `strategy_loss`, `strategy_win`, `timeout_exit`, `ops_reconcile`
  - Builds rolling metrics from closed trades (strategy-loss rate, weak-confluence loss shares, trades/day)
  - Computes bounded adaptive overlays:
    - `conf_delta` (range `-3..+8`)
    - `volume_min_ratio_delta` (range `0.0..0.4`)
    - `ob_fvg_requirement_mode` (`soft` / `required_when_risk_high`)
  - Enforces safety controls:
    - update interval rate-limit: 6h
    - capped step-size per adaptation cycle
    - conservative fallback defaults when sample is insufficient

### ⚙️ Engine Integration (Global-first)
- `Bismillah/app/autotrade_engine.py`
  - Added periodic adaptive refresh (every 10 min, best-effort).
  - Applies adaptive overlay to scan confidence threshold and volume strictness.
  - Extends signal pipeline with adaptive-aware gates:
    - dynamic internal min confidence (risk-profile + adaptive delta)
    - high-risk borderline entries can require OB/FVG confluence.
- `Bismillah/app/scalping_engine.py`
  - Added periodic adaptive refresh (every 10 min, best-effort).
  - Applies adaptive confidence and volume gates in `validate_scalping_entry` for trending + sideways paths.
  - Startup message now includes active adaptive deltas.

### 📊 Admin Visibility
- `Bismillah/app/admin_daily_report.py`
  - Added 24h strategy vs ops closure taxonomy section.
  - Added active adaptive thresholds snapshot.
  - Added 7-day trend metrics:
    - strategy loss rate
    - strategy trades/day.

### 🗄️ Data Interface
- Added migration file: `db/add_adaptive_config_state.sql`
  - Defines singleton table `adaptive_config_state` for global adaptive state persistence.

### ✅ Tests
- Added `tests/test_adaptive_confluence.py` covering:
  - outcome classification correctness (including status-only rows)
  - ops/reconcile exclusion from strategy-loss learning
  - controller tighten/relax behavior based on synthetic metrics.

## [2.2.7] — 2026-04-16 — Scalping SL/TP Risk-Reward Consistency Fix

### 🛡️ Scalping Risk Management Consistency
- Fixed a critical RR drift path where entry validation could mutate SL against live mark price while keeping TP unchanged.
  - This could produce executed trades with mismatched TP/SL RR versus pre-trade risk sizing.
  - New behavior: invalid SL/TP vs mark now **fails fast** (`invalid_prices`) instead of auto-adjusting SL.

### 🎯 Execution-Level TP Alignment
- Updated unified execution path to support explicit TP passthrough from strategy signal:
  - `open_managed_position(..., tp_price=...)` now honors signal TP when provided.
  - Scalping engine now passes `signal.tp_price` into execution, so validated RR matches placed TP/SL.

### 📣 Notification Accuracy
- Updated scalping open notification text to display computed live RR from actual entry/TP/SL instead of hardcoded `1.5R`.

### 🗂️ Files Updated
- `Bismillah/app/trade_execution.py`
- `Bismillah/app/scalping_engine.py`

## [2.2.6] — 2026-04-16 — Onboarding Group Invite Follow-Up

### 🤖 Telegram Onboarding UX
- Updated onboarding flow to consistently include Telegram group join as the next step:
  - Added Step 4 in onboarding copy: **Join CryptoMentor x Bitunix Group**
  - Added button in onboarding paths: `👥 Join CryptoMentor x Bitunix Group`
  - Added same group step/button in `VER_REJECTED` path for consistency.

### 📩 New Post-Onboarding Follow-Up Message
- Added dedicated follow-up message sent to users after onboarding milestones:
  - After UID submission via bot (`process_uid_input_bot`)
  - After admin approval of UID (`callback_uid_acc`)
- Message includes CTA button to join group:
  - URL source: `exchange_registry.bitunix.group_url`
  - Fallback: `BITUNIX_GROUP_URL` env var.

### 🗂️ Files Updated
- `Bismillah/app/handlers_autotrade.py`
- `Bismillah/app/handlers_autotrade_admin.py`

## [2.2.5] — 2026-04-16 — Pending-Lock Reliability Fix + Scalping Pair Standardization (15 Pairs)

### 🛡️ Engine Reliability (Coordinator Pending Lock)
- **Fixed stale `blocked_pending_order` lock paths** in both engines so symbols do not remain falsely blocked after failed/aborted entries.
  - `Bismillah/app/autotrade_engine.py`
    - Added pending lifecycle guard and cleanup on:
      - TP-validation skip paths (pre-order abort)
      - unexpected loop exceptions
      - cancellation paths
  - `Bismillah/app/scalping_engine.py`
    - Added pending lifecycle guard and cleanup on:
      - terminal timeout/exception retry exhaustion
      - all terminal failure exits
      - preserved pending state correctly on successful open

### 💹 PnL Accounting & Trade Close Consistency
- Added `get_roundtrip_financials()` to `Bismillah/app/bitunix_autotrade_client.py`:
  - best-effort retrieval of close realized PnL from Bitunix history orders
  - fee-aware net PnL computation: `net = close_realized_pnl - open_fee - close_fee`
  - includes open/close leg resolution and optional avg open/close prices.
- Updated `Bismillah/app/trade_history.py`:
  - `save_trade_close()` now also persists `close_reason` field explicitly when closing a trade.

### 📊 Trading Pair Standard
- **Scalping runtime standard set to 15 pairs** (aligned with startup messaging standard).
  - Updated `Bismillah/app/trading_mode.py` `ScalpingConfig.pairs` by adding:
    - `CLUSDT`
    - `QQQUSDT`
  - Runtime verification result: `PAIR_COUNT=15`.

### 🚀 Ops / Deployment Notes (2026-04-16)
- Restarted bot/engine worker service on VPS:
  - `systemctl restart cryptomentor`
  - Service status verified: `active/running`.
- Deployed updated `trading_mode.py` to VPS and re-verified live runtime pair count = 15.
- Executed targeted Telegram promo broadcast to **non-verified** users:
  - Targeted: `212`
  - Sent: `66`
  - Failed: `146`
  - Blocked/Forbidden subset: `42`

## [2.2.4] — 2026-04-15 — Confidence & Startup Message Accuracy + Single Notification Flow

### 🎯 Signal & Mode Accuracy
- **Scalping Confidence Updated**: lowered scalping minimum confidence from **80%** to **72%**.
  - Updated in `Bismillah/app/trading_mode.py` and reflected in `Bismillah/app/scalping_engine.py`.

- **Dynamic Threshold Display (Per User/Mode)**:
  - **Scalping** startup/mode message now displays the live configured threshold (72%).
  - **Swing/AutoTrade** startup/mode message now displays threshold derived from each user’s `risk_per_trade` profile (dynamic, not fixed 68%).
  - Implemented in:
    - `Bismillah/app/scheduler.py`
    - `Bismillah/app/handlers_autotrade.py`
    - `Bismillah/app/autotrade_engine.py`

### 📣 Notification UX Fixes
- **Leverage Message Clarified**:
  - Startup messages now show:
    - `Base leverage setting`
    - `Applied leverage is auto-adjusted per pair (max-safe)`
  - This removes misleading fixed-leverage wording and aligns with live execution behavior.

- **Duplicate Startup Message Removed**:
  - Users previously received 2 startup messages (scheduler + engine startup notification).
  - Scheduler-triggered engine starts now run with `silent=True`, preserving one consolidated startup message for both **Scalping** and **Swing** flows.

### ✅ Deploy Notes
1. Pushed to Ajax git (`main`): confidence + message accuracy + dedup startup notification.
2. VPS synced and bot service restarted.
3. Startup notifications now match actual runtime configuration and send as a single message.

## [2.2.3] — 2026-04-14 — Health-Check Status Restoration Fix

### 🛠️ Platform Stability
- **Graceful Error Recovery**: Updated health-check logic in `handlers_autotrade.py` and `scheduler.py` to restore user status to `uid_verified` (instead of a hard `stopped`) if their API key fails but their Bitunix UID is still approved.
  - **Goal**: Prevent users from being permanently "stopped" due to transient API key issues or rotation, allowing the system to resume once keys are updated.

## [2.2.2] — 2026-04-14 — Auto Max-Safe Leverage Enforcement

### 🛡️ Risk Management Optimization
- **Centralized Leverage Enforcement**: Implemented `calculate_max_safe_leverage` based on SL distance to dynamically maximize capital efficiency while preventing early liquidations.
  - **Goal**: Allow users to open trades safely using minimal required margin without violating the Stop Loss price buffer (15% safety bound for maintenance margin).
  - **Effect**: Deprecated the "Legacy baseline setting" (e.g. 10x/20x hardcoded limits) in favor of intelligent, dynamic leverage capping (up to exchange max 125x) calculated per-trade based on the precise entry/SL distance.

### ✅ Deploy Notes
1. Updated `Bismillah/app/position_sizing.py` to add `calculate_max_safe_leverage`.
2. Updated `Bismillah/app/scalping_engine.py` and `Bismillah/app/autotrade_engine.py` to remove hardcoded limits and pass `effective_leverage` properly to the risk calculation and `trade_execution` pipeline.
3. Live VPS codebase synchronized.

## [2.2.1] — 2026-04-14 — Signal Engine Sensitivity Patch

### 📡 Signal Engine Optimization
- **Decreased Threshold**: Lowered `MIN_CONFIDENCE` from 75% to **72%** in `app/autosignal_fast.py`.
  - **Goal**: Increase signal frequency during market consolidation by picking up high-probability setups previously filtered by the strict 75% floor.
  - **Effect**: More frequent broadcasts for top 25 CMC coins while maintaining a significant confidence gap over random noise.

### ✅ Deploy Notes
1. Updated `Bismillah/app/autosignal_fast.py`
2. Bot restart required to reload global constant in memory.
3. Pushed to Ajax Git for live redeployment.


## [2.2.0] — 2026-04-14 — 🎯 Multi-User Coordination, Real-Time Analytics, Position Ownership Tracking

**Major Milestone**: Implemented comprehensive multi-user, multi-symbol position coordination system ensuring single active strategy owner per (user_id, symbol) pair, plus real-time observability dashboard for admin monitoring.

### 🎯 Core Changes

#### 1) Multi-User Symbol Coordination System
- **New Module**: `Bismillah/app/symbol_coordinator.py` (591 lines)
  - `MultiUserSymbolCoordinator` class manages position ownership across SWING, SCALP, ONE_CLICK, MANUAL strategies
  - `StrategyOwner` enum: NONE, SCALP, SWING, ONE_CLICK, MANUAL, UNKNOWN
  - `PositionSide` enum: NONE, LONG, SHORT
  - `SymbolState` dataclass: tracks ownership, position metadata, pending orders, cooldowns
  - Per-(user_id, symbol) asyncio.Lock ensures thread-safe concurrent access
  - 5-minute cooldown after position close prevents immediate re-entry

- **Core Methods**:
  - `can_enter()`: Gate before order submission (blocks if another strategy owns symbol)
  - `set_pending()`: Mark strategy intent before order submission
  - `confirm_open()`: Lock ownership after successful execution
  - `confirm_closed()`: Release ownership when position closes
  - `reconcile_user()`: Restore state on startup from exchange positions + DB hints
  - `export_debug_snapshot()`: Admin observability snapshot
  - `force_reset_symbol()`: Admin emergency override

- **Safety Features**:
  - UNKNOWN owner state blocks all automation (orphaned position protection)
  - Reversals allowed: same strategy can re-enter during reversal without explicit close
  - Multi-user isolation: User A's BTC swing doesn't affect User B's BTC
  - Multi-symbol independence: User A's BTC swing doesn't block User A's ETH scalp

#### 2) Coordinator Integration Across All Engines

- **Swing/AutoTrade Engine** (`Bismillah/app/autotrade_engine.py`):
  - Added can_enter() gate before set_leverage + place_order_with_tpsl
  - Added set_pending() on allowed entry
  - Added confirm_open() after successful order execution
  - Added confirm_closed() after position close (TP/SL/flip)
  - Non-blocking: failed gates notify user but don't crash engine

- **Scalping Engine** (`Bismillah/app/scalping_engine.py`):
  - Added can_enter() gate before open_managed_position
  - Added set_pending() on allowed entry
  - Added confirm_open() after position creation
  - Added clear_pending() in all error paths
  - Added confirm_closed() in all close methods:
    - `_close_position_max_hold()` (30min max hold)
    - `_close_sideways_max_hold()` (2min sideways max hold)
    - `_close_position_tp()` (take profit)
    - `_close_position_sl()` (stop loss)

- **Engine Restore** (`Bismillah/app/engine_restore.py`):
  - Added `reconcile_coordinator_state()` function
  - Calls coordinator.reconcile_user() with:
    - Live exchange positions (via client.get_open_positions)
    - DB open trades (strategy hints for ownership inference)
  - Scheduled as background task on engine startup
  - Ensures coordinator state matches actual positions after bot restart

- **StackMentor** (`Bismillah/app/stackmentor.py`):
  - Added confirm_closed() in handle_tp1_hit() when position closes
  - Coordinator state synced with TP/SL hit events

#### 3) Real-Time Analytics Dashboard & API

- **Analytics Backend API** (`Bismillah/analytics_api.py`, 517 lines):
  - FastAPI app on port 8896 (analytics4896.cryptomentor.id)
  - Admin-only JWT authentication (validates against ADMIN_ALLOWLIST from bot.py)
  - Rate limiting: 100 req/minute per authenticated admin
  - CORS enabled for frontend dashboard
  - Real data pulled from DB and coordinator (never faked)

- **Analytics Endpoints**:
  - `GET /health`: Health check (no auth required)
  - `GET /api/analytics/coordinator-state`: Symbol ownership and position state
    - Shows SWING/SCALP/UNKNOWN/etc owners per user+symbol
    - Tracks pending orders, cooldowns, position metadata
    - Filterable by user_id and symbol
  - `GET /api/analytics/trading-stats`: Trading performance analytics
    - Win rate, total PnL, trade duration statistics
    - Daily aggregations for last N days
    - Open/closed position counts per user
  - `GET /api/analytics/engine-health`: Engine status and error tracking
    - Running/stopped status per user
    - 24h error count from error logs
    - Strategy mode detection

- **Analytics Frontend Dashboard** (`Bismillah/analytics_dashboard.html`, 661 lines):
  - Modern dark theme with neon (#00ff88) aesthetics
  - Admin JWT authentication (token reused from API)
  - Responsive design: desktop, tablet, mobile
  - Three main panels: Coordination State, Engine Health, Trading Performance
  - Interactive filtering by user ID and symbol
  - Auto-refresh every 30 seconds + manual refresh
  - Detailed table view of all coordinator states
  - Local storage caching of JWT token
  - Smooth animations and hover effects

#### 4) Test Coverage

- **Coordinator Unit Tests** (`tests/test_coordinator.py`, 16.6 KB):
  - 20 comprehensive tests covering:
    - Entry gating (9 tests): fresh symbols, pending orders, strategy conflicts, multi-user/symbol isolation, UNKNOWN blocking, cooldown, reversals
    - Pending order lifecycle (2 tests): mark/clear with owner preservation
    - Position lifecycle (3 tests): open with metadata, close with cooldown, pending flag clearing
    - Reconciliation (3 tests): with DB hints, orphaned positions, multiple positions
    - Concurrency (2 tests): parallel ops on different symbols, serialized same-symbol
    - Debug export (1 test): snapshot generation
  - All 20 tests passing

- **Non-Regression Tests** (`tests/test_regression.py`, 386 lines):
  - Ensures coordinator integration doesn't break existing behavior
  - Risk calculation tests: qty calculations, exposure limits, edge cases
  - Signal generation tests: confidence thresholds, same-direction rejection
  - Trade execution tests: StackMentor levels, LONG/SHORT handling
  - StackMentor tracking tests: registration, removal, lifecycle
  - Scalping engine tests: config defaults, position creation, cooldown
  - Engine loop tests: cooldown expiration, trade history, daily stats
  - Error handling tests: graceful failures, exception handling
  - All tests use pytest + asyncio + mocks

### ✅ Required Actions After Deploy

1. **Database Setup**:
   - No schema changes needed (coordinator is in-memory)
   - Ensure error_logs table exists for analytics engine-health endpoint

2. **Environment Variables**:
   - Ensure ADMIN_IDS, ADMIN1-5 are set (used by both bot and analytics API)
   - Set JWT_SECRET if custom JWT validation needed (default: "analytics-secret-key")

3. **Deploy & Restart**:
   - Deploy new files:
     - Bismillah/app/symbol_coordinator.py
     - Bismillah/analytics_api.py
     - Bismillah/analytics_dashboard.html (serve from web server)
   - Restart Telegram bot (uses updated autotrade_engine.py, scalping_engine.py, engine_restore.py)
   - Start analytics API: `uvicorn Bismillah.analytics_api:app --host 0.0.0.0 --port 8896`

4. **Smoke Tests**:
   - Verify no two SWING positions on same (user, symbol)
   - Verify SCALP blocks SWING on same (user, symbol) and vice versa
   - Verify reversals still work (same strategy can re-enter)
   - Verify multi-user isolation (User A's swing doesn't affect User B)
   - Verify analytics dashboard authenticates with admin token
   - Verify coordinator state snapshot shows correct ownership
   - Run non-regression tests: `pytest tests/test_regression.py -v`

### 📊 Statistics

- **Lines Added**: ~3,500 (coordinator + analytics + tests)
- **New Files**: 4 (coordinator, analytics_api, analytics_dashboard, test_regression)
- **Modified Files**: 4 (autotrade_engine, scalping_engine, engine_restore, stackmentor)
- **Git Commits**: 6 (Phase 2B-2F + Phase 3-4 + Phase 6)
- **Test Coverage**: 40 tests covering coordinator and regression

### 🚀 Performance Impact

- **Minimal**: Coordinator is in-memory async-safe with per-symbol locks
  - Lock contention only on same (user_id, symbol) pairs
  - No DB calls in critical path
  - Analytics API is separate and doesn't block trading engines

- **Memory**: ~1KB per (user_id, symbol) position + metadata (~100 bytes overhead per symbol)

## [2.1.2] — 2026-04-11 — Dashboard Stability, Notification UX, Trade Audio Cues, Data Accuracy

### 🚀 What Changed

#### 1) Dashboard Access and Rendering Stability
- Fixed dashboard render blocker caused by missing `riskSettings` wiring in frontend tabs.
- Added safer defaults and session boot error handling to avoid blank/indefinite loading states.
- Improved verification/session resilience in web login flow and gatekeeper transitions.

#### 2) Portfolio/Engine Risk UI Cleanup
- Removed duplicate **Risk Management** card from Engine Controls.
- Removed Risk Management block from Portfolio Status to prevent layout collisions.
- Kept single canonical risk control surface in Engine Controls.

#### 3) Responsive Layout Hardening
- Fixed resize/overflow issues in Portfolio Status:
  - Better wrapping behavior for header controls.
  - Safer flex shrink behavior (`min-w-0`) in main content.
  - Grid breakpoint tuning to prevent card clipping on medium widths.
  - Horizontal overflow guards added to root/main containers.

#### 4) Branding Update
- Replaced Bitunix branding image with `bitunix.jpg` and updated rendered card usage.

#### 5) Trade Notifications (Telegram, Professional Format)
- Added admin-triggerable web endpoint to send sample trade notifications:
  - `POST /dashboard/admin/broadcast-sample-trades`
  - Supports **trade opened** + **trade closed** messages.
  - Professional emoji-rich formatting and CTA button.
  - Added optional `target_chat_id` for single-user test sends before mass broadcast.
- Sent verified sample open/close notifications to Telegram user `1187119989`.

#### 6) Realized PnL / Closed Trades Accuracy Fix
- Fixed backend trade aggregation that incorrectly filtered only `status = closed`.
- Updated portfolio/performance/leaderboard queries to include real close variants:
  - `closed_tp`, `closed_sl`, `closed_tp1`, `closed_tp2`, `closed_tp3`, `closed_flip`, `closed_manual`.
- Result: 30D realized PnL and closed trade counts now reflect real engine outcomes.

#### 7) Web Sound Effects for Trade Lifecycle
- Added browser-side audio cues in dashboard:
  - Trade Open: ascending chime.
  - Trade Close: descending confirmation tone.
- Implemented with Web Audio API and live position diff detection from polling.
- Includes user-interaction unlock handling for browser autoplay restrictions.

### ✅ Deploy/Verification Notes

1. Frontend was rebuilt and redeployed multiple times with final responsive + audio updates.
2. Backend (`cryptomentor-web.service`) was restarted with notification and PnL-status fixes.
3. Telegram sample notification delivery to `1187119989` returned Telegram API `ok: true` for both open and close messages.

## [2.1.1] — 2026-04-10 — Unified Verification, Anti-Flip Stabilization, StackMentor 1:3, UI Hardening

### 🚀 What Changed

#### 1) Unified Bitunix UID Verification (single source of truth)
- Added centralized verification table migration:
  - `db/verification_access_control.sql`
  - New `user_verifications` with statuses: `pending | approved | rejected`
  - Added indexes, trigger-managed `updated_at`, RLS policies, and legacy backfill from `autotrade_sessions`
- Backend verification routes now use `user_verifications`:
  - `website-backend/app/routes/user.py`
  - Web UID submission writes `pending` + sends Telegram admin inline action buttons
- Verification guard now enforces strict `approved` access only:
  - `website-backend/app/middleware/verification_guard.py`
  - Changed behavior to fail-closed when verification lookup fails (prevents accidental bypass)
- Telegram admin approval handlers now update centralized verification status + admin audit fields:
  - `Bismillah/app/handlers_autotrade_admin.py`
- Telegram UID submit flow now writes to centralized verification and includes inline approve/reject keyboard:
  - `Bismillah/app/handlers_autotrade.py`

#### 2) Anti-Flip / Churn Control for Sideways Trades
- Added stability and anti-flip controls in scalping:
  - `Bismillah/app/scalping_engine.py`
  - Added close dedupe protection, close-lock guard, and idempotent close write path
  - Added consecutive signal confirmation gate before entry
  - Added opposite-direction re-entry block window after close
- Added config knobs:
  - `Bismillah/app/trading_mode.py`
  - `sideways_reentry_cooldown_seconds`
  - `anti_flip_opposite_seconds`
  - `signal_confirmations_required`
  - `signal_confirmation_max_gap_seconds`

#### 3) StackMentor Risk Model Update: Fixed 1:3
- Updated StackMentor to unified fixed target model:
  - `Bismillah/app/stackmentor.py`
  - All trades now target fixed `R:R 1:3`
  - Full position closes at TP (100% at TP1), compatibility fields retained (`tp2/tp3 = tp1`, `qty_tp2/qty_tp3 = 0`)
  - TP hit now finalizes trade status as `closed_tp`

#### 4) Frontend UI Updates
- Added Bitunix logo to API Management/API Bridges card:
  - `website-frontend/src/assets/bitunix-logo.png`
  - `website-frontend/src/App.jsx`
- Disabled unfinished tabs from sidebar and content routing:
  - Performance
  - Skills & Education
  - File: `website-frontend/src/App.jsx`

### ✅ Required Actions After Deploy

1. Run SQL migration in Supabase:
   - `db/verification_access_control.sql`
2. Ensure env vars are set and correct:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `ADMIN_IDS`
3. Redeploy/restart all runtime processes:
   - Telegram bot process
   - Backend API process
   - Frontend app
4. Smoke-test verification flow:
   - Submit UID via web and Telegram -> status becomes `pending`
   - Approve/reject via Telegram admin button -> status updates immediately in Supabase
   - Web trading endpoints allow only `approved`
5. Smoke-test anti-flip behavior:
   - Confirm no rapid opposite-direction re-entry on same symbol within configured block window
6. Smoke-test StackMentor:
   - New trades should show fixed `1:3` target behavior and full close on TP

## [2.1.0] — 2026-04-10 — 🚀 Phase 1 & 2 Migration: Bot Gatekeeper & Pro Money Management

**Major Milestone**: Successfully transitioned the Telegram bot from a primary trading interface to a **Web-Dashboard-first Gatekeeper**. All trading features, configuration, and identity verification are now centralized on the web, with the bot serving as a secure onboarding and notification bridge.

### 🚀 Core Changes

#### 🔥 Bot-to-Web Transformation (`Bismillah/`)
- **Refacted Handlers**: `handlers_autotrade.py` converted into a tight **Gatekeeper Flow** (Verified, Pending, Unverified).
- **Simplified Menus**: Telegram menu (`menu_system.py`) reduced to a 3-button model focused on the Web Dashboard.
- **Auto-Login URLs**: Created `app/lib/auth.py` to generate secure JWT-based URLs for seamless bot-to-web redirection.
- **Retired Features**: Manual signals, AI market analysis, and education commands now redirect users to the web dashboard.

#### 🔥 Identity Verification & Security
- **UID Submission**: Native bot-based flow for Bitunix UID submission.
- **Admin Verification**: New `handlers_autotrade_admin.py` allows admins to approve/reject UIDs with one click inside Telegram.
- **Verification Guard**: New backend middleware blocks unverified users from all trading-related endpoints.

#### 🔥 Professional Money Management (Phase 2)
- **Engine Hardening**: `scalping_engine.py` now strictly honors database-persisted **Leverage (1x-20x)** and **Margin Mode (Cross/Isolated)**.
- **Rich Frontend Controls**: Added unified `RiskManagementCard` to the dashboard for fine-grained risk control.
- **Live Equity Sizing**: Risk per trade is now calculated against live Bitunix account equity (Wallet + Unrealized PnL).

#### 🔥 Enhanced Onboarding Flow
- **Onboarding Wizard**: New step-by-step registration and API setup wizard for verified users.
- **Verification Gates**: Frontend screens for UID submission and pending verification status.
- **Referral Integration**: Integrated Bitunix VIP code `sq45` directly into the onboarding registration prompts.

### 🌍 Localization & UX
- Translated Telegram bot welcome screens and onboarding messages to English for global support.
- Added live profit tickers and social proof components to the web dashboard.
- Consolidated bot command responses with consistent redirect messaging.

### Why
- Better UX — web interface is richer than inline keyboards
- Unified platform — one place for all trading management
- Easier maintenance — no duplicate feature implementations
- Aligns with the Bitunix Community Bot model

### What Users Should Do
Use the **web dashboard** for all trading features:
- Portfolio & open positions
- Engine start/stop controls
- Signals & market analysis
- Risk, leverage & margin settings
- Performance metrics & trade history
- API key management

---
*Generated by Antigravity AI*
