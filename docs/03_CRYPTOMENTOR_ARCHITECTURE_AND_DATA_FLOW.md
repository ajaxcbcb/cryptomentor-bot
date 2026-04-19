# CryptoMentor - Full System Structure, Design Structure, and Data Flow

**Document Type:** System Architecture + Design Structure + Data Flow  
**Scope:** End-to-end CryptoMentor stack in this repository  
**Last Updated:** 2026-04-17

---

## 1. System At A Glance

CryptoMentor is a multi-surface trading platform with:
- Telegram-first runtime (`Bismillah`)
- Web onboarding + dashboard (`website-frontend` + `website-backend`)
- SMC engine service (`smc_trading_engine`)
- Shared Supabase persistence for sessions/trades/users
- Exchange adapters (Bitunix primary, multi-exchange capable)

---

## 2. Repository Structure (Top-Level)

```text
cryptomentorAI/
|- Bismillah/                 # Telegram bot + autotrade orchestration
|- website-frontend/          # React frontend
|- website-backend/           # FastAPI backend
|- smc_trading_engine/        # Standalone SMC engine service/API
|- db/                        # SQL migrations/DDL scripts
|- docs/                      # Internal technical docs
|- tests/                     # Test suites
|- tools/                     # Operational scripts
|- deploy*.py|.sh             # Deployment helpers
`- CHANGELOG.md               # Release history
```

---

## 3. Design Structure (Service/Layer Design)

### 3.1 Telegram Bot Design (`Bismillah`)

Core layers:
- **Interaction Layer:** handlers and menus (`handlers_*`, `menu_system.py`)
- **Trading Orchestration Layer:** swing/scalp loops (`autotrade_engine.py`, `scalping_engine.py`)
- **Execution Layer:** unified managed entry (`trade_execution.py`)
- **Risk/Adaptive Layer:** `position_sizing.py`, `adaptive_confluence.py`, `win_playbook.py`
- **Coordination Layer:** `symbol_coordinator.py` (ownership + pending-lock safety)
- **Data Layer:** `supabase_repo.py`, `trade_history.py`
- **Infra Layer:** `scheduler.py`, `engine_restore.py`, `maintenance_notifier.py`

Key runtime standards:
- Pair universe is dynamic Top 10 by Bitunix `quoteVol`
- Adaptive + playbook overlay refresh cadence is 10 minutes
- Runtime risk overlay only affects sizing at runtime (not persisted base risk)

### 3.2 SMC Engine Service Design (`smc_trading_engine`)

Internal package design:
- `app/api/` for routes (health/status/pairs/trades/admin)
- `app/core/` for market-structure decision logic
- `app/data/` for candle normalization/indicators
- `app/exchange/` for adapter abstractions
- `app/services/` for scan scheduler + trade/state services
- `app/storage/` for DB access

### 3.3 Web Platform Design

Frontend (`website-frontend/src`):
- App shell, onboarding/dashboard/admin slices, settings flows

Backend (`website-backend/app`):
- `routes/` for auth/user/dashboard/engine/signals/bitunix
- `services/` for exchange and queue helpers
- `db/supabase.py` for persistence access

### 3.4 Shared Data Design

Primary operational tables:
- `users`
- `user_api_keys`
- `autotrade_sessions`
- `autotrade_trades`
- `user_verifications`

Design principle:
- Session is source-of-truth for eligibility/engine state
- Trades table is source-of-truth for execution history
- Verification table is source-of-truth for referral/UID verification context

---

## 4. High-Level Architecture Flow

```text
[Telegram User] ----\
                     \                     +--------------------+
[Web User] -----------> [Bismillah Bot] -->| Exchange Adapters  |
                      \                    | (Bitunix + others) |
                       \                   +--------------------+
                        \
                         -> [website-backend] <-> [website-frontend]
                                  |
                                  v
                           [Supabase/Postgres]
                                  ^
                                  |
                         [smc_trading_engine]
```

---

## 5. End-to-End Data Flow Structure

### 5.1 Onboarding and Verification Flow

1. User starts from Telegram or web onboarding.
2. User submits exchange UID + API keys.
3. Services update verification/session/key records.
4. Engine activation toggles `autotrade_sessions.engine_active=true`.
5. User receives status confirmation.

### 5.2 Signal Scan and Candidate Flow

1. Scheduler/engine loops trigger scans by mode interval.
2. Runtime fetches top-volume symbols via `get_ranked_top_volume_pairs(10)`.
3. Signal logic computes confluence, direction, entry/SL/TP candidates.
4. Gating applies (confidence, cooldown, ownership, risk, concurrency).
5. Candidate goes to execution path.

### 5.3 Trade Execution Flow

1. Eligibility checks: session status, engine flag, API keys.
2. Position sizing uses **Equity** as risk basis (not available-balance-only logic).
3. Managed execution validates SL/TP vs mark and places entry + protection.
4. Trade row persisted in `autotrade_trades`.
5. Telegram/web notifications emitted.

### 5.4 Exit Management Flow (StackMentor Runtime)

1. Position is monitored by engine + StackMentor monitor paths.
2. Current runtime strategy is unified single-target (`target_rr=3.0`).
3. Full-close on target/SL/timeout/flip/manual reconcile paths.
4. Final close reason + PnL metadata persisted.

### 5.5 Settings Flow (Web -> Runtime)

1. User updates settings from dashboard.
2. Backend writes session settings to shared DB.
3. Engines consume latest session config on next loop/read.
4. Updated state appears in Telegram + dashboard.

---

## 6. Operational State Machine

Typical `autotrade_sessions.status` progression:

```text
none/no_session
  -> pending_verification
  -> uid_verified
  -> active
  -> stopped
```

Supporting flag:
- `engine_active` controls runtime loop participation.

---

## 7. Reliability Controls (Current)

- Dynamic pair selector fallback: fresh -> cache -> bootstrap
- Startup stale-trade reconcile in scheduler
- Per-user/per-symbol ownership with pending lock lifecycle tracking
- Pending lock stale self-heal (`90s`) when no open position exists
- Startup sanitize/stop cleanup clear orphan pending states
- Adaptive confluence controller with bounded deltas and sample gating
- Runtime risk overlay guardrails (ramp/brake), capped effective risk (`<=10.0%`)
- Timeout protection in scalping is feature-flagged and alias-compatible

---

## 8. Deployment and Runtime Topology (Current Pattern)

- Bot process: Python service under systemd supervision
- Web backend: FastAPI service
- Frontend: bundled static app
- SMC engine: independent Python service with scheduler + APIs
- Shared DB: Supabase/Postgres

---

## 9. Terminology and Messaging Standard

- Use **Equity** for account-value/risk basis.
- Use **Available balance** only for free margin context.
- Avoid fixed pair-count claims; runtime standard is dynamic top-volume routing.

---

## 10. Quick Trace Map

- Telegram UX: `Bismillah/app/handlers_*.py`
- Swing engine loop: `Bismillah/app/autotrade_engine.py`
- Scalping engine loop: `Bismillah/app/scalping_engine.py`
- Managed entry flow: `Bismillah/app/trade_execution.py`
- Risk/adaptive overlay: `Bismillah/app/adaptive_confluence.py`, `Bismillah/app/win_playbook.py`
- Pair routing: `Bismillah/app/volume_pair_selector.py`
- Symbol ownership/pending safety: `Bismillah/app/symbol_coordinator.py`
- Web control routes: `website-backend/app/routes/`

---

## 11. Operational Flow Addendum (2026-04-19)

### 11.1 Hourly Admin Runtime Summary
- Script: `scripts/hourly_admin_engine_report.py`
- Provides hourly status/trade/no-trade context to Telegram admins:
  - service/session mode snapshot,
  - opened/closed/open-now trade counts,
  - no-trade reason signals from logs/governor state.

### 11.2 Verification Recovery (Reset + Approval)
- Script: `scripts/reset_bitunix_registration.py`
- Recovery path:
1. Reset target to pending verification with new UID.
2. Preserve session risk/mode fields while forcing `engine_active=false`.
3. Re-approve when requested and mirror legacy status (`uid_verified`).
4. Send user/admin notifications and keep `logs/*.json` artifact evidence.

Compatibility:
- `user_verifications.submitted_via` must stay within supported DB values (`web`, `telegram`).
