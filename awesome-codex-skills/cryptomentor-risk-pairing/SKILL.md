---
name: cryptomentor-risk-pairing
description: Enforce CryptoMentor risk defaults, pairing universe rules, and runtime selector checks. Use when changing trading_mode, position sizing, volume pair selection, win playbook risk overlay behavior, equity wording, or top-volume universe standards.
---

# CryptoMentor Risk Pairing

Keep risk and pair universe behavior consistent with policy and user-facing messaging.

## Code Scope

- `Bismillah/app/trading_mode.py`
- `Bismillah/app/position_sizing.py`
- `Bismillah/app/volume_pair_selector.py`
- `Bismillah/app/win_playbook.py`

## Non-Negotiable Rules

- Keep declared pair standard aligned with runtime behavior and all user-facing messages.
- Record any pair-count change explicitly in `CHANGELOG.md`.
- Maintain dynamic universe standard (`v2.2.9+`): top `10` pairs by Bitunix `quoteVol`.
- Use wording consistently:
- `Equity` for account-value/risk basis
- `Available balance` only for free margin context
- Keep base-risk clamp at `0.25%–5.0%`.
- Allow only runtime overlay to extend effective sizing risk, capped at `10.0%`.
- Keep timeout-protection config in `ScalpingConfig` feature-flagged and backward-safe.
- Preserve env-key backward compatibility:
- `SCALPING_TIMEOUT_PROTECTION_ENABLED` must still activate runtime behavior.

## Runtime Verification Commands

Run and report output for pair selector health:

```bash
python3 - <<'PY'
from app.volume_pair_selector import get_ranked_top_volume_pairs, get_selector_health
pairs = get_ranked_top_volume_pairs(10)
print(len(pairs), pairs)
print(get_selector_health())
PY
```

Run and report output for win playbook state:

```bash
python3 - <<'PY'
from app.win_playbook import refresh_global_win_playbook_state, get_win_playbook_snapshot
refresh_global_win_playbook_state()
print(get_win_playbook_snapshot())
PY
```

## Output Expectations

Always report:
- Whether top-10 ordering is intact
- Selector fallback status and health
- Overlay guardrail values and caps
- Any config compatibility risks