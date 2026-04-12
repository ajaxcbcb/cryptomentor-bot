# Module Interfaces (Key Runtime Contracts)

## Scope

This file captures high-impact modules/classes/functions used by the live trading and signal runtime.

---

## 1) Engine Entrypoints

## `Bismillah/app/autotrade_engine.py`

### `start_engine(bot, user_id, api_key, api_secret, amount, leverage, notify_chat_id, is_premium=False, silent=False, exchange_id="bitunix")`
- Inputs: bot instance, user credentials/config, mode context.
- Output: none (starts async task, updates `_running_tasks`).
- Side effects:
  - DB updates to `autotrade_sessions.engine_active`.
  - Starts either swing loop task or `ScalpingEngine.run()`.

### `stop_engine(user_id)`
- Inputs: user id.
- Output: none.
- Side effects:
  - Cancels task for user if running.
  - DB sets `engine_active=False`.

### `_trade_loop(...)` (async)
- Inputs: full user runtime settings and exchange creds.
- Output: none (long-running loop).
- Side effects:
  - Reads/writes DB (`autotrade_sessions`, `signal_queue`, `autotrade_trades`).
  - Sends Telegram notifications.
  - Calls exchange APIs and opens/closes live positions.

### `_compute_signal_pro(base_symbol, btc_bias=None, user_risk_pct=1.0)`
- Inputs: base symbol and context.
- Output: signal dict or `None`.
- Side effects: market-data fetches through provider, logging.

### `_generate_confluence_signal(symbol, candles_1h, user_risk_pct=0.5, btc_bias=None)`
- Inputs: symbol + candle series + risk profile.
- Output: confluence signal dict or `None`.
- Side effects: none beyond logs.

---

## 2) Scalping Engine

## `Bismillah/app/scalping_engine.py`

### `class ScalpingEngine`

### `run(self)` (async)
- Inputs: instance fields.
- Output: none (long-running loop).
- Side effects: reads stop flags, monitors positions, executes trades, sends messages.

### `generate_scalping_signal(self, symbol)` (async)
- Inputs: symbol.
- Output: `ScalpingSignal`/`MicroScalpSignal` or `None`.
- Side effects: reads mode config + market data.

### `_try_sideways_signal(self, symbol)` (async)
- Inputs: symbol.
- Output: `MicroScalpSignal` or `None`.
- Dependencies:
  - `SidewaysDetector`, `RangeAnalyzer`, `BounceDetector`, `RSIDivergenceDetector`, `MicroMomentumDetector`, `candle_cache`.

### `_passes_anti_flip_filters(self, signal)`
- Inputs: signal object.
- Output: bool.
- Side effects: mutates `signal_streaks`, checks `last_closed_meta`.

### `place_scalping_order(self, signal)` (async)
- Inputs: validated signal.
- Output: bool success.
- Side effects:
  - calls `trade_execution.open_managed_position`.
  - persists open trade and in-memory position.

---

## 3) Unified Execution Layer

## `Bismillah/app/trade_execution.py`

### `open_managed_position(...)` (async)
- Inputs:
  - client, user_id, symbol, side, entry/sl/qty/leverage,
  - flags (`set_leverage`, `register_in_stackmentor`, `reconcile`).
- Output: `ExecutionResult` dataclass.
- Side effects:
  - exchange calls (`get_ticker`, `set_leverage`, `place_order_with_tpsl`, optional repair calls),
  - optional StackMentor registry mutation.

### `build_stackmentor_levels(...)`
- Inputs: entry, sl, side, qty, symbol, precision.
- Output: `StackMentorLevels`.
- Side effects: none.

### `validate_entry_prices(side, entry, tp1, sl, mark_price)`
- Output: `(is_valid, adjusted_sl, error)`.

### `reconcile_position(...)` (async)
- Inputs: expected live position invariants.
- Output: `(healthy: bool, notes: list, actual_qty: float)`.
- Side effects:
  - can call TP/SL repair APIs,
  - can trigger emergency close.

---

## 4) Position Monitoring

## `Bismillah/app/stackmentor.py`

### `register_stackmentor_position(...)`
- Inputs: full trade/level/split metadata.
- Output: none.
- Side effects: mutates in-memory `_stackmentor_positions`.

### `monitor_stackmentor_positions(bot, user_id, client, notify_chat_id)` (async)
- Inputs: bot + exchange client + user context.
- Output: none.
- Side effects:
  - mark-price polling,
  - partial/close calls,
  - DB updates in `autotrade_trades`,
  - Telegram messages.

---

## 5) Exchange Adapter

## `Bismillah/app/bitunix_autotrade_client.py`

### `class BitunixAutoTradeClient`
- Responsibility: signed REST calls, account/position/order operations.

Key methods:
- `get_account_info()` -> normalized account dict.
- `get_positions()` -> normalized positions list.
- `get_ticker(symbol)` -> mark/last price.
- `place_order_with_tpsl(symbol, side, qty, tp_price, sl_price)`.
- `place_order(...)`, `close_partial(...)`.
- `set_leverage(...)`, `set_margin_mode(...)`.
- `set_position_sl(...)`, `set_position_tpsl(...)`.

Side effects:
- Live exchange mutations and signed HTTP I/O.

---

## 6) Market Data + Signal Dependencies

### `Bismillah/app/providers/alternative_klines_provider.py`
- `get_klines(symbol, interval, limit)` -> Binance-format OHLCV list.
- Fallback chain: Bitunix -> Binance Futures -> CryptoCompare -> CoinGecko.

### `Bismillah/app/autosignal_async.py`
- `compute_signal_scalping_async(base_symbol)` -> trend/scalping signal dict.

### `Bismillah/app/candle_cache.py`
- `get_candles_cached(fetch_func, symbol, timeframe, limit)` with TTL cache + semaphore.

### `Bismillah/app/sideways_detector.py`
- `SidewaysDetector.detect(...)` -> `SidewaysResult`.

### `Bismillah/app/range_analyzer.py`
- `RangeAnalyzer.analyze(...)` -> `RangeResult` or None.

### `Bismillah/app/bounce_detector.py`
- `BounceDetector.detect(...)` -> `BounceResult` or None.

### `Bismillah/app/micro_momentum_detector.py`
- `MicroMomentumDetector.detect(...)` -> `MomentumSignal` or None.

### `Bismillah/app/rsi_divergence_detector.py`
- `RSIDivergenceDetector.detect(...)` -> `DivergenceResult`.

---

## 7) Web Control Plane Interfaces

## `website-backend/app/routes/engine.py`
- `/dashboard/engine/start`, `/stop`, `/state`.
- Dynamically imports Bismillah modules and triggers engine functions.

## `website-backend/app/routes/signals.py`
- `/dashboard/signals` -> confluence/ticker signal feed.
- `/dashboard/signals/execute` -> one-click live execution.

## `website-backend/app/routes/bitunix.py`
- `/bitunix/account`, `/positions`, `/positions/close`, `/trade-history`, `/positions/tpsl`, keys endpoints.

## `website-backend/app/services/bitunix.py`
- credential load/decrypt + async wrappers for Bitunix client calls.

---

## 8) Coupling Notes

Confirmed coupling:
- Web backend imports and executes bot engine module directly (tight coupling across projects).
- Signal generation and execution logic exist in both bot and web code paths with partial duplication.
- DB (`autotrade_sessions`, `autotrade_trades`, `signal_queue`) is shared control-plane state.

Unclear from code:
- Intended long-term ownership boundary between bot runtime and web execution path is not explicit.
