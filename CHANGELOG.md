# Changelog

## [2.1.18] — 2026-04-13 — Fix AutoTrade Risk Slider Reseting to 0.5%

### 🛠️ Bug Fix

#### 1) Fixed Slider Commit Event Bug Causing Min Clamp
- Root cause: `onMouseUp` / `onTouchEnd` / `onPointerUp` passed event objects into `commitRisk(...)`.
- `commitRisk` interpreted those events as invalid numbers and normalized to slider min (`0.5%`).
- Result was AutoTrade risk repeatedly resetting to `0.5%` after slider interactions.
- Fix:
  - Wrapped slider release handlers to call `commitRisk()` with no event payload.
  - AutoTrade risk now commits the actual selected value correctly.
- File:
  - `website-frontend/src/App.jsx`

## [2.1.17] — 2026-04-13 — Faster Risk Slider Reflection + Visible Live Build Tag

### 🚀 What Changed

#### 1) Decoupled AutoTrade vs 1-Click Slider Saving State
- AutoTrade risk slider now uses its own save/loading state.
- 1-click risk slider now uses a separate save/loading state.
- This prevents one slider save from blocking the other and improves responsiveness while users adjust risk.
- File:
  - `website-frontend/src/App.jsx`

#### 2) Added Visible Live Build Tag in Signals Header
- Signals header now shows the active bundle hash (`Build <hash>`).
- This makes it immediately clear whether users are on the latest deployed frontend.
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deployment Intent

- Deploy frontend to live nginx root and verify new bundle hash is served.
- Keep trading engine process state unchanged during rollout.

## [2.1.16] — 2026-04-13 — Faster User Reflection via In-App Update Detection

### 🚀 What Changed

#### 1) Added Automatic Frontend Update Detection Banner
- App now periodically checks deployed `index.html` for a newer hashed JS bundle.
- If a newer bundle is detected, users get a non-blocking in-app banner:
  - `Refresh Now` (immediate reload)
  - `Later` (dismiss)
- This reduces lag where users stay on old tabs and don’t see fresh changes quickly.
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deployment Verification

- Rebuilt and deployed to live nginx web root.
- Verified public HTML points to latest bundle:
  - `/assets/index-gUG7Cbpj.js`

## [2.1.15] — 2026-04-13 — 1-Click Dynamic Capacity Run-Through (Effective in Live UI)

### 🚀 What Changed

#### 1) Signals UI Now Mirrors Backend Dynamic Capacity Logic
- Updated 1-click signal cards to use live context for dynamic preview:
  - current open positions count
  - leverage tier capacity target
  - remaining slots
  - AutoTrade-running headroom ratio
- Added visible capacity line per card:
  - `Capacity: X/Y open · slots left Z`
- This aligns what users see in UI with backend concurrency-aware sizing behavior.
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deployment Verification

- Rebuilt frontend locally and deployed directly to live nginx root `/var/www/cryptomentor`.
- Verified public site now serves latest bundle:
  - `/assets/index-NklXPItR.js`
- No trading engine restart performed; engine state preserved.

## [2.1.14] — 2026-04-13 — Dynamic 1-Click Risk Sizing With Leverage-Concurrency Headroom

### 🚀 What Changed

#### 1) 1-Click Sizing Now Accounts for Leverage to Improve Concurrent Trade Capacity
- Enhanced `/dashboard/signals/execute` sizing logic so leverage increases practical concurrency:
  - Added dynamic per-trade margin budget based on leverage tier and current open positions.
  - Added reserved margin headroom when AutoTrade is running, to reduce contention between AutoTrade and 1-click.
  - Added clean rejection when no per-trade budget remains (actionable message).
- This makes risk selection more dynamic for users while preventing one trade from consuming too much available margin.
- File:
  - `website-backend/app/routes/signals.py`

#### 2) Added Rich Sizing Telemetry in Execute Response
- Response now includes effective risk and capacity fields:
  - `effective_risk_amount`, `effective_risk_pct`
  - `open_positions_count`, `max_concurrent_target`
  - `autotrade_running`
  - `margin_cap_dynamic`, `margin_cap_hard`, `effective_margin_cap`
- File:
  - `website-backend/app/routes/signals.py`

### ✅ Deploy/State Safety Notes

- Backend route deployed and `cryptomentor-web.service` restarted successfully.
- `nginx` reloaded.
- Verified trading engine untouched:
  - `cryptomentor.service` stayed `active`
  - `ExecMainPID=457177` unchanged

## [2.1.13] — 2026-04-13 — Production Web Root Deployment Fix (Reflection Issue Resolved)

### 🚀 What Changed

#### 1) Fixed Why UI Changes Were Not Reflecting Publicly
- Root cause identified: frontend deploy script uploaded to a non-served path
  (`/root/cryptomentor-bot/website-frontend/dist`) while nginx serves
  `/var/www/cryptomentor`.
- Synced latest built assets into live nginx root and reloaded nginx.
- Public site now serves current bundle:
  - `/assets/index-BBVyvRMg.js`

#### 2) Updated Deploy Scripts to Correct Live Destination
- Changed default frontend deploy target to nginx web root:
  - `deploy_frontend.py` → `/var/www/cryptomentor`
  - `deploy_frontend.ps1` → `/var/www/cryptomentor`

### ✅ Deploy/State Safety Notes

- Frontend files deployed to live web root and ownership corrected.
- Reloaded `nginx` only.
- Trading engine state verified unchanged:
  - `cryptomentor.service` remains `active`
  - `ExecMainPID=457177` unchanged

## [2.1.12] — 2026-04-13 — Precision Risk Input + Non-Blocking Warning UX

### 🚀 What Changed

#### 1) Precision Text Input Made Explicit for Risk Controls
- Risk input box is now more prominent and clearly labeled for precise typing.
- Added helper text under sliders: users can type exact risk instead of dragging only.
- Applied consistently to both:
  - AutoTrade risk slider
  - 1-Click risk slider
- File:
  - `website-frontend/src/App.jsx`

#### 2) Removed Annoying Blocking Risk Popup Flow
- Removed blocking high-risk modal confirmation from risk updates.
- High-risk remains communicated via inline danger text, without interrupting interaction.
- File:
  - `website-frontend/src/App.jsx`

#### 3) Hard Guard Against Native Browser Dialogs
- Added startup-level dialog patch (`alert/confirm/prompt`) to prevent native browser popups from appearing.
- Dialog messages are routed to in-web notice event flow.
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend-only deployment performed (no backend route/service restart).
- Reloaded `nginx` only.
- Verified trading engine state untouched:
  - `cryptomentor.service` still `active`
  - `ExecMainPID=457177` unchanged

## [2.1.11] — 2026-04-13 — Effective 1-Click Risk Display Per Signal

### 🚀 What Changed

#### 1) Risk Per Trade Display Now Uses Effective Per-Signal Calculation
- Updated each 1-click signal card to show effective risk based on reflected signal values:
  - Entry zone midpoint
  - Stop loss distance
  - Estimated position size and margin
  - Margin-cap impact (95% available balance cap)
- Main `1-Click will risk` value now reflects effective loss at SL (not only raw target % of equity).
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend rebuilt and redeployed to VPS with latest JS:
  - `index-B-6fjmST.js`
- Reloaded `nginx` successfully.

## [2.1.10] — 2026-04-13 — Force Native Browser Dialogs Into In-App Modal

### 🚀 What Changed

#### 1) Hard Block on Browser Popup Dialogs
- Added app-level runtime override for native dialogs:
  - `window.alert`
  - `window.confirm`
  - `window.prompt`
- All such calls are now routed to in-web modal notice UI (`NoticeModal`) so users no longer see browser popup boxes.
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend rebuilt and redeployed to VPS with latest JS:
  - `index-CLSata6O.js`
- Reloaded `nginx` successfully.

## [2.1.9] — 2026-04-13 — Live Per-Signal 1-Click Risk Recalculation

### 🚀 What Changed

#### 1) Recalculate 1-Click Risk Across All Signal Pairs on Slider Change
- Each 1-click signal card now recalculates risk panel metrics live when risk slider changes.
- Recalculation is signal-specific (based on that card’s reflected signal values):
  - Entry zone midpoint
  - Stop loss distance (%)
  - Estimated position size (USDT)
  - Estimated margin (USDT, using selected leverage)
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend rebuilt and redeployed to VPS with latest assets:
  - `index-B18f90b3.css`
  - `index-C3uGWPSU.js`
- Reloaded `nginx` successfully.

## [2.1.8] — 2026-04-13 — Segregated AutoTrade vs 1-Click Risk Controls

### 🚀 What Changed

#### 1) Separated Risk Sliders by Trade Type
- AutoTrade risk and 1-click risk are now independent settings.
- Engine tab controls `AutoTrade` risk only.
- Signals/1-click controls update `1-click` risk only.
- Files:
  - `website-frontend/src/App.jsx`
  - `website-backend/app/routes/dashboard.py`
  - `website-backend/app/routes/signals.py`

#### 2) AutoTrade Risk Range Restored
- AutoTrade slider range is now **0.5% to 10%**.
- Default AutoTrade risk is now **5%**.
- Backend validation now enforces the same range for AutoTrade updates.
- Files:
  - `website-frontend/src/App.jsx`
  - `website-backend/app/routes/dashboard.py`

#### 3) Numeric Risk Input Added Beside Slider
- Users can type exact risk percentage directly beside each slider.
- Input respects min/max clamp and commits on `Enter`/blur.
- Files:
  - `website-frontend/src/App.jsx`

#### 4) Warning Popup Behavior De-spammed During Sliding
- Slider drag now previews values live but only commits on release/Enter/blur.
- High-risk warning modal appears on commit, not repeatedly while dragging.
- File:
  - `website-frontend/src/App.jsx`

#### 5) Backward-Compatible Fallback for Existing DB Schema
- Added safe fallback when `one_click_risk_per_trade` column is unavailable:
  - Settings endpoint falls back gracefully.
  - 1-click execution accepts `risk_override_pct` from web request.
  - Frontend keeps a local persisted 1-click risk value (`localStorage`) so separation still works.
- Files:
  - `website-backend/app/routes/dashboard.py`
  - `website-backend/app/routes/signals.py`
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend rebuilt and deployed to VPS dist path:
  - `/root/cryptomentor-bot/website-frontend/dist`
- Uploaded backend route updates:
  - `/root/cryptomentor-bot/website-backend/app/routes/dashboard.py`
  - `/root/cryptomentor-bot/website-backend/app/routes/signals.py`
- Restarted `cryptomentor-web.service` and confirmed active.
- Reloaded `nginx` and confirmed active.

## [2.1.7] — 2026-04-13 — Instant Risk Reflection + Full Web Modal Migration

### 🚀 What Changed

#### 1) Risk/Trade Now Reflects During Slider Drag
- Added live risk preview path (`onPreview`) so `risk_per_trade` and all derived `Risk/Trade` values update immediately while dragging, before API commit returns.
- Applied across Engine, Signals top bar, and per-signal 1-click slider.
- Files:
  - `website-frontend/src/App.jsx`

#### 2) Removed Remaining Native Browser Popups
- Replaced Telegram login flow `alert()` errors with in-app modal (`NoticeModal`).
- Result: warning/error prompts are now rendered inside the web UI, not native browser dialogs.
- Files:
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend rebuilt and deployed to VPS dist path:
  - `/root/cryptomentor-bot/website-frontend/dist`
- Reloaded `nginx` successfully.
- No trading engine restart performed.

## [2.1.6] — 2026-04-13 — Risk Slider Sync + In-App Warning Modal (No Browser Popup)

### 🚀 What Changed

#### 1) Fixed Risk/Slider Reflection Drift
- Risk selection now updates UI immediately (optimistic sync) so all risk displays and sliders stay aligned while editing.
- Added rollback safety if risk API update fails, so UI returns to the last confirmed risk.
- Normalized numeric parsing from API responses to avoid stale/incorrect slider values.
- File:
  - `website-frontend/src/App.jsx`

#### 2) High-Risk Warning Flow Hardened
- Kept high-risk guard (`>5%`) in web UI and improved state handling:
  - Stores previous risk before warning.
  - Restores previous value if user cancels.
  - Applies selected risk only after confirmation.
- File:
  - `website-frontend/src/App.jsx`

#### 3) Replaced Browser Warning Popup With Web Modal (API Bridge Disconnect)
- Removed native browser `confirm()` flow for API Bridge disconnect.
- Added integrated in-app warning modal for disconnect confirmation.
- Added in-app success message for key test/connection status (removing native popup dependency).
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend rebuilt and deployed to VPS dist path:
  - `/root/cryptomentor-bot/website-frontend/dist`
- Reloaded `nginx` successfully.
- No trading engine service restart performed for this frontend-only patch.

## [2.1.5] — 2026-04-13 — Risk Slider Reflection Hotfix (Live Sync While Sliding)

### 🚀 What Changed

#### 1) Fixed Risk Not Reflecting in Dashboard Summary
- Resolved mismatch where slider draft value (e.g., `56%`) could display while `Risk/Trade` still showed previous persisted risk.
- Root cause: commit timing on some touch/mobile interactions.
- Hotfix:
  - Added auto-commit while slider moves (short debounce).
  - Added robust commit triggers (`mouse`, `touch`, `pointer`, `enter`).
- File:
  - `website-frontend/src/App.jsx`

#### 2) Re-verified Backend Acceptance for Extended Risk Range
- Confirmed live backend routes are aligned for risk updates beyond legacy `5%` cap:
  - `website-backend/app/routes/dashboard.py`
  - `website-backend/app/routes/signals.py`

### ✅ Deploy/State Safety Notes

- Performed **state-safe deploy**:
  - Restarted `cryptomentor-web.service` only
  - Reloaded `nginx`
  - **Did not restart `cryptomentor.service` (trading bot engine)**
- Verified bot engine process continuity:
  - `ExecMainPID` unchanged before/after deploy (`457177`)
  - Active enter timestamp unchanged

## [2.1.4] — 2026-04-13 — Risk Slider Upgrade (0.5% → ALL IN 100%) + High-Risk Safeguards

### 🚀 What Changed

#### 1) Unified Risk Slider Across Web
- Replaced fixed risk buttons with a real slider in:
  - Engine Controls risk management
  - Signals risk control bar
  - Per-signal 1-click risk control
  - Onboarding risk configuration step
- New range: **0.5% to 100% (ALL IN)**.
- File:
  - `website-frontend/src/App.jsx`

#### 2) Mandatory High-Risk Warning Pop-up
- Added confirmation pop-up for any risk selection **above 5%**.
- Added stronger warning text for **100% ALL IN** selection.
- Warning is enforced in shared risk update flow so it applies consistently from all UI entry points.
- File:
  - `website-frontend/src/App.jsx`

#### 3) Backend Risk Range Expanded
- Updated dashboard/API validation and normalization to support **0.5% - 100%**:
  - `website-backend/app/routes/dashboard.py`
  - `website-backend/app/routes/signals.py`

#### 4) Bot/Engine Risk Clamp Alignment
- Updated bot-side persistence and risk clamps to the same range to avoid web/bot mismatch:
  - `Bismillah/app/supabase_repo.py`
  - `Bismillah/app/autotrade_engine.py`
  - `Bismillah/app/scalping_engine.py`

### ✅ Deploy/State Safety Notes

- Deployed with **state-safe policy**:
  - Updated frontend static bundle + website backend routes
  - Reloaded/restarted web-facing services only
  - **Did not restart active trading engine service** during this deployment step
- Goal: preserve currently running user autotrade sessions while applying web risk UX and API changes.

## [2.1.3] — 2026-04-12 — V4.0 Branding Sync (Bot + Web)

### 🚀 What Changed

#### 1) Login Hero Version Upgrade
- Updated login hero version label in web frontend:
  - `V2.0 AutoTrade Engine` → `V4.0 Unified Trading System`
- File:
  - `website-frontend/src/App.jsx`

#### 2) Feature Highlights Synced to Current Platform
- Replaced legacy login-card bullets to reflect current architecture:
  - Unified **Bot + Web** control for AutoTrade and 1-Click execution
  - Adaptive risk engine with position sizing up to **5%** equity risk
  - Professional trade lifecycle alerts (open, close, live status)
- File:
  - `website-frontend/src/App.jsx`

### ✅ Deploy/State Safety Notes

- Frontend-only deploy path used for this change.
- No trading engine logic, parameters, or backend route behavior changed.
- Bot/engine runtime state is preserved (no engine session resets required).

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
