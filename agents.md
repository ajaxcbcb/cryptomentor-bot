# Agents SOP

## Purpose
Standard operating guide for the core CryptoMentor operators: Admin, Engine, Risk & Pairing, Broadcast, and Deploy/Sync.

## Operating Principles
- Keep runtime behavior and user-facing messages aligned at all times.
- Treat `autotrade_sessions` as control-plane source of truth, but validate runtime post-start state before notifying users.
- Prioritize safety invariants over throughput (risk, sizing, SL/TP integrity, and state reconciliation correctness).
- No production-impact restart without changelog, deploy-ready files, and verification evidence.

## 1) Admin Agent
- Owner: release coordination and final approval.
- Must do:
- Approve production-impact changes before VPS restart.
- Require `CHANGELOG.md` update for every production patch.
- Confirm audience before any broadcast (`all`, `verified`, `non-verified`, `premium`, etc.).
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
- `Bismillah/app/pair_strategy_router.py`
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
- Restore/startup must preserve persisted trading mode; no shared-path coercion (for example forced swing->scalp).
- Startup/restart notifications must use post-start runtime mode source-of-truth, never stale pre-mutation session variables.
- Auto-switch transitions must use full lifecycle mode switch (`switch_mode`) so runtime engine class and DB mode change together; no active DB-only mode flips.
- Legacy global auto-switcher must be bypassed for `trading_mode == "mixed"`.
- Global adaptive/governor/playbook refresh cadence: every 10 minutes.
- Runtime risk overlay is memory/runtime only; never mutate persisted base user risk (`autotrade_sessions.risk_per_trade`).
- Effective risk formula is fixed: `effective_risk_pct = min(10.0, base_risk_pct + risk_overlay_pct)`.
- Overlay guardrails are strict: ramp only when rolling win rate >= 75% and rolling expectancy > 0.
- Overlay brake behavior must be gradual (step-down), never instant hard reset unless explicitly requested.
- Overlay affects position sizing only; do not relax confluence/signal-quality gates.
- Scalping open rows must persist `entry_reasons`.
- Winning close paths (`closed_tp`, `closed_tp3`, profitable `closed_flip`) must persist non-empty `win_reasoning` + `win_reason_tags`.
- StackMentor close updates must set `close_reason` consistently, not only `status`.
- StackMentor runner rollout must stay feature-flagged by default: `STACKMENTOR_RUNNER_ENABLED=false` unless explicitly approved.
- Runner behavior standard (when enabled): TP1 fixed at `3R` with partial close (`STACKMENTOR_TP1_CLOSE_PCT`, default `0.80`), move SL to breakeven, and final runner target at `STACKMENTOR_TP3_RR` (default `5.0`).
- Exchange TP must align with runtime mode: unified mode uses TP1 on exchange; runner mode uses TP3 on exchange while StackMentor monitor executes TP1 partial handling.
- Trade close persistence must use cumulative PnL for partial-flow exits (`profit_tp1/2/3 + final_leg_pnl`) so positive net outcomes are never misclassified as losses.
- User close-alert standard is mandatory: every realized trade close event must emit one detailed Telegram alert to the trade owner (`symbol`, `side`, `close_reason`, `entry`, `exit`, `pnl`).
- Swing close detection must be symbol-diff based from successful exchange snapshots; do not rely on all-or-none local flags for close notification.
- Reconcile pathways must return structured `healed_closes` payloads and runtime callers (swing/scalping/startup scheduler) must notify users from that payload with dedupe safety.
- Timeout protection policy is feature-flagged (`adaptive_timeout_protection_enabled` default false) and must emit structured timeout loss reasoning when timeout exits occur.
- Timeout protection env compatibility is mandatory:
- support both `SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED` and legacy `SCALPING_TIMEOUT_PROTECTION_ENABLED`.
- support both `SWING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED` and legacy `SWING_TIMEOUT_PROTECTION_ENABLED`.
- Dynamic universe standard for swing/scalp is Bitunix top-volume routing (`Top 10 by quoteVol`, highest-first).
- Volume selector fallback policy is fixed: last-good cache first, bootstrap list only if cache unavailable.
- Queue/scan priority must preserve volume rank before secondary quality sort (confidence/R:R).
- Blocked pending skip alerts must be deduped per symbol (10-minute TTL) while keeping full logs.
- Swing/scalp execution must share managed open contract (`trade_execution.open_managed_position`) for normal/flip/emergency entries.
- Swing flip lifecycle must persist old-trade close immediately after successful close (before reopen attempt), and coordinator paths must confirm close then confirm reopened ownership.
- Position size must always be computed from final validated SL (no SL mutation after sizing in either engine).
- Scalping sizing precision must always use the actual signal symbol (never hardcoded BTC precision path).
- Risk basis standard for both engines is `equity = available + frozen + unrealized`.
- Mixed-mode governance:
- Pair universe is top-10 by volume.
- Pair assignment cadence is 10 minutes sticky.
- Swing/scalp symbol sets must be disjoint and cover routed symbols.
- Parallel components must both be healthy for mixed runtime to be considered healthy.
- Max concurrent exposure policy is per-engine (`4 + 4`), no shared global cap unless explicitly approved.
- Open/reconcile/close data paths must be strategy-isolated via `trade_type` filtering.
- Required checks:
- Compile/syntax pass for touched files.
- Negative-path verification (timeouts, order failure, validation skip).
- R:R parity check: verify `abs(TP-entry)/abs(entry-SL)` from executed levels matches strategy expectation.
- Playbook safety fallback check: if playbook service fails, engines degrade to base-risk behavior with no crash.
- Win-reason coverage check for winners: target >=95% non-empty `win_reasoning`.
- Close-alert coverage check: all close reasons (`closed_tp`, `closed_sl`, `closed_tp1/2/3`, `closed_flip`, `max_hold_time_exceeded`, `sideways_max_hold_exceeded`, `stale_reconcile`) emit user Telegram close alerts with non-empty detail fields.
- Mode lifecycle matrix check: persisted `swing`/`scalping`/`mixed` sessions restart in same mode with matching startup message.
- Mixed health check: `is_running` true only when required mixed components are alive.

## 3) Risk & Pairing Agent
- Owner: risk defaults and symbol universe.
- Code scope:
- `Bismillah/app/trading_mode.py`
- `Bismillah/app/position_sizing.py`
- `Bismillah/app/volume_pair_selector.py`
- `Bismillah/app/pair_strategy_router.py`
- `Bismillah/app/win_playbook.py`
- Rules:
- Keep declared pair standard aligned with runtime behavior and all user-facing messages.
- Any pair-count change requires explicit changelog line.
- Dynamic universe standard: `Top 10 by volume` from Bitunix tickers (`quoteVol`).
- Mixed routing standard: top-10 input, 10-minute sticky reassignments, disjoint swing/scalp outputs.
- Equity wording standard: use `Equity` for account-value/risk basis; use `Available balance` only for free-margin context.
- Base-risk clamp policy remains `0.25%–5.0%`; only runtime overlay may extend effective sizing risk up to `10.0%` cap.
- Timeout-protection config keys must remain feature-flagged and backward-safe.
- Equity canonical basis for risk calculations/audits is `available + frozen + unrealized`.
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
- For `non-verified`, include users with missing verification rows unless told otherwise.

## 5) ML & Playbook Enhancement Agent (Expected Scope)
- Owner: model-assisted signal quality and playbook intelligence upgrades.
- Scope:
- `Bismillah/app/adaptive_confluence.py`
- `Bismillah/app/win_playbook.py`
- `Bismillah/app/playbook_analytics.py`
- `Bismillah/app/admin_daily_report.py`
- Rules:
- ML overlay must remain feature-flagged and fail-open; trading runtime must continue safely when ML path is degraded.
- ML/playbook outputs may reprioritize candidates and sizing overlays only; they must never bypass core risk, SL/TP, and confluence guardrails.
- Persist explainable decision metadata per trade (`model/version/score/decision_reason`) for replay and audits.
- Playbook enhancement changes must preserve backward compatibility for existing `win_reasoning`/`win_reason_tags` coverage.
- Any ML threshold or playbook weighting change requires explicit changelog entry and validation evidence.
- Required checks:
- Guardrail invariance check: disabling ML yields baseline behavior parity.
- Degradation check: service timeout/exception path falls back without engine crash.
- KPI check: report sample size, expectancy delta, and win-rate change with confidence bounds before enabling by default.

## 6) Registration Reset & Verification Recovery
- Owner: controlled UID-registration recovery for individual users.
- Purpose:
- Handle one-time Bitunix UID reset, force re-verification, and optionally complete re-approval.
- Required flow (default):
1. Preflight (must pass before write):
- Confirm target user exists in `users`.
- Read `user_verifications`, `autotrade_sessions`, `user_api_keys`.
- Abort if open trades exist.
2. Reset to pending re-verification:
- `user_verifications`: set `bitunix_uid` to new UID, `status=pending`, clear review fields.
- `autotrade_sessions`: set `bitunix_uid` to new UID, `status=pending_verification`, `engine_active=false`.
- Delete Bitunix API key rows for the user (`exchange in ('bitunix','')`) when reset policy requires relink.
3. Approval completion (when explicitly requested):
- `user_verifications.status=approved`, set `reviewed_at`, `reviewed_by_admin_id`.
- Mirror legacy status in `autotrade_sessions.status=uid_verified`.
4. Notifications + evidence:
- Notify target user and admins via Telegram.
- Persist run artifact log (`logs/*.json`) including before/after snapshots and send metrics.
- Compatibility rule:
- `user_verifications.submitted_via` is constrained; use only supported values (`web`, `telegram`).
- Do not write unsupported sources (for example `admin_reset`) unless DB constraint is expanded first.

## 7) Deploy/Sync Agent
- Owner: local <-> ajax <-> VPS alignment.
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
11. For timeout-flag patches, verify both env-key paths resolve correctly for runtime booleans.
12. For StackMentor runner patches, verify default flag OFF and `3R/5R` levels when enabled; verify cumulative PnL persistence after partial TP.
13. For mode lifecycle patches, verify restore/startup preserves persisted mode and startup message matches actual running engine.
14. For mixed runtime patches, verify both components restore/start and mixed-mode health reflects both components.
15. For Telegram callback patches, verify mode menu + mixed select + risk toggle + dashboard back path are functional.
16. For close-alert patches, verify per-trade close alert delivery for TP/SL/timeout/reconcile paths and dedupe behavior (trade-id based where available).

## Release Checklist
1. Code patch complete.
2. `CHANGELOG.md` updated.
3. Commit created and pushed to `ajax/main`.
4. VPS file sync complete.
5. `cryptomentor` restarted once.
6. Health and runtime validations passed.
7. Broadcast/reporting (if applicable) recorded.
8. For pairing/routing changes: verify selector health and top-10 ordering output.
9. For messaging changes: verify startup/restart notification uses live `Equity` and `Top 10 by volume`.
10. For schema-impact patches: DB migration applied and acknowledged before restart.
11. For win-playbook patches: admin report contains playbook section and win-reason coverage KPI.
12. For timeout policy patches: timeout-loss metrics appear in admin report and logs.
13. For timeout flag alias patches: runtime must read enabled state correctly from `.env` without code-side override.
14. For StackMentor runner patches: verify expected split (default `80/20`), breakeven transition after TP1, and final runner close reason (`closed_tp3`) with cumulative PnL.
15. For mode lifecycle patches: restore/startup matrix confirms persisted `swing`, `scalping`, and `mixed`.
16. For mixed routing patches: verify 10-minute sticky assignments and disjoint swing/scalp sets in runtime logs.
17. For Telegram callback patches: verify callback quality gate:
- `trading_mode_menu` opens correctly.
- `mode_select_mixed` activates mixed mode successfully.
- `at_switch_risk_mode` toggles persisted risk mode.
- `at_dashboard` returns to gatekeeper dashboard flow.
18. For registration reset operations: verify target post-state (`pending` or `approved` as intended), no blocked open-trade condition, and Telegram send metrics recorded.
19. For close-alert patches: verify one sample each for strategy close and reconcile close includes `symbol`, `side`, `close_reason`, `entry`, `exit`, and `pnl` in user Telegram output.

## Guardrails
- No destructive git actions without explicit instruction.
- No production restart without deploy-ready files.
- Do not claim `synced` without commit hash + hash parity evidence.
- Keep operational messages and actual runtime config in line.
- Do not auto-adjust SL/TP post-sizing unless position size is recomputed and revalidated.
- Do not bypass runtime guardrails to force risk ramp; if guardrails fail, overlay must brake down.
- Do not ship timeout-protection default-on without explicit approval.
- Do not write unsupported `submitted_via` values to `user_verifications`; keep compatibility with DB check constraints.
