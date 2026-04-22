# Secrets and Credentials Policy

## Rules
- Never commit live credentials, tokens, passwords, or private keys.
- Use environment variables or secret manager values at runtime.
- `.env` and `.env.local` are local-only and must stay untracked.
- Runtime user snapshots (for example `Bismillah/data/users_local.json`) must stay untracked.

## VPS Script Standard
- All SSH scripts must read `VPS_HOST`, `VPS_USER`, `VPS_PORT`.
- Authentication must use either:
  - `VPS_SSH_KEY` (recommended), or
  - `VPS_PASSWORD` from environment.
- Hardcoded password literals are prohibited.

## Local Validation
- Run `python tools/security/enforce_repo_secrets.py`.
- Run `pre-commit run --all-files` (includes gitleaks hook).

## CI Enforcement
- GitHub Actions workflow `security-secrets-scan.yml` blocks merges when:
  - tracked-file policy fails, or
  - gitleaks detects leaked credentials.

