# Config Inventory (Redacted)

## Scope

- Bot runtime config from code and `Bismillah/.env.example`
- Web backend config from code and `website-backend/.env.example`
- Strategy/runtime constants in engine modules

Security note:
- This repo snapshot contains sensitive-looking literal examples in `website-backend/.env.example` (token/key-like values).
- Those values are treated as secrets and are not reproduced here.

---

## 1) Bot Environment Variables

Source files:
- `Bismillah/main.py`, `Bismillah/bot.py`, `Bismillah/app/*`
- `Bismillah/.env.example`

### Core runtime
- `TELEGRAM_BOT_TOKEN` (required for bot runtime)
- `TOKEN` (legacy token alias in template)
- `WEB_DASHBOARD_URL` (default `https://cryptomentor.id`)

### Admin / control
- `ADMIN_IDS`, `ADMIN1`, `ADMIN2`, `ADMIN3`, `ADMIN_USER_ID`, `ADMIN2_USER_ID`

### Data / persistence
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ANON_KEY` (present in template/utility paths)

### Exchange / market-data
- `BITUNIX_API_KEY` (fallback only if user key not supplied)
- `BITUNIX_API_SECRET` (fallback only)
- `BITUNIX_BASE_URL` (default `https://fapi.bitunix.com`)
- `BITUNIX_GATEWAY_URL` (optional proxy gateway)
- `BITUNIX_WS_URL` (optional explicit WS URL)
- `PROXY_URL` (comma-separated proxy list)
- `CRYPTOCOMPARE_API_KEY`

### Other optional providers/services
- `HELIUS_API_KEY`
- AI/provider keys and settings in template (not part of core trade execution path)

### Scheduler / ops
- `RESTART_ALERT_COOLDOWN_SECONDS` (health-check alert throttling)
- `USE_GDRIVE` (log sync strategy)

---

## 2) Website Backend Environment Variables

Source files:
- `website-backend/config.py`
- `website-backend/.env.example`
- route modules reading `os.getenv`

### Required runtime
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_BOT_USERNAME`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `JWT_SECRET`

### Optional / defaults
- `JWT_EXPIRE_HOURS` (default 24)
- `FRONTEND_URL` (default localhost in config)
- `DEBUG`
- `ENCRYPTION_KEY` (required for decrypting stored API secrets)

### Admin routing
- `ADMIN_IDS`, `ADMIN1`, `ADMIN2`, `ADMIN_USER_ID`, `ADMIN2_USER_ID`

---

## 3) Engine Strategy Constants (Code-Level)

## 3.1 Swing (`autotrade_engine.py`)

`ENGINE_CONFIG` includes:
- `symbols` universe
- `scan_interval`
- `min_confidence`
- `max_trades_per_day`
- `max_concurrent`
- `min_rr_ratio`
- `daily_loss_limit` (tracked, breaker behavior commented as disabled)
- ATR multipliers and filters:
  - `atr_sl_multiplier`, `atr_tp1_multiplier`, `atr_tp2_multiplier`
  - `min_atr_pct`, `max_atr_pct`
- RSI/volume/wick filters:
  - `rsi_long_max`, `rsi_short_min`, `volume_spike_min`, `wick_rejection_max`
- StackMentor toggle `use_stackmentor`

Risk bounds:
- `RISK_MIN_PCT = 0.25`
- `RISK_MAX_PCT = 5.0`

Reversal controls:
- `FLIP_COOLDOWN_SECONDS = 1800`
- `FLIP_COOLDOWN_SIDEWAYS_SECS = 900`
- confidence thresholds for flips.

## 3.2 Scalping (`trading_mode.py` + `scalping_engine.py`)

`ScalpingConfig` defaults include:
- timeframe/scan interval
- min confidence and min RR
- max hold time, concurrent positions
- daily loss limit
- cooldowns and anti-flip values
- ATR bounds and volume ratio thresholds

Additional runtime caps in scalping engine:
- risk capped at 5%
- leverage capped at 10x

## 3.3 StackMentor (`stackmentor.py`)

`STACKMENTOR_CONFIG` (effective current mode):
- `target_rr = 3.0`
- `tp1_pct = 1.00`, `tp2_pct = 0.00`, `tp3_pct = 0.00`
- compatibility fields for tp2/tp3 retained.

---

## 4) Database Tables/Fields Used as Config or Control

Confirmed key tables:
- `autotrade_sessions`
  - fields used include: `status`, `engine_active`, `initial_deposit`, `leverage`, `risk_per_trade`, `trading_mode`, `auto_mode_enabled`.
- `user_api_keys`
- `autotrade_trades`
- `signal_queue`
- `users`, `user_verifications`

---

## 5) Overrides and Precedence

Confirmed from code:
- Runtime risk read from DB (`risk_per_trade`) then clamped by path-level bounds.
- Trading mode read from DB determines swing vs scalping path.
- Web one-click execution uses web-side session settings and live account pulls (not bot in-memory settings).

Unclear from code:
- Full precedence between risk profile dynamic confidence and static swing min confidence is path-dependent and not centrally documented.

---

## 6) Redaction Policy Applied

- Secret values are not copied.
- Any key/token-like literals in `.env.example` are treated as redacted placeholders.
