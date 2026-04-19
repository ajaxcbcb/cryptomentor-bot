# Signal Engine Spec (Current Code Snapshot)

**As Of:** 2026-04-17

## Scope

- Swing/autotrade signal path: `Bismillah/app/autotrade_engine.py`.
- Scalping signal path: `Bismillah/app/scalping_engine.py` + `Bismillah/app/autosignal_async.py`.
- Web signal path: `website-backend/app/routes/signals.py`.
- Adaptive/risk overlay path: `Bismillah/app/adaptive_confluence.py` + `Bismillah/app/win_playbook.py`.

---

## A) Confirmed From Code

### A.1 Swing / Autotrade Signal Flow

- Candidate symbol universe is runtime dynamic via `get_ranked_top_volume_pairs(10)`.
- Signals are generated then filtered with confidence/cooldown/concurrency/ownership gates.
- Adaptive confluence overrides are applied via:
  - `conf_delta`
  - `volume_min_ratio_delta`
  - `ob_fvg_requirement_mode`
- Engine refresh cadence for adaptive/playbook snapshots is **10 minutes**.
- Execution path validates SL/TP against mark before opening position.
- R:R validation is enforced against strategy expectations before order placement.

### A.2 Scalping Signal Flow

- Mode-aware pipeline in `ScalpingEngine.generate_scalping_signal(...)`.
- Sideways-first path (`_try_sideways_signal`) with range/bounce/divergence context.
- Fallback path uses async scalping signal computation.
- Anti-flip + cooldown filters enforce churn control.
- Ownership gate blocks conflicting strategy entries on same `(user, symbol)`.
- Timeout exits include structured reasoning and optional timeout protection actions when feature-flag enabled.

### A.3 Risk Overlay / Effective Risk

From `win_playbook.py`:
- Base risk clamp: `0.25%-5.0%`
- Overlay max: `+5.0%`
- Effective cap: `10.0%`
- Effective risk formula: `effective_risk_pct = min(10.0, base_risk_pct + risk_overlay_pct)`
- Guardrail conditions require sample threshold + healthy win-rate/expectancy to ramp.
- Overlay actions are gradual (`ramp_up`/`brake_down`) with a minimum action interval.

### A.4 Timeout Flag Compatibility

From `trading_mode.py`:
- Primary key: `SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED`
- Legacy alias: `SCALPING_TIMEOUT_PROTECTION_ENABLED`
- Runtime default stays disabled when both keys are absent (`false`).

### A.5 Pending Lock / Coordination Safety

From `symbol_coordinator.py` and engine startup paths:
- Pending locks are explicitly set before order placement.
- Clear/confirm paths exist for fail/success/cancel flows.
- Stale pending-without-position auto-expire at `90s`.
- Startup sanitize + reconcile routines clear orphan pending states.

### A.6 StackMentor Runtime Exit Model

Current runtime strategy is unified single-target:
- `target_rr = 3.0`
- full close at TP (`qty_tp1=100%, qty_tp2=0, qty_tp3=0`)
- `tp1/tp2/tp3` fields retained for compatibility

---

## B) Notes for Readers (Snapshot Intent)

- This file is a code snapshot summary, not a product promise document.
- Legacy wording in some log/comment strings may reference older staged TP phrasing.
- Runtime behavior should be interpreted from managed execution + StackMentor config paths first.

---

## C) Web Signal Path (Current)

- `/dashboard/signals` produces signal cards from confluence/fallback builders.
- `/dashboard/signals/execute` recomputes a live execution-ready signal and applies sizing checks before placement.
- Execution metadata should preserve risk and close-reason traceability.

---

## D) Verification Gate Context (Operational)

- Signal/entry runtime is operationally coupled with verification/session status:
  - recovery reset phase uses pending states (`pending`, `pending_verification`) to block normal trading readiness.
  - approval phase restores ready state (`approved`, `uid_verified`) before normal entry lifecycle.
- Reset/recovery operations must keep DB-compatible `submitted_via` values (`web|telegram`) to avoid verification-write failures.
