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
- Must enforce:
- No stale pending locks (`set_pending` must be paired with clear/confirm paths).
- Stale pending lock policy: auto-expire pending-without-position after 90s; run restart/startup pending cleanup per user.
- Risk behavior consistent with user profile and safety fallback.
- SL/TP validation must never mutate SL/TP in a way that changes pre-sized risk.
- Executed TP/SL must match the strategy signal used for entry validation.
- Startup messages consistent with live runtime values.
- Runtime pair universe for swing + scalp must use Bitunix dynamic top-volume routing (top 10 by `quoteVol`, highest-first priority).
- Volume selector fallback policy is fixed: last-good cache first, bootstrap list only if cache unavailable.
- Queue/scan priority must preserve volume rank before secondary quality sort (confidence/R:R).
- Blocked pending skip alerts must be deduped per symbol (10-minute TTL) while keeping full logs.
- Required checks:
- Compile/syntax pass for touched files.
- Negative-path verification (timeouts, order failure, validation skip).
- R:R parity check: verify `abs(TP-entry)/abs(entry-SL)` from executed levels matches strategy expectation.

## 3) Risk & Pairing Agent
- Owner: risk defaults and symbol universe.
- Code scope:
- `Bismillah/app/trading_mode.py`
- `Bismillah/app/position_sizing.py`
- `Bismillah/app/volume_pair_selector.py`
- Rules:
- Keep declared pair standard aligned with runtime behavior and all user-facing messages.
- Any pair-count change requires explicit changelog line.
- Dynamic universe standard (v2.2.9+): `Top 10 by volume` from Bitunix tickers (`quoteVol`).
- Equity wording standard: use `Equity` for account-value/risk basis; use `Available balance` only for free margin context.
- Runtime verification command (VPS/local):
- `python3 - <<'PY'`
- `from app.volume_pair_selector import get_ranked_top_volume_pairs, get_selector_health`
- `pairs = get_ranked_top_volume_pairs(10)`
- `print(len(pairs), pairs)`
- `print(get_selector_health())`
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

## Guardrails
- No destructive git actions without explicit instruction.
- No production restart without deploy-ready files.
- Do not claim “synced” without commit hash + hash parity evidence.
- Keep operational messages and actual runtime config in line.
- Do not auto-adjust SL/TP post-sizing unless position size is recomputed and revalidated.
