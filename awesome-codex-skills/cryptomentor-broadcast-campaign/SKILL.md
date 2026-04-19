---
name: cryptomentor-broadcast-campaign
description: Execute CryptoMentor Telegram broadcast campaigns with strict audience normalization and delivery metrics. Use when segmenting users from Supabase, sending campaign messages, and reporting send outcomes for verified, non-verified, premium, or custom audiences.
---

# CryptoMentor Broadcast Campaign

Run targeted broadcasts safely and report delivery quality clearly.

## Workflow

1. Define target audience explicitly before any send.
2. Query/prepare target users from Supabase tables:
- `users`
- `user_verifications`
3. Normalize verification statuses before filtering.
4. Apply delivery with rate limiting.
5. Produce final metrics summary.

## Audience Policy

- Never assume status mappings; normalize first.
- Treat verification labels as potentially variant values (`approved`, `uid_verified`, `active`, `verified`).
- For `non-verified` campaigns, include users with missing verification rows unless instructed otherwise.

## Required Metrics

Always output all four keys:
- `TOTAL_TARGET`
- `SENT`
- `FAILED`
- `BLOCKED_OR_FORBIDDEN`

## Safety Rules

- Stop and clarify if audience scope is ambiguous.
- Keep raw delivery failures visible; do not silently drop failed sends.
- Keep counts internally consistent (`SENT + FAILED + BLOCKED_OR_FORBIDDEN` should explain `TOTAL_TARGET`, or document exclusions).

## Output Template

```markdown
Campaign Summary:
- Audience: <segment>
- TOTAL_TARGET: <n>
- SENT: <n>
- FAILED: <n>
- BLOCKED_OR_FORBIDDEN: <n>
- Notes: <normalization choices, exclusions, anomalies>
```