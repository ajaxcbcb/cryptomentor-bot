# Design Document: Telegram to Web Migration

## Overview

This design document describes the technical architecture for migrating CryptoMentor AutoTrade from a Telegram-only interface to a web-first platform. The Telegram bot is simplified into a gatekeeper and notification hub, while all trading management features move to the web dashboard.

### Key Design Principles

1. **Web-First**: All trading configuration and monitoring happens on the web dashboard
2. **Gatekeeper Bot**: Telegram bot handles only UID verification flow and trade notifications
3. **Verification Gate**: New users must complete UID verification before accessing trading features
4. **Guided Onboarding**: Verified users with no API keys see a 3-step wizard to get started
5. **Backward Compatible**: Existing users with active sessions are not disrupted
6. **Clean Codebase**: Retired Telegram handlers are deleted, not just disabled

### Technology Stack

- **Backend**: Python (FastAPI) — `website-backend/`
- **Frontend**: React (Vite) — `website-frontend/`
- **Telegram Bot**: python-telegram-bot — `Bismillah/`
- **Database**: Supabase (PostgreSQL) — `autotrade_sessions` table
- **Auth**: JWT tokens for web API authentication

## Architecture

### Migration Overview

```
BEFORE:
  Telegram Bot
  ├── /autotrade → full onboarding (API key, leverage, risk, etc.)
  ├── /portfolio → position status
  ├── /analyze   → market analysis
  ├── /signals   → signal generation
  └── /ai        → AI chat

AFTER:
  Telegram Bot (Gatekeeper)
  ├── /autotrade → UID verification only → "Open Dashboard" button
  ├── /menu      → 3 buttons: Dashboard, Status, Support
  └── All other commands → redirect to web

  Web Dashboard (Primary Interface)
  ├── Verification Gate (new users)
  ├── Onboarding Wizard (verified, no API keys)
  └── Full Dashboard (active users)
```

### Request Flow — New User

```
User opens web → Login → Check /user/verification-status
                                    ↓
                            status === 'none'
                                    ↓
                        Show GatekeeperScreen
                        (Bitunix referral + UID input)
                                    ↓
                        POST /user/submit-uid
                                    ↓
                        Admin receives Telegram notification
                        (Approve / Reject buttons)
                                    ↓
                        status === 'pending_verification'
                                    ↓
                        Show VerificationPendingScreen
                        (auto-poll every 30s)
                                    ↓
                        Admin approves → status = 'uid_verified'
                                    ↓
                        User gets Telegram: "Open Dashboard" button
                                    ↓
                        Web detects uid_verified + no API keys
                                    ↓
                        Show OnboardingWizard (3 steps)
                                    ↓
                        Step 1: Connect API Key
                        Step 2: Configure Risk/Leverage
                        Step 3: Start Engine
                                    ↓
                        Full Dashboard
```

### Request Flow — Returning User

```
User opens web → Login → Check /user/verification-status
                                    ↓
                            status === 'active'
                                    ↓
                        Check connectorStatus.linked
                                    ↓
                            linked === true
                                    ↓
                        Show Full Dashboard (no wizard)
```

## Components and Interfaces

### 1. Backend — Verification Status Endpoint

**File:** `website-backend/app/routes/user.py`

**New Endpoints:**

```python
GET /user/verification-status
# Headers: Authorization: Bearer <jwt>
# Response:
{
  "status": "none" | "pending_verification" | "uid_verified" | "active",
  "exchange": "bitunix" | null,
  "uid": "123456789" | null,
  "community_code": "XXXX" | null
}

POST /user/submit-uid
# Headers: Authorization: Bearer <jwt>
# Body: {"uid": "123456789"}
# Validation: numeric, min 5 digits
# Response: {"status": "pending_verification"}
# Side effect: sends admin Telegram notification with approve/reject keyboard
```

**Admin Notification Format:**
```python
keyboard = [[
    InlineKeyboardButton("✅ Approve", callback_data=f"uid_acc_{user_id}"),
    InlineKeyboardButton("❌ Reject", callback_data=f"uid_reject_{user_id}")
]]
# Sent to all admin_ids from config
```

### 2. Backend — Verification Guard Middleware

**File:** `website-backend/app/middleware/verification_guard.py` (NEW)

```python
UNPROTECTED_ROUTES = [
    "/auth/",
    "/user/me",
    "/user/verification-status",
    "/user/submit-uid",
    "/dashboard/system",
]

def is_protected_route(path: str) -> bool:
    return not any(path.startswith(prefix) for prefix in UNPROTECTED_ROUTES)

# Returns 403 for unverified users on protected routes:
# {"error": "verification_required", "status": "none|pending_verification"}
```

**Protected Route Groups:**
- `/bitunix/*` — exchange API key management
- `/dashboard/engine/*` — engine start/stop
- `/dashboard/signals/*` — signal management

### 3. Backend — Settings Endpoints

**File:** `website-backend/app/routes/dashboard.py`

**New Endpoints:**

```python
PUT /dashboard/settings/leverage
# Body: {"leverage": 10}
# Validation: integer, 1-20
# Updates: autotrade_sessions.leverage
# Response: {"leverage": 10}

PUT /dashboard/settings/margin-mode
# Body: {"margin_mode": "cross"}
# Validation: "cross" or "isolated"
# Updates: autotrade_sessions.margin_mode
# Response: {"margin_mode": "cross"}
```

### 4. Frontend — Verification Gate

**File:** `website-frontend/src/App.jsx`

**State additions:**
```jsx
const [verStatus, setVerStatus] = useState(null); // null = loading

useEffect(() => {
  if (!isLoggedIn) return;
  fetch(`${base}/user/verification-status`, { headers: authHeaders })
    .then(r => r.json())
    .then(setVerStatus);
}, [isLoggedIn]);
```

**GatekeeperScreen component:**
- Title: "Welcome to CryptoMentor AutoTrade"
- Step 1: Bitunix referral link button → `https://www.bitunix.com/register?vipCode=sq45`
- Step 2: UID input field + [Submit for Verification] button
- On submit → `POST /user/submit-uid` → transition to pending screen

**VerificationPendingScreen component:**
- Spinner/hourglass icon
- "Your Bitunix UID is being verified"
- "You'll receive a Telegram notification once approved"
- [Refresh Status] button → re-fetches `/user/verification-status`
- Auto-poll every 30 seconds

**Gate logic in main render:**
```jsx
if (isLoggedIn && verStatus?.status === 'none')
  return <GatekeeperScreen onSubmit={...} />;
if (isLoggedIn && verStatus?.status === 'pending_verification')
  return <VerificationPendingScreen onRefresh={...} />;
// else: render normal dashboard
```

### 5. Frontend — Onboarding Wizard

**File:** `website-frontend/src/App.jsx`

**Wizard trigger:**
```jsx
if (isLoggedIn && ['uid_verified','active'].includes(verStatus?.status) && connectorStatus?.linked === false)
  return <OnboardingWizard onComplete={() => { fetchConnectorStatus(); setActiveTab('portfolio'); }} />;
```

**Step 1 — Connect Bitunix API Key:**
- API Key input (text), API Secret input (password)
- Expandable guide: "How to create your API Key"
- [Open Bitunix API Management] button → `https://www.bitunix.com/account/api-management`
- [Test Connection] → `POST /bitunix/keys/test` → green checkmark or red error
- [Save & Continue] → `POST /bitunix/keys` → advance to Step 2

**Step 2 — Configure Risk:**
- Risk per trade: 4 toggle buttons `[0.25%] [0.5%] [0.75%] [1.0%]` (default 0.5%)
  - On select → `PUT /dashboard/settings/risk`
- Leverage: number input 1x-20x (default 10x)
  - On change → `PUT /dashboard/settings/leverage`
- Margin mode: 2 toggle buttons `[Cross ♾️] [Isolated 🔒]` (default cross)
  - On select → `PUT /dashboard/settings/margin-mode`
- [Continue] → advance to Step 3

**Step 3 — Start Trading:**
- Summary card:
  ```
  🏦 Bitunix  |  🔑 ...xxxx  |  ⚙️ 10x Cross  |  📊 0.5% risk
  ```
- [🚀 Start AutoTrade Engine] → `POST /dashboard/engine/start` → navigate to portfolio
- [Skip for now] → go to dashboard without starting engine

### 6. Telegram Bot — Gatekeeper Rewrite

**File:** `Bismillah/app/handlers_autotrade.py`

**`cmd_autotrade()` rewrite:**

For RETURNING users (has API keys + active/verified session):
```python
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)],
    [InlineKeyboardButton("📋 Quick Status", callback_data="at_quick_status")],
    [InlineKeyboardButton("💬 Support", callback_data="at_support")],
])
```

For NEW users (no session or not verified):
```python
keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("Bitunix", callback_data="at_exchange_bitunix")],
    [InlineKeyboardButton("Bybit (Coming Soon)", callback_data="at_coming_soon")],
    [InlineKeyboardButton("Binance (Coming Soon)", callback_data="at_coming_soon")],
    [InlineKeyboardButton("BingX", callback_data="at_exchange_bingx")],
    [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")],
])
```

**`callback_confirm_referral()` update:**
- OLD: asks for API key → `WAITING_API_KEY`
- NEW: asks for UID only → `WAITING_BITUNIX_UID`

**`callback_uid_approve()` update:**
- After admin approves, send user message with [Open Dashboard] button

**Removed conversation states:**
- `WAITING_API_KEY`
- `WAITING_API_SECRET`
- `WAITING_TRADE_AMOUNT`
- `WAITING_LEVERAGE`
- `WAITING_NEW_LEVERAGE`
- `WAITING_NEW_AMOUNT`
- `WAITING_MANUAL_MARGIN`

**New constant at top of file:**
```python
WEB_DASHBOARD_URL = os.getenv("WEB_DASHBOARD_URL", "https://app.cryptomentor.ai")
```

### 7. Telegram Bot — Simplified Menu

**File:** `Bismillah/menu_system.py`, `Bismillah/menu_handlers.py`

**New `build_main_menu()`:**
```python
def build_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)],
        [InlineKeyboardButton("📋 Account Status", callback_data="account_status")],
        [InlineKeyboardButton("💬 Support", callback_data="support")],
    ])
```

**Redirect handler (replaces all feature handlers):**
```python
REDIRECT_MESSAGE = "📊 This feature is now available on the web dashboard.\n\nTap below to open it:"
REDIRECT_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)]
])

async def handle_redirect(update, context):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        REDIRECT_MESSAGE, reply_markup=REDIRECT_KEYBOARD
    )
```

**`handle_account_status()` handler:**
- Shows: verification status, API key hint (last 4 chars), engine running status
- Buttons: [Open Dashboard], [Back]

### 8. Telegram Bot — Retired Command Redirects

**File:** `Bismillah/bot.py`

**Generic redirect handler:**
```python
async def redirect_to_web(update, context):
    await update.message.reply_text(
        "📊 This feature is now available on the web dashboard.\n\nTap below to open it:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)]
        ])
    )
```

**Commands to redirect:**
`/analyze`, `/futures`, `/futures_signals`, `/signal`, `/signals`, `/ai`, `/chat`, `/aimarket`, `/free_signal`, `/portfolio`, `/price`, `/market`

**Commands to keep:**
`/start`, `/autotrade`, `/id`, `/help`, `/admin`, `/set_premium`, `/remove_premium`, `/grant_credits`, `/signal_on`, `/signal_off`, `/signal_status`, `/serverip`

### 9. Telegram Bot — Trade Notification Updates

**File:** `Bismillah/app/autotrade_engine.py`

**Dashboard button appended to all trade notifications:**
```python
reply_markup=InlineKeyboardMarkup([
    [InlineKeyboardButton("📊 View on Dashboard", url=WEB_DASHBOARD_URL)]
])
```

**Notification points to update:**
- Trade opened
- Trade closed (TP hit / SL hit)
- Engine started/stopped
- Error notifications (API disconnected, etc.)

### 10. Handler Cleanup

**Files to delete:**
```
Bismillah/app/handlers_manual_signals.py
Bismillah/app/handlers_deepseek.py
Bismillah/app/handlers_free_signal.py
Bismillah/app/handlers_skills.py
Bismillah/app/handlers_risk_mode.py
```

**Steps:**
1. Delete the 5 files above
2. Remove their imports from `bot.py`
3. Remove their handler registrations from `bot.py`
4. Verify: `python -m py_compile Bismillah/bot.py`
5. Verify: `python -m py_compile Bismillah/app/handlers_autotrade.py`

## Data Models

### autotrade_sessions (existing table — no schema changes)

The existing `autotrade_sessions` table already has the required columns:
- `telegram_id` — user identifier
- `exchange` — exchange name (bitunix, bingx, etc.)
- `bitunix_uid` — user's exchange UID
- `status` — `none` | `pending_verification` | `uid_verified` | `active`
- `leverage` — leverage setting (1-20)
- `margin_mode` — `cross` | `isolated`
- `updated_at` — last update timestamp

### New Environment Variables

```
# Telegram Bot (Bismillah/.env)
WEB_DASHBOARD_URL=https://app.cryptomentor.ai

# Website Backend (website-backend/.env)
# No new variables required — uses existing SUPABASE_URL, JWT_SECRET, TELEGRAM_BOT_TOKEN
```

## Correctness Properties

### Property 1: Verification Status Completeness
For any logged-in user, `GET /user/verification-status` SHALL always return a response with a `status` field. It SHALL never return 500 for a valid JWT.

### Property 2: UID Validation
For any input to `POST /user/submit-uid`, if the UID is non-numeric or fewer than 5 digits, THE Platform SHALL return HTTP 400. If valid, it SHALL return HTTP 200 with `{"status": "pending_verification"}`.

### Property 3: Verification Guard Coverage
For any request to `/bitunix/*`, `/dashboard/engine/*`, or `/dashboard/signals/*` with a session status of `none` or `pending_verification`, THE Platform SHALL return HTTP 403.

### Property 4: Leverage Bounds
For any `PUT /dashboard/settings/leverage` request, if leverage is outside [1, 20], THE Platform SHALL return HTTP 400. If within bounds, it SHALL update the database and return the new value.

### Property 5: Wizard Completion
After completing all 3 wizard steps (API key saved, risk configured, engine started), `connectorStatus.linked` SHALL be `true` and the engine SHALL be running.

### Property 6: Redirect Coverage
For every retired command (`/analyze`, `/futures`, etc.), the bot SHALL respond with a message containing `WEB_DASHBOARD_URL`. It SHALL never respond with feature content.

### Property 7: Notification Dashboard Link
For every trade notification sent by `autotrade_engine.py`, the message SHALL include an `InlineKeyboardMarkup` with a button linking to `WEB_DASHBOARD_URL`.

### Property 8: Clean Compilation
After handler cleanup, `python -m py_compile` on `bot.py` and `handlers_autotrade.py` SHALL succeed with exit code 0.
