# Signal Engine Spec (Current Code)

## Scope

- Swing/autotrade signal path: `Bismillah/app/autotrade_engine.py` (`_compute_signal_pro`, `_generate_confluence_signal`, `_get_btc_bias`).
- Scalping signal path: `Bismillah/app/scalping_engine.py` (`generate_scalping_signal`, `_try_sideways_signal`) + `Bismillah/app/autosignal_async.py`.
- Web signal path: `website-backend/app/routes/signals.py` (`generate_confluence_signals`, `_build_signal` fallback).

---

## A) Confirmed From Code

## A.1 Swing/Autotrade Signal (`_compute_signal_pro`)

- Symbol universe from `ENGINE_CONFIG["symbols"]` in `autotrade_engine.py`:
  - `BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, DOT, MATIC, LINK, UNI, ATOM, XAU, CL, QQQ`.
- Timeframes:
  - 1h candles (primary trend/volatility),
  - 15m candles (entry trigger / structure).
- Data source:
  - `alternative_klines_provider.get_klines(base_symbol, interval=...)`.

### BTC bias gating (`_get_btc_bias`)

- Inputs: BTC 4h/1h/15m.
- Bias scoring uses:
  - EMA structure (4h and 1h),
  - 15m momentum (EMA9 vs EMA21),
  - market structure (HH/HL or LH/LL),
  - volume ratio,
  - RSI penalties at extremes.
- Altcoin hard skip when BTC strength `< 40`.
- Additional alignment filter: altcoin trend cannot contradict BTC bullish/bearish bias.

### Primary confluence system (`_generate_confluence_signal`)

- Factor scoring:
  - near S/R: +30,
  - RSI extreme: +25,
  - volume spike (>1.5x): +20,
  - trending regime (ATR% > 0.3): +15,
  - price above MA50: +10.
- Adaptive risk profile inputs:
  - `_risk_profile(user_risk_pct)` -> `min_confidence`, `atr_multiplier` for TP width.
- Direction:
  - LONG if RSI<30,
  - SHORT if RSI>70,
  - otherwise LONG default.
- Price levels:
  - LONG: `entry=support`, `tp1=entry+0.75*ATR*atr_multiplier`, `tp2=entry+1.25*ATR*atr_multiplier`, `sl=support-0.5*ATR`.
  - SHORT mirrored around resistance.

### Secondary fallback (SMC/hybrid block inside `_compute_signal_pro`)

- Triggered when confluence missing/weak.
- Components:
  - 1h EMA trend (`EMA21/EMA50`),
  - 15m EMA crossover/EMA alignment,
  - RSI filters (`rsi_long_max`, `rsi_short_min`),
  - volume ratio bonus/penalty,
  - structure bonuses (BOS via swing highs/lows),
  - order block and FVG heuristics,
  - wick-rejection/manipulation filter (`wick_rejection_max`),
  - ATR volatility bounds (`min_atr_pct`, `max_atr_pct`).
- SL/TP construction:
  - `sl_dist = atr_1h * atr_sl_multiplier`,
  - `tp1_dist = atr_1h * atr_tp1_multiplier`,
  - `tp2_dist = atr_1h * atr_tp2_multiplier`.
- R:R gate:
  - `rr = tp1_dist / sl_dist`; requires `>= ENGINE_CONFIG["min_rr_ratio"]`.

### Reversal/flip logic (`_is_reversal`)

- Requires opposite direction + confidence threshold.
- Trending mode branch:
  - stricter CHoCH-style checks (`trend_1h`, `market_structure`) + 30m cooldown.
- Sideways mode branch:
  - relaxed checks + RSI/trend permissive conditions + 15m cooldown.

## A.2 Scalping Signal

### Pipeline (`ScalpingEngine.generate_scalping_signal`)

- Mode check via `TradingModeManager.get_mode(user_id)`.
- If `SCALPING`, attempt sideways signal first:
  - `_try_sideways_signal(symbol)`.
- If no sideways signal, fallback:
  - `autosignal_async.compute_signal_scalping_async(...)`.

### Sideways signal (`_try_sideways_signal`)

- Inputs:
  - candles 5m/15m via cache (`candle_cache.get_candles_cached`).
- Steps:
  - `SidewaysDetector.detect(...)` (2-of-3 vote: ATR relative, EMA spread, range width),
  - `RangeAnalyzer.analyze(...)` for support/resistance,
  - `BounceDetector.detect(...)` for wick bounce,
  - optional `MicroMomentumDetector.detect(...)` from 1m/3m if bounce absent,
  - optional RSI divergence bonus via `RSIDivergenceDetector.detect(...)`.
- Confidence floor for sideways branch:
  - requires `>= 70`.
- TP/SL:
  - TP around 70% toward opposite range edge,
  - SL padded by `0.75 * ATR` (fallback 0.35%),
  - requires R:R `>= 1.0`.

### Trending scalping fallback (`autosignal_async.compute_signal_scalping_async`)

- Trend basis from 15m EMA structure.
- Entry trigger from 5m RSI + volume ratio.
- Supports strong-trend and weak/ranging conditions.
- TP/SL:
  - `sl_distance = atr_5m * 1.5`,
  - `tp_distance = sl_distance * 1.5`.

### Scalping anti-churn gates

- `_passes_anti_flip_filters(...)`:
  - consecutive signal confirmation (`signal_confirmations_required`, max gap),
  - opposite-direction reentry cooldown (`anti_flip_opposite_seconds`, widened for sideways closes).
- Symbol cooldown tracking in `cooldown_tracker`.

## A.3 Web Signals (`website-backend/app/routes/signals.py`)

- `/dashboard/signals`:
  - tries `generate_confluence_signals(sym, user_risk_pct)` per watchlist symbol,
  - fallback to `_build_signal(...)` momentum-style from Binance 24h ticker.
- Confluence scoring in web route mirrors swing-style point model (S/R, RSI, volume, ATR trend proxy, MA).
- `/dashboard/signals/execute`:
  - enforces entry age window,
  - recomputes a **live** signal via `_live_signal(...)` (ticker-based fallback builder),
  - then computes risk-based quantity from live SL distance.

---

## B) Likely Inferred From Naming/Comments (Not Strictly Enforced Everywhere)

- “Confluence minimum can adapt by risk” is documented in comments, but enforcement has additional static gates in swing flow.
- “StackMentor 3-tier exits (60/30/10)” language appears in logs/comments in some places, while current StackMentor config declares unified full close.

---

## C) Unclear From Code

- Exact intended precedence between confluence adaptive thresholds vs static `ENGINE_CONFIG["min_confidence"]` gate in swing path is unclear from code.
- Intended production path for web signal execution (confluence-derived vs momentum `_build_signal`) is unclear from code because execute path currently re-derives via ticker builder.
- Presence of `app.analysis.range_analyzer` import in swing confluence S/R branch is unclear from code (path does not exist in this repo snapshot).

