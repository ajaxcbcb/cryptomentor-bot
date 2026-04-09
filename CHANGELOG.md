# CryptoMentor V2.0 Changelog

All notable changes to the CryptoMentor Artificial Intelligence Trading project will be documented in this file.

## [Unreleased / Latest] - 2026-04-10

### 🌍 Telegram Bot Localization — English Translation for Onboarding Flow
**Improvement**: Translated Telegram bot welcome screen and onboarding messages from Indonesian to English for international users.

**Changes**:
- 🔥 **Onboarding Welcome Screen** (`Bismillah/app/ui_components.py`):
  - Translated: "Setup dalam 4 langkah mudah" → "Setup in 4 easy steps"
  - Translated: "Pilih Exchange, Connect API Key, Setup Risk Management, Start Trading" steps to English
  - Translated: "Estimasi waktu: 5 menit" → "Estimated time: 5 minutes"
  - Translated: "Mari kita mulai!" → "Let's get started!"

- 🔥 **Exchange Selection Screen** (`Bismillah/app/handlers_autotrade.py`):
  - Translated: "Auto Trade — Pilih Exchange" → "Auto Trade — Select Exchange"
  - Translated: "Kami support beberapa exchange terpercaya" → "We support several trusted exchanges"
  - Translated: "Pilih exchange yang ingin kamu gunakan" → "Select the exchange you want to use"

- 🔥 **UID Verification Flow**:
  - Translated: "UID Kamu Sudah Diverifikasi!" → "Your UID Has Been Verified!"
  - Translated: "Akun Bitunix kamu sudah terkonfirmasi" → "Your Bitunix account has been confirmed"
  - Translated: "UID sedang diverifikasi" → "UID is being verified"
  - Translated: "Ketua komunitas akan memverifikasi" → "The community leader will verify your UID"
  - Translated: "Kamu akan mendapat notifikasi setelah disetujui" → "You will receive a notification after approval"

- 🔥 **Help Menu & Error Messages** (`Bismillah/app/ui_components.py`):
  - Translated: "Butuh Bantuan?" → "Need Help?"
  - Translated: "Perbaiki dalam 2 menit" → "Fix in 2 minutes"

**Benefits**:
✅ Improved UX for international English-speaking users  
✅ Consistent English messaging across onboarding flow  
✅ Professional appearance for global user base  

---

### 🔄 State Persistence & Connection Recovery — Post-Deployment Improvements
**Problem Resolved**: After deployment/restart, both Telegram bot and web dashboard would lose connection to previous API state, requiring users to restart their sessions, re-authenticate, and restart trading engines. This degraded user experience and interrupted active trading.

#### Root Causes Identified & Fixed:
1. **In-Memory State Loss** — Signal queue, execution status, and engine state lived only in Python memory. On restart, all context was lost.
2. **No API Session Recovery** — Bitunix API connections were dropped on deployment without graceful reconnection logic.
3. **Missing State Sync** — Telegram bot and web dashboard had separate state management; sync only happened at request time.
4. **No Heartbeat Monitoring** — Dead connections weren't detected until next trade attempt (too late).

#### Solutions Implemented:

##### Signal Queue Persistence (Web-Telegram Sync)
- 🔥 **SignalQueueManager** (`website-backend/app/services/signal_queue.py`): New service class manages signal queues with full Supabase persistence.
  - Signals stored in `signal_queue` table with status lifecycle: `pending` → `executing` → `executed|failed`
  - Both Telegram bot and web dashboard read/write to same queue
  - No duplicate execution across systems (unique constraint: `(user_id, symbol, status)`)
  - Queue survives bot/web restart — signals auto-load from DB on startup

- 🔥 **Telegram Bot Queue Sync** (`Bismillah/app/autotrade_engine.py`):
  - Engine now syncs generated signals to `signal_queue` table immediately
  - Execution status updates propagated to DB in real-time (pending → executing → executed)
  - Helper function `_cleanup_signal_queue()` ensures atomicity of queue operations
  - Web dashboard sees Telegram's queued signals with zero lag

- 🔥 **Supabase Migration** (`website-backend/app/db/migrations/signal_queue_table.sql`):
  - Created `signal_queue` table with proper indexing for fast lookups
  - RLS policies limit users to their own signals
  - Auto-update triggers keep `updated_at` fresh
  - Constraint prevents race conditions on same symbol

##### Unified State Management
- 🔥 **Shared Menu Structure** (`Bismillah/menu_system.py`, `Bismillah/menu_handlers.py`):
  - Restructured Telegram menu to match web dashboard tabs (6 primary navigation sections)
  - Both platforms now have identical feature discovery and navigation
  - Users see consistent UI/UX across Telegram and web

- 🔥 **API Connection Health Checks**:
  - `bitunix_autotrade_client.py` now includes connection validation on startup
  - Stale API credentials detected before trading begins
  - Clear error messages guide users to re-authenticate

- 🔥 **Graceful Reconnection** (`autotrade_engine.py`):
  - On startup, engine loads previous session state from `autotrade_sessions` table
  - Validates that Bitunix API keys still work before resuming trading
  - If keys are invalid: notifies user, pauses engine (doesn't fail hard)
  - Implements exponential backoff on API failures (max 5 retries over 5 minutes)

##### User Experience Improvements
- 🚀 **Telegram Bot State Recovery**:
  - `/start` or `/autotrade` on restart checks if engine was running → offers to resume
  - Shows last known balance and open positions (from cache)
  - Syncs latest signal queue with web dashboard
  - No re-authentication required for same session

- 🚀 **Web Dashboard State Recovery**:
  - On login, automatically fetches current engine status from Supabase
  - Restores previous trading mode, leverage, risk settings
  - Shows live signal queue pulled from `signal_queue` table
  - Displays "engine was interrupted" banner if restart detected

- 🚀 **Zero Data Loss on Deployment**:
  - All critical state (signals, trades, settings, equity) now persisted to Supabase
  - In-memory caches are performance optimization only, not source of truth
  - Database is single source of truth for all user state

#### Benefits
✅ **Continuous Trading** — Engine resumes after restart without user intervention  
✅ **No Re-Authentication** — Session persists across deployments  
✅ **Unified State** — Telegram and web see same signals and execution status  
✅ **Connection Resilience** — API failures handled gracefully with retry logic  
✅ **Transparent Status** — Users see exactly what happened during downtime  
✅ **Improved Reliability** — No more "connection lost after deploy" complaints  

---

## [Previous] - 2026-04-09

### Trading Signal Algorithm Redesign — Confluence-Based Multi-Factor Detection
- 🔥 **Confluence-Based Signal Generation** (`website-backend/app/routes/signals.py`): Replaced momentum-only signal algorithm with multi-factor confluence validation combining: Support/Resistance detection (RangeAnalyzer), RSI extremes (oversold/overbought), Volume spike confirmation (>1.5× 20-period MA), Trending market validation (ATR > 0.3%), and long-term price trend alignment (>50-candle moving average). Only generates signals when 2+ factors align with confluence score ≥ 50 (prevents false breakouts & momentum chasing).
- 🔥 **ATR-Scaled Realistic TP/SL** (`generate_confluence_signals`): Replaced fixed-% profit targets (TP1=1%, TP2=2%, TP3=3%) with volatility-adaptive ATR-based scaling: TP1 = entry ± 0.75 ATR, TP2 = entry ± 1.25 ATR, TP3 = entry ± 1.5 ATR, SL = entry ± 0.5 ATR. Automatically widens TPs in high-volatility markets and tightens in low-volatility, matching realistic take-profit distances (2–3% typical).
- 🚀 **Zero-Caching Signal Generation** (`GET /dashboard/signals`): Removed 5-minute signal cache entirely → allows multiple high-probability signals per day when confluence conditions change. No artificial limiting of signal density. Each request generates fresh signals from live market data, enabling traders to act on new confluent setups immediately without waiting for cache expiry.
- 📊 **Confluence Scoring Matrix** (`generate_confluence_signals`): Transparent scoring system visible in signal `reason` field: S/R bounce (30 pts), RSI extreme (25 pts), Volume spike (20 pts), Trending regime (15 pts), Price trend alignment (10 pts). Min 50 pts required, typically requires 2+ factors. Dashboard users can see exactly which confluence factors triggered each signal.
- 🎯 **Adaptive Signal Generation by Risk Tolerance** (`generate_confluence_signals`): Signal generation now reads user's `risk_per_trade` setting and adapts confidence threshold + TP scaling accordingly:
  - **Conservative (0.25%)**: min_confidence=60, tighter TPs (0.5× ATR) — only high-conviction signals
  - **Moderate (0.5%)**: min_confidence=50, standard TPs (0.75–1.5× ATR) — balanced approach
  - **Aggressive (0.75%)**: min_confidence=45, wider TPs (1.25× ATR) — more signals, wider targets
  - **Very Aggressive (1.0%)**: min_confidence=40, widest TPs (1.5× ATR) — maximum signal frequency
  - Enables traders to tune signal density and target distances to their risk appetite, matching high-frequency low-risk trading profiles.
- 🛠️ **Multi-Source Candle Fetching**: Integrated with `alternative_klines_provider` for 1-hour candle data with priority chain: Bitunix (primary) → Binance Futures (fallback) → CryptoCompare/CoinGecko. Ensures signal generation never blocks on a single data source.

### Risk Management — Fixed Dollar Risk Per Trade
- 🔥 **Risk Settings API** (`website-backend/app/routes/dashboard.py`): New `GET /dashboard/settings` endpoint returns current user's `risk_per_trade`, `leverage`, `trading_mode`, and `risk_mode`. New `PUT /dashboard/settings/risk` endpoint accepts `{"risk_per_trade": float}` payload, validates against allowed values [0.25, 0.5, 0.75, 1.0], and persists to `autotrade_sessions` table.
- 🎛️ **Risk Slider UI** (`website-frontend/src/App.jsx`): New "Risk Management" card in Engine tab with:
  - Four toggle buttons for risk levels (0.25%, 0.5%, 0.75%, 1.0%)
  - Text descriptions: "Conservative", "Balanced", "Aggressive", "Very Aggressive"
  - Live dollar risk preview: "Account $10k will risk $100 at 1%" (recalculates as user types or changes balance)
  - Visual risk gauge with color scaling (green → cyan → yellow → orange as risk increases)
  - Immediate save to backend on selection change
- 🧮 **Fixed Dollar Risk Position Sizing**: Position size formula: `qty = (balance × risk%) / |entry − sl|`. Dollar risk stays constant across all trades regardless of SL distance. Enables high-frequency trading where:
  - Tight SL (2%) = larger position size (higher units traded)
  - Wide SL (5%) = smaller position size (fewer units traded)
  - Both trades risk the same absolute dollars ($100 per trade if set to 1% on $10k account)
  - Traders can scale position frequency/size by adjusting risk slider without manual recalculation.

### Critical Fix: StackMentor TP Partials Not Executing
- 🚨 **Root-cause fixed — `calculate_qty_splits` wrong positional argument** (`Bismillah/app/autotrade_engine.py` line 1477): `calculate_qty_splits(qty, precision)` was passing the symbol's `QTY_PRECISION` integer (e.g. `3`) as the `min_qty` parameter instead of as `precision`. The bundling guard inside `calculate_qty_splits` then treated any position smaller than 3 units as below minimum, collapsing `qty_tp2` and `qty_tp3` to `0.0`. TP1 received 100% of the qty, leaving nothing to close at TP2 and TP3. Fixed by importing `MIN_QTY_MAP` from `trade_execution.py` and calling `calculate_qty_splits(qty, min_qty=min_qty, precision=precision)` — identical to the correct pattern already used in `scalping_engine.py` and `trade_execution.py`.
- 🛡️ **Hardened `close_partial` against zero-qty orders** (`Bismillah/app/bitunix_autotrade_client.py`): Added an early-return guard that returns `{'success': False, 'error': 'qty=0 ...'}` before touching the exchange, preventing silent Bitunix rejections when qty is invalid.
- 🛡️ **Fail-loud guards in `handle_tp2_hit` / `handle_tp3_hit`** (`Bismillah/app/stackmentor.py`): If `qty_tp2` or `qty_tp3` is 0 at hit time, the handlers now log a clear error, mark the tier as hit (so monitoring isn't stuck), and return — rather than sending a 0-qty order that Bitunix rejects silently.
- 📝 **Fixed misleading log label** in `autotrade_engine.py`: `"TP1=50%"` corrected to `"TP1=60%"`. Log now also prints the actual computed `qty_splits` for every new StackMentor position.



### Engine Start/Stop — Web Dashboard
- 🔥 **Engine Start/Stop API** (`website-backend/app/routes/engine.py`): New `POST /engine/start` and `POST /engine/stop` endpoints wire the web dashboard directly into the same `autotrade_engine` that the Telegram bot runs. Starting the engine from the web now has identical effect to the Telegram `/start_autotrade` command.
- 🔥 **Real JWT Authentication**: Replaced dev-only auth bypass with full `HTTPBearer` token validation across all engine and portfolio routes. Every protected endpoint now decodes the Telegram-issued JWT before executing.
- 🔥 **Live Unrealized PnL on Portfolio Page**: Portfolio tab now surfaces real-time unrealized PnL pulled directly from Bitunix live positions, not just the closed-trade total in Supabase.
- 🚀 **Critical Fix: Bitunix API Authentication** (`bitunix_autotrade_client.py`): Resolved a critical "not authenticated" error that broke all Bitunix connections. Switched from the legacy double-SHA256 signature scheme to the now-required **HMAC-SHA256** standard.
- 🛠️ **Fixed: "Start Bot" Button Error (`No module named 'app.autotrade_engine'`)**: Resolved a Python `sys.path` namespace collision where the web backend's own `app/` package shadowed Bismillah's. Fixed by:
  - Forcing `Bismillah/` to `sys.path[0]` to guarantee import priority.
  - Loading `autotrade_engine` via `importlib.util.spec_from_file_location` under the alias `bismillah.autotrade_engine`, bypassing the namespace conflict entirely.
  - Caching the module in `sys.modules` so the in-memory `_running_tasks` state persists across HTTP requests.
  - Fixed a scope bug where `ae` was consumed outside its `try` block.
- 🛠️ **Fixed: Import Paths + Supabase Stop Signal** (`engine.py`, `autotrade_engine.py`, `scalping_engine.py`): Corrected relative import paths broken by the `sys.path` fix. Added a Supabase-backed stop signal that each engine loop polls so `POST /engine/stop` from the web cleanly halts the running trade loops.

### Performance Tab
- 🚀 **Real Performance Endpoint** (`website-backend/app/routes/performance.py`): New `GET /performance` endpoint returns an equity curve, win/loss breakdown, average PnL, best/worst trades, and 30-day PnL trend — all derived from live `autotrade_trades` data in Supabase rather than mock values.

### AI Intelligence Hub — Live Signals
- 🔥 **Live Signals Pipeline**: Replaced the hardcoded `MOCK_SIGNALS` on the dashboard with a real-time `GET /dashboard/signals` endpoint that derives direction, confidence, entry zone, TPs and SL from Binance public 24h ticker data for BTC/ETH/AVAX. Auto-refreshes every 30 seconds with a "Updated HH:MM:SS" stamp.
- 🔥 **Signal Outcome Tracking**: Each card now cross-references `autotrade_trades` (last 24h) and renders one of three outcome states: **In Position** (cyan, live PnL), **Take Profit Hit** (lime, shows TP1/TP2/TP3 hit + PnL), or **Stop Loss Hit** (rose, PnL). Prevents users from re-entering an idea the bot has already taken.
- 🔥 **Risk-Based 1-Click Entry**: New `POST /dashboard/signals/execute` opens a market position with TP/SL attached, sized dynamically from the *live* SL distance: `qty = (balance × risk%) / |entry − sl|`. Late entries automatically rescale — closer to SL = larger size, further from SL = smaller size — so risk per trade stays constant regardless of fill timing. Pulls `risk_per_trade` and `leverage` from the user's `autotrade_sessions`, syncs leverage on Bitunix, then routes through `place_order_with_tpsl`.
- 🔥 **5-Minute Entry Window**: 1-click execution is gated to 5 minutes from the signal's `generated_at` timestamp. The card shows a live MM:SS countdown (cyan → amber under 60s → rose when expired), and the button auto-locks to "Entry Window Closed" once the window elapses. Server enforces with HTTP 410 if the window has passed.
- 🛠️ **Dynamic Sizing Guards**: Backend validates SL distance (0.1%–15%), caps margin at 95% of available balance, enforces per-symbol qty precision (`BTCUSDT=3, ETHUSDT=2, AVAXUSDT=2`), and rejects sub-minimum quantities before hitting the exchange.

### StackMentor & Localization Improvements
- 🔥 **Corrected Notification Splits**: Updated signal notification labels to accurately reflect the 60%/30%/10% StackMentor quantity splits (fixing the previous 50%/40%/10% display error).
- 🔥 **R:R Correction**: Updated the R:R targets in progress messages to 1:2 → 1:3 → 1:5 to match the actual StackMentor execution logic.
- 🚀 **Critical Fix: Partial Close Execution**: Resolved a persistent bug where StackMentor partial Take Profits failed on Bitunix. Switched from `place_order` (which set `tradeSide: OPEN`) to the correct `close_partial` method (`reduceOnly: True`).
- 🌐 **Full English Localization**: Translated all Indonesian trading signals and StackMentor profit-taking notifications into English.

### Scheduler & Startup Safety
- 🛠️ **Startup Cross-Validation**: The bot's startup check now fetches live positions from the exchange per-user before issuing a conflict alert. Stale DB trades that no longer exist on the exchange are auto-closed, and notifications are suppressed if the exchange fetch fails — eliminating false-positive conflict alerts on restart.

### Infrastructure
- 🚀 **License Server Ported to Bismillah**: Moved `license_server/` components into `Bismillah/license_server/`, consolidating the service into a single deployable unit. Cleaned up the root `license_server/` folder post-migration.
- 🛠️ **Nginx Config Fix**: Corrected nginx to serve the built frontend directly from the `dist/` folder — no manual copy step required on deploy.
- 🛠️ **`.env.example` Corrected**: Set the correct `ENCRYPTION_KEY` placeholder in `website-backend/.env.example` so new deployments don't silently fail key decryption.

### AI Intelligence Hub — Live Signals
- 🔥 **Live Signals Pipeline**: Replaced the hardcoded `MOCK_SIGNALS` on the dashboard with a real-time `GET /dashboard/signals` endpoint that derives direction, confidence, entry zone, TPs and SL from Binance public 24h ticker data for BTC/ETH/AVAX. Auto-refreshes every 30 seconds with a "Updated HH:MM:SS" stamp.
- 🔥 **Signal Outcome Tracking**: Each card now cross-references `autotrade_trades` (last 24h) and renders one of three outcome states: **In Position** (cyan, live PnL), **Take Profit Hit** (lime, shows TP1/TP2/TP3 hit + PnL), or **Stop Loss Hit** (rose, PnL). Prevents users from re-entering an idea the bot has already taken.
- 🔥 **Risk-Based 1-Click Entry**: New `POST /dashboard/signals/execute` opens a market position with TP/SL attached, sized dynamically from the *live* SL distance: `qty = (balance × risk%) / |entry − sl|`. Late entries automatically rescale — closer to SL = larger size, further from SL = smaller size — so risk per trade stays constant regardless of fill timing. Pulls `risk_per_trade` and `leverage` from the user's `autotrade_sessions`, syncs leverage on Bitunix, then routes through `place_order_with_tpsl`.
- 🔥 **5-Minute Entry Window**: 1-click execution is gated to 5 minutes from the signal's `generated_at` timestamp. The card shows a live MM:SS countdown (cyan → amber under 60s → rose when expired), and the button auto-locks to "Entry Window Closed" once the window elapses. Server enforces with an HTTP 410 if the client clock is tampered with.
### StackMentor & Localization Improvements
- 🔥 **Corrected Notification Splits**: Updated signal notification labels to accurately reflect the 60%/30%/10% StackMentor quantity splits (fixing the previous 50%/40%/10% display error).
- 🔥 **R:R Correction**: Updated the R:R targets in progress messages to 1:2 → 1:3 → 1:5 to match the actual StackMentor execution logic.
- 🚀 **Critical Fix: Partial Close execution**: Resolved a persistent bug in the StackMentor monitor where partial Take Profits failed to execute on Bitunix. Switched from `place_order` (which erroneously set `tradeSide: OPEN`) to the correct `close_partial` method (enforcing `reduceOnly: True` and `tradeSide: OPEN`).
- 🌐 **Full English Localization**: Completed the translation of all Indonesian trading signals and StackMentor profit-taking notifications into English for a consistent professional interface.
- 🛠️ **Dynamic Sizing Guards**: Backend validates SL distance (0.1%–15%), caps margin at 95% of available balance, enforces per-symbol qty precision (`BTCUSDT=3, ETHUSDT=2, AVAXUSDT=2`), and rejects sub-minimum quantities before hitting the exchange.

### Web App Architecture (V2)
- 🔥 **Bot Start/Stop Controls**: Added a prominent Start/Stop bot toggle button in the sidebar (always visible) and a full Engine Controls card in the Engine tab with a live pulsing indicator showing whether the engine is running or stopped.
- 🔥 **Post-API-Save Bot Launch Prompt**: After successfully saving Bitunix API keys in the Settings tab, a modal confirmation overlay (`BotStartModal`) is displayed — allowing users to immediately launch the AutoTrade engine or defer startup with "Start Later". Includes a risk disclaimer banner.
- 🔥 **Bitunix Web Bridge Configured**: Exposes the same `API Key` and `API Secret` storage architecture behind AES-256-GCM encryption natively through the React Web Dashboard `SettingsTab`. Users can setup their bot's credentials without touching Telegram.
- 🔥 **Web Dashboard PnL Synchronization**: Corrected the logic in the web app's `PortfolioTab` to utilize backend Engine statistics (`engine.total_profit` and `engine.current_balance`). This perfectly mirrors what the AutoTrade session holds, curing discrepancies (e.g., where `Total PnL (30D)` rendered `$0.00`).
- 🔥 **Graceful UI Emptiness**: When users have zero active positions, the system will natively render a beautifully mapped `No Open Positions` card instead of dummy mockup placeholder fields. 
- 🛠️ **Test Endpoint**: A `POST /api/bitunix/keys/test` dry run engine was released to allow users to trial their API configuration natively via the web before persistent storage commits.
- 🛠️ **Dev Mode Auth Bypass**: Refactored `handleTelegramLogin` in `App.jsx` to directly consume the Telegram widget's user object without requiring a backend `/api/auth/telegram` server, enabling standalone local frontend development.
- 🛠️ **Vite IPv4 Binding + Localtunnel Support**: Forced Vite dev server to bind on `127.0.0.1` (IPv4) to resolve Telegram widget iframe security blocks; added `allowedHosts` whitelist to allow secure `localtunnel` HTTPS proxying for Telegram OAuth domain verification.

### Bitunix Client (Telegram & Web Core) 
- 🚀 **Thread-Safe Proxy Rate Limiter**: Implemented a globally-enforced `RateLimiter` token bucket strictly enforcing API payloads (e.g. `get_ticker`) across the application to <10req/s strictly, negating 429 penalties during heavy parallel validation.
- 🚀 **Smart Proxy Rotation & Blacklisting**: Integrated dynamic proxy health-checks into the `BitunixAutoTradeClient` which dynamically tracks and forcefully isolates broken gateways (from HTTP 403 blocks or massive timeouts) into temporary blackout pools.
- 🚀 **Parallel Signal Scanning (Concurrency)**: Refactored `ScalpingEngine` loops into pure `asyncio.gather` wraps, dropping portfolio signal generation latency from 15 seconds to under ~500ms whilst accurately retaining local `max_concurrent_positions` constraints.
- 🛠️ **StackMentor Fragment Protection (MIN_QTY Check)**: Crushed a critical math issue where closing small positions safely tripped below Bitunix's Exchange limits (e.g. TP3 fragment: 0.0005 BTC). If `qty_tp3` calculates below MIN_QTY, it intrinsically blends the payout forward into `tp2` or `tp1` fully to protect users seamlessly.
- 🚀 **Self-Healing TP/SL Endpoint Rotation**: The outdated `/api/v1/futures/tpsl/place_order` was universally substituted with the verified, highly elastic `modify_order` endpoint for real time partial adjustment.
- 🛠️ **Dual-Leg Safety Submissions**: Fixed an API schema conflict where issuing an updated Take Profit dynamically erased Stop Losses. The client now inherently mirrors existing unset targets (`slPrice=""`) without clearing bounds or halting rate limits.
- 🛠️ **Dynamic Position Resourcing**: `set_position_tpsl` and `set_position_sl` now aggressively resolve positional mappings internally without relying on fragile UUID callbacks.

## [Previous] - 2026-04-07

### AutoTrade System
- 🔥 **Swing Trade Engine Fix (13 Pairs)**: Expanded the Swing Engine to 13 altcoin pairs.
- 🔥 **StackMentor 3-Tier TP**: Implemented professional TP scale outs (at 1:2, 1:3 and 1:10) dropping minimum required bounds.
- 🔥 **Auto Mode Switcher**: Aggressive automatic pivoting between SCALPING vs SWING based on ADX/ATR metrics natively displayed on Dashboards.
- 🛠️ **Scalping Edge Safety**: 10x safety limitation cap with dynamic Max position risk caps running at 5% ceilings. 
  - Added XAUUSDT, CLUSDT, QQQUSDT as verifiable trading pairs.
