---
name: cryptomentor-deploy-sync
description: Execute CryptoMentor local-to-ajax-to-VPS deployment sync with restart and parity verification. Use when shipping production code, syncing files to VPS, restarting cryptomentor service, proving hash parity, and validating runtime checks after deploy.
---

# CryptoMentor Deploy Sync

Deploy safely with evidence-backed sync validation.

## Mandatory Sequence

Run in this order without skipping:

1. Commit local changes.
2. Push to `ajax/main`.
3. Deploy the same files to VPS path `/root/cryptomentor-bot/...`.
4. Restart exactly once:
- `sudo systemctl restart cryptomentor`
5. Verify service health:
- `systemctl is-active cryptomentor`
- `systemctl show cryptomentor -p MainPID -p ActiveState -p SubState`
6. Verify hash parity for deployed files (local vs VPS).
7. Verify runtime checks (for example pair count).
8. For trading engine patches, verify a live/open notification sample has consistent Entry/TP/SL and R:R math.
9. For playbook/risk patches, verify runtime snapshot exposes expected overlay and guardrails.
10. For timeout-protection patches, verify feature flag default/active state and timeout KPI log/report path.
11. For timeout-flag patches, verify both env-key paths resolve correctly:
- `SCALPING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED`
- `SCALPING_TIMEOUT_PROTECTION_ENABLED`

## Guardrails

- Do not use destructive git actions without explicit instruction.
- Do not restart production without deploy-ready files.
- Do not claim synced without commit hash and hash parity evidence.
- Keep operational messages aligned with runtime config.

## Required Deploy Report

Always provide:
- Commit hash deployed
- Files synced
- Restart evidence
- Health command outputs
- Hash parity evidence
- Runtime validation evidence tied to patch type
- Final status: `DEPLOYED` or `BLOCKED`