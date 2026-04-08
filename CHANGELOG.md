# CryptoMentor V2.0 Changelog

All notable changes to the CryptoMentor Artificial Intelligence Trading project will be documented in this file.

## [Unreleased / Latest] - 2026-04-08

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
