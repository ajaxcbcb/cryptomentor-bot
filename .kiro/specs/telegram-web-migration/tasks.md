# Implementation Plan: Telegram to Web Migration

## Overview

This implementation plan breaks down the Telegram-to-Web migration into discrete, incremental tasks following the vibe coding breakdown. Each task is self-contained and maps directly to a step in the migration. Complete them in order.

**Implementation Language:** Python (FastAPI backend), React (frontend), python-telegram-bot (Telegram bot)

**Implementation Status:** Not started.

## Tasks

- [x] 1. Backend — Verification Status Endpoint
  - Add `GET /user/verification-status` endpoint in `website-backend/app/routes/user.py`
    - Extract `telegram_id` from JWT token
    - Query `autotrade_sessions` where `telegram_id = user_id`
    - Return JSON with `status`, `exchange`, `uid`, `community_code`
    - If no session found → return `{"status": "none"}`
  - Add `POST /user/submit-uid` endpoint in `website-backend/app/routes/user.py`
    - Extract `telegram_id` from JWT token
    - Accept body: `{"uid": "123456789"}`
    - Validate: UID must be numeric, min 5 digits — return 400 if invalid
    - Upsert to `autotrade_sessions` with `status = "pending_verification"`
    - Send admin Telegram notification with approve/reject inline keyboard (reuse logic from `handlers_autotrade.py:780-830`)
    - Return `{"status": "pending_verification"}`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  - **Test:** Call `GET /user/verification-status` with valid JWT → `{"status": "none"}` for new user. Call `POST /user/submit-uid` with `{"uid": "123456"}` → `{"status": "pending_verification"}` and admin receives Telegram message.

- [x] 2. Backend — Verification Guard Middleware
  - Create `website-backend/app/middleware/verification_guard.py` (NEW file)
    - Define `UNPROTECTED_ROUTES` list: `/auth/`, `/user/me`, `/user/verification-status`, `/user/submit-uid`, `/dashboard/system`
    - Implement `is_protected_route(path)` function
    - Implement middleware that checks `autotrade_sessions.status` for protected routes
    - Return 403 with `{"error": "verification_required", "status": "<current_status>"}` for unverified users
  - Apply verification check to route groups: `/bitunix/*`, `/dashboard/engine/*`, `/dashboard/signals/*`
  - Register middleware in `website-backend/main.py`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  - **Test:** Call `POST /bitunix/keys` without verified session → 403. After verification → succeeds.

- [x] 3. Backend — Leverage & Margin Settings Endpoints
  - Add `PUT /dashboard/settings/leverage` in `website-backend/app/routes/dashboard.py`
    - Accept body: `{"leverage": 10}`
    - Validate: integer, range 1-20 — return 400 if invalid
    - Update `autotrade_sessions` set `leverage = value`
    - Return `{"leverage": 10}`
  - Add `PUT /dashboard/settings/margin-mode` in `website-backend/app/routes/dashboard.py`
    - Accept body: `{"margin_mode": "cross"}`
    - Validate: must be `"cross"` or `"isolated"` — return 400 if invalid
    - Update `autotrade_sessions` set `margin_mode = value`
    - Return `{"margin_mode": "cross"}`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - **Test:** `PUT /dashboard/settings/leverage` with `{"leverage": 15}` → DB updated. With `{"leverage": 25}` → 400 error.

- [x] 4. Frontend — Verification Gate & Registration Flow
  - Add `verStatus` state to `App.jsx`: `const [verStatus, setVerStatus] = useState(null)`
  - Add `useEffect` to fetch `/user/verification-status` on login
  - Create `<GatekeeperScreen />` component (shown when `verStatus.status === 'none'`):
    - Title: "Welcome to CryptoMentor AutoTrade"
    - Subtitle: "Complete your Bitunix registration to start trading"
    - Step 1: Bitunix referral link button → `https://www.bitunix.com/register?vipCode=sq45`
    - Step 2: UID input field + [Submit for Verification] button
    - On submit → `POST /user/submit-uid` → transition to pending screen on success
  - Create `<VerificationPendingScreen />` component (shown when `verStatus.status === 'pending_verification'`):
    - Spinner/hourglass icon
    - "Your Bitunix UID is being verified"
    - "You'll receive a Telegram notification once approved"
    - [Refresh Status] button → re-fetches `/user/verification-status`
    - Auto-poll every 30 seconds using `setInterval`
  - Add gate logic to main render in `App.jsx`:
    - `verStatus.status === 'none'` → render `<GatekeeperScreen />`
    - `verStatus.status === 'pending_verification'` → render `<VerificationPendingScreen />`
    - Otherwise → render normal dashboard
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_
  - **Test:** Login as new user → see registration screen. Submit UID → see pending screen. Admin approves → refresh → see dashboard.

- [x] 5. Frontend — Onboarding Wizard
  - Create `<OnboardingWizard />` component in `website-frontend/src/App.jsx`
    - Triggered when: `verStatus.status` is `'uid_verified'` or `'active'` AND `connectorStatus.linked === false`
    - 3-step wizard with progress bar
  - Implement Wizard Step 1 — Connect Bitunix API Key:
    - API Key input (text), API Secret input (password type)
    - Expandable guide section: "How to create your API Key"
    - [Open Bitunix API Management] button → `https://www.bitunix.com/account/api-management`
    - [Test Connection] button → `POST /bitunix/keys/test` → green checkmark on success, red error on failure
    - [Save & Continue] button → `POST /bitunix/keys` → advance to Step 2 on success
  - Implement Wizard Step 2 — Configure Risk:
    - Risk per trade: 4 toggle buttons `[0.25%] [0.5%] [0.75%] [1.0%]` (default 0.5%)
      - On select → `PUT /dashboard/settings/risk` with `{risk_per_trade: value}`
    - Leverage: number input 1x-20x (default 10x)
      - On change → `PUT /dashboard/settings/leverage` with `{leverage: value}`
    - Margin mode: 2 toggle buttons `[Cross ♾️] [Isolated 🔒]` (default cross)
      - On select → `PUT /dashboard/settings/margin-mode` with `{margin_mode: value}`
    - [Continue] button → advance to Step 3
  - Implement Wizard Step 3 — Start Trading:
    - Summary card: `🏦 Bitunix  |  🔑 ...xxxx  |  ⚙️ 10x Cross  |  📊 0.5% risk`
    - [🚀 Start AutoTrade Engine] button → `POST /dashboard/engine/start` → set `activeTab = 'portfolio'`, hide wizard
    - [Skip for now] link → go to dashboard without starting engine
  - Add wizard trigger in main render:
    - `verStatus.status in ['uid_verified','active'] && connectorStatus?.linked === false` → render `<OnboardingWizard />`
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10_
  - **Test:** Login as verified user with no API keys → see wizard. Enter API key → test → save → configure risk → start engine → lands on portfolio with live data.

- [x] 6. Telegram Bot — Rewrite `/start` as Gatekeeper
  - Add `WEB_DASHBOARD_URL` constant at top of `Bismillah/app/handlers_autotrade.py`:
    ```python
    WEB_DASHBOARD_URL = os.getenv("WEB_DASHBOARD_URL", "https://app.cryptomentor.ai")
    ```
  - Rewrite `cmd_autotrade()` function:
    - For RETURNING users (has API keys + active/verified session): show welcome back message with [Open Dashboard], [Quick Status], [Support] buttons
    - For NEW users (no session or not verified): show exchange selection keyboard (Bitunix, Bybit Coming Soon, Binance Coming Soon, BingX, Cancel)
  - Update `callback_confirm_referral()`:
    - Remove `WAITING_API_KEY` state
    - Ask for UID directly → return `WAITING_BITUNIX_UID`
  - Update `callback_uid_approve()`:
    - After admin approves, send user message with [Open Dashboard] button and instructions to complete setup on web
  - Remove conversation states from ConversationHandler:
    - `WAITING_API_KEY`, `WAITING_API_SECRET`, `WAITING_TRADE_AMOUNT`, `WAITING_LEVERAGE`, `WAITING_NEW_LEVERAGE`, `WAITING_NEW_AMOUNT`, `WAITING_MANUAL_MARGIN`
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  - **Test:** Send `/start` as new user → see exchange selection. Select Bitunix → see referral + UID input (NOT API key input). Submit UID → admin approves → user gets "Open Dashboard" button.

- [x] 7. Telegram Bot — Simplify Menu System
  - In `Bismillah/menu_system.py`, replace `build_main_menu()`:
    - 3 buttons only: [Open Dashboard], [Account Status], [Support]
  - In `Bismillah/menu_handlers.py`, replace all feature handlers with redirect responses:
    - Define `REDIRECT_MESSAGE` and `REDIRECT_KEYBOARD` constants
    - Create `handle_redirect(update, context)` function
    - Apply to all old callbacks: `portfolio_status`, `engine_controls`, `signals_market`, etc.
  - Add `handle_account_status(update, context)` handler:
    - Query session and API keys for the user
    - Show: verification status, API key hint (`...xxxx`), engine running status
    - Buttons: [Open Dashboard], [Back]
  - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - **Test:** `/menu` → see 3 buttons. Tap "Account Status" → see verification/key/engine status. Tap "Open Dashboard" → web opens.

- [x] 8. Telegram Bot — Redirect Retired Commands
  - In `Bismillah/bot.py`, create `redirect_to_web(update, context)` generic handler
  - Replace command registrations for retired commands with `redirect_to_web`:
    - `/analyze`, `/futures`, `/futures_signals`, `/signal`, `/signals`
    - `/ai`, `/chat`, `/aimarket`, `/free_signal`
    - `/portfolio`, `/price`, `/market`
  - Keep unchanged: `/start`, `/autotrade`, `/id`, `/help`, `/admin`, `/set_premium`, `/remove_premium`, `/grant_credits`, `/signal_on`, `/signal_off`, `/signal_status`, `/serverip`
  - Update `/help` command text to reflect new bot purpose (gatekeeper + notifications)
  - _Requirements: 8.1, 8.2, 8.3_
  - **Test:** Send `/analyze BTCUSDT` → see redirect message. Send `/portfolio` → see redirect message. Send `/admin` → still works normally.

- [x] 9. Telegram Bot — Update Notifications with Dashboard Link
  - In `Bismillah/app/autotrade_engine.py`, find all `send_message` calls for trade notifications
  - Add `reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 View on Dashboard", url=WEB_DASHBOARD_URL)]])` to:
    - Trade opened notification
    - Trade closed notification (TP hit / SL hit)
    - Engine started/stopped notification
    - Error notifications (API disconnected, etc.)
  - Import `WEB_DASHBOARD_URL` from `handlers_autotrade.py` or define separately in engine file
  - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - **Test:** Start engine on web → wait for trade → verify Telegram notification includes "View on Dashboard" button.

- [x] 10. Cleanup — Remove Retired Handler Files
  - Delete the following files:
    - `Bismillah/app/handlers_manual_signals.py`
    - `Bismillah/app/handlers_deepseek.py`
    - `Bismillah/app/handlers_free_signal.py`
    - `Bismillah/app/handlers_skills.py`
    - `Bismillah/app/handlers_risk_mode.py`
  - In `Bismillah/bot.py`:
    - Remove all `import` statements for deleted files
    - Remove all `add_handler()` registrations for handlers from deleted files
  - Verify compilation:
    - Run `python -m py_compile Bismillah/bot.py` → must succeed
    - Run `python -m py_compile Bismillah/app/handlers_autotrade.py` → must succeed
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - **Test:** Bot starts without errors. All remaining commands work. Deleted commands show redirect.

- [x] 11. Documentation — Update CHANGELOG.md
  - Add new section to `CHANGELOG.md` documenting the migration:
    - What changed: Telegram bot is now a gatekeeper
    - Why: Better UX, unified platform, easier maintenance
    - What users should do: Use web dashboard for all trading features
    - What stayed: Notifications, admin commands, UID verification
  - Commit and push:
    ```bash
    git add -A
    git commit -m "feat(migration): migrate autotrade from telegram bot to web dashboard"
    git push ajax master
    ```
  - _Requirements: all_
  - **Test:** Verify changelog is clear and complete. Verify push succeeds.
