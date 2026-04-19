---
name: cryptomentor-admin-release
description: Coordinate CryptoMentor production approvals and release readiness with strict changelog and audience checks. Use when preparing a production patch, deciding go/no-go for deploy, confirming broadcast audience scope, or producing release-note sections for CHANGELOG.md.
---

# CryptoMentor Admin Release

Coordinate final approval before any production-impact restart.

## Run This Workflow

1. Confirm the requested change scope and whether it affects production runtime.
2. Require a `CHANGELOG.md` update for every production patch before approving deploy.
3. Verify audience scope before any broadcast: `all users`, `verified`, `non-verified`, `premium`, or another explicit segment.
4. Produce two explicit outputs before handoff:
- Release-note section text for `CHANGELOG.md`
- Go/no-go decision with blocking reasons if no-go

## Hard Gates

- Refuse production restart approval if changelog is missing or incomplete.
- Refuse broadcast execution if target audience is ambiguous.
- Keep decisions traceable: always state what checks passed and what remains blocked.

## Output Template

Use this structure in responses:

```markdown
Release Note Draft:
- <bullet 1>
- <bullet 2>

Approval Decision:
- Status: GO | NO-GO
- Reason(s): <concise reasons>
- Required Follow-ups: <if any>
```