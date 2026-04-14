# Trading Engine Overview (Code Snapshot)

## 1) Runtime Topology

- Telegram runtime entry: `Bismillah/main.py` -> `bot.TelegramBot.run_bot()` in `Bismillah/bot.py`.
- Engine orchestration: `Bismillah/app/scheduler.py` starts restore/health tasks and (indirectly) engine instances.
- Engine start function: `start_engine(...)` in `Bismillah/app/autotrade_engine.py`.
- Mode split:
  - `TradingMode.SCALPING` -> `ScalpingEngine.run()` in `Bismillah/app/scalping_engine.py`.
  - else -> swing loop `_trade_loop(...)` in `Bismillah/app/autotrade_engine.py`.

## 2) Control Flow: Market Data -> Signal -> Risk -> Execution -> Position Management

### Swing/Autotrade path (`autotrade_engine._trade_loop`)

1. Poll account/positions from exchange client (`client.get_account_info`, `client.get_positions`).
2. Generate market regime proxy (`_get_btc_bias()`), then per-symbol signal via `_compute_signal_pro(...)`.
3. Candidate filtering:
   - confidence gates (`ENGINE_CONFIG["min_confidence"]`, plus sideways scan bump),
   - occupied symbol exclusion,
   - max concurrent positions.
4. Queue candidates by confidence into in-memory `_signal_queues` and DB `signal_queue`.
5. For next queued signal:
   - compute quantity with `calc_qty_with_risk(...)` (equity-based sizing; fallback fixed margin),
   - validate SL/TP vs current mark price (`client.get_ticker`),
   - place order atomically with TP/SL (`client.place_order_with_tpsl`).
6. Persist trade (`trade_history.save_trade_open`), start PnL tracker (`bitunix_ws_pnl.start_pnl_tracker`), notify Telegram.
7. Ongoing management:
   - `monitor_stackmentor_positions(...)` for TP handling,
   - reversal/flip branch via `_is_reversal(...)` + close/reopen flow,
   - close detection and DB close updates.

### Scalping path (`ScalpingEngine.run`)

1. Scan each configured symbol concurrently every `scan_interval`.
2. Signal generation (`generate_scalping_signal`):
   - sideways-first path: `_try_sideways_signal(...)` (SidewaysDetector, RangeAnalyzer, BounceDetector, optional MicroMomentum, RSI divergence),
   - fallback trending path: `autosignal_async.compute_signal_scalping_async(...)`.
3. Validation/gating:
   - `validate_scalping_entry(...)`,
   - `_passes_anti_flip_filters(...)`,
   - cooldown + concurrency checks.
4. Risk sizing via `calculate_position_size_pro(...)` (risk capped to 5% in code, leverage capped to 10 for scalping path).
5. Order execution via unified helper `trade_execution.open_managed_position(...)`.
6. Local tracking (`self.positions`) + DB open row + Telegram notification.
7. Position maintenance:
   - `monitor_stackmentor_positions(...)`,
   - 2-minute forced close for sideways positions,
   - 30-minute max hold forced close.

## 3) Exchange Integration Flow

- Primary exchange adapter: `BitunixAutoTradeClient` (`Bismillah/app/bitunix_autotrade_client.py`).
- Public data for signal generation:
  - OHLCV via `AlternativeKlinesProvider` (Bitunix public kline -> Binance Futures -> CryptoCompare -> CoinGecko fallback chain).
  - Web signal fallback uses Binance 24h ticker endpoint (`api.binance.com/api/v3/ticker/24hr`).
- Private trade/account:
  - account, positions, place order, TP/SL mutation, partial close, leverage/margin mode.

## 4) Persistence and State

- In-memory state:
  - swing: `_running_tasks`, `_signal_queues`, `_signals_being_processed`, `_flip_cooldown`, `_tp1_hit_positions`.
  - scalping: `positions`, `cooldown_tracker`, `signal_streaks`, `last_closed_meta`.
  - stackmentor: `_stackmentor_positions`.
- DB state (Supabase):
  - `autotrade_sessions`, `autotrade_trades`, `signal_queue`, `user_api_keys`, `user_verifications`, `users`.

## 5) Web Control Plane Coupling

- Engine web start/stop: `website-backend/app/routes/engine.py` dynamically imports Bismillah engine module and calls `start_engine/stop_engine`.
- Dashboard settings/risk updates: `website-backend/app/routes/dashboard.py` writes to `autotrade_sessions`.
- 1-click execution path: `website-backend/app/routes/signals.py` computes sizing and calls `services.bitunix.place_market_with_tpsl`.

## 6) Processing Model

- Confirmed from code: **hybrid polling + event-driven**.
  - Polling loops: swing/scalping engines, scheduler health checks, auto-mode switcher.
  - Event-like stream: Bitunix private WS tracker (`bitunix_ws_pnl.py`) for unrealized PnL updates.

