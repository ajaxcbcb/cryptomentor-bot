# Changelog

## [Unreleased] — Telegram to Web Migration

### What Changed

The Telegram bot has been transformed into a **gatekeeper and notification hub**. All trading features have moved to the web dashboard.

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

### What Stayed in the Bot

- UID verification flow (Bitunix registration gatekeeper)
- Trade notifications (entry, exit, TP/SL hits, engine status)
- Admin commands (`/admin`, `/set_premium`, `/signal_on`, etc.)
- `/id` command (show Telegram ID)
- Community registration deep links

### What Was Removed from the Bot

- API key input conversation
- Risk mode & leverage configuration
- Engine start/stop controls
- Portfolio display
- Manual signal generation (`/analyze`, `/futures`, `/signals`)
- AI analysis (`/ai`, `/chat`, `/aimarket`)
- Free signals (`/free_signal`)
- Skills & education (`/skills`)
- Price check (`/price`)
- Market overview (`/market`)

All removed commands now respond with a redirect message and an "Open Dashboard" button.

### Files Changed

**Backend (website-backend)**
- `app/routes/user.py` — Added `GET /user/verification-status` and `POST /user/submit-uid`
- `app/routes/dashboard.py` — Added `PUT /dashboard/settings/leverage` and `PUT /dashboard/settings/margin-mode`
- `app/middleware/verification_guard.py` — New: blocks unverified users from trading endpoints
- `main.py` — Registered verification guard middleware

**Frontend (website-frontend)**
- `src/App.jsx` — Added verification gate, `GatekeeperScreen`, `VerificationPendingScreen`, `OnboardingWizard`

**Telegram Bot (Bismillah)**
- `app/handlers_autotrade.py` — Rewritten as gatekeeper (UID verification only)
- `app/autotrade_engine.py` — All notifications now include "View on Dashboard" button
- `menu_system.py` — Simplified to 3-button menu
- `menu_handlers.py` — All feature callbacks redirect to web
- `bot.py` — Retired commands redirect to web
- **Deleted:** `handlers_manual_signals.py`, `handlers_deepseek.py`, `handlers_free_signal.py`, `handlers_skills.py`, `handlers_risk_mode.py`
