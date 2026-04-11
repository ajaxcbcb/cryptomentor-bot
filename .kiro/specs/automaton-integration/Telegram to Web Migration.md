# Telegram Bot → Web Dashboard Migration Plan



## Context



We are retiring the Telegram bot from providing autotrading features. The bot will become a **gatekeeper** — welcoming users, verifying identity, and redirecting them to the web dashboard for all trading functionality. This simplifies maintenance (one trading UI instead of two), improves UX (web is richer than inline keyboards), and aligns with the Bitunix Community Bot model (PDF reference) where the bot manages community access while the platform handles trading.



**Current state:**

- Telegram bot (`Bismillah/`) has full autotrade: exchange setup, API keys, engine controls, signals, portfolio, settings, education

- Web dashboard (`website-backend/` + `website-frontend/`) already has most trading features: API key management, engine start/stop, portfolio, signals, performance, risk settings

- Both systems share the same Supabase database and autotrade engine



**Goal:** Telegram bot = gatekeeper + notifications. Web = all trading features.



---



## Current Onboarding Flow (What Users See Today)



### Telegram Bot — Current 4-Step Flow (`handlers_autotrade.py:142 cmd_autotrade`)



```

NEW USER sends /start (or /autotrade)

│

├─ User registered in Supabase + SQLite (background)

├─ Community code captured if via t.me/bot?start=community_XXXX

│

├─ CHECK: Has API keys + Active session?

│   └─ YES → Show Dashboard (portfolio, engine, settings)

│

├─ CHECK: Has API keys + No risk mode?

│   └─ YES → Step 3/4: Risk Mode Selection

│

└─ NO API keys → Step 1/4: Select Exchange

    │

    ├─ [Bitunix] → Step 2/4: Registration & API Key

    │   ├─ Show referral link + group join

    │   ├─ "Already Registered" → API Key input

    │   │   ├─ User types API key (WAITING_API_KEY)

    │   │   ├─ User types API secret (WAITING_API_SECRET)

    │   │   └─ Keys saved → UID Verification

    │   │       ├─ User enters Bitunix UID (WAITING_BITUNIX_UID)

    │   │       ├─ Sent to admin/community leader for approval

    │   │       └─ Wait for approval notification

    │   └─ Step 3/4: Risk Mode Selection

    │       ├─ Recommended (risk-based) or Manual

    │       └─ Step 4/4: Start Trading → Engine starts

    │

    ├─ [BingX] → Direct API Key input (no UID needed)

    └─ [Bybit/Binance] → Coming Soon

```



### Web Dashboard — Current Flow (No Onboarding)



```

USER visits web

│

├─ Login page → "Log in with Telegram" button

├─ Telegram OAuth → JWT token → Logged in

│

└─ Lands on Portfolio tab

    ├─ If NO API keys → Yellow banner: "Go to API Bridges"

    │   └─ User must manually find API Bridges tab

    │       ├─ Enter API key + secret

    │       ├─ Test connection

    │       └─ Save

    │

    └─ If HAS API keys → Shows portfolio data

        └─ User can start engine from Engine tab

```



---



## Conflicts & Issues Identified



### Conflict 1: UID Verification is Coupled to API Key Flow

**Problem:** In the current bot, UID verification happens AFTER API key input (line ~740-790 in `handlers_autotrade.py`). If API keys move to web, the UID verification step breaks — it's triggered by the bot conversation flow, not independently.



**Solution:** Decouple UID verification. Make it a **separate gatekeeper step** on the bot that happens BEFORE redirecting to web. Flow becomes:

1. Bot: Select Exchange → Register via Referral → Submit UID → Wait for approval

2. Once approved → Bot redirects to web with "Open Dashboard" button

3. Web: API key setup → Risk config → Start trading



### Conflict 2: Web Has No Onboarding Wizard

**Problem:** New users on web land on Portfolio tab with just a warning banner. No guided setup. If we redirect from bot to web, users will be confused about what to do next.



**Solution:** Add a web onboarding wizard that auto-triggers when user has no API keys. Wizard guides: Exchange → API Key → Risk → Start.



### Conflict 3: Community Deep Links Only Work in Telegram

**Problem:** `t.me/bot?start=community_XXXX` deep links capture community_code in bot context. If user goes directly to web, community affiliation is lost.



**Solution:** Already handled — `cmd_autotrade()` saves `community_code` to `autotrade_sessions` table in Supabase (line 196-207). Web reads from same table.



### Conflict 4: Admin Approval Still Happens in Telegram

**Problem:** UID verification requires admin to tap approve/reject inline buttons in Telegram.



**Solution:** No conflict — admin approval stays in Telegram bot. Admins are Telegram users. Web only checks verification status from Supabase.



### Conflict 5: Direct Web Login (Bypassing Gatekeeper)

**Problem:** Users might go directly to the web, log in with Telegram OAuth, and bypass the bot's exchange registration + UID verification entirely.



**Solution — Defense in Depth (3 layers):**



1. **Backend middleware** blocks all trading API calls for unverified users (403)

2. **Web registration flow** allows direct web users to complete Bitunix registration without going to Telegram (submit UID on web → admin approves on Telegram)

3. **Frontend gate** prevents rendering dashboard until verified



See **Risk 6** in the Risks section for full implementation details.



**Result:** The gatekeeper cannot be bypassed. Users who come to web directly can still register, but through the same verification process. Bot remains the preferred entry point (promoted, linked) but web works as a fallback.



### Scope: Bitunix Only

This migration focuses exclusively on **Bitunix exchange**. Multi-exchange support (BingX, Bybit, Binance) is out of scope for now.

- Exchange selection UI on bot simplified to show Bitunix as primary, others as "Coming Soon"

- Web onboarding wizard assumes Bitunix

- `exchange_registry.py` unchanged — other exchanges stay `coming_soon: True`



---



## Phase 1: Telegram Bot — Gatekeeper Transformation



**Objective:** Strip trading features from bot, replace with web redirects. Keep: onboarding, identity verification, notifications, admin commands.



### 1.1 New `/start` Flow — Two Paths

**File:** `Bismillah/app/handlers_autotrade.py` — rewrite `cmd_autotrade()`



```

NEW USER sends /start

│

├─ Register user in Supabase (keep existing logic, lines 156-207)

├─ Capture community_code if present (keep existing logic)

│

├─ CHECK: User already verified (session.status == "active" or "uid_verified")?

│   │

│   └─ YES → RETURNING USER welcome

│       ┌─────────────────────────────────────┐

│       │ 👋 Welcome back, {first_name}!      │

│       │                                      │

│       │ 🟢 Engine: Running / 🟡 Inactive    │

│       │ 🏦 Exchange: Bitunix                │

│       │                                      │

│       │ [🌐 Open Dashboard]  ← URL button   │

│       │ [📋 Quick Status]                    │

│       │ [💬 Support]                         │

│       └─────────────────────────────────────┘

│

└─ NO → NEW USER onboarding (gatekeeper steps)

    │

    ├─ Step 1: Select Exchange

    │   ┌─────────────────────────────────────┐

    │   │ 🎉 Welcome to CryptoMentor!         │

    │   │                                      │

    │   │ Setup in 2 easy steps:               │

    │   │ 1️⃣ Register & Verify Exchange       │

    │   │ 2️⃣ Complete setup on Dashboard       │

    │   │                                      │

    │   │ [Bitunix]                            │

    │   │ [BingX]                              │

    │   │ [Bybit (Coming Soon)]               │

    │   │ [Binance (Coming Soon)]             │

    │   └─────────────────────────────────────┘

    │

    └─ Step 2: Bitunix Referral + UID Verification

        ├─ Show referral link + group join (keep existing logic)

        ├─ "Already Registered" → Ask for UID only (NOT API key)

        ├─ User enters UID → sent to admin for approval

        └─ On approval → Bot sends:

            ┌─────────────────────────────────────┐

            │ ✅ Your UID Has Been Verified!       │

            │                                      │

            │ Now complete your setup on the       │

            │ dashboard:                           │

            │ • Connect your Bitunix API Key       │

            │ • Configure risk settings            │

            │ • Start trading                      │

            │                                      │

            │ [🌐 Open Dashboard]  ← URL button   │

            └─────────────────────────────────────┘

```



**Key change:** Bot does exchange selection + UID verification ONLY. API key input, risk mode, leverage, engine controls — all on web.



**Conversation states to KEEP:**

- `WAITING_BITUNIX_UID` — still needed for UID verification



**Conversation states to REMOVE:**

- `WAITING_API_KEY` — moves to web

- `WAITING_API_SECRET` — moves to web

- `WAITING_TRADE_AMOUNT` — moves to web

- `WAITING_LEVERAGE` — moves to web

- `WAITING_NEW_LEVERAGE` — moves to web

- `WAITING_NEW_AMOUNT` — moves to web

- `WAITING_MANUAL_MARGIN` — moves to web



### 1.2 Redesign Menu System

**Files:** `Bismillah/menu_system.py`, `Bismillah/menu_handlers.py`



**New main menu (3 items, down from 6):**



| Button | Type | Action |

|--------|------|--------|

| 🌐 Open Dashboard | URL button | Opens web app directly (no callback needed) |

| 📋 Account Status | Callback | Quick inline status: verified?, engine running?, exchange connected? + "Open Dashboard" link |

| 💬 Support | Callback | Contact admin @BillFarr / FAQ / community links |



**Remove these menus entirely:**

- Portfolio Status submenu (→ web Portfolio tab)

- Engine Controls submenu (→ web Engine tab)

- Signals & Market submenu (→ web Signals tab)

- Performance Metrics submenu (→ web Performance tab)

- API Settings submenu (→ web API Bridges tab)

- Skills & Education submenu (→ web Skills tab)



**Redirect handler for old commands:** Any old callback (like `at_status`, `at_history`, `at_start_engine_now`) should respond with:

```

📊 This feature has moved to the web dashboard.

[🌐 Open Dashboard]

```



### 1.3 Keep These Bot Features

**Identity & Access:**

- `/start` — Welcome + web redirect

- UID verification flow (Bitunix referral check)

- Community registration (`handlers_community.py`)

- Admin UID approval/rejection callbacks (`uid_acc_*`, `uid_reject_*`)



**Notifications (bot → user, not interactive):**

- Trade execution alerts (entry/exit)

- Engine status changes (started/stopped/error)

- UID verification result

- Daily performance summary



**Admin Commands (keep all):**

- `/admin` — Admin panel

- `/set_premium`, `/remove_premium`, `/grant_credits`

- `/signal_on`, `/signal_off`, `/signal_status`

- `/serverip`



**Utility:**

- `/id` — Show Telegram ID

- `/help` — Updated command list



### 1.4 Remove These Bot Features

**Files to gut/simplify:**



| Feature | Current File | Action |

|---------|-------------|--------|

| API key input conversation | `handlers_autotrade.py` (states: WAITING_API_KEY, WAITING_API_SECRET) | Remove — redirect to web Settings tab |

| Risk mode selection | `handlers_risk_mode.py` | Remove — redirect to web Engine tab |

| Leverage/margin config | `handlers_autotrade.py` (WAITING_LEVERAGE, at_set_leverage, at_set_margin) | Remove — redirect to web |

| Trade amount setup | `handlers_autotrade.py` (WAITING_TRADE_AMOUNT) | Remove — redirect to web |

| Engine start/stop | `handlers_autotrade.py` (at_start_engine_now, at_stop_engine) | Remove — redirect to web Engine tab |

| Portfolio display | `menu_handlers.py` (handle_portfolio) | Remove — redirect to web Portfolio tab |

| Manual signals | `handlers_manual_signals.py` (cmd_analyze, cmd_futures, cmd_signals) | Remove — redirect to web Signals tab |

| AI analysis | `handlers_deepseek.py` (handle_ai_analyze, handle_ai_chat, handle_ai_market_summary) | Remove — redirect to web |

| Free signals | `handlers_free_signal.py` | Remove — redirect to web |

| Skills/education | `handlers_skills.py` | Remove — redirect to web Skills tab |

| Price check | `menu_handlers.py` (handle_check_price) | Remove — redirect to web |

| Market overview | `menu_handlers.py` (handle_market_overview) | Remove — redirect to web |



---



## Phase 2: Web Dashboard — Fill the Gaps



**Objective:** Ensure web has everything users need so bot removal doesn't create feature gaps.



### 2.1 Features Already on Web (no work needed)

- ✅ API key management — save/test/delete (`website-backend/app/routes/bitunix.py`)

- ✅ Engine start/stop (`website-backend/app/routes/engine.py`)

- ✅ Portfolio with live positions (`website-frontend/src/App.jsx` PortfolioTab)

- ✅ Confluence-validated signals + 1-click execution (`website-backend/app/routes/signals.py`)

- ✅ Performance metrics (`website-backend/app/routes/performance.py`)

- ✅ Risk per trade settings (`website-backend/app/routes/dashboard.py`)

- ✅ Telegram OAuth login (`website-backend/app/auth/telegram.py`)



### 2.2 Features to Add to Web



| Feature | Priority | Details |

|---------|----------|---------|

| **Onboarding wizard** | HIGH | Guided flow for first-time users. Replaces bot's API key + risk setup |

| **UID verification status** | HIGH | Show Bitunix verification status. If pending/unverified, show "Go to Telegram bot" message |

| **Leverage/margin controls** | HIGH | Add to Engine tab or onboarding: leverage selector (1x-20x), margin mode toggle |

| **Trade history page** | MEDIUM | Full trade history with filters. Backend endpoint exists (`/bitunix/trade-history`) |

| **Notification preferences** | LOW | Toggle Telegram notifications (trades, summary, errors) |



### 2.3 Verification Gate (New — Prevents Bypassing Gatekeeper)

**File:** `website-frontend/src/App.jsx` — add gate check after login



Every logged-in user hits this check before seeing any dashboard content:



```jsx

// After Telegram OAuth login succeeds:

const verStatus = await fetch('/user/verification-status');

// Returns: { status: "uid_verified"|"pending_verification"|"none", exchange: "bitunix" }



if (verStatus.status === 'none') {

  // Never registered → show "Go to Telegram Bot" gate screen

  return <GatekeeperScreen />;

}

if (verStatus.status === 'pending_verification') {

  // UID submitted but not approved → show waiting screen

  return <VerificationPendingScreen />;

}

// status === 'uid_verified' or 'active' → proceed to dashboard or onboarding wizard

```



### 2.4 Web Onboarding Wizard (New Component)

**File:** `website-frontend/src/App.jsx` — new `<OnboardingWizard />` component



**Trigger:** User is verified BUT has no API keys saved (`/bitunix/status` returns `linked: false`).



**The wizard handles only what comes AFTER bot verification — Bitunix API key setup + risk config.**



```

VERIFIED USER with no API keys → Show Onboarding Wizard

│

├─ Step 1/3: Connect Bitunix API Key ━━━━━ [33%]

│   ├─ "Connect your Bitunix account"

│   ├─ API key input field

│   ├─ API secret input field

│   ├─ Expandable: "How to create your API Key" (same instructions from exchange_registry.py)

│   ├─ Link: "Open Bitunix API Management" → https://www.bitunix.com/account/api-management

│   ├─ [Test Connection] → POST /bitunix/keys/test

│   └─ [Save & Continue] → POST /bitunix/keys

│

├─ Step 2/3: Configure Risk ━━━━━━━━━━━━━ [66%]

│   ├─ Risk per trade: [0.25%] [0.5%] [0.75%] [1.0%] toggle buttons

│   ├─ Leverage: slider or dropdown (1x → 20x), default 10x

│   ├─ Margin mode: [Cross ♾️] [Isolated 🔒] toggle

│   ├─ Brief explanation of each setting

│   └─ [Continue]

│

└─ Step 3/3: Start Trading ━━━━━━━━━━━━━━ [100%]

    ├─ Summary card:

    │   🏦 Bitunix | 🔑 ...xxxx | ⚙️ 10x Cross | 📊 0.5%

    ├─ [🚀 Start AutoTrade Engine] → POST /dashboard/engine/start

    └─ On success → redirect to Portfolio tab

```



### 2.5 New Backend Endpoints Needed



| Endpoint | Purpose | File |

|----------|---------|------|

| `GET /user/verification-status` | Returns `{status, exchange, uid}` from `autotrade_sessions` | `website-backend/app/routes/user.py` |

| `POST /user/submit-uid` | Submit Bitunix UID for verification from web (sends admin notification via Bot API) | `website-backend/app/routes/user.py` |

| `PUT /dashboard/settings/leverage` | Update leverage in `autotrade_sessions` | `website-backend/app/routes/dashboard.py` |

| `PUT /dashboard/settings/margin-mode` | Update margin mode in `autotrade_sessions` | `website-backend/app/routes/dashboard.py` |



### 2.6 Backend Verification Middleware

**File:** `website-backend/app/middleware/verification_guard.py` (NEW)



All trading-related endpoints check verification status. Unprotected routes (login, verification status, UID submission) are whitelisted. Returns 403 with `{error: "verification_required"}` for unverified users. See Risk 6 Layer 1 for implementation details.



---



## Phase 3: Notification Bridge



**Objective:** Bot keeps sending trade notifications to users via Telegram (push notifications). This is the bot's key remaining value — Telegram push notifications are instant and reliable.



### 3.1 Keep Notification System

**File:** `Bismillah/app/autotrade_engine.py` — trade execution notifications already send to Telegram



**Notifications to keep:**

- Trade opened (symbol, direction, entry, TP/SL levels)

- Trade closed (symbol, PnL, duration)

- TP hit (which tier: TP1/TP2/TP3)

- SL hit

- Engine started/stopped

- Daily performance summary

- Error alerts (API disconnected, insufficient balance)



**Enhancement:** Add "View on Dashboard →" URL button to every notification so users can tap to see full details on web.



### 3.2 Notification Format Update

Each notification should end with:

```

📊 View details → [Open Dashboard]

```



---



## Phase 4: Cleanup & Code Removal



### 4.1 Files to Simplify (keep but gut)

- `Bismillah/app/handlers_autotrade.py` — Keep only: /start welcome, UID verification, exchange selection for referral. Remove: API key input, risk mode, leverage, engine controls, portfolio

- `Bismillah/menu_system.py` — Replace 6-menu system with 3-button gatekeeper menu

- `Bismillah/menu_handlers.py` — Remove all feature handlers, keep only redirect responses

- `Bismillah/bot.py` — Remove command registrations for retired features



### 4.2 Files to Remove Entirely

- `Bismillah/app/handlers_manual_signals.py` — All signal generation moves to web

- `Bismillah/app/handlers_deepseek.py` — AI features move to web

- `Bismillah/app/handlers_free_signal.py` — Free signals move to web

- `Bismillah/app/handlers_skills.py` — Education moves to web

- `Bismillah/app/handlers_risk_mode.py` — Risk config moves to web



### 4.3 Files to Keep Unchanged

- `Bismillah/app/autotrade_engine.py` — Core engine, still runs server-side

- `Bismillah/app/autotrade_reminder.py` — Telegram reminders still useful

- `Bismillah/app/handlers_admin_premium.py` — Admin commands stay

- `Bismillah/app/handlers_autosignal_admin.py` — Admin signal control stays

- `Bismillah/app/handlers_community.py` — Community management stays

- All exchange clients (`bitunix_autotrade_client.py`, etc.) — Used by web backend too

- `Bismillah/app/credits_guard.py` — May still be needed for web

- `Bismillah/app/premium_checker.py` — Used by both systems



---



## Implementation Order



**Must be done in this order** — later steps depend on earlier ones.



| Step | Description | Files | Depends On |

|------|-------------|-------|------------|

| 1 | Add `GET /user/verification-status` + `POST /user/submit-uid` endpoints | `website-backend/app/routes/user.py` | — |

| 2 | Add verification guard middleware (403 for unverified users) | `website-backend/app/middleware/verification_guard.py` | Step 1 |

| 3 | Add leverage + margin-mode settings endpoints | `website-backend/app/routes/dashboard.py` | — |

| 4 | Build web registration flow (Bitunix referral + UID submission) | `website-frontend/src/App.jsx` | Steps 1-2 |

| 5 | Build onboarding wizard (API key + risk config + start engine) | `website-frontend/src/App.jsx` | Steps 3-4 |

| 6 | Rewrite bot `/start` as gatekeeper (Bitunix registration + UID only) | `Bismillah/app/handlers_autotrade.py` | Step 5 |

| 7 | Replace bot menu system with 3-button redirect | `Bismillah/menu_system.py`, `menu_handlers.py` | Step 6 |

| 8 | Add redirect responses for retired commands | `Bismillah/bot.py`, handler files | Step 7 |

| 9 | Update notifications with "View on Dashboard" links | `Bismillah/app/autotrade_engine.py` | Step 6 |

| 10 | Remove retired handler files | `handlers_manual_signals.py`, `handlers_deepseek.py`, etc. | Step 8 |

| 11 | Update CHANGELOG.md and push | `CHANGELOG.md` | Step 10 |



**Scope:** Bitunix exchange only. Other exchanges remain "Coming Soon" — no changes to `exchange_registry.py`.



**Critical deployment gate:** Steps 1-5 (web readiness) MUST be deployed and verified working before Steps 6-10 (bot gutting). Use `MIGRATION_MODE` feature flag for safe rollback.



**Critical rule:** Steps 1-3 (web readiness) MUST be deployed before Steps 4-8 (bot gutting). Otherwise users will have no way to set up API keys or manage their trading.



---



## Verification



### Test Scenario 1: Brand New Bitunix User

1. Send `/start` to bot → See "Welcome to CryptoMentor" + exchange selection

2. Select Bitunix → See referral link + "Already Registered"

3. Click "Already Registered" → Asked for UID only (NOT API key)

4. Enter UID → "UID is being verified" message

5. Admin approves → User gets notification with "Open Dashboard" button

6. Tap "Open Dashboard" → Web opens → Onboarding wizard shows

7. Wizard Step 1: Enter API key + secret → Test → Save

8. Wizard Step 2: Choose risk, leverage, margin

9. Wizard Step 3: Start engine

10. Lands on Portfolio tab with live data



### Test Scenario 2: Direct Web Login (No Bot Interaction)

1. User visits web directly → Logs in with Telegram OAuth

2. Backend checks `autotrade_sessions` → No session found

3. **Gate screen shown:** "Account Setup Required — Open Telegram Bot"

4. User clicks deep link → Opens bot → Completes registration + UID verification

5. Returns to web → Refreshes → Gate clears → Onboarding wizard shows



### Test Scenario 3: Existing User (Already Set Up)

1. Send `/start` → See "Welcome back" + quick status + "Open Dashboard"

2. Tap "Open Dashboard" → Web loads, engine running, portfolio visible



### Test Scenario 4: Retired Commands

1. Tap old menu buttons (portfolio, signals, engine) → See "This feature has moved to the web dashboard" + link

2. Send `/analyze`, `/futures`, `/signals` → Same redirect message



### Test Scenario 5: Admin Commands

1. `/admin`, `/set_premium`, `/signal_on` → Work unchanged



### Test Scenario 6: Pending Verification User on Web

1. User submitted UID on bot but admin hasn't approved yet

2. Goes to web → Logs in → Sees "Verification Pending" screen with refresh button

3. Admin approves on Telegram → User clicks refresh → Gate clears → Wizard shows



---



## Risks & Mitigations



### Risk 1: Users Confused by Change

**Impact:** HIGH — Users who relied on Telegram bot for trading may not know about the web dashboard.



**Mitigations:**

1. **Pre-migration announcement:** Send Telegram broadcast to all active users explaining the change, 1 week before migration

2. **Gradual transition messages:** Every retired command responds with a friendly redirect message (not an error), including a direct URL button to the web dashboard

3. **Welcome message update:** Bot's `/start` message explicitly explains: "Trading features have moved to the web dashboard for a better experience"

4. **In-bot tutorial:** Add a "How It Works" button in the gatekeeper menu that explains the new flow with simple steps

5. **Fallback period:** Keep old bot handlers alive for 2 weeks post-migration but have them show "This feature has moved → [Open Dashboard]" messages instead of errors



### Risk 2: Web Not Ready When Bot is Gutted

**Impact:** CRITICAL — Users would have no way to set up API keys or manage trading.



**Mitigations:**

1. **Strict deployment order:** Web changes (Steps 1-3) MUST be deployed and verified BEFORE any bot changes (Steps 4-8)

2. **Feature flag approach:** Add a `MIGRATION_MODE` env variable. When `false`, bot keeps full functionality. When `true`, bot switches to gatekeeper mode. This allows instant rollback

3. **Parallel operation period:** Run both systems simultaneously for 1 week — bot still works, web also works. Only disable bot features after confirming web handles all use cases

4. **Smoke test checklist:** Before flipping the switch, verify: web login works, onboarding wizard completes, API keys save, engine starts/stops, portfolio loads, signals generate



### Risk 3: Existing Users Mid-Setup (Partial State)

**Impact:** MEDIUM — Users who started on bot but didn't finish may be stuck.



**Mitigations:**

1. **Detect partial states in web wizard:** Check `autotrade_sessions` for existing data and skip completed steps:

   - Has session + verified UID + API keys + risk mode → Dashboard (skip wizard)

   - Has session + verified UID + API keys, no risk mode → Wizard starts at Step 2 (risk config)

   - Has session + verified UID, no API keys → Wizard starts at Step 1 (API key)

   - Has session + pending verification → Show waiting screen

2. **Preserve all Supabase data:** No migration deletes existing user data — session, keys, settings all persist

3. **Bot still accepts UID:** If user is mid-verification, bot gatekeeper still handles UID submission and admin approval



### Risk 4: Notification Delivery Disruption

**Impact:** MEDIUM — Users depend on Telegram trade notifications for real-time awareness.



**Mitigations:**

1. **Notifications are untouched:** The `autotrade_engine.py` notification system is completely separate from interactive handlers. Gutting menus/commands does NOT affect push notifications

2. **Enhanced notifications:** Add "View on Dashboard →" URL button to every trade notification, making notifications more useful

3. **Health monitoring:** Add a daily "bot alive" check — if bot goes down, web shows a banner "Telegram notifications may be delayed"



### Risk 5: Admin Workflow Disruption

**Impact:** LOW — Admin UID approval flow could break if handlers are accidentally removed.



**Mitigations:**

1. **Admin handlers explicitly protected:** `handlers_admin_premium.py` and UID approval callbacks (`uid_acc_*`, `uid_reject_*`) are on the "keep" list

2. **Separate admin handler registration:** Admin handlers registered independently from user-facing handlers in `bot.py`

3. **Test admin flow specifically:** Verification test scenario includes admin approving a UID after migration



### Risk 6: Direct Web Access Bypasses Gatekeeper

**Impact:** HIGH — Unverified users could access dashboard without Bitunix registration.



**Root cause:** Telegram OAuth only proves the user has a Telegram account — not that they've completed exchange registration or UID verification through the bot.



**Strategy: Defense in Depth (3 layers)**



#### Layer 1: Backend Middleware — Verification Enforcement

Every protected API route checks verification status before processing. This is the hard security boundary — even if frontend is bypassed, backend blocks unauthorized access.



```python

# website-backend/app/middleware/verification_guard.py



UNPROTECTED_ROUTES = [

    "/auth/telegram",

    "/auth/logout",

    "/user/verification-status",

    "/user/me",

]



async def verify_user_access(request, user_id):

    """Middleware: block unverified users from trading endpoints."""

    if request.url.path in UNPROTECTED_ROUTES:

        return  # allow



    session = get_autotrade_session(user_id)

    if not session or session.get("status") not in ("uid_verified", "active"):

        raise HTTPException(

            status_code=403,

            detail={

                "error": "verification_required",

                "status": session.get("status") if session else "none",

                "message": "Complete exchange registration before accessing trading features."

            }

        )

```



**Result:** Even if a user manipulates the frontend, they cannot call `/bitunix/keys`, `/dashboard/engine/start`, or any trading endpoint without being verified.



#### Layer 2: Web Registration Flow (Fallback for Direct Web Users)

Instead of just showing "Go to Telegram Bot," the web can handle the FULL Bitunix registration flow as a fallback. This eliminates the friction of bouncing users back to Telegram.



```

UNVERIFIED USER on web

│

├─ Gate Screen: "Complete Bitunix Registration"

│   │

│   ├─ Step 1: Register on Bitunix

│   │   ├─ Show referral link: https://www.bitunix.com/register?vipCode=sq45

│   │   ├─ "Open Bitunix Registration" URL button

│   │   ├─ Explain why referral is required

│   │   └─ [I've Registered → Continue]

│   │

│   ├─ Step 2: Submit Your Bitunix UID

│   │   ├─ UID input field

│   │   ├─ "How to find your UID" expandable guide

│   │   ├─ [Submit for Verification] → POST /user/submit-uid

│   │   │   └─ Backend saves UID to autotrade_sessions (status=pending_verification)

│   │   │   └─ Backend sends approval request to admin via Telegram Bot API:

│   │   │       context.bot.send_message(admin_id, "New UID verification request...")

│   │   └─ Shows "Verification Pending" screen

│   │

│   └─ Step 3: Wait for Admin Approval

│       ├─ "Your UID is being verified by an admin"

│       ├─ Auto-poll every 30 seconds: GET /user/verification-status

│       ├─ Also: "You'll receive a Telegram notification when approved"

│       └─ On approved → Auto-redirect to onboarding wizard (API key setup)

```



**New backend endpoint needed:**

```

POST /user/submit-uid

Body: { "uid": "123456789" }

→ Saves to autotrade_sessions (status=pending_verification)

→ Sends admin notification via Telegram Bot API (reuses existing admin notification logic)

→ Returns { "status": "pending_verification" }

```



**Key insight:** The admin approval flow stays in Telegram (admin taps approve/reject inline button). But the USER doesn't need to be in Telegram — they can submit their UID from the web and wait for approval. The bot sends the approval notification to the admin automatically.



#### Layer 3: Frontend Verification Gate

React-level gate that prevents rendering any dashboard content for unverified users. This is the UX layer — provides clear guidance to the user.



```jsx

// In App.jsx, wraps all dashboard content

function App() {

  const [verStatus, setVerStatus] = useState(null);

  

  useEffect(() => {

    if (isLoggedIn) {

      fetch('/user/verification-status')

        .then(r => r.json())

        .then(setVerStatus);

    }

  }, [isLoggedIn]);



  if (isLoggedIn && verStatus) {

    if (verStatus.status === 'none')

      return <RegistrationFlow />;  // Full Bitunix registration on web

    if (verStatus.status === 'pending_verification')

      return <VerificationPending autoRefresh={true} />;

    // 'uid_verified' or 'active' → proceed

  }



  return <Dashboard />;  // Normal dashboard with onboarding wizard if no API keys

}

```



**Result of 3-layer approach:**

- **Layer 1 (Backend):** Hard security — no API access without verification, regardless of frontend state

- **Layer 2 (Web Registration):** Smooth UX — users who come to web directly can still register without going to Telegram

- **Layer 3 (Frontend Gate):** Clear guidance — users see exactly what they need to do



**Why this is better than "redirect to Telegram":**

- No friction — user stays on the platform they chose (web)

- Same outcome — UID submitted, admin verifies via Telegram

- Bot is still the preferred path (marketed, linked everywhere), but web works too

- Admin workflow unchanged — they still approve via Telegram inline buttons



### Risk 7: Data Inconsistency Between Bot and Web

**Impact:** MEDIUM — Both systems read/write to same Supabase tables. Concurrent writes could conflict.



**Mitigations:**

1. **Single source of truth:** Supabase is already the single source of truth for both systems

2. **Bot becomes read-mostly:** After migration, bot only writes during UID verification. All other writes (API keys, settings, engine state) happen on web only

3. **Unique constraints:** `user_api_keys` table has unique constraint on `(telegram_id, exchange)` preventing duplicate API key entries

4. **Idempotent operations:** All Supabase operations use `upsert` (not `insert`), making them safe for concurrent access



### Risk 8: Performance Impact on Web

**Impact:** LOW-MEDIUM — Web onboarding wizard adds new API calls and the verification gate adds a check on every page load.



**Mitigations:**

1. **Cache verification status:** After first check, cache verification status in React state/localStorage for the session (refresh on explicit user action or every 5 minutes)

2. **Lightweight endpoint:** `GET /user/verification-status` is a single Supabase query — <50ms response time

3. **Lazy load wizard:** Onboarding wizard component only loads when needed (no impact on returning users)



---



## Vibe Code Breakdown — Step-by-Step Tasks



Each task below is self-contained and can be coded independently. Complete them in order.



---



### STEP 1: Backend — Verification Status Endpoint

**File:** `website-backend/app/routes/user.py`

**What to do:**



1.1. Add `GET /user/verification-status` endpoint:

- Read JWT token → extract `telegram_id`

- Query Supabase: `autotrade_sessions` where `telegram_id = user_id`

- Return JSON:

  ```json

  {

    "status": "none" | "pending_verification" | "uid_verified" | "active",

    "exchange": "bitunix",

    "uid": "123456789" | null,

    "community_code": "XXXX" | null

  }

  ```

- If no session found → return `{"status": "none"}`



1.2. Add `POST /user/submit-uid` endpoint:

- Read JWT token → extract `telegram_id`

- Accept body: `{"uid": "123456789"}`

- Validate: UID must be numeric, min 5 digits

- Upsert to `autotrade_sessions`:

  ```python

  {

    "telegram_id": user_id,

    "exchange": "bitunix",

    "bitunix_uid": uid,

    "status": "pending_verification",

    "updated_at": now()

  }

  ```

- Send admin notification via Telegram Bot API (reuse logic from `handlers_autotrade.py:780-830`):

  ```python

  # Build inline keyboard with approve/reject buttons

  keyboard = [[

    InlineKeyboardButton("✅ Approve", callback_data=f"uid_acc_{user_id}"),

    InlineKeyboardButton("❌ Reject", callback_data=f"uid_reject_{user_id}")

  ]]

  # Send to all admin IDs

  for admin_id in admin_ids:

      bot.send_message(admin_id, verification_text, reply_markup=keyboard)

  ```

- Return: `{"status": "pending_verification"}`



**Test:** Call `GET /user/verification-status` with a valid JWT → should return `{"status": "none"}` for new user. Call `POST /user/submit-uid` with `{"uid": "123456"}` → should return `{"status": "pending_verification"}` and admin should receive Telegram message.



---



### STEP 2: Backend — Verification Guard Middleware

**File:** `website-backend/app/middleware/verification_guard.py` (NEW)



2.1. Create middleware function that checks verification status:

```python

UNPROTECTED_ROUTES = [

    "/auth/",           # login/logout

    "/user/me",         # profile

    "/user/verification-status",  # check status

    "/user/submit-uid",           # submit UID

    "/dashboard/system",          # health check

]



def is_protected_route(path: str) -> bool:

    return not any(path.startswith(prefix) for prefix in UNPROTECTED_ROUTES)

```



2.2. In the route handlers that need protection, add verification check:

- For `/bitunix/*` routes → check verification before processing

- For `/dashboard/engine/*` routes → check verification

- For `/dashboard/signals/*` routes → check verification

- Return 403 with `{"error": "verification_required", "status": "none|pending_verification"}`



2.3. Register middleware in `website-backend/main.py`



**Test:** Call `POST /bitunix/keys` without verified session → should get 403. After verification → should succeed.



---



### STEP 3: Backend — Leverage & Margin Settings Endpoints

**File:** `website-backend/app/routes/dashboard.py`



3.1. Add `PUT /dashboard/settings/leverage`:

- Accept body: `{"leverage": 10}` (validate: 1-20, integer)

- Update `autotrade_sessions` set `leverage = value`

- Return: `{"leverage": 10}`



3.2. Add `PUT /dashboard/settings/margin-mode`:

- Accept body: `{"margin_mode": "cross"}` (validate: "cross" or "isolated")

- Update `autotrade_sessions` set `margin_mode = value`

- Return: `{"margin_mode": "cross"}`



**Test:** Call `PUT /dashboard/settings/leverage` with `{"leverage": 15}` → verify DB updated. Call with `{"leverage": 25}` → should get 400 validation error.



---



### STEP 4: Frontend — Verification Gate & Registration Flow

**File:** `website-frontend/src/App.jsx`



4.1. Add state for verification:

```jsx

const [verStatus, setVerStatus] = useState(null); // null = loading

```



4.2. Add `useEffect` to check verification on login:

```jsx

useEffect(() => {

  if (!isLoggedIn) return;

  fetch(`${base}/user/verification-status`, { headers: authHeaders })

    .then(r => r.json())

    .then(setVerStatus);

}, [isLoggedIn]);

```



4.3. Create `<GatekeeperScreen />` component (shown when `verStatus.status === 'none'`):

- Card with:

  - Title: "Welcome to CryptoMentor AutoTrade"

  - Subtitle: "Complete your Bitunix registration to start trading"

  - Step 1: Register on Bitunix → show referral link button (opens `https://www.bitunix.com/register?vipCode=sq45`)

  - Step 2: Enter your Bitunix UID → input field

  - [Submit for Verification] button → calls `POST /user/submit-uid`

  - On success → switch to pending screen



4.4. Create `<VerificationPendingScreen />` component (shown when `verStatus.status === 'pending_verification'`):

- Card with:

  - Spinner/hourglass icon

  - "Your Bitunix UID is being verified"

  - "You'll receive a Telegram notification once approved"

  - [Refresh Status] button → re-fetches `/user/verification-status`

  - Auto-poll every 30 seconds



4.5. Add gate logic to main render:

```jsx

if (isLoggedIn && verStatus?.status === 'none')

  return <GatekeeperScreen onSubmit={...} />;

if (isLoggedIn && verStatus?.status === 'pending_verification')

  return <VerificationPendingScreen onRefresh={...} />;

// else: render normal dashboard

```



**Test:** Login as new user (no session) → see registration screen. Submit UID → see pending screen. Have admin approve on Telegram → refresh → see dashboard.



---



### STEP 5: Frontend — Onboarding Wizard

**File:** `website-frontend/src/App.jsx`



5.1. Create `<OnboardingWizard />` component:

- Triggered when: `verStatus.status` is `'uid_verified'` or `'active'` AND `connectorStatus.linked === false` (no API keys)

- 3-step wizard with progress bar



5.2. **Wizard Step 1: Connect Bitunix API Key**

- Two input fields: API Key, API Secret (password type)

- Expandable guide section: "How to create your API Key" (copy text from `exchange_registry.py` bitunix `api_key_help`)

- URL button: "Open Bitunix API Management" → `https://www.bitunix.com/account/api-management`

- [Test Connection] button → `POST /bitunix/keys/test` with `{api_key, api_secret}`

  - Show green checkmark on success, red error on failure

- [Save & Continue] button → `POST /bitunix/keys` with `{api_key, api_secret}`

  - On success → move to Step 2



5.3. **Wizard Step 2: Configure Risk**

- Risk per trade: 4 toggle buttons `[0.25%] [0.5%] [0.75%] [1.0%]` (default 0.5%)

  - On select → `PUT /dashboard/settings/risk` with `{risk_per_trade: 0.5}`

- Leverage: slider or number input (1x-20x, default 10x)

  - On change → `PUT /dashboard/settings/leverage` with `{leverage: 10}`

- Margin mode: 2 toggle buttons `[Cross ♾️] [Isolated 🔒]` (default cross)

  - On select → `PUT /dashboard/settings/margin-mode` with `{margin_mode: "cross"}`

- [Continue] button → move to Step 3



5.4. **Wizard Step 3: Start Trading**

- Summary card showing all settings:

  ```

  🏦 Bitunix  |  🔑 ...xxxx  |  ⚙️ 10x Cross  |  📊 0.5% risk

  ```

- [🚀 Start AutoTrade Engine] button → `POST /dashboard/engine/start`

  - On success → set `activeTab = 'portfolio'`, hide wizard

- [Skip for now] link → go to dashboard without starting engine



5.5. Add wizard trigger in main render:

```jsx

if (isLoggedIn && verStatus?.status in ['uid_verified','active'] && connectorStatus?.linked === false)

  return <OnboardingWizard onComplete={() => { fetchConnectorStatus(); setActiveTab('portfolio'); }} />;

```



**Test:** Login as verified user with no API keys → see wizard. Enter API key → test → save → configure risk → start engine → lands on portfolio with live data.



---



### STEP 6: Telegram Bot — Rewrite `/start` as Gatekeeper

**File:** `Bismillah/app/handlers_autotrade.py`



6.1. Rewrite `cmd_autotrade()` function:



**For RETURNING users** (has API keys + active/verified session):

```python

# Show simple welcome with dashboard link

keyboard = InlineKeyboardMarkup([

    [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)],

    [InlineKeyboardButton("📋 Quick Status", callback_data="at_quick_status")],

    [InlineKeyboardButton("💬 Support", callback_data="at_support")],

])

await update.message.reply_text(

    f"👋 <b>Welcome back, {user.first_name}!</b>\n\n"

    f"🏦 Exchange: Bitunix\n"

    f"⚙️ Engine: {'🟢 Running' if engine_on else '🟡 Inactive'}\n\n"

    "Manage your trading on the dashboard:",

    parse_mode='HTML', reply_markup=keyboard

)

```



**For NEW users** (no session or not verified):

```python

# Show exchange selection (Bitunix only for now)

keyboard = InlineKeyboardMarkup([

    [InlineKeyboardButton("Bitunix", callback_data="at_exchange_bitunix")],

    [InlineKeyboardButton("Bybit (Coming Soon)", callback_data="at_coming_soon")],

    [InlineKeyboardButton("Binance (Coming Soon)", callback_data="at_coming_soon")],

    [InlineKeyboardButton("BingX", callback_data="at_exchange_bingx")],

    [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")],

])

await update.message.reply_text(

    onboarding_welcome_gatekeeper(),  # New welcome text for gatekeeper mode

    parse_mode='HTML', reply_markup=keyboard

)

```



6.2. Update `callback_confirm_referral()` — after referral confirmation, ask for UID only (remove API key input):

```python

# OLD: asks for API key (WAITING_API_KEY)

# NEW: asks for UID directly (WAITING_BITUNIX_UID)

await query.edit_message_text(

    "🔢 <b>Submit Your Bitunix UID</b>\n\n"

    f"{ex['uid_help']}\n\n"

    "Enter your UID below:",

    parse_mode='HTML'

)

return WAITING_BITUNIX_UID

```



6.3. Update `callback_uid_approve()` — after admin approves UID, send dashboard link:

```python

await bot.send_message(

    chat_id=target_user_id,

    text=(

        "✅ <b>Your UID Has Been Verified!</b>\n\n"

        "Now complete your setup on the dashboard:\n"

        "• Connect your Bitunix API Key\n"

        "• Configure risk settings\n"

        "• Start trading\n"

    ),

    parse_mode='HTML',

    reply_markup=InlineKeyboardMarkup([

        [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)]

    ])

)

```



6.4. Remove conversation states: `WAITING_API_KEY`, `WAITING_API_SECRET`, `WAITING_TRADE_AMOUNT`, `WAITING_LEVERAGE`, `WAITING_NEW_LEVERAGE`, `WAITING_NEW_AMOUNT`, `WAITING_MANUAL_MARGIN`



6.5. Add `WEB_DASHBOARD_URL` constant at top of file (from env or hardcoded)



**Test:** Send `/start` as new user → see exchange selection. Select Bitunix → see referral + UID input (NOT API key input). Submit UID → admin approves → user gets "Open Dashboard" button.



---



### STEP 7: Telegram Bot — Simplify Menu System

**File:** `Bismillah/menu_system.py`, `Bismillah/menu_handlers.py`



7.1. In `menu_system.py`, replace `build_main_menu()`:

```python

def build_main_menu():

    return InlineKeyboardMarkup([

        [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)],

        [InlineKeyboardButton("📋 Account Status", callback_data="account_status")],

        [InlineKeyboardButton("💬 Support", callback_data="support")],

    ])

```



7.2. In `menu_handlers.py`, replace all feature handlers with redirect responses:

```python

REDIRECT_MESSAGE = (

    "📊 This feature is now available on the web dashboard.\n\n"

    "Tap below to open it:"

)

REDIRECT_KEYBOARD = InlineKeyboardMarkup([

    [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)]

])



# For every old callback (portfolio_status, engine_controls, signals_market, etc.):

async def handle_redirect(update, context):

    await update.callback_query.answer()

    await update.callback_query.edit_message_text(

        REDIRECT_MESSAGE, parse_mode='HTML', reply_markup=REDIRECT_KEYBOARD

    )

```



7.3. Add `account_status` handler that shows quick status:

```python

async def handle_account_status(update, context):

    user_id = update.callback_query.from_user.id

    session = get_autotrade_session(user_id)

    keys = get_user_api_keys(user_id)

    

    status_lines = []

    status_lines.append(f"✅ Verified" if session and session['status'] in ('uid_verified','active') else "⏳ Pending Verification")

    status_lines.append(f"🔑 API Key: ...{keys['key_hint']}" if keys else "❌ No API Key (set up on dashboard)")

    status_lines.append(f"⚙️ Engine: {'🟢 Running' if engine_running(user_id) else '🟡 Inactive'}")

    

    await update.callback_query.edit_message_text(

        "📋 <b>Account Status</b>\n\n" + "\n".join(status_lines),

        parse_mode='HTML',

        reply_markup=InlineKeyboardMarkup([

            [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)],

            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]

        ])

    )

```



**Test:** `/menu` → see 3 buttons. Tap "Account Status" → see verification/key/engine status. Tap "Open Dashboard" → web opens.



---



### STEP 8: Telegram Bot — Redirect Retired Commands

**File:** `Bismillah/bot.py`



8.1. Replace command handlers for retired features:

```python

# Create a generic redirect handler

async def redirect_to_web(update, context):

    await update.message.reply_text(

        "📊 This feature is now available on the web dashboard.\n\n"

        "Tap below to open it:",

        parse_mode='HTML',

        reply_markup=InlineKeyboardMarkup([

            [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)]

        ])

    )



# Replace these command registrations:

app.add_handler(CommandHandler("analyze", redirect_to_web))

app.add_handler(CommandHandler("futures", redirect_to_web))

app.add_handler(CommandHandler("futures_signals", redirect_to_web))

app.add_handler(CommandHandler("signal", redirect_to_web))

app.add_handler(CommandHandler("signals", redirect_to_web))

app.add_handler(CommandHandler("ai", redirect_to_web))

app.add_handler(CommandHandler("chat", redirect_to_web))

app.add_handler(CommandHandler("aimarket", redirect_to_web))

app.add_handler(CommandHandler("free_signal", redirect_to_web))

app.add_handler(CommandHandler("portfolio", redirect_to_web))

app.add_handler(CommandHandler("price", redirect_to_web))

app.add_handler(CommandHandler("market", redirect_to_web))

```



8.2. Keep these command handlers unchanged:

- `/start`, `/autotrade` → gatekeeper (from Step 6)

- `/id` → show Telegram ID

- `/help` → update help text to reflect new bot purpose

- `/admin` → admin panel

- `/set_premium`, `/remove_premium`, `/grant_credits` → admin commands

- `/signal_on`, `/signal_off`, `/signal_status` → admin signal control

- `/serverip` → admin utility



**Test:** Send `/analyze BTCUSDT` → see redirect message. Send `/portfolio` → see redirect message. Send `/admin` → still works normally.



---



### STEP 9: Telegram Bot — Update Notifications with Dashboard Link

**File:** `Bismillah/app/autotrade_engine.py`



9.1. Find all `send_message` calls that notify users about trades and add dashboard URL button:

```python

# After every trade notification, append:

reply_markup=InlineKeyboardMarkup([

    [InlineKeyboardButton("📊 View on Dashboard", url=WEB_DASHBOARD_URL)]

])

```



9.2. Key notification points to update:

- Trade opened notification

- Trade closed notification (TP hit / SL hit)

- Engine started/stopped notification

- Error notifications (API disconnected, etc.)



**Test:** Start engine on web → wait for trade → verify Telegram notification includes "View on Dashboard" button.



---



### STEP 10: Cleanup — Remove Retired Handler Files

**Files to delete:**



```

Bismillah/app/handlers_manual_signals.py   # Signal generation → web

Bismillah/app/handlers_deepseek.py         # AI analysis → web

Bismillah/app/handlers_free_signal.py      # Free signals → web

Bismillah/app/handlers_skills.py           # Education → web

Bismillah/app/handlers_risk_mode.py        # Risk config → web

```



10.1. Remove imports of these files from `bot.py`

10.2. Remove handler registrations from `bot.py` for deleted files

10.3. Run `python -m py_compile Bismillah/bot.py` to verify no import errors

10.4. Run `python -m py_compile Bismillah/app/handlers_autotrade.py` to verify syntax



**Test:** Bot starts without errors. All remaining commands work. Deleted commands show redirect.



---



### STEP 11: Documentation — Update CHANGELOG.md

**File:** `CHANGELOG.md`



11.1. Add new section documenting the migration:

- What changed: Telegram bot is now a gatekeeper

- Why: Better UX, unified platform, easier maintenance

- What users should do: Use web dashboard for all trading features

- What stayed: Notifications, admin commands, UID verification



11.2. Commit and push to ajax:

```bash

git add -A

git commit -m "feat(migration): migrate autotrade from telegram bot to web dashboard"

git push ajax master

```



**Test:** Verify changelog is clear and complete. Verify push succeeds.

