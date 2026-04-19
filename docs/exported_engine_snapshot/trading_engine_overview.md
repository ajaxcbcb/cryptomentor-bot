# Trading Engine Overview (Code Snapshot)

**As Of:** 2026-04-17

## 1) Runtime Topology

- Telegram runtime entry: `Bismillah/main.py` -> `bot.TelegramBot.run_bot()` in `Bismillah/bot.py`.
- Engine orchestration: `Bismillah/app/scheduler.py` starts restore/health/startup checks.
- Engine start function: `start_engine(...)` in `Bismillah/app/autotrade_engine.py`.
- Mode split:
  - `TradingMode.SCALPING` -> `ScalpingEngine.run()` in `Bismillah/app/scalping_engine.py`.
  - otherwise -> swing loop `_trade_loop(...)` in `Bismillah/app/autotrade_engine.py`.

## 2) Control Flow: Market Data -> Signal -> Risk -> Execution -> Position Management

### Swing path (`autotrade_engine._trade_loop`)

1. Poll account/positions from exchange client.
2. Refresh adaptive/playbook state every 10 minutes.
3. Build symbol universe using `get_ranked_top_volume_pairs(10)` (highest `quoteVol` first).
4. Generate candidates and gate by confidence/cooldown/concurrency/coordinator ownership.
5. Compute risk size using effective runtime risk (base + overlay, capped).
6. Validate SL/TP against mark (no SL mutation that breaks pre-sized risk).
7. Execute managed entry and persist trade metadata (`effective_risk_pct`, `risk_overlay_pct`).
8. Monitor exits + reconcile/close handling.

### Scalping path (`ScalpingEngine.run`)

1. Initial startup reconcile + pending-lock sanitize.
2. Refresh adaptive/playbook state every 10 minutes.
3. Build active scan set via `get_ranked_top_volume_pairs(10)`.
4. Generate sideways-first then fallback trend scalping signal.
5. Apply anti-flip filters, cooldown, and symbol ownership checks.
6. Use managed execution (`trade_execution.open_managed_position`) and persist open row.
7. Monitor position lifecycle, timeout logic, and close updates with structured reasoning.

## 3) Pair Universe and Selector Behavior

- Standard runtime universe: dynamic **Top 10 Bitunix USDT symbols by `quoteVol`**.
- Selector fallback order:
  1. fresh ticker fetch
  2. cache fallback
  3. bootstrap fallback
- Cache TTL: 300 seconds.

## 4) Adaptive + Risk Overlay Model

Adaptive confluence snapshot fields consumed by engines:
- `conf_delta`
- `volume_min_ratio_delta`
- `ob_fvg_requirement_mode`

Win-playbook overlay behavior:
- Base risk clamp: `0.25%-5.0%`
- Overlay cap: `+5.0%`
- Effective risk cap: `10.0%`
- Effective risk formula: `effective_risk_pct = min(10.0, base_risk_pct + risk_overlay_pct)`
- Guardrails control ramp/brake; overlay is runtime-only (not persisted as new base risk)

## 5) Timeout Protection and Pending-Lock Safety

Timeout protection (scalping):
- Feature-flagged config key: `SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED`
- Legacy alias supported: `SCALPING_TIMEOUT_PROTECTION_ENABLED`
- Min update gap default: `45s`

Pending-lock safety (`symbol_coordinator.py`):
- `set_pending` is paired with clear/confirm paths
- stale pending-without-position self-heal at `90s`
- startup sanitize and reconcile paths clear orphans

## 6) StackMentor Runtime Exit Model

Current runtime mode is unified single-target:
- `target_rr = 3.0`
- full close at TP target (`qty_tp1=100%, qty_tp2=0, qty_tp3=0`)
- `tp1/tp2/tp3` fields remain for compatibility wiring

## 7) Web Control-Plane Coupling

- Engine start/stop/state: `website-backend/app/routes/engine.py`
- Dashboard settings/risk updates: `website-backend/app/routes/dashboard.py`
- Signal view + execute path: `website-backend/app/routes/signals.py`

## 8) Processing Model

- Runtime is hybrid polling + event-assisted:
  - polling loops in swing/scalp/scheduler
  - websocket PnL stream via `bitunix_ws_pnl.py`

---

## 9) Ops Addendum (2026-04-19)

- Hourly admin status/report pipeline:
  - `scripts/hourly_admin_engine_report.py`
  - emits trade/no-trade diagnostics to Telegram admins every hour.
- Verification recovery pipeline:
  - `scripts/reset_bitunix_registration.py`
  - supports one-time UID reset to pending and explicit approval completion.
- Current recovery lifecycle standard:
1. reset -> pending (`user_verifications`) + pending verification (`autotrade_sessions`),
2. approval -> approved (`user_verifications`) + uid_verified (`autotrade_sessions`),
3. Telegram confirmation and artifact logging.
