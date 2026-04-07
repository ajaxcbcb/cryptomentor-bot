# Bismillah Bot - Complete Overview

**Path:** `Bismillah/`  
**Type:** Main Product - Telegram Trading Bot  
**Status:** ✅ Production

---

## 🎯 Purpose

Bismillah Bot adalah Telegram bot untuk crypto trading yang menyediakan:
- Free & Premium trading signals
- AutoTrade automation (copy trading)
- Manual signal generation
- Trading education & skills
- Community features

---

## 📁 Directory Structure

```
Bismillah/
├── bot.py                          # Main bot entry point
├── main.py                         # Application launcher
├── config.py                       # Configuration
├── database.py                     # SQLite database (legacy)
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
│
├── app/                           # Core application modules
│   ├── handlers_autotrade.py     # AutoTrade command handlers
│   ├── handlers_manual_signals.py # Manual signal handlers
│   ├── handlers_free_signal.py   # Free signal handlers
│   ├── handlers_skills.py        # Skills/education handlers
│   ├── handlers_community.py     # Community features
│   ├── handlers_risk_mode.py     # Risk management UI
│   │
│   ├── autotrade_engine.py       # Swing trade engine
│   ├── scalping_engine.py        # Scalping trade engine (NEW: StackMentor)
│   ├── stackmentor.py            # 3-tier TP system
│   ├── trading_mode_manager.py   # Mode switching logic
│   │
│   ├── auto_mode_switcher.py    # Auto mode switching (background)
│   ├── market_sentiment_detector.py # Market analysis
│   │
│   ├── exchange_registry.py     # Multi-exchange support
│   ├── bitunix_autotrade_client.py
│   ├── bingx_autotrade_client.py
│   ├── binance_autotrade_client.py
│   ├── bybit_autotrade_client.py
│   │
│   ├── supabase_repo.py          # Supabase database operations
│   ├── position_sizing.py        # Risk-based position sizing
│   ├── risk_calculator.py        # Risk management
│   │
│   ├── autosignal_async.py       # Signal generation (async)
│   ├── autosignal_fast.py        # Signal generation (fast)
│   ├── candle_cache.py           # Candle data caching
│   │
│   ├── sideways_detector.py     # Sideways market detection
│   ├── range_analyzer.py         # Support/resistance analysis
│   ├── bounce_detector.py        # Bounce confirmation
│   ├── rsi_divergence_detector.py # RSI divergence
│   │
│   ├── engine_restore.py         # Auto-restore engines on restart
│   ├── maintenance_notifier.py   # Maintenance notifications
│   ├── scheduler.py              # Background task scheduler
│   │
│   └── providers/                # Data providers
│       ├── alternative_klines_provider.py
│       ├── advanced_data_provider.py
│       └── multi_source_provider.py
│
└── db/                            # Database migrations
    ├── setup_supabase.sql
    ├── add_trading_mode.sql
    ├── add_auto_mode_switcher.sql
    ├── add_tp_partial_tracking.sql
    └── ...
```

---

