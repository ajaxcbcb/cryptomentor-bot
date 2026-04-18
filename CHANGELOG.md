# Changelog

## [2.2.54] — 2026-04-19 — Daily Report Live Equity Refresh + Balance Drift Backfill

### 💰 Live Equity in Admin Report
- Updated `Bismillah/app/admin_daily_report.py` to resolve per-user live equity using exchange account info:
  - `equity = available + frozen + unrealized`.
- Daily report active/stopped sections now display `Equity` instead of stale `Bal`.

### 🔄 DB Balance Drift Backfill
- During daily report generation, when live equity differs from `autotrade_sessions.current_balance`, the report flow now backfills:
  - `autotrade_sessions.current_balance = live_equity`
  - `updated_at = now()`
- This keeps control-plane snapshots closer to runtime reality, especially for stopped users with changed exchange equity.

### ⚙️ Safety + Performance
- Added bounded concurrency (`Semaphore(8)`) for report-time live equity hydration.
- Added graceful fallback to DB balance when API keys are missing or exchange calls fail.

### ✅ Validation
- `python -m py_compile Bismillah/app/admin_daily_report.py`

## [2.2.53] — 2026-04-19 — Web Engine Controls Rework (Auto/Mode/StackMentor)

### 🎛️ Engine Control API Wiring
- Added new dashboard control endpoints in `website-backend/app/routes/dashboard.py`:
  - `PUT /dashboard/engine/auto-mode`
  - `PUT /dashboard/engine/mode`
  - `PUT /dashboard/engine/stackmentor`
- Added shared engine-control helpers for:
  - normalized control-state payload shaping,
  - runtime-running detection with safe fallback,
  - live mode switch orchestration via `TradingModeManager.switch_mode(..., switch_source="manual")` when runtime is active.
- Mixed-mode lock behavior enforced:
  - mixed mode forces `auto_mode_enabled=false`,
  - response now includes lock metadata (`auto_mode_locked`, `auto_mode_lock_reason`).
- Stopped-engine mode changes are persist-only (`runtime_action="persisted_only"`), no implicit engine start.

### 🗄️ Session Schema + Payload Alignment
- Added migration: `db/add_stackmentor_enabled_and_mixed_mode.sql`
  - `autotrade_sessions.stackmentor_enabled BOOLEAN DEFAULT TRUE`
  - `chk_trading_mode` constraint now allows `mixed`.
- Updated `/dashboard/portfolio` engine payload:
  - added `stackmentor_enabled`,
  - added auto-mode lock metadata fields,
  - fixed `stackmentor_active` mapping to use stackmentor preference instead of `engine_active`.

### 🌐 Frontend Engine Controls (Immediate Apply)
- Updated `website-frontend/src/App.jsx` Engine Controls:
  - Auto Mode toggle now calls `PUT /dashboard/engine/auto-mode`.
  - Trading mode buttons now call `PUT /dashboard/engine/mode`.
  - StackMentor toggle now calls `PUT /dashboard/engine/stackmentor` (preference-only).
  - Added per-control loading states and inline error surface.
  - Mixed-mode UI explicitly shows auto-switch lock reason and disables auto toggle.
  - Mode buttons remain available only when Auto Mode is OFF.

### 🧭 Route Ambiguity Cleanup
- Removed duplicate `/dashboard/engine/*` registration path by removing `engine_router` inclusion from `website-backend/main.py`.
- Canonical web engine control path is now dashboard router implementation.

### 🧪 Tests
- Added targeted backend tests: `tests/test_dashboard_engine_controls.py`
  - mixed auto-mode forced OFF + lock,
  - stopped mode switch persist-only behavior,
  - running mode switch uses live switch path,
  - switching to mixed forces auto OFF,
  - StackMentor preference persistence.

## [2.2.52] — 2026-04-19 — Manual Admin Daily Report Trigger Command

### 📣 Admin Command
- Updated `Bismillah/bot.py` to add admin-only manual resend command:
  - `/daily_report_now`
  - alias `/dailyreport_now`
- New command calls existing `app.admin_daily_report.send_daily_report(...)` and returns in-chat success/failure status.

### 🛡️ Admin ID Consistency
- Expanded bot admin env key loader to include `ADMIN3` in `Bismillah/bot.py` for command-gate parity with report/admin flows.

### 📚 Help Text
- Updated `/help` admin command list to include `/daily_report_now`.

### ✅ Validation
- `python -m py_compile Bismillah/bot.py Bismillah/app/admin_daily_report.py`

## [2.2.51] — 2026-04-19 — Admin Daily Report Full Delivery (No Truncation)

### 📣 Telegram Admin Report Completeness
- Updated `Bismillah/app/admin_daily_report.py` so daily admin report is no longer intentionally truncated:
  - removed hard caps that previously limited sections (`stopped` to 10, `active` to 8, `new users` to 5).
  - report now includes full row listings for those sections.

### 🧩 Long Message Delivery Hardening
- Added line-safe chunking helper to avoid Telegram 4096-char failures:
  - new `_split_message_lines(...)` splits oversized reports into multiple messages while preserving readability.
  - continuation messages include `CryptoMentor Daily Report (Cont. x/y)` header.

### 🛡️ HTML Safety
- Added HTML escaping for dynamic user/symbol/mode fields in report lines to prevent malformed entity issues during `parse_mode='HTML'`.

### ✅ Validation
- `python -m py_compile Bismillah/app/admin_daily_report.py`

## [2.2.50] — 2026-04-18 — Mixed Runtime Callback Hardening + SOP Alignment

### 🎯 Telegram Callback Hardening
- Updated `Bismillah/app/handlers_autotrade.py` registration coverage so active callback buttons are routable in bot runtime:
  - mode menu + mixed selectors: `trading_mode_menu`, `mode_select_scalping`, `mode_select_swing`, `mode_select_mixed`
  - settings/risk controls: `at_settings`, `at_set_amount`, `at_set_leverage`, `at_set_margin`, `at_toggle_auto_mode`, `at_risk_settings`, `at_set_risk_*`, `at_risk_edu`, `at_risk_sim`
- Added missing callback handlers to remove dead paths:
  - `at_switch_risk_mode` now toggles persisted risk mode (`risk_based` ↔ `manual`)
  - `at_dashboard` now routes back to canonical gatekeeper dashboard flow (`/autotrade` equivalent callback path)
- Added legacy callback aliases still emitted by older flows:
  - `at_choose_risk_mode` (redirected to settings)
  - `at_lev_*` (mapped to leverage selection handler)

### 🛡️ Runtime Safety Follow-up
- Added missing imports in `Bismillah/app/handlers_autotrade.py` used by settings paths:
  - `get_risk_mode`, `get_risk_per_trade`, `set_risk_mode`
  - UI helpers `section_header`, `settings_group`
- Added explicit callback state constants for amount/leverage input flow safety:
  - `WAITING_NEW_AMOUNT`, `WAITING_NEW_LEVERAGE`, `WAITING_MANUAL_MARGIN`, `WAITING_LEVERAGE`
- Conversation states expanded for new amount/leverage text input handling (`WAITING_NEW_AMOUNT`, `WAITING_NEW_LEVERAGE`).

### ⚖️ Mixed Runtime + Risk/Leverage Messaging Alignment
- Confirmed mixed startup messaging in `Bismillah/app/autotrade_engine.py` includes:
  - top-10 routing cadence (10 minutes sticky)
  - concurrent cap (`Swing 4 + Scalping 4`)
  - base leverage and applied leverage policy (`Auto max-safe per pair`)
- Reinforced strategy-isolated reconcile path:
  - `Bismillah/app/scalping_engine.py` startup reconcile uses `trade_type="scalping"`
  - `Bismillah/app/trade_history.py` reconcile helper accepts `trade_type` filter

### 📚 Documentation Alignment
- Updated `AGENTS.md` with a full SOP rewrite to align mixed-mode governance, callback quality gates, and deploy verification expectations.

### ✅ Validation
- `python -m py_compile Bismillah/app/handlers_autotrade.py Bismillah/app/autotrade_engine.py Bismillah/app/scalping_engine.py Bismillah/app/trade_history.py`
- `pytest -q tests/test_pair_strategy_router.py tests/test_engine_shared_core.py tests/test_auto_mode_switcher_policy.py tests/test_trade_history_reconcile.py`

## [2.2.49] — 2026-04-18 — Mixed Top-10 Pair Routing (Parallel Swing+Scalp)

### ⚖️ Mixed Mode Runtime + Routing
- Added first-class `mixed` trading mode support:
  - `Bismillah/app/trading_mode.py`
  - `Bismillah/app/trading_mode_manager.py`
- Added shared per-user router service: `Bismillah/app/pair_strategy_router.py`
  - Universe: dynamic Top 10 by volume
  - Classifier: per-symbol market sentiment (`recommended_mode`)
  - Sticky reassignment window: 10 minutes
  - Output: disjoint `swing` + `scalp` symbol partitions
- Refactored engine lifecycle in `Bismillah/app/autotrade_engine.py` for mixed mode:
  - starts swing + scalping components in parallel
  - supervisor tears down sibling when one component dies
  - mixed `is_running` requires both components healthy

### 🧠 Strategy Isolation + Trade Management Safety
- Strategy-isolated open-trade reads/writes:
  - `Bismillah/app/trade_history.py`:
    - added optional `trade_type` filters for open-trade helpers
    - swing open rows now persist `trade_type="swing"` and `timeframe="15m"`
    - `reconcile_open_trades_with_exchange(...)` now supports `trade_type` filtering
  - `Bismillah/app/scalping_engine.py`:
    - startup reconcile now runs with `trade_type="scalping"`
    - load/lookup/close paths filter to scalping rows with legacy fallback detection
- Preserved trade-management and risk-management core behavior:
  - shared managed execution paths remain in use
  - per-engine concurrency cap remains `4 + 4` in mixed mode
  - leverage policy remains auto max-safe per pair (no forced leverage escalation)

### 📣 Telegram + Web Surface Sync
- Telegram mode/menu and mixed messaging updates:
  - `Bismillah/app/handlers_autotrade.py`
  - `Bismillah/app/scheduler.py`
  - `Bismillah/app/auto_mode_switcher.py` (legacy auto-switch disabled for mixed users)
  - `Bismillah/app/autotrade_engine.py` mixed startup notice includes leverage policy
- Web surface updates:
  - `website-frontend/src/App.jsx` mixed mode UI/control updates
  - `website-backend/app/routes/engine.py` / `dashboard.py` mixed-compatible mode reads
  - dashboard settings mode fallback normalized to `swing` (no legacy `auto` fallback)

### 🧪 Validation
- Added/updated tests:
  - `tests/test_pair_strategy_router.py`
  - `tests/test_auto_mode_switcher_policy.py`
  - `tests/test_engine_shared_core.py`
  - `tests/test_trade_history_reconcile.py`

## [2.2.48] — 2026-04-18 — Swing/Scalping R:R Integrity Stabilization

### 🎯 Close Persistence + Reconcile Accuracy
- Updated `Bismillah/app/engine_execution_shared.py` close payload:
  - no longer zeroes `qty` / `quantity` on close updates.
  - keeps size fields intact for post-trade risk analytics; only `remaining_quantity=0` is enforced.
- Updated `Bismillah/app/trade_history.py` stale reconcile flow:
  - reconciliation now attempts `client.get_roundtrip_financials(...)` first for exchange-history close PnL/price.
  - if exchange close-leg financials are unavailable, fallback is forced to:
    - `close_reason=stale_reconcile`
    - `pnl_usdt=0.0`
    - neutral `exit_price=entry_price`
  - removes ticker-estimated stale-reconcile PnL guesses to prevent fake large wins/losses.

### ⚡ Scalping Open-Row Completeness
- Updated `Bismillah/app/scalping_engine.py` `_save_position_to_db(...)`:
  - persists derived `rr_ratio` from executed `entry/sl/tp`.
  - enforces non-positive quantity guard (rejects DB insert when quantity <= 0).
  - keeps `qty`, `quantity`, `original_quantity`, `remaining_quantity` consistent from a single validated quantity source.

### 📊 Daily Read-Only R:R Audit Path
- Added `get_daily_rr_integrity_audit(...)` in `Bismillah/app/trade_history.py`:
  - day-windowed per-mode audit (`swing`, `scalping`, `unknown`) with:
    - opened/closed counts
    - configured R:R median
    - realized R-multiple median
    - close-reason mix
  - includes runtime snapshot metadata for:
    - adaptive (`updated_at`, `decision_reason`, deltas)
    - sideways governor (`mode`, `decision_reason`, `updated_at`)
    - win playbook (`guardrails_healthy`, `rolling_expectancy`, `risk_overlay_pct`, `updated_at`)

### 🧪 Regression Coverage
- Extended `tests/test_engine_shared_core.py`:
  - verifies close payload preserves `qty`/`quantity` fields (not force-zeroed).
- Added `tests/test_scalping_persistence.py`:
  - validates scalping open-row `rr_ratio` derivation + quantity consistency.
  - validates non-positive quantity insert rejection.
- Added `tests/test_trade_history_reconcile.py`:
  - validates exchange-history reconcile path.
  - validates stale fallback policy (`stale_reconcile + pnl_usdt=0.0`) when roundtrip financials are unavailable.
- Added `tests/test_trade_history_daily_audit.py`:
  - validates per-mode daily audit metrics.
  - validates runtime snapshot reason metadata inclusion.

### ✅ Validation
- `python -m compileall Bismillah/app/engine_execution_shared.py Bismillah/app/scalping_engine.py Bismillah/app/trade_history.py tests/test_engine_shared_core.py tests/test_scalping_persistence.py tests/test_trade_history_reconcile.py tests/test_trade_history_daily_audit.py`
- `pytest -q tests/test_engine_shared_core.py tests/test_scalping_persistence.py tests/test_trade_history_reconcile.py tests/test_trade_history_daily_audit.py`

## [2.2.47] — 2026-04-18 — Gatekeeper Verification Drift Fix (Admin + Partner)

### 🎯 Root Cause + Access Fix
- Fixed UID review callback authorization drift in `Bismillah/app/handlers_autotrade_admin.py`:
  - `uid_acc_*` / `uid_reject_*` now allow **admin OR assigned community partner**.
  - Partner authorization resolution order:
    - `user_verifications.resolved_partner_telegram_id`
    - fallback `community_code -> community_partners(status=active).telegram_id`
  - Non-owner/non-admin reviewers now receive a clear unauthorized response.

### 🔄 Canonical Status Write Parity
- Enforced canonical gatekeeper write parity on all approval paths:
  - `uid_acc_*` / `uid_reject_*` always upsert `user_verifications` (`approved` / `rejected`) and mirror `autotrade_sessions` (`uid_verified` / `uid_rejected`).
  - `Bismillah/app/handlers_community.py` member approve/reject (`cmember_acc_*`, `cmember_reject_*`) now also updates `user_verifications` (previously only legacy session status changed).

### 🛡️ Consistency Hardening
- Added missing `ADMIN3` support in backend admin loader:
  - `website-backend/app/routes/user.py`
- Expanded bot status normalization in `Bismillah/app/handlers_autotrade.py`:
  - canonical statuses (`approved/pending/rejected`) and aliases now normalize consistently for bot/web parity.

### 🧰 Ops Repair Utility
- Added one-time drift repair script: `scripts/repair_verification_drift.py`
  - default mode: dry-run (no writes)
  - apply mode: `--apply`
  - optional scan bound: `--limit N`
  - repair mapping:
    - `user_verifications.status='pending'` + `autotrade_sessions.status in ('uid_verified','active')` -> `approved`
    - `user_verifications.status='pending'` + `autotrade_sessions.status='uid_rejected'` -> `rejected`
  - summary output metrics: `scanned`, `eligible`, `updated`, `unchanged`, `errors`

## [2.2.46] — 2026-04-18 — Open-Trade R:R Parity Persistence Fix (StackMentor)

### 🎯 Trade Persistence Parity
- Updated `Bismillah/app/trade_history.py` open-trade persistence:
  - `rr_ratio` is now derived from executed levels (`entry`, `sl`, `tp1`) instead of trusting stale pre-execution signal values.
  - Ensures DB `rr_ratio` matches actual open-trade TP/SL math in StackMentor runner paths.

### 🧪 Regression Coverage
- Extended `tests/test_engine_shared_core.py`:
  - added `save_trade_open` coverage to assert executed-level `rr_ratio` persistence (including stackmentor TP1 override path).

### ✅ Validation
- `python -m py_compile Bismillah/app/trade_history.py tests/test_engine_shared_core.py`
- `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py tests/test_trade_history_win_reasoning.py -q`

## [2.2.45] — 2026-04-18 — Bitunix 710002 Unsupported-Pair Hardening (Swing + Scalping)

### 🎯 OpenAPI Unsupported Pair Protection
- Hardened `Bismillah/app/volume_pair_selector.py` to pre-filter top-volume symbols using Bitunix tradability metadata:
  - Added `/api/v1/futures/market/trading_pairs` fetch.
  - Dynamic universe now requires `USDT` quote + `symbolStatus=OPEN` + ticker presence.
- Added runtime unsupported-symbol quarantine in selector:
  - New helper: `mark_runtime_untradable_symbol(symbol, ttl_sec=21600)`.
  - Quarantined symbols are excluded from returned top-volume pairs for 6 hours by default.

### ⚙️ Execution Error Classification
- Updated `Bismillah/app/trade_execution.py` error classifier:
  - Bitunix `710002` and OpenAPI unsupported-pair message now map to `error_code="unsupported_symbol_api"`.
  - Existing auth/balance/SL classification behavior remains unchanged.

### 🤖 Engine Handling (Non-Retryable Path)
- Updated `Bismillah/app/autotrade_engine.py`:
  - Added explicit `unsupported_symbol_api` branch to clear pending, quarantine symbol, notify user, and continue scanning without auth-style retry.
- Updated `Bismillah/app/scalping_engine.py`:
  - Treats `unsupported_symbol_api` as non-retryable, clears pending, applies quarantine, notifies user, and continues normal scan flow.

### 🧪 Regression Coverage
- Extended `tests/test_volume_pair_selector.py`:
  - verifies tradability filtering using `trading_pairs`,
  - verifies runtime quarantine exclude + expiry behavior,
  - preserves cache/bootstrap fallback behavior.
- Extended `tests/test_swing_scalp_parity.py`:
  - verifies `open_managed_position(...)` returns `error_code="unsupported_symbol_api"` for Bitunix `710002`.

## [2.2.44] — 2026-04-18 — Stale-Signal Hardening (Preflight Cooldown + Freshness Gate)

### 🎯 Runtime Hardening
- Updated `Bismillah/app/autotrade_engine.py`:
  - preflight stale rejects now mark per-user symbol stale cooldown immediately (120s),
  - queue execution logging now includes `selected_idx`, `queue_age`, and stale-cooldown state for traceability,
  - pending `signal_queue` sync now guarantees non-null `tp3` fallback (uses `tp2`, then `tp1`).
- Updated `Bismillah/app/providers/alternative_klines_provider.py`:
  - added candle freshness gating by interval age before accepting source data,
  - stale source data is rejected and fallback chain continues.

### 🧪 Regression Coverage
- Added/extended tests in:
  - `tests/test_swing_scalp_parity.py`
  - `tests/test_engine_shared_core.py`
- New checks cover:
  - preflight stale reject cooldown marking path,
  - queue processing log markers (`selected_idx`, `queue_age`),
  - pending sync `tp3` fallback behavior,
  - klines freshness accept/reject helper behavior.

### ✅ Validation
- `python -m py_compile Bismillah/app/autotrade_engine.py Bismillah/app/providers/alternative_klines_provider.py tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py`
- `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py -q`
  - Result: `32 passed`.

## [2.2.43] — 2026-04-18 — Swing Final Pre-Open Stale Gate (Post-StackMentor)

### 🎯 Final Execution-Race Guard
- Added a final stale validation gate in `Bismillah/app/autotrade_engine.py` immediately before pending/open calls.
- This gate runs after queue selection and after final TP/SL shaping (including StackMentor path), then:
  - rejects stale levels before order submission,
  - applies existing 120s stale cooldown,
  - removes queued item and continues scanning.

### ✅ Policy Preserved
- No TP/SL mutation.
- No forced entry.
- Unified `open_managed_position(...)` strict validation remains unchanged as final guard.

### 🧪 Regression Coverage
- Updated `tests/test_swing_scalp_parity.py` with source-level guard check for final pre-open stale reject hook.

### ✅ Validation
- `python -m py_compile Bismillah/app/autotrade_engine.py tests/test_swing_scalp_parity.py`
- `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py -q`
  - Result: `29 passed`.

## [2.2.42] — 2026-04-18 — Swing Pre-Execution Stale Guard (Queue Path)

### 🎯 Additional Stale Protection
- Added a second stale-price guard in swing queue processing (`Bismillah/app/autotrade_engine.py`) right before execution handoff.
- Behavior:
  - re-check queued signal levels against live mark proxy,
  - if already invalid, drop queued signal before execution,
  - apply existing 120s stale cooldown for that symbol,
  - continue scanning without sending execution-time stale failure for that queued item.

### ✅ Policy Preserved
- No TP/SL mutation.
- No forced entry.
- `open_managed_position(...)` strict validation remains the final hard gate.

### 🧪 Regression Coverage
- Updated `tests/test_swing_scalp_parity.py`:
  - coverage for mark-unavailable pass-through behavior,
  - source-level guard for queue pre-exec stale rejection hook.

### ✅ Validation
- `python -m py_compile Bismillah/app/autotrade_engine.py tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py`
- `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py -q`
  - Result: `28 passed`.

## [2.2.41] — 2026-04-18 — Swing Live-Mark Preflight Gate (Stale Signal Suppression)

### 🎯 Stale-Signal Suppression
- Added strict preflight live-mark gating in `Bismillah/app/autotrade_engine.py` before swing signals are returned/queued.
- New behavior: if generated levels are already invalid vs live mark (`LONG TP1 <= mark`, `SHORT TP1 >= mark`, or SL on wrong side), signal is rejected early.
- Policy preserved:
  - no TP/SL mutation,
  - no forced entry,
  - existing `open_managed_position(...)` strict validation unchanged (this is a prefilter, not a validator replacement).

### ⚙️ Runtime Efficiency
- Added short-lived mark proxy cache (5s TTL) for preflight checks to avoid repeated per-symbol fetch bursts across users.

### 🧪 Regression Coverage
- Updated `tests/test_swing_scalp_parity.py`:
  - preflight rejects stale short levels against live mark,
  - preflight accepts valid short levels.
- Updated `tests/test_engine_shared_core.py`:
  - mark-proxy cache hit behavior within TTL.

### ✅ Validation
- `python -m py_compile Bismillah/app/autotrade_engine.py tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py`
- `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py -q`
  - Result: `26 passed`.

## [2.2.40] — 2026-04-18 — Swing Queue Hotfix (Runtime `time` Scope Regression)

### 🚑 Hotfix Summary
- Fixed a production regression introduced in `2.2.39` where swing `_trade_loop` could raise:
  - `UnboundLocalError: cannot access local variable 'time'`
- Root cause: function-local `import time` statements inside `_trade_loop` shadowed the module-level `time` import on control-flow paths where local import was not executed.

### 🔧 Engine Fix
- Updated `Bismillah/app/autotrade_engine.py`:
  - removed local `import time` statements inside `_trade_loop`,
  - ensured all `_trade_loop` time usage resolves to the module-level `time` import consistently.
- No SL/TP validation behavior changes.
- No queue policy changes from `2.2.39`.

### ✅ Validation
- `python -m py_compile Bismillah/app/autotrade_engine.py`
- `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py -q`
  - Result: `23 passed`.

## [2.2.39] — 2026-04-18 — Swing Queue Freshness Hardening (Stale-Signal Repeat Fix)

### 🎯 Swing Stale-Signal Stability
- Kept strict `invalid_prices` rejection behavior unchanged (no TP/SL mutation, no forced entry).
- Hardened swing queue freshness in `Bismillah/app/autotrade_engine.py`:
  - added internal queue timestamp tracking (`_queued_at_ts`),
  - switched same-symbol queue behavior from keep-old to refresh-upsert (unless symbol is already in-flight),
  - added 90s queued-signal age gate before execution selection.
- Fixed queue status rendering to exclude the actual active entry index/symbol from the "Queued remaining" list.

### 🛡️ Runtime Safety + Visibility
- Added exception/cancellation-safe in-flight marker cleanup to prevent ghost `_signals_being_processed` locks after loop tracebacks.
- Updated Supabase pending queue sync behavior to refresh existing pending rows on same-symbol upsert (not insert-only).

### 🧪 Regression Coverage
- Updated `tests/test_swing_scalp_parity.py`:
  - covers swing queue upsert refresh behavior and in-flight skip behavior,
  - covers 90s queue age pruning,
  - covers queue remaining list correctness when active index is non-zero,
  - covers exception-path in-flight marker cleanup helper behavior.
- Updated `tests/test_engine_shared_core.py`:
  - covers queue age-gate behavior that preserves active in-flight symbols.

### ✅ Validation
- Compile check:
  - `python -m py_compile Bismillah/app/autotrade_engine.py tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py`
- Targeted tests:
  - `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py -q`
  - Result: `23 passed`.

## [2.2.38] — 2026-04-17 — Win Tag Fallback Enforcement + Historical Winner Backfill

### 🏷️ Win Tag Contract Enforcement
- Hardened winning close metadata contract to guarantee non-empty `win_reason_tags` on enforced winner paths:
  - `Bismillah/app/engine_execution_shared.py`
  - `Bismillah/app/trade_history.py`
- Added fallback tag policy when playbook match returns no tags:
  - `["win_close", "<close_reason>"]`
- Applied on:
  - `closed_tp` / `closed_tp3` (always),
  - profitable `closed_flip`,
  - positive cumulative closes (including partial-flow net winners).

### 🧪 Regression Coverage
- `tests/test_engine_shared_core.py`:
  - verifies `closed_tp` path persists non-empty `win_reasoning` and non-empty `win_reason_tags` even on slight net-negative close.
- `tests/test_trade_history_win_reasoning.py`:
  - verifies fallback non-empty tag normalization behavior.

### 🗄️ Data Backfill (Production)
- Ran controlled historical backfill for winner rows missing win metadata:
  - candidates scanned: `378`
  - rows updated: `378`
  - failures: `0`
- Post-backfill coverage snapshot:
  - all-time winner `win_reasoning` coverage: `100%`
  - 24h winner `win_reasoning` coverage: `100%`
  - fallback tag policy active for future closes.

### ✅ Validation
- Targeted tests:
  - `pytest -q tests/test_engine_shared_core.py tests/test_trade_history_win_reasoning.py tests/test_swing_scalp_parity.py tests/test_risk_audit.py`
  - Result: `24 passed`.
- Full suite:
  - `pytest -q tests`
  - Result: `99 passed, 6 skipped`.

## [2.2.37] — 2026-04-17 — Stale-Price Skip Stabilization (Swing + Scalping)

### 🎯 Entry Validation Handling
- Kept strict `open_managed_position(...)` SL/TP vs mark validation unchanged (no force-entry, no SL/TP mutation).
- Reclassified `invalid_prices` runtime skips as stale-signal outcomes in both engines.

### ⚙️ Runtime Cooldown + Queue Behavior
- Added shared TTL cooldown helpers in `Bismillah/app/engine_runtime_shared.py`:
  - `set_ttl_cooldown(...)`
  - `is_ttl_cooldown_active(...)`
- Swing (`Bismillah/app/autotrade_engine.py`):
  - added per-user stale-price cooldown map (120s),
  - on `invalid_prices`, applies stale cooldown and emits clear stale-market skip message,
  - skips stale-cooled symbols during candidate scan/queue processing,
  - queue status footer text now matches actual policy: volume-rank first, confidence tie-break.
- Scalping (`Bismillah/app/scalping_engine.py`):
  - on `invalid_prices`, applies stale cooldown (120s) with explicit user message,
  - generic 300s failure cooldown now preserves active stale cooldown (no override).

### 🧪 Regression Coverage
- Updated `tests/test_engine_shared_core.py`:
  - added TTL cooldown helper set/active/expiry coverage.
- Updated `tests/test_swing_scalp_parity.py`:
  - added scalping stale-cooldown non-override coverage,
  - added source-level guard for swing queue messaging (volume-priority wording).

### ✅ Validation
- `pytest tests/test_engine_shared_core.py tests/test_swing_scalp_parity.py -q`
  - Result: `18 passed`.

## [2.2.36] — 2026-04-17 — Win Reasoning Coverage Hotfix (Winning Close Path Policy)

### 🏆 Win Strategy Persistence Fix
- Hardened winning-close reasoning policy in both shared and legacy close persistence paths:
  - `Bismillah/app/engine_execution_shared.py`
  - `Bismillah/app/trade_history.py`
- Win reasoning is now persisted when either:
  - cumulative PnL is positive, or
  - close reason is `closed_tp` / `closed_tp3`, or
  - close reason is profitable `closed_flip`.
- Prevented contradictory auto `loss_reasoning` injection on enforced winning close paths (`closed_tp`/`closed_tp3`), even when net PnL is slightly negative from fees.

### 🧪 Regression Coverage
- Updated `tests/test_engine_shared_core.py`:
  - added coverage ensuring `closed_tp` paths persist non-empty `win_reasoning` even for slight net-negative exits.
- Updated `tests/test_trade_history_win_reasoning.py`:
  - added policy coverage for `_should_enforce_win_reasoning(...)`.

### ✅ Validation
- Targeted tests:
  - `pytest -q tests/test_engine_shared_core.py tests/test_trade_history_win_reasoning.py tests/test_swing_scalp_parity.py tests/test_risk_audit.py`
  - Result: `20 passed`.
- Full suite:
  - `pytest -q tests`
  - Result: `95 passed, 6 skipped`.

## [2.2.35] — 2026-04-17 — Auto Mode Switcher Hardening (Hysteresis + Cooldown + Manual Override)

### 🎯 Orchestration Policy
- Kept `TradingModeManager.switch_mode(...)` + `autotrade_engine` restart lifecycle as the single switch orchestration backbone.
- Preserved manual mode switch UX and auto mode toggle UX (hybrid model remains).

### 🛡️ Auto Switcher Safety Hardening
- Hardened `Bismillah/app/auto_mode_switcher.py` with low-trust detector guardrails:
  - configurable confidence floor (`AUTO_MODE_SWITCH_MIN_CONFIDENCE`, default `65`),
  - recommendation hysteresis cycles (`AUTO_MODE_SWITCH_CONFIRMATION_CYCLES`, default `2`),
  - per-user auto-switch cooldown (`AUTO_MODE_SWITCH_COOLDOWN_SECONDS`, default `1800`).
- Repurposed `switched_users` tracker to store per-user last successful auto-switch timestamps.
- Added per-user recommendation streak tracking so first recommendation no longer flips mode immediately by default.
- Added manual-override precedence gate: auto-switch skips users while manual override window is active.
- Updated switcher status timestamp to timezone-aware UTC (`datetime.now(timezone.utc)`).

### ⚙️ Trading Mode Manager Updates
- Extended `TradingModeManager.switch_mode(...)` with `switch_source` (`manual` / `auto`) for policy-aware switching.
- Added in-memory manual override controls in `Bismillah/app/trading_mode_manager.py`:
  - `mark_manual_override(...)`
  - `clear_manual_override(...)`
  - `is_manual_override_active(...)`
- Manual source switches now activate override window (`AUTO_MODE_MANUAL_OVERRIDE_SECONDS`, default `1800`).
- Auto source switches continue to use full stop→persist→restart path without creating manual override.

### 🧩 Handler Wiring
- Updated manual callbacks in `Bismillah/app/handlers_autotrade.py` to call:
  - `switch_mode(..., switch_source="manual")`
- Auto mode switcher now calls:
  - `switch_mode(..., switch_source="auto")`

### 🧪 Validation
- New tests:
  - `tests/test_auto_mode_switcher_policy.py`
  - `tests/test_trading_mode_manager_switch_source.py`
- Updated parity test for new hysteresis default:
  - `tests/test_swing_scalp_parity.py`

## [2.2.34] — 2026-04-17 — Dual Engine Shared-Core Refactor (Swing + Scalp)

### 🧩 Architecture Decision Applied
- Kept **two strategy engines** (swing + scalping) and extracted shared orchestration/execution plumbing.
- Preserved public runtime API (`start_engine_async(...)`) and mode-switch behavior.

### ⚙️ Shared Runtime Layer
- Added `Bismillah/app/engine_runtime_shared.py` with shared helpers for:
  - startup pending-lock sanitize,
  - stop-signal polling (`autotrade_sessions.status/engine_active`),
  - 10-minute refresh cadence orchestration,
  - top-volume pair refresh with fallback,
  - blocked-pending notification dedupe TTL.
- Wired both engines to this shared runtime layer (no strategy merge).

### 🧠 Shared Execution + Close Persistence Layer
- Added `Bismillah/app/engine_execution_shared.py` with shared helpers for:
  - playbook risk evaluation + signal field attachment,
  - risk-audit formatting + structured emission,
  - coordinator pending/open/close wrappers,
  - cumulative close payload builder (`profit_tp1/2/3 + final_leg_pnl`) with win/loss reasoning persistence.
- Updated scalping close persistence path to use shared cumulative payload helper.

### 🔒 Compatibility + Control Plane
- Added backward-compatible `get_scalping_engine(user_id)` alias in `Bismillah/app/autotrade_engine.py` delegating to `get_engine(...)`.
- Updated mode-switch cleanup path to use alias (`Bismillah/app/trading_mode_manager.py`) so runtime accessor naming stays consistent.

### 🧪 Validation
- Compile/syntax pass:
  - `python -m compileall Bismillah/app/engine_runtime_shared.py Bismillah/app/engine_execution_shared.py Bismillah/app/autotrade_engine.py Bismillah/app/scalping_engine.py Bismillah/app/trading_mode_manager.py`
- New unit coverage:
  - `tests/test_engine_shared_core.py`:
    - alias runtime path (`get_scalping_engine`),
    - shared runtime cadence/stop behavior,
    - shared cumulative close payload (PnL + win/loss reasoning metadata).
- Targeted regressions:
  - `pytest -q tests/test_engine_shared_core.py tests/test_timeout_protection_policy.py tests/test_swing_scalp_parity.py`
  - Result: `16 passed`.

## [2.2.33] — 2026-04-17 — Swing/Scalp Adaptive Parity + Win Strategy Sync Hardening

### 🎯 Mode Lifecycle + Auto-Switch Consistency
- Preserved persisted trading mode during restore/restart flows (no forced swing→scalp coercion in shared restore helper path).
- Kept runtime mode transitions on full switch path (`TradingModeManager.switch_mode`) so DB mode and running engine stay in sync.
- Startup/restart notifications now continue to resolve mode from runtime source-of-truth (`TradingModeManager.get_mode(...)` after engine start).

### ⚙️ Execution/Risk Contract Unification
- Completed swing flip path migration to unified managed execution:
  - replaced direct `client.place_order_with_tpsl(...)` call with `open_managed_position(...)`,
  - aligned flip execution with shared validation/reconcile behavior used by scalp + normal swing entries.
- Hardened flip coordinator lifecycle:
  - explicit `confirm_closed(...)` before flipped reopen,
  - explicit `confirm_open(...)` after successful flipped reopen,
  - prevents symbol-ownership drift/clash between swing/scalp after flip events.
- Hardened flip close persistence ordering:
  - old swing trade rows are now closed/persisted immediately after flip-close succeeds (even if flipped reopen later fails), preventing stale DB-open rows.
- Removed stale restore helper that forced scalping mode (`set_scalping_mode`) from `engine_restore.py`.

### 🏆 Win Strategy + Persistence Parity
- Extended flip open persistence to store StackMentor execution fields (`tp1/2/3`, `qty_tp1/2/3`, `strategy`) in addition to playbook/risk overlay metadata.
- Preserved winning-close metadata contract (`win_reasoning`, `win_reason_tags`, playbook + effective risk fields) across swing close paths and flip closures.

### 🧪 Regression Coverage Added
- New `tests/test_swing_scalp_parity.py` coverage for:
  - invalid SL/TP rejection without order placement in managed execution,
  - scalping sizing symbol propagation (no hardcoded BTC precision path),
  - swing timeout env alias compatibility (`SWING_TIMEOUT_PROTECTION_ENABLED`),
  - auto-mode switcher using full `switch_mode(...)` path (not direct DB-only mode set),
  - guard that swing engine no longer uses direct `place_order_with_tpsl` calls.
- Minor resilience hardening in scalping timeout helper:
  - `_max_hold_seconds_for_position(...)` now safely handles missing `_sideways_governor_snapshot` attribute fallback.
- Added bot-package compatibility shim `Bismillah/app/routes/signals.py` for mixed test namespace imports so one-click token/sizing/replay security tests resolve consistently without depending on website package load order.

### ✅ Validation
- Syntax/compile pass:
  - `python -m py_compile Bismillah/app/autotrade_engine.py Bismillah/app/engine_restore.py Bismillah/app/scalping_engine.py Bismillah/app/scheduler.py Bismillah/app/trading_mode.py tests/test_swing_scalp_parity.py`
- Targeted parity/risk/win tests:
  - `pytest -q tests/test_swing_scalp_parity.py tests/test_timeout_protection_policy.py tests/test_win_playbook.py tests/test_trade_history_win_reasoning.py tests/test_coordinator.py tests/test_risk_audit.py`
  - `pytest -q tests/test_stackmentor_runner.py tests/test_volume_pair_selector.py tests/test_sideways_governor.py`
  - Result: `49 passed`.
- Full suite confirmation:
  - `pytest -q tests`
  - Result: `77 passed, 6 skipped`.

## [2.2.32] — 2026-04-17 — Bitunix Key Save/Test Import Crash Hotfix

### 🛠️ Website API Route Hardening
- Fixed `/bitunix/keys` and `/bitunix/keys/test` crash path by removing invalid direct import of `app.bitunix_autotrade_client`.
- Added shared connection test helper in `website-backend/app/services/bitunix.py`:
  - `fetch_connection_with_keys(api_key, api_secret)`
- Updated key save/test routes to use service-layer client wiring (same runtime path used by existing Bitunix account/positions endpoints).
- Added explicit exception mapping in routes so failures always return JSON `detail` (no unhandled plaintext 500).

### 🎨 Frontend Error UX Guard (Onboarding + API Bridges)
- Improved API error extraction in `website-frontend/src/App.jsx`:
  - prefer JSON `detail/message/error`,
  - fallback to raw response text when JSON parsing fails.
- Applied to:
  - Settings tab (`Test Connection`, `Save Connectivity`)
  - Onboarding step 1 (`Test Connection`, `Save & Continue`)
- Result: users now see actionable backend error text instead of generic `Failed to save keys`.

### ✅ Validation
- Syntax/compile pass:
  - `python -m py_compile website-backend/app/routes/bitunix.py website-backend/app/services/bitunix.py`
- Frontend build pass:
  - `npm run build` (in `website-frontend`)

## [2.2.31] — 2026-04-17 — API Key DB Population + Hardcode Removal

### 🔐 Bitunix Key Source Normalization
- Populated `user_api_keys` for Telegram user `8263889133` (`exchange=bitunix`) via encrypted save path.
- Removed temporary UID-scoped hardcoded API-key override from:
  - `Bismillah/app/handlers_autotrade.py`
  - `website-backend/app/services/bitunix.py`
- Runtime now resolves this user’s Bitunix key strictly from `user_api_keys` table again.

### ✅ Validation
- DB verification:
  - `user_api_keys` row exists for `telegram_id=8263889133`, `exchange=bitunix`, with non-empty `api_secret_enc`.
- Compile/syntax pass:
  - `python -m py_compile Bismillah/app/handlers_autotrade.py website-backend/app/services/bitunix.py`

## [2.2.30] — 2026-04-17 — Web API Concurrency Hotfix (504 Login/Gatekeeper)

### 🚀 Service Runtime Capacity Patch
- Updated website backend systemd unit template `website-backend/cryptomentor-web.service`:
  - switched uvicorn from single process to multi-worker:
    - `--workers 4`
    - `--timeout-keep-alive 10`
- Purpose:
  - reduce request queue starvation during high-frequency dashboard polling,
  - keep lightweight auth and gatekeeper endpoints (`/auth/telegram`, `/user/verification-status`) responsive under load.

### ✅ Validation
- Service status check target after deploy:
  - `systemctl is-active cryptomentor-web`
  - `systemctl show cryptomentor-web -p MainPID -p ActiveState -p SubState`
  - process list includes uvicorn master + 4 workers.

## [2.2.29] — 2026-04-17 — Website API Timeout Mitigation (Login/Gatekeeper Stability)

### ⚡ Backend Stability Hotfix
- Added lightweight in-memory live-data cache in `website-backend/app/services/bitunix.py` to reduce upstream Bitunix fan-out under heavy dashboard polling:
  - account cache TTL: `2.5s` (`BITUNIX_ACCOUNT_CACHE_TTL_SECONDS`),
  - positions cache TTL: `2.0s` (`BITUNIX_POSITIONS_CACHE_TTL_SECONDS`).
- Applied cache usage to:
  - `fetch_account(...)`
  - `fetch_positions(...)`
- Added cache invalidation on trade-mutating paths to avoid stale post-action reads:
  - `set_position_tpsl(...)`
  - `set_position_sl(...)`
  - `place_market_with_tpsl(...)`
  - `close_market_position(...)`
- Goal: keep `/auth/telegram` and `/user/verification-status` responsive when concurrent portfolio polling spikes.

### ✅ Validation
- Compile/syntax pass:
  - `python -m py_compile website-backend/app/services/bitunix.py`

## [2.2.28] — 2026-04-17 — Bitunix UID-Scoped API Key Override (Emergency)

### 🔐 Runtime Key Override (Targeted)
- Added temporary Bitunix API-key override for one specific verified UID in runtime key loaders:
  - `Bismillah/app/handlers_autotrade.py`
  - `website-backend/app/services/bitunix.py`
- Override scope:
  - activates only when the user's session UID (`exchange_uid` or legacy `bitunix_uid`) equals `481262194`,
  - takes precedence over `user_api_keys` table lookup for that UID,
  - all other users continue normal encrypted DB key flow.
- Added warning log line when override is applied:
  - `[API Keys Override] Using hardcoded Bitunix keys ...`

### ✅ Validation
- Compile/syntax pass:
  - `python -m py_compile Bismillah/app/handlers_autotrade.py website-backend/app/services/bitunix.py`

## [2.2.27] — 2026-04-17 — Website Telegram Login 500 Guardrails

### 🔐 Website Auth Stability Patch
- Fixed login upsert timestamp serialization in `website-backend/app/db/supabase.py`:
  - replaced `updated_at: "now()"` with UTC ISO timestamp to avoid invalid timestamp payloads during user updates.
- Hardened referral-column compatibility for mixed schemas:
  - `upsert_web_login(...)` now retries without `referred_by_code` when Supabase reports unknown-column/schema-cache errors,
  - insert path now includes `referred_by_code` only when a value is present, with safe fallback retry.
- Added defensive error handling in `website-backend/app/routes/auth.py`:
  - wraps login user upsert in `try/except`,
  - logs backend exception and returns controlled `503 Login service temporarily unavailable` instead of unhandled `500`.

### ✅ Validation
- Compile/syntax pass:
  - `python -m py_compile website-backend/app/db/supabase.py website-backend/app/routes/auth.py`

## [2.2.26] — 2026-04-17 — Intro Deck Mobile Dynamic Viewport Optimization

### 📱 Frontend Mobile UX Hardening (Onboarding Deck)
- Updated `website-frontend/public/cryptomentor-onboarding-deck.html` for stronger mobile dynamic viewport behavior without changing scroll-native section architecture:
  - enabled `viewport-fit=cover` and safe-area-aware spacing using `env(safe-area-inset-*)`,
  - introduced dynamic viewport tokens (`--vh`, `--topbar-h`) and applied them to section min-height + scroll offsets,
  - tuned mobile snap behavior (`mandatory` desktop, `proximity` small screens) and repositioned section dots to a bottom-center touch-friendly control on phones,
  - improved notch/home-indicator handling for top bar, shell padding, and progress/dot controls.
- Added lightweight JS viewport synchronization:
  - `visualViewport` + `resize` + `orientationchange` hooks update `--vh` and `--topbar-h`,
  - scroll progress now uses dynamic viewport height for stable progress tracking when browser chrome expands/collapses.
- Preserved all required core content/logic:
  - 8-section flow,
  - EN/ID translation system,
  - signal values and pairs,
  - projection milestones and CTA routes.

### ✅ Validation
- Inline JS parse check passed.
- Structural check confirmed 8 sections remain in flow.
- Key preserved values verified:
  - `BTCUSDT 89%`, `ETHUSDT 73%`, `SOLUSDT 58%`, `XRPUSDT 81%`
  - `$1,000 -> $1,360 -> $1,920 -> $2,670`

## [2.2.25] — 2026-04-17 — Intro Deck Scroll-Native Story Mode (Intro Color Match)

### 🎨 Frontend UX Refactor (Onboarding Deck)
- Updated `website-frontend/public/cryptomentor-onboarding-deck.html` to switch from slideshow navigation to scroll-native storytelling:
  - replaced stacked slide-state behavior with vertical scroll sections and viewport snap (`scroll-snap-type: y mandatory`),
  - converted slide activation flow to `IntersectionObserver` state tracking for current section and animations,
  - removed autoplay/pause/prev/next/timeline slideshow controls and related runtime logic,
  - added scroll progress UI:
    - fixed top progress bar,
    - fixed right-side section dots for direct scene navigation.
- Matched intro theme palette/style direction to align with `intro.cryptomentor.id`:
  - base and accents aligned to intro tokens (`--bg: #04060f`, `--cyan: #22d3ee`, `--emerald: #34d399`),
  - panel/surface contrast and glow/border treatment tuned to intro visual language.
- Preserved core onboarding content architecture and critical values:
  - 8 sections retained in same order,
  - signal cards unchanged for key pairs/percentages:
    - `BTCUSDT 89%`, `ETHUSDT 73%`, `SOLUSDT 58%`, `XRPUSDT 81%`,
  - projection milestones unchanged:
    - `$1,000 -> $1,360 -> $1,920 -> $2,670`,
  - EN/ID translation model and CTA destinations preserved.

### ✅ Validation
- Inline JS parse check passed after runtime refactor.
- `data-i18n` key coverage check passed (no missing translation keys).
- Structural checks passed:
  - section count remains `8`,
  - required signal/projection values remain present,
  - scroll snap and scroll progress UI markers detected.

## [2.2.24] — 2026-04-17 — Intro Deck Cinematic AI Engine Redesign (In-Place)

### 🎨 Frontend Redesign (Onboarding Deck)
- Updated `website-frontend/public/cryptomentor-onboarding-deck.html` in place with a premium cinematic style while preserving deck architecture and behavior:
  - dark neon token system (`#080B0F`, lime/blue accents), glass panels, glow borders, animated grid/scan overlays,
  - stronger launch-style typography hierarchy and refined spacing rhythm,
  - upgraded EN/ID language toggle presentation and deck control polish (including pause chip state styling),
  - hero refactor to AI-engine activation narrative with status chips and stronger CTA hierarchy,
  - progression-node restyle for step journey (Connect/Configure/Activate/Scale labels),
  - market confidence cards reworked into live signal widgets while preserving required values:
    - `BTCUSDT 89%`, `ETHUSDT 73%`, `SOLUSDT 58%`, `XRPUSDT 81%`,
  - inserted compact in-flow “WHAT THE ENGINE IS WATCHING” live status panel,
  - projection path reframed as scenario milestones while preserving values:
    - `$1,000 -> $1,360 -> $1,920 -> $2,670`,
  - final CTA slide upgraded to “SYSTEM READY” conversion framing while keeping website-first CTA target (`https://cryptomentor.id`).
- Kept core runtime behavior unchanged:
  - 8-slide structure,
  - EN/ID translation architecture,
  - autoplay/pause/timeline/keyboard/wheel/touch navigation logic.

### ✅ Validation
- JS parse check passed for inline script block.
- `data-i18n` coverage check passed (no missing keys).
- Structural invariants verified:
  - `8` slides present,
  - required signal and projection values preserved.

## [2.2.23] — 2026-04-17 — Intro HTTPS Fallback Guardrail (Cert Reuse + Misroute Block)

### 🔒 Deploy/Sync Hardening (Intro Subdomain)
- Updated `scripts/deploy_intro_onboarding.sh` to prevent `https://intro.cryptomentor.id` from silently falling onto a token-protected backend when SSL issuance is skipped:
  - now auto-detects and reuses an existing Let’s Encrypt cert for the intro domain, enabling HTTPS vhost without forcing a fresh cert issue,
  - keeps the previous `ISSUE_SSL=1` flow for first-time cert issuance,
  - in no-cert + no-issue mode, now runs an HTTPS misroute probe and hard-fails if response body contains `Invalid or missing token`.
- Verification output now includes HTTPS URLs whenever HTTPS is active via either freshly issued or reused cert.

## [2.2.22] — 2026-04-17 — Intro HTTPS Routing Guardrail (Onboarding Deck)

### 🔒 Deploy/Sync Hardening (Intro Subdomain)
- Updated `scripts/deploy_intro_onboarding.sh` SSL flow to prevent silent HTTPS misroutes:
  - added explicit HTTPS + SNI validation via `curl --resolve ${DOMAIN}:443:127.0.0.1` after nginx reload,
  - verifies expected status codes on:
    - `https://<domain>/` (`302`)
    - `https://<domain>/intro.html` (`200`)
    - `https://<domain>/cryptomentor-onboarding-deck.html` (`200`)
  - fails deploy if onboarding deck body contains auth middleware payload (`Invalid or missing token`), catching wrong-vhost/proxy routing immediately.
- Step output numbering for SSL path updated to reflect added verification phase (`[8/10]`, `[9/10]`, `[10/10]`).

## [2.2.21] — 2026-04-17 — Adaptive Exit + Sideways Recovery (Balanced Fast Rollout)

### 🎯 Trading Engine Runtime Upgrades
- Added runtime adaptive sideways governor (`normal|strict|pause`) with 10-minute refresh cadence:
  - `Bismillah/app/sideways_governor.py`
  - strict trigger: sample >= 20 and (`expectancy < 0` or `timeout_loss_rate >= 55%`)
  - pause trigger: sample >= 30 and (`expectancy < -0.005` and `timeout_loss_rate >= 65%`)
  - strict mode actions:
    - disables sideways fallback entries
    - raises sideways quality floors (`RR >= 1.25`, `volume >= 1.1x`, `+3` confidence)
    - requires 2 confirmation streak for sideways entries
  - pause mode blocks sideways entries for 60 minutes
  - recovery requires 2 consecutive healthy windows (`expectancy >= 0`, `timeout_loss_rate <= 45%`)
- Wired governor into scalping runtime:
  - `Bismillah/app/scalping_engine.py`
  - pre-scan expired-position processing runs before new signal scan
  - dynamic max-hold windows now adaptive by subtype/symbol performance:
    - sideways: 90–150s
    - non-sideways: 1200–2400s
  - hourly KPI logs added for:
    - sideways expectancy (24h)
    - sideways timeout-loss rate (24h)
    - governor mode + sample size

### 🧹 Learning Data Hygiene
- Hardened close persistence defaults:
  - `Bismillah/app/trade_history.py`
  - always writes fallback metadata defaults on close path:
    - `playbook_match_score`
    - `effective_risk_pct`
    - `risk_overlay_pct`
  - enforces non-empty fallback reasoning:
    - negative close -> `loss_reasoning` fallback
    - positive close -> `win_reasoning` fallback builder
- Reconcile close classification hardened:
  - orphan exchange-reconciled closes without TP evidence now persisted as `stale_reconcile`
  - near-flat stale reconcile closes normalized to neutral PnL (0.0), avoiding false strategy-win learning

### 📊 Observability + Reporting
- Daily report headline closed-trade count now includes timeout exits (all non-open statuses):
  - `Bismillah/app/admin_daily_report.py`
- Added tests:
  - `tests/test_sideways_governor.py` (mode transitions + hold resolution + KPI metrics)
  - `tests/test_adaptive_confluence.py` (ops reconcile classification coverage for new `stale_reconcile` flow)

### ✅ Validation
- Targeted compile pass succeeded for touched modules.
- Targeted tests passed:
  - `tests/test_sideways_governor.py`
  - `tests/test_adaptive_confluence.py`
  - `tests/test_win_playbook.py`
  - `tests/test_trade_history_win_reasoning.py`

## [2.2.20] — 2026-04-17 — Onboarding Slide-1 Social Proof Panel (Alignment Fix)

### 🎨 Intro Deck UI Patch (Production-Facing)
- Updated `website-frontend/public/cryptomentor-onboarding-deck.html` slide-1 right panel:
  - removed the misaligned terminal chart block,
  - replaced it with a full compliance-safe social proof panel (trust badges, user-outcome callouts, and "Why users stay" checklist),
  - preserved deck visual style and responsive behavior.
- Added new EN/ID `data-i18n` keys for all social proof content to keep bilingual rendering complete.
- Removed unused hero-chart JS/CSS remnants in the same file to prevent dead code drift.

## [2.2.19] — 2026-04-17 — Open-Trade Risk Audit Transparency (Swing + Scalping)

### 🔎 Per-Order Risk Audit Line (User + Ops)
- Added shared helper `Bismillah/app/risk_audit.py`:
  - `format_risk_audit_line(...)`
  - `emit_order_open_risk_audit(...)`
- Updated swing open-notification path in `Bismillah/app/autotrade_engine.py`:
  - appends one-line Telegram audit with `base_risk`, `overlay`, `effective_risk`, `implied_risk_usdt`,
  - emits structured backend `order_open_risk_audit` log event per successful open order.
- Updated scalping StackMentor open-notification path in `Bismillah/app/scalping_engine.py`:
  - persists `base_risk_pct` on signal context,
  - appends same one-line Telegram audit,
  - emits structured backend `order_open_risk_audit` log event per successful open order.

### ✅ Tests + Ops Docs
- Added `tests/test_risk_audit.py` to validate:
  - output formatting,
  - invalid-value fallback handling,
  - structured log emission for `order_open_risk_audit`.
- Updated `docs/02_AUTOTRADE_SYSTEM.md` with runtime transparency section and ready-to-run `journalctl/grep` verification commands.

## [2.2.18] — 2026-04-17 — 1-Click UX Hardening (Tokenized Deterministic Execute + Preview + Idempotency)

### 🔐 Deterministic 1-Click Signal Execution
- Updated `website-backend/app/routes/signals.py`:
  - added server-signed `signal_token` on `GET /dashboard/signals` with payload fields:
    `signal_id`, `symbol`, `pair`, `direction`, `stop_loss`, `targets`, `generated_at`, `expires_at`, `model_source`, and signature.
  - replaced execute trust model from `symbol + generated_at` to token validation (signature + expiry).
  - execution now uses token snapshot for direction/SL/TP source and live mark price only for final sizing.
  - removed stale/dead cache path comments; route behavior remains fresh, no-cache generation.

### 🧮 New 1-Click Preview + Safer Execute Contract
- Added `POST /dashboard/signals/preview`:
  - input: `signal_token`, optional `risk_override_pct`, `all_in`, `client_request_id`.
  - output: `can_execute`, account snapshot, sizing preview, cap info, warning list.
- Updated `POST /dashboard/signals/execute` contract:
  - input now requires `signal_token` + `client_request_id` (+ optional risk override/all-in).
  - response includes canonical sizing summary and `idempotency_status` (`fresh` or `replayed`).

### 🧾 First-Class 1-Click Lifecycle Persistence
- Added `website-backend/app/db/migrations/one_click_trades.sql`:
  - new `one_click_trades` table with lifecycle statuses:
    `pending_submit`, `open`, `rejected`, `closed_tp`, `closed_sl`, `closed_manual`, `closed_unknown`.
  - unique idempotency index: `(telegram_id, client_request_id)`.
- Added `website-backend/app/services/one_click_trades.py` for attempt/open/reject/close updates and recent/open lookup helpers.

### 🛡️ Reliability + Attribution Improvements
- Updated `website-backend/app/routes/bitunix.py`:
  - source attribution now prioritizes `one_click_trades` open rows before autotrade fallback.
  - manual close flow now syncs `one_click_trades` (`closed_manual`) and coordinator close with timestamp:
    `confirm_closed(..., now_ts=time.time())`.
- Updated signal status/user-state enrichment to include one-click lifecycle outcomes in addition to autotrade snapshots.

### 🖥️ Frontend UX Hardening
- Updated `website-frontend/src/App.jsx`:
  - added pre-trade confirmation modal (entry/TP/SL, qty, margin, estimated max loss, leverage, cap warning).
  - added high-risk friction:
    - risk `>=50%`: explicit risk-ack checkbox required.
    - risk `100%`: hold-to-confirm for 1.2 seconds.
  - integrated `/dashboard/signals/preview` before execute and token-based execute payload.
  - added reason-code mapping to actionable error messages.
  - normalized 1-click risk controls to consistent snapped values (`1`, then `5`-step increments up to `100`).

### ✅ Tests
- Added `tests/test_one_click_signal_security.py`:
  - token roundtrip validation,
  - expired token rejection,
  - tampered token signature rejection,
  - sizing cap correctness with effective risk verification after cap.

## [2.2.17] — 2026-04-17 — StackMentor 3R Runner Rollout (Flagged 80/20 + BE + 5R)

### 🎯 StackMentor Runner Mode (Default OFF)
- Added feature-flagged runner controls in `Bismillah/app/stackmentor.py`:
  - `STACKMENTOR_RUNNER_ENABLED` (default `false`)
  - `STACKMENTOR_TP1_CLOSE_PCT` (default `0.80`)
  - `STACKMENTOR_TP3_RR` (default `5.0`)
- Runner OFF keeps existing behavior: full close at 3R.
- Runner ON behavior:
  - TP1 remains 3R and closes partial size (default 80%),
  - SL moves to breakeven after TP1 partial fill,
  - remaining size runs to TP3 (default 5R).

### ⚙️ Execution Path Alignment
- Updated `Bismillah/app/trade_execution.py`:
  - when runner is enabled, exchange TP attached at TP3,
  - reconciliation now validates against the TP actually placed on exchange.

### 🧾 PnL Persistence and Partial-Close Safety
- Updated `Bismillah/app/stackmentor.py` TP handlers:
  - TP1 runner path now persists partial realization while keeping trade row open,
  - TP3 close finalizes cumulative realized PnL with staged-profit fields.
- Updated `Bismillah/app/scalping_engine.py` close/update paths:
  - close quantity resolves from DB/exchange remaining size (safer after partial TP),
  - final close persistence now adds prior realized partial profit (`profit_tp1/2/3`) to final-leg PnL,
  - local stale position trackers are cleaned when DB row is no longer open.
- Updated `Bismillah/app/trade_history.py` close persistence:
  - supports cumulative PnL composition for trades with partial profit fields.

### 📣 Messaging + Docs
- Updated open/TP notifications to reflect runner mode (TP1 partial + runner TP3) when active.
- Updated `docs/02_AUTOTRADE_SYSTEM.md` StackMentor section with runner flag defaults and behavior.

## [2.2.16] — 2026-04-17 — Intro Onboarding 404 Hardening

### 🌐 Intro Subdomain Deploy Reliability
- Hardened `scripts/deploy_intro_onboarding.sh` to prevent persistent nginx `404 Not Found` on `intro.cryptomentor.id`:
  - switched default static root to nginx-safe path `/var/www/intro-cryptomentor` (with backward-compatible override support for `ROOT_DIR`/`SITE_ROOT`),
  - replaced wildcard `scp` with tar-over-ssh deploy flow and enforced readable file permissions (`chmod -R a+rX`) on deployed assets,
  - added automatic cleanup for conflicting `sites-enabled` server blocks that also claim `intro.cryptomentor.id`,
  - added VPS-local routing verification (`curl -H "Host: ..." http://127.0.0.1`) that fails deploy if `/` is not `302` or onboarding file is not `200`.
- Updated `nginx/intro-cryptomentor.conf.example` to document the same safe root (`/var/www/intro-cryptomentor`) for both HTTP-first and HTTPS phases.

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

## [2.1.1] — 2026-04-17 — Credibility-First Stress Scenario Upgrade (Onboarding + Intro)

### 🌐 Frontend (Investor Messaging Hardening)
- Updated onboarding deck growth section to lead with drawdown risk before upside projections:
  - Added interactive scenario tabs: `Conservative`, `Base`, `Stress` (default), `Extreme`
  - Added stress metrics: `Max Drawdown`, `Recovery Window`, `Outcome at 12M`
  - Added scenario-specific explanations (`Loss phase -> Stabilization -> Recovery conditions`)
  - Added “How to read this” risk-interpretation guidance
  - Reframed projection disclaimer as simulation ranges (not promises)
- Applied the same scenario explorer interaction and drawdown-first framing to intro growth section for consistency.
- Added EN + ID localization keys for all new scenario labels, metrics, explanations, and disclaimers.

### ✅ Deployment Notes
- Scope: `website-frontend/public/cryptomentor-onboarding-deck.html`, `website-frontend/public/intro.html`
- Runtime copies synced to `website-frontend/dist/*` for VPS static-site rollout.

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
