---
name: cryptomentor-engine-guardrails
description: Apply CryptoMentor engine safety and execution guardrails for trading-runtime edits. Use when modifying or reviewing autotrade/scalping engines, pending-lock behavior, SL/TP and risk sizing parity, win playbook integration, timeout protection behavior, or winner reasoning persistence.
---

# CryptoMentor Engine Guardrails

Protect runtime behavior for engine-level changes.

## Code Scope

Prioritize these files:
- `Bismillah/app/autotrade_engine.py`
- `Bismillah/app/scalping_engine.py`
- `Bismillah/app/symbol_coordinator.py`
- `Bismillah/app/volume_pair_selector.py`
- `Bismillah/app/win_playbook.py`
- `Bismillah/app/trade_history.py`
- `Bismillah/app/stackmentor.py`

## Mandatory Runtime Rules

- Pair every `set_pending` path with clear/confirm paths.
- Auto-expire pending-without-position after `90s` and run startup/restart pending cleanup per user.
- Keep risk behavior aligned to profile and safety fallback.
- Never mutate SL/TP in a way that changes pre-sized risk unless size is recomputed and revalidated.
- Ensure executed TP/SL matches the strategy signal used for entry validation.
- Keep startup messages aligned to live runtime values.
- Refresh global win playbook every `10 minutes`.
- Keep runtime risk overlay memory/runtime only; never mutate persisted base risk.
- Keep formula fixed: `effective_risk_pct = min(10.0, base_risk_pct + risk_overlay_pct)`.
- Enforce strict overlay ramp guardrails: ramp only when rolling win rate `>= 75%` and rolling expectancy `> 0`.
- Use gradual overlay brake step-down; never hard reset unless explicitly requested.
- Let overlay affect sizing only; do not relax confluence or signal-quality gates.
- Persist `entry_reasons` for scalping open rows.
- Persist non-empty `win_reasoning` and `win_reason_tags` for winning close paths (`closed_tp`, `closed_tp3`, profitable `closed_flip`).
- Set `close_reason` consistently in StackMentor close updates.
- Keep timeout protection feature-flagged (`adaptive_timeout_protection_enabled` default `false`).
- Support timeout env compatibility aliases:
  - `SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED`
  - `SCALPING_TIMEOUT_PROTECTION_ENABLED` (legacy alias)
- Use Bitunix dynamic top-volume routing for swing + scalp (`top 10` by `quoteVol`, highest-first).
- Keep volume selector fallback order fixed: `last-good cache` then `bootstrap list` only if cache unavailable.
- Preserve volume rank before secondary quality sorting.
- Deduplicate blocked pending skip alerts per symbol with `10-minute TTL` while keeping full logs.

## Required Verification

Run these checks after changes:

1. Compile/syntax pass for touched files.
2. Negative-path verification for timeout exits, order failure, and validation skip.
3. R:R parity check from executed levels:
- `abs(TP-entry)/abs(entry-SL)` must match strategy expectation.
4. Playbook failure fallback check:
- Service failure must degrade to base-risk behavior without crash.
5. Win-reason coverage check for new winners:
- Target `>=95%` non-empty `win_reasoning`.

## Reporting Format

Always summarize:
- Files touched
- Guardrails validated
- Gaps or residual risk
- Exact commands/tests executed