# Bismillah Bot - Complete Overview

**Path:** `Bismillah/`  
**Type:** Main Product - Telegram Trading Bot  
**Status:** Production  
**Last Updated:** 2026-04-17

---

## Purpose

Bismillah Bot adalah Telegram bot untuk crypto trading yang menyediakan:
- Free and premium signal surfaces
- AutoTrade automation (swing + scalping)
- Risk-managed execution with exchange adapters
- Trading education and community features
- Web control-plane integration (dashboard + settings)

---

## Directory Structure (Current)

```text
Bismillah/
|- main.py                          # Runtime entrypoint
|- bot.py                           # Telegram app bootstrap
|- config.py                        # App configuration
|- requirements.txt                 # Python dependencies
|- .env / .env.example              # Environment variables
|
|- app/
|  |- autotrade_engine.py           # Swing engine loop
|  |- scalping_engine.py            # Scalping engine loop
|  |- trade_execution.py            # Unified managed entry flow
|  |- stackmentor.py                # Unified TP model (single-target runtime)
|  |- symbol_coordinator.py         # Per-user per-symbol ownership + pending locks
|  |- volume_pair_selector.py       # Dynamic top-volume pair routing
|  |- adaptive_confluence.py        # Adaptive confluence thresholds
|  |- win_playbook.py               # Runtime risk overlay logic
|  |- trading_mode.py               # Scalping config + timeout feature flags
|  |- trading_mode_manager.py       # Mode persistence and switching
|  |- auto_mode_switcher.py         # Sentiment-driven auto mode switching
|  |- market_sentiment_detector.py  # SIDEWAYS/TRENDING detector
|  |- trade_history.py              # Open/close persistence + reconciliation
|  |- scheduler.py                  # Startup checks + periodic health tasks
|  |- supabase_repo.py              # Supabase data access
|  |- bitunix_autotrade_client.py   # Primary exchange adapter
|  |- exchange_registry.py          # Multi-exchange client factory
|  |- handlers_autotrade.py         # Main autotrade UX handlers
|  |- handlers_autotrade_admin.py   # Admin autotrade controls
|  |- handlers_autosignal_admin.py  # Admin autosignal tools
|  |- handlers_admin_premium.py     # Premium/admin related handlers
|  |- handlers_community.py         # Community features
|  |- position_sizing.py            # Risk-based position sizing
|  |- risk_calculator.py            # Risk helper utilities
|  |- autosignal_async.py           # Async signal computations
|  |- autosignal_fast.py            # Fast signal path helpers
|  |- candle_cache.py               # Market data cache
|  |- range_analyzer.py             # Range analysis
|  |- sideways_detector.py          # Sideways detector
|  |- bounce_detector.py            # Bounce confirmation
|  |- rsi_divergence_detector.py    # RSI divergence confirmation
|  |- engine_restore.py             # Engine restore helpers
|  |- maintenance_notifier.py       # Maintenance notifications
|  `- providers/                    # Market data providers
|
`- db/
   |- user_api_keys.sql
   |- community_partners.sql
   `- autotrade_reminder_log.sql
```

---

## Runtime Standards (Code-Truth)

- Pair universe standard: **Top 10 Bitunix USDT symbols by `quoteVol`**, highest-first.
- Pair selector fallback order: **fresh -> cache fallback -> bootstrap fallback**.
- Adaptive refresh cadence: swing/scalp runtime refresh every **10 minutes**.
- Risk overlay is **runtime-only** (memory/state), never mutates persisted base user risk.
- Effective risk cap: base risk clamp `0.25%-5.0%`, effective clamp `<=10.0%`.
- Timeout protection is feature-flagged and backward compatible with alias env key.
- Pending lock safety is enforced with auto-clear for stale pending-without-position (`90s` TTL) plus startup sanitize/reconcile paths.

---

## Wording Standard

- Use **Equity** for account-value/risk basis.
- Use **Available balance** only for free margin context.

---

## Operational Update (2026-04-19)

- Added ops script: `scripts/hourly_admin_engine_report.py`
  - Sends hourly engine/trade/no-trade summary to Telegram admins.
- Added ops script: `scripts/reset_bitunix_registration.py`
  - One-time user UID reset flow with re-verification gating.
- Registration recovery lifecycle standard:
1. Reset user to pending (`user_verifications=pending`, `autotrade_sessions=pending_verification`).
2. Re-verify/approve via reviewer flow (`user_verifications=approved`, `autotrade_sessions=uid_verified`).
3. Notify user/admin and keep run evidence in `logs/*.json`.
- Compatibility constraint:
  - `user_verifications.submitted_via` must use allowed DB values (`web` or `telegram`).
