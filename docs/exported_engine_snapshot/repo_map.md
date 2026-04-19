# Engine-Relevant Repo Map (Snapshot)

**As Of:** 2026-04-17

Scope: files that directly participate in signal generation, trade execution, risk/adaptive behavior, engine lifecycle, web control-plane, and exchange integration.

## Telegram/Bot Runtime Core (`Bismillah/`)

```text
Bismillah/
  main.py                                 # Process entrypoint
  bot.py                                  # Telegram runtime bootstrap
  app/
    autotrade_engine.py                   # Swing loop, candidate queue, execution orchestration
    scalping_engine.py                    # Scalping loop, signal path, timeout/pending safeguards
    trade_execution.py                    # Unified managed entry flow for swing+scalp
    stackmentor.py                        # Runtime TP/SL target model and monitor
    adaptive_confluence.py                # Global adaptive confluence state
    win_playbook.py                       # Runtime risk overlay + guardrails
    volume_pair_selector.py               # Top-10 by Bitunix quoteVol selector + fallback chain
    symbol_coordinator.py                 # Single-owner-per-user-per-symbol + pending TTL self-heal
    trading_mode.py                       # Config dataclasses + timeout feature flags/alias
    trading_mode_manager.py               # Trading mode persistence/switching
    trade_history.py                      # Open/close persistence + reconcile helpers
    scheduler.py                          # Startup stale checks + health routines
    engine_restore.py                     # Engine restore helpers
    exchange_registry.py                  # Exchange config + client factory
    supabase_repo.py                      # Supabase read/write operations
    auto_mode_switcher.py                 # Sentiment-driven mode switch task
    market_sentiment_detector.py          # SIDEWAYS/TRENDING classifier
    bitunix_autotrade_client.py           # Primary exchange adapter
    bitunix_ws_pnl.py                     # Private websocket unrealized PnL tracker
    autosignal_async.py                   # Async signal computation path
    autosignal_fast.py                    # Fast signal utilities
    candle_cache.py                       # Candle cache + throttling
    sideways_detector.py                  # Sideways detection
    range_analyzer.py                     # Range extraction
    bounce_detector.py                    # Bounce confirmation
    rsi_divergence_detector.py            # RSI divergence signal helper
    position_sizing.py                    # Risk-based sizing helper
```

## Website Backend Runtime (`website-backend/`)

```text
website-backend/
  main.py                                 # FastAPI entrypoint
  config.py                               # Env-driven config
  app/
    db/supabase.py                        # Supabase client
    services/bitunix.py                   # Web wrapper for exchange actions
    services/signal_queue.py              # Queue helper abstraction
    routes/
      auth.py                             # Telegram auth/JWT
      user.py                             # UID/verification status routes
      dashboard.py                        # Settings, portfolio, engine toggles
      engine.py                           # Direct engine start/stop/state bridge
      signals.py                          # Signal list + execute endpoints
      bitunix.py                          # Account/positions/history/tpsl routes
```

## Infra / Runtime Standards Anchors

```text
Bismillah/app/volume_pair_selector.py     # Dynamic Top-10 pair standard + fallback order
Bismillah/app/win_playbook.py             # Base/overlay/effective risk caps and guardrails
Bismillah/app/adaptive_confluence.py      # conf_delta/vol_delta/ob_mode adaptive controls
Bismillah/app/symbol_coordinator.py       # pending_ttl_seconds=90 and startup/reconcile safety
Bismillah/app/trading_mode.py             # timeout feature flag + legacy alias compatibility
```

## Notes

- Runtime pair-count messaging should reflect dynamic Top-10 routing, not fixed pair counts.
- Risk wording standard: **Equity** (risk basis) vs **Available balance** (free margin context only).

## Operational Scripts (2026-04-19)

- `scripts/hourly_admin_engine_report.py`
  - Hourly Telegram admin summary for engine/trade/no-trade status.
- `scripts/reset_bitunix_registration.py`
  - One-time Bitunix UID reset + re-verification recovery workflow.
- `scripts/broadcast_api_issue_verified.py`
  - Verified-audience API issue campaign (missing/invalid API key remediation).
