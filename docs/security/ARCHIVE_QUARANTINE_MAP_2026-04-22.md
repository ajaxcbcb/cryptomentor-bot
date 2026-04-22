# Archive Quarantine Map (2026-04-22)

Sensitive archive artifacts were copied to local private quarantine storage before redaction:

- Private location: `.private_quarantine/2026-04-22/` (gitignored)
- Public repo copies: redacted placeholders only

## Quarantined Source Set
- `archive/tests/run_migration_supabase.py`
- `archive/tests/verify_scalping_deployment.py`
- `archive/tests/test_bitunix.py`
- `archive/tests/test_bitunix_debug.py`
- `archive/tests/test_proxy.py`
- `archive/tests/test_proxy_list.py`
- `archive/tests/test_worker_direct.py`
- `archive/deploy/deploy_license_to_vps.sh`
- `archive/deploy/deploy_license_to_vps_final.sh`
- `archive/docs/DEPLOY_TO_VPS_GUIDE.md`
- `archive/docs/LICENSE_DEPLOYMENT_SUCCESS.md`
- `archive/docs/QUICK_START_LICENSE.md`
- `archive/deploy/commands/VPS_COMMANDS_TEST_LICENSE.txt`
- `archive/deploy/docs/DEPLOY_LICENSE_TEST_TO_VPS.md`
- `archive/deploy/docs/README_DEPLOY_LICENSE.md`
- `archive/features/LICENSE_SYSTEM_TEST_RESULTS.md`

## Note
- This mapping is for internal operational traceability only.
- If external private storage is required, export from the local quarantine directory into your organization vault and then securely delete local private copies.

