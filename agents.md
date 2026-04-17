# Agents SOP

## Purpose
Standard operating guide for the core CryptoMentor operators: Admin, Engine, Broadcast, and Deploy/Sync.

## 1) Admin Agent
- Owner: release coordination and final approval.
- Must do:
- Approve production-impact changes before VPS restart.
- Require `CHANGELOG.md` update for every production patch.
- Confirm audience before any broadcast (all users, verified, non-verified, premium, etc).
- Outputs:
- Release note section in changelog.
- Go/no-go decision for deploy.

## 2) Engine Agent
- Owner: trading runtime logic.
- Code scope:
- `Bismillah/app/autotrade_engine.py`
- `Bismillah/app/scalping_engine.py`
- `Bismillah/app/symbol_coordinator.py`
- `Bismillah/app/volume_pair_selector.py`
- `Bismillah/app/win_playbook.py`
- `Bismillah/app/trade_history.py`
- `Bismillah/app/stackmentor.py`
- Must enforce:
- No stale pending locks (`set_pending` must be paired with clear/confirm paths).
- Stale pending lock policy: auto-expire pending-without-position after 90s; run restart/startup pending cleanup per user.
- Risk behavior consistent with user profile and safety fallback.
- SL/TP validation must never mutate SL/TP in a way that changes pre-sized risk.
- Executed TP/SL must match the strategy signal used for entry validation.
- Startup messages consistent with live runtime values.
- Restore/startup must preserve persisted trading mode; no shared-path coercion (for example forced swing→scalp).
- Startup/restart notifications must use post-start runtime mode source-of-truth, never stale pre-mutation session variables.
- Auto-switch transitions must use full lifecycle mode switch (`switch_mode`) so runtime engine class and DB mode change together; no active DB-only mode flips.
- Global win playbook refresh cadence: every 10 minutes (aligned with adaptive overlay refresh).
- Runtime risk overlay is memory/runtime only; never mutate persisted base user risk (`autotrade_sessions.risk_per_trade`).
- Effective risk formula is fixed: `effective_risk_pct = min(10.0, base_risk_pct + risk_overlay_pct)`.
- Overlay guardrails are strict: ramp only when rolling win rate >= 75% and rolling expectancy > 0.
- Overlay brake behavior must be gradual (step-down), never instant hard reset unless explicitly requested.
- Overlay affects position sizing only; do not relax confluence/signal-quality gates.
- Scalping open rows must persist `entry_reasons`.
- Winning close paths (`closed_tp`, `closed_tp3`, profitable `closed_flip`) must persist non-empty `win_reasoning` + `win_reason_tags`.
- StackMentor close updates must set `close_reason` consistently, not only `status`.
- StackMentor runner rollout must stay feature-flagged by default: `STACKMENTOR_RUNNER_ENABLED=false` unless explicitly approved to enable.
- Runner behavior standard (when enabled): TP1 fixed at `3R` with partial close (`STACKMENTOR_TP1_CLOSE_PCT`, default `0.80`), move SL to breakeven, and final runner target at `STACKMENTOR_TP3_RR` (default `5.0`).
- Exchange TP must align with runtime mode: unified mode uses TP1 on exchange; runner mode uses TP3 on exchange while StackMentor monitor executes TP1 partial handling.
- Trade close persistence must use cumulative PnL for partial-flow exits (`profit_tp1/2/3 + final_leg_pnl`) so positive net outcomes are never misclassified as losses.
- Timeout protection policy is feature-flagged (`adaptive_timeout_protection_enabled` default false) and must emit structured timeout loss reasoning when timeout exits occur.
- Timeout protection env compatibility is mandatory: support both `SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED` and legacy `SCALPING_TIMEOUT_PROTECTION_ENABLED` (alias) in runtime parsing.
- Swing timeout protection must follow the same compatibility rule: support both `SWING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED` and legacy `SWING_TIMEOUT_PROTECTION_ENABLED` (alias), default OFF.
- Runtime pair universe for swing + scalp must use Bitunix dynamic top-volume routing (top 10 by `quoteVol`, highest-first priority).
- Volume selector fallback policy is fixed: last-good cache first, bootstrap list only if cache unavailable.
- Queue/scan priority must preserve volume rank before secondary quality sort (confidence/R:R).
- Blocked pending skip alerts must be deduped per symbol (10-minute TTL) while keeping full logs.
- Swing/scalp execution must share managed open contract (`trade_execution.open_managed_position`) for normal/flip/emergency entries.
- Swing flip lifecycle must persist old-trade close immediately after successful close (before reopen attempt), and pair coordinator paths must confirm close then confirm reopened ownership.
- Position size must always be computed from final validated SL (no SL mutation after sizing in either engine).
- Scalping sizing precision must always use the actual signal symbol (never hardcoded BTC precision path).
- Risk basis standard for both engines is `equity = available + frozen + unrealized` for sizing and risk-audit reporting.
- Adaptive parity from scalp to swing is required:
- confirmation streak gate
- emergency candidate fallback
- adaptive/governor/playbook refresh cadence every 10 minutes
- swing consumption of sideways governor must apply non-sideways controls only
- timeout-protection and dynamic max-hold exits remain feature-flagged OFF by default
- Win strategy parity must cover all swing entry types (normal/flip/emergency) with persisted playbook match metadata and overlay/effective risk fields.
- Winning close persistence parity target remains >=95% non-empty `win_reasoning` with non-empty `win_reason_tags`.
- Required checks:
- Compile/syntax pass for touched files.
- Negative-path verification (timeouts, order failure, validation skip).
- R:R parity check: verify `abs(TP-entry)/abs(entry-SL)` from executed levels matches strategy expectation.
- Playbook safety fallback check: if playbook service fails, engines degrade to base-risk behavior with no crash.
- Win-reason coverage check for new winners: target >=95% non-empty `win_reasoning`.
- Mode lifecycle matrix check: persisted `swing`/`scalping` sessions must restart in same mode with matching startup message.
- Auto-switch correctness check: trending/sideways transitions must switch runtime engine and DB mode in sync.

## 3) Risk & Pairing Agent
- Owner: risk defaults and symbol universe.
- Code scope:
- `Bismillah/app/trading_mode.py`
- `Bismillah/app/position_sizing.py`
- `Bismillah/app/volume_pair_selector.py`
- `Bismillah/app/win_playbook.py`
- Rules:
- Keep declared pair standard aligned with runtime behavior and all user-facing messages.
- Any pair-count change requires explicit changelog line.
- Dynamic universe standard (v2.2.9+): `Top 10 by volume` from Bitunix tickers (`quoteVol`).
- Equity wording standard: use `Equity` for account-value/risk basis; use `Available balance` only for free margin context.
- Base-risk clamp policy remains `0.25%–5.0%`; only runtime overlay may extend effective sizing risk up to `10.0%` cap.
- Timeout-protection config keys in `ScalpingConfig` must remain feature-flagged and backward-safe.
- Timeout flag backward-compatibility rule: legacy env key (`SCALPING_TIMEOUT_PROTECTION_ENABLED`) must still activate runtime flag behavior.
- Swing adaptive config surface must mirror scalp controls with `SWING_*` env keys and safe defaults.
- Swing timeout flag backward-compatibility rule: legacy env key (`SWING_TIMEOUT_PROTECTION_ENABLED`) must still activate runtime timeout flag behavior.
- Equity canonical basis for risk calculations/audits is `available + frozen + unrealized`; this must stay aligned across swing/scalp and user-facing outputs.
- Runtime verification command (VPS/local):
- `python3 - <<'PY'`
- `from app.volume_pair_selector import get_ranked_top_volume_pairs, get_selector_health`
- `pairs = get_ranked_top_volume_pairs(10)`
- `print(len(pairs), pairs)`
- `print(get_selector_health())`
- `PY`
- Win playbook verification command (VPS/local):
- `python3 - <<'PY'`
- `from app.win_playbook import refresh_global_win_playbook_state, get_win_playbook_snapshot`
- `refresh_global_win_playbook_state()`
- `print(get_win_playbook_snapshot())`
- `PY`

## 4) Broadcast Agent
- Owner: Telegram campaign execution.
- Scope:
- Target filtering from Supabase (`users`, `user_verifications`).
- Delivery with rate limit and send metrics.
- Required output metrics:
- `TOTAL_TARGET`, `SENT`, `FAILED`, `BLOCKED_OR_FORBIDDEN`.
- Audience policy:
- Never assume status mappings; normalize first (`approved/uid_verified/active/verified`).
- For “non-verified”, include users with missing verification rows unless told otherwise.

## 5) Deploy/Sync Agent
- Owner: local ↔ ajax ↔ VPS alignment.
- Required sequence (no skipping):
1. Commit local changes.
2. Push to `ajax/main`.
3. Deploy same files to VPS (`/root/cryptomentor-bot/...`).
4. Restart once: `sudo systemctl restart cryptomentor`.
5. Verify service health:
- `systemctl is-active cryptomentor`
- `systemctl show cryptomentor -p MainPID -p ActiveState -p SubState`
6. Verify hash parity for deployed files (local vs VPS).
7. Verify runtime checks (for example pair count).
8. For trading engine patches, verify one live/open notification sample has consistent Entry/TP/SL and R:R math.
9. For playbook/risk patches, verify runtime snapshot exposes expected guardrails/overlay values.
10. For timeout-protection patches, verify feature flag default/active state and timeout KPI log/report path.
11. For timeout-flag patches, verify both env-key paths (`SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED` and `SCALPING_TIMEOUT_PROTECTION_ENABLED`) resolve to expected runtime boolean.
12. For StackMentor runner patches, verify default flag is OFF, TP1/TP3 levels resolve to `3R/5R` when enabled, and cumulative PnL persistence remains correct after partial TP.
13. For swing timeout-flag patches, verify both env-key paths (`SWING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED` and `SWING_TIMEOUT_PROTECTION_ENABLED`) resolve to expected runtime boolean.
14. For mode lifecycle patches, verify restore/startup preserves persisted mode and startup message matches actual running engine.
15. For adaptive-parity patches, verify swing startup/admin report includes adaptive + win-playbook snapshot visibility.

## Release Checklist
1. Code patch complete.
2. `CHANGELOG.md` updated.
3. Commit created and pushed to `ajax/main`.
4. VPS file sync complete.
5. `cryptomentor` restarted once.
6. Health and runtime validations passed.
7. Broadcast/reporting (if applicable) recorded.
8. For pairing/routing changes: verify live selector health and top-10 ordering output.
9. For messaging changes: verify startup/restart notification uses live `Equity` and `Top 10 by volume`.
10. For schema-impact patches: DB migration applied and acknowledged before restart.
11. For win-playbook patches: admin report contains playbook section and win-reason coverage KPI.
12. For timeout policy patches: timeout-loss metrics appear in admin report and logs.
13. For timeout flag alias patches: runtime must read enabled state correctly from `.env` without code-side override.
14. For StackMentor runner patches: verify canary open message and close logs show expected split (`80/20` default), breakeven transition after TP1, and final runner close reason (`closed_tp3`) with cumulative PnL.
15. For mode lifecycle patches: restore/startup matrix confirms persisted `swing` and `scalping` restart into same mode with matching notification.
16. For adaptive parity patches: swing must expose adaptive + win playbook summary and keep high-impact timeout/max-hold controls OFF unless explicitly enabled.

## Guardrails
- No destructive git actions without explicit instruction.
- No production restart without deploy-ready files.
- Do not claim “synced” without commit hash + hash parity evidence.
- Keep operational messages and actual runtime config in line.
- Do not auto-adjust SL/TP post-sizing unless position size is recomputed and revalidated.
- Do not bypass runtime guardrails to force risk ramp; if guardrails fail, overlay must brake down.
- Do not ship timeout-protection default-on without explicit approval.
