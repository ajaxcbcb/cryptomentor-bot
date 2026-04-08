# CryptoMentor V2.0 Changelog

All notable changes to the CryptoMentor Artificial Intelligence Trading project will be documented in this file.

## [Unreleased / Latest] - 2026-04-08

### Web App Architecture (V2)
- 🔥 **Bitunix Web Bridge Configured**: Exposes the same `API Key` and `API Secret` storage architecture behind AES-256-GCM encryption natively through the React Web Dashboard `SettingsTab`. Users can setup their bot's credentials without touching Telegram.
- 🔥 **Web Dashboard PnL Synchronization**: Corrected the logic in the web app's `PortfolioTab` to utilize backend Engine statistics (`engine.total_profit` and `engine.current_balance`). This perfectly mirrors what the AutoTrade session holds, curing discrepancies (e.g., where `Total PnL (30D)` rendered `$0.00`).
- 🔥 **Graceful UI Emptiness**: When users have zero active positions, the system will natively render a beautifully mapped `No Open Positions` card instead of dummy mockup placeholder fields. 
- 🛠️ **Test Endpoint**: A `POST /api/bitunix/keys/test` dry run engine was released to allow users to trial their API configuration natively via the web before persistent storage commits.

### Bitunix Client (Telegram & Web Core) 
- 🚀 **Self-Healing TP/SL Endpoint Rotation**: The outdated `/api/v1/futures/tpsl/place_order` was universally substituted with the verified, highly elastic `modify_order` endpoint for real time partial adjustment.
- 🛠️ **Dual-Leg Safety Submissions**: Fixed an API schema conflict where issuing an updated Take Profit dynamically erased Stop Losses. The client now inherently mirrors existing unset targets (`slPrice=""`) without clearing bounds or halting rate limits.
- 🛠️ **Dynamic Position Resourcing**: `set_position_tpsl` and `set_position_sl` now aggressively resolve positional mappings internally without relying on fragile UUID callbacks.

## [Previous] - 2026-04-07

### AutoTrade System
- 🔥 **Swing Trade Engine Fix (13 Pairs)**: Expanded the Swing Engine to 13 altcoin pairs.
- 🔥 **StackMentor 3-Tier TP**: Implemented professional TP scale outs (at 1:2, 1:3 and 1:10) dropping minimum required bounds.
- 🔥 **Auto Mode Switcher**: Aggressive automatic pivoting between SCALPING vs SWING based on ADX/ATR metrics natively displayed on Dashboards.
- 🛠️ **Scalping Edge Safety**: 10x safety limitation cap with dynamic Max position risk caps running at 5% ceilings. 
