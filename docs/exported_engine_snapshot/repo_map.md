# Engine-Relevant Repo Map (Snapshot)

Scope: files confirmed to participate in signal generation, trade execution, risk, engine lifecycle, web control-plane, or exchange integration.

## Telegram/Bot Runtime Core (`Bismillah/`)

```text
Bismillah/
  main.py                                 # Bot process entrypoint; loads env, starts Telegram bot
  bot.py                                  # TelegramBot.run_bot(); starts scheduler + auto mode switcher
  app/
    autotrade_engine.py                   # Swing/autotrade loop, signal scan, queueing, risk sizing, order placement
    scalping_engine.py                    # Scalping loop, sideways + trend signal path, anti-flip, order placement path
    trade_execution.py                    # Unified managed-entry helper (used by scalping path)
    stackmentor.py                        # In-memory TP/SL monitor + staged close handlers
    bitunix_autotrade_client.py           # Bitunix REST adapter (account, positions, orders, TP/SL mutation)
    bitunix_ws_pnl.py                     # Bitunix private WS unrealized-PnL tracker
    trade_history.py                      # DB persistence/reconciliation of open/closed trades
    trading_mode.py                       # TradingMode/ScalpingConfig/ScalpingPosition/MicroScalpSignal dataclasses
    trading_mode_manager.py               # Trading mode persistence + switch orchestration
    scheduler.py                          # Startup restore + periodic health check + startup reconciliation
    engine_restore.py                     # Alternate restore helpers (risk migration + engine restore)
    exchange_registry.py                  # Exchange config + client factory
    supabase_repo.py                      # Supabase read/write helpers, risk settings, API key storage
    auto_mode_switcher.py                 # Regime-driven mode switching task
    market_sentiment_detector.py          # SIDEWAYS/TRENDING classification for auto mode switcher
    autosignal_async.py                   # Async/cached scalping signal generation (trend path)
    candle_cache.py                       # Candle cache + API concurrency semaphore
    providers/
      alternative_klines_provider.py      # Multi-source OHLCV ingestion (Bitunix -> Binance -> CryptoCompare -> CoinGecko)
    sideways_detector.py                  # Sideways vote model (ATR/EMA spread/range width)
    range_analyzer.py                     # Range S/R extraction for sideways logic
    bounce_detector.py                    # Wick-based bounce confirmation
    micro_momentum_detector.py            # 1m/3m momentum detector for sideways micro-scalps
    rsi_divergence_detector.py            # RSI divergence detector used in confluence/sideways
    position_sizing.py                    # Risk-based sizing helper (used by scalping)
```

## Website Backend Runtime (`website-backend/`)

```text
website-backend/
  main.py                                 # FastAPI app entrypoint, middleware + routers
  config.py                               # Environment-driven config constants
  app/
    db/supabase.py                        # Supabase client for web backend
    auth/jwt.py                           # JWT create/decode
    auth/telegram.py                      # Telegram Login Widget signature validation
    middleware/verification_guard.py      # Route guard for UID verification status
    services/bitunix.py                   # Web wrapper around BitunixAutoTradeClient + key encryption/decryption
    services/signal_queue.py              # Queue manager abstraction (DB-backed), mostly sidecar currently
    routes/
      auth.py                             # Telegram login to JWT
      user.py                             # UID submission + verification status endpoints
      dashboard.py                        # Engine toggle, settings, performance, portfolio aggregate
      engine.py                           # Direct engine start/stop/state via dynamic Bismillah module loading
      bitunix.py                          # Live account/positions/history/tpsl + close 1-click position endpoint
      signals.py                          # Signal generation endpoint + 1-click trade execution endpoint
    db/migrations/signal_queue_table.sql  # Signal queue persistence schema
```

## Infra/Dependency Manifests

```text
Bismillah/requirements.txt                # Bot/runtime Python deps
website-backend/requirements.txt          # Web API Python deps
Bismillah/.env.example                    # Bot env variable inventory (template)
website-backend/.env.example              # Web env variable inventory (contains sensitive sample literals; redact in docs)
```

