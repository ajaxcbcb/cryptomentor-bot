# Requirements Document: Telegram to Web Migration

## Introduction

This document specifies the requirements for migrating the CryptoMentor AutoTrade feature from a Telegram-only interface to a web-first platform. The Telegram bot will be simplified into a gatekeeper and notification hub, while all trading management features move to the web dashboard. This migration improves UX, reduces bot complexity, and creates a unified platform experience.

## Glossary

- **Gatekeeper**: The simplified Telegram bot role — handles UID verification and sends notifications only
- **Web Dashboard**: The React frontend at `website-frontend/` that becomes the primary trading interface
- **Verification Gate**: The UI flow that blocks unverified users from accessing trading features
- **Onboarding Wizard**: A 3-step web UI flow for new users to connect API keys, configure risk, and start trading
- **UID Verification**: The process where admin approves a user's Bitunix UID before they can trade
- **WEB_DASHBOARD_URL**: The public URL of the web dashboard, stored as environment variable
- **Retired Commands**: Telegram commands that are removed and replaced with web redirects

## Requirements

### Requirement 1: Verification Status API

**User Story:** As a user, I want the web dashboard to know my verification status, so that it can show me the right screen.

#### Acceptance Criteria

1. WHEN a user calls `GET /user/verification-status` with a valid JWT, THE Platform SHALL return their current status (`none`, `pending_verification`, `uid_verified`, `active`)
2. WHEN no autotrade session exists for the user, THE Platform SHALL return `{"status": "none"}`
3. WHEN returning status, THE Platform SHALL include `exchange`, `uid`, and `community_code` fields
4. WHEN a user calls `POST /user/submit-uid` with a valid UID, THE Platform SHALL upsert to `autotrade_sessions` with status `pending_verification`
5. WHEN a UID is submitted, THE Platform SHALL validate it is numeric and at least 5 digits
6. WHEN a UID is submitted, THE Platform SHALL send an admin Telegram notification with approve/reject inline keyboard

### Requirement 2: Verification Guard

**User Story:** As the platform, I want to protect trading routes from unverified users, so that only verified users can access trading features.

#### Acceptance Criteria

1. WHEN a request hits a protected route without a verified session, THE Platform SHALL return HTTP 403 with `{"error": "verification_required"}`
2. WHEN returning 403, THE Platform SHALL include the current verification status in the response
3. THE Platform SHALL NOT protect auth routes, profile routes, verification status routes, and health check routes
4. WHEN a user's session status is `uid_verified` or `active`, THE Platform SHALL allow access to protected routes
5. THE Platform SHALL register the verification guard middleware in `main.py`

### Requirement 3: Leverage and Margin Settings API

**User Story:** As a user, I want to configure leverage and margin mode from the web dashboard, so that I don't need to use the Telegram bot.

#### Acceptance Criteria

1. WHEN a user calls `PUT /dashboard/settings/leverage` with a valid value, THE Platform SHALL update `autotrade_sessions.leverage`
2. WHEN leverage value is outside 1-20 range, THE Platform SHALL return HTTP 400 validation error
3. WHEN a user calls `PUT /dashboard/settings/margin-mode` with a valid value, THE Platform SHALL update `autotrade_sessions.margin_mode`
4. WHEN margin_mode is not `cross` or `isolated`, THE Platform SHALL return HTTP 400 validation error
5. WHEN settings are updated, THE Platform SHALL return the updated value in the response

### Requirement 4: Verification Gate UI

**User Story:** As a new user, I want to see a registration screen when I first log in, so that I know how to get started.

#### Acceptance Criteria

1. WHEN a logged-in user has `verStatus.status === 'none'`, THE Platform SHALL show the `GatekeeperScreen` component
2. WHEN `GatekeeperScreen` is shown, THE Platform SHALL display a Bitunix referral link button (`https://www.bitunix.com/register?vipCode=sq45`)
3. WHEN `GatekeeperScreen` is shown, THE Platform SHALL provide a UID input field and submit button
4. WHEN a user submits their UID, THE Platform SHALL call `POST /user/submit-uid` and transition to pending screen
5. WHEN a logged-in user has `verStatus.status === 'pending_verification'`, THE Platform SHALL show the `VerificationPendingScreen` component
6. WHEN `VerificationPendingScreen` is shown, THE Platform SHALL auto-poll `/user/verification-status` every 30 seconds
7. WHEN `VerificationPendingScreen` is shown, THE Platform SHALL provide a manual [Refresh Status] button

### Requirement 5: Onboarding Wizard UI

**User Story:** As a verified user with no API keys, I want a guided setup wizard, so that I can start trading without confusion.

#### Acceptance Criteria

1. WHEN a verified user has no API keys linked (`connectorStatus.linked === false`), THE Platform SHALL show the `OnboardingWizard` component
2. WHEN Wizard Step 1 is shown, THE Platform SHALL provide API Key and API Secret input fields
3. WHEN Wizard Step 1 is shown, THE Platform SHALL provide a [Test Connection] button that calls `POST /bitunix/keys/test`
4. WHEN connection test succeeds, THE Platform SHALL show a green checkmark; on failure, show a red error
5. WHEN [Save & Continue] is clicked, THE Platform SHALL call `POST /bitunix/keys` and advance to Step 2
6. WHEN Wizard Step 2 is shown, THE Platform SHALL provide risk per trade toggle buttons (0.25%, 0.5%, 0.75%, 1.0%)
7. WHEN Wizard Step 2 is shown, THE Platform SHALL provide leverage input (1x-20x) and margin mode toggle (Cross/Isolated)
8. WHEN Wizard Step 3 is shown, THE Platform SHALL show a summary of all configured settings
9. WHEN [Start AutoTrade Engine] is clicked, THE Platform SHALL call `POST /dashboard/engine/start` and navigate to portfolio tab
10. WHEN [Skip for now] is clicked, THE Platform SHALL navigate to the dashboard without starting the engine

### Requirement 6: Telegram Bot Gatekeeper Mode

**User Story:** As a new Telegram user, I want the bot to guide me through UID verification, so that I can get started without needing to know the web dashboard URL.

#### Acceptance Criteria

1. WHEN a new user sends `/autotrade`, THE Platform SHALL show exchange selection keyboard (Bitunix, Bybit Coming Soon, Binance Coming Soon, BingX)
2. WHEN a returning user (has API keys + active session) sends `/autotrade`, THE Platform SHALL show a welcome back message with dashboard link
3. WHEN a user selects Bitunix, THE Platform SHALL ask for UID only (NOT API key)
4. WHEN admin approves a UID, THE Platform SHALL send the user a message with a [Open Dashboard] button
5. THE Platform SHALL remove conversation states: `WAITING_API_KEY`, `WAITING_API_SECRET`, `WAITING_TRADE_AMOUNT`, `WAITING_LEVERAGE`, `WAITING_NEW_LEVERAGE`, `WAITING_NEW_AMOUNT`, `WAITING_MANUAL_MARGIN`
6. THE Platform SHALL add `WEB_DASHBOARD_URL` constant at the top of `handlers_autotrade.py`

### Requirement 7: Simplified Telegram Menu

**User Story:** As a Telegram user, I want a simple menu that directs me to the web dashboard, so that I don't get confused by outdated features.

#### Acceptance Criteria

1. WHEN the main menu is displayed, THE Platform SHALL show only 3 buttons: Open Dashboard, Account Status, Support
2. WHEN any retired feature callback is triggered, THE Platform SHALL respond with a redirect message and [Open Dashboard] button
3. WHEN [Account Status] is tapped, THE Platform SHALL show verification status, API key hint, and engine status
4. WHEN [Account Status] is shown, THE Platform SHALL include an [Open Dashboard] button and [Back] button

### Requirement 8: Retired Command Redirects

**User Story:** As a user who sends an old command, I want to be redirected to the web dashboard, so that I know where to find the feature.

#### Acceptance Criteria

1. WHEN a user sends `/analyze`, `/futures`, `/futures_signals`, `/signal`, `/signals`, `/ai`, `/chat`, `/aimarket`, `/free_signal`, `/portfolio`, `/price`, or `/market`, THE Platform SHALL respond with a redirect message and [Open Dashboard] button
2. THE Platform SHALL keep `/start`, `/autotrade`, `/id`, `/help`, `/admin`, and admin commands unchanged
3. WHEN `/help` is sent, THE Platform SHALL show updated help text reflecting the new bot purpose

### Requirement 9: Trade Notification Dashboard Links

**User Story:** As a user, I want trade notifications to include a dashboard link, so that I can quickly view my positions.

#### Acceptance Criteria

1. WHEN a trade is opened, THE Platform SHALL include a [View on Dashboard] button in the Telegram notification
2. WHEN a trade is closed (TP or SL), THE Platform SHALL include a [View on Dashboard] button in the notification
3. WHEN the engine starts or stops, THE Platform SHALL include a [View on Dashboard] button in the notification
4. WHEN an error notification is sent (API disconnected, etc.), THE Platform SHALL include a [View on Dashboard] button

### Requirement 10: Handler Cleanup

**User Story:** As a developer, I want retired handler files removed, so that the codebase is clean and maintainable.

#### Acceptance Criteria

1. THE Platform SHALL delete `handlers_manual_signals.py`, `handlers_deepseek.py`, `handlers_free_signal.py`, `handlers_skills.py`, and `handlers_risk_mode.py`
2. WHEN handler files are deleted, THE Platform SHALL remove all their imports from `bot.py`
3. WHEN handler files are deleted, THE Platform SHALL remove all their handler registrations from `bot.py`
4. AFTER cleanup, `python -m py_compile Bismillah/bot.py` SHALL succeed without errors
5. AFTER cleanup, `python -m py_compile Bismillah/app/handlers_autotrade.py` SHALL succeed without errors
