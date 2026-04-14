# Changelog

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
- Sent verified sample open/close notifications to Telegram user `1234500009`.

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
3. Telegram sample notification delivery to `1234500009` returned Telegram API `ok: true` for both open and close messages.

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
