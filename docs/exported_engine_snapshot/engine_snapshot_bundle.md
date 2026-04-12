# Engine Snapshot Bundle

This is the import-friendly index for the exported trading/signal engine snapshot.

## Contents

1. `repo_map.md`
2. `trading_engine_overview.md`
3. `signal_engine_spec.md`
4. `risk_and_execution_spec.md`
5. `state_machine_and_decision_tree.md`
6. `decision_tree.mmd`
7. `state_machine.mmd`
8. `module_interfaces.md`
9. `config_inventory.md`
10. `exchange_integration.md`
11. `signal_rules.csv`
12. `dependency_map.json`
13. `known_gaps_and_uncertainties.md`
14. `rebuild_prompt.md`

## Suggested import order into ChatGPT

1. `trading_engine_overview.md`
2. `signal_engine_spec.md`
3. `risk_and_execution_spec.md`
4. `state_machine_and_decision_tree.md`
5. `module_interfaces.md`
6. `config_inventory.md`
7. `exchange_integration.md`
8. `known_gaps_and_uncertainties.md`
9. `signal_rules.csv`
10. `dependency_map.json`
11. `rebuild_prompt.md`

## Classification convention used in docs

- **Confirmed from code**: directly observed in runtime files.
- **Likely inferred**: based on naming/comments, not strictly enforced.
- **Unclear from code**: ambiguous or unresolved in this snapshot.

## Security note

Secrets are intentionally not copied into exported docs. Any key/token-like literals in env templates are treated as redacted.
