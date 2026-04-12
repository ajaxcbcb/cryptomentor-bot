# Rebuild Prompt (Faithful Engine Reconstruction)

Use this prompt with another coding agent to rebuild the current engine behavior as documented.

---

You are rebuilding a trading system from an audited snapshot. Your job is fidelity, not optimization.

## Hard constraints

1. Reproduce current behavior exactly from exported docs.
2. Do not add strategy improvements, refactors, or new risk models unless explicitly marked unresolved.
3. Preserve hybrid architecture: polling loops plus WS PnL tracking.
4. Preserve DB schema contracts and side effects.
5. Preserve web + bot split and current coupling points.
6. Where docs mark ambiguity, implement the confirmed behavior and annotate ambiguity rather than guessing new logic.

## Authoritative source order

1. `docs/exported_engine_snapshot/trading_engine_overview.md`
2. `docs/exported_engine_snapshot/signal_engine_spec.md`
3. `docs/exported_engine_snapshot/risk_and_execution_spec.md`
4. `docs/exported_engine_snapshot/state_machine_and_decision_tree.md`
5. `docs/exported_engine_snapshot/decision_tree.mmd`
6. `docs/exported_engine_snapshot/state_machine.mmd`
7. `docs/exported_engine_snapshot/module_interfaces.md`
8. `docs/exported_engine_snapshot/config_inventory.md`
9. `docs/exported_engine_snapshot/exchange_integration.md`
10. `docs/exported_engine_snapshot/signal_rules.csv`
11. `docs/exported_engine_snapshot/dependency_map.json`
12. `docs/exported_engine_snapshot/known_gaps_and_uncertainties.md`

## Required rebuilt components

- Entrypoints and orchestration:
  - Bot runtime entry, scheduler start, engine start/stop/state.
- Swing engine:
  - BTC bias gating, confluence + fallback signal generation, queueing, risk sizing, order placement, reversal flow.
- Scalping engine:
  - sideways-first pipeline, trend fallback, anti-flip logic, max-hold closures.
- Unified execution:
  - mark-price validation, TP/SL attach on entry, post-entry reconciliation.
- Position management:
  - StackMentor current unified 1:3 target behavior.
- Web control plane:
  - engine control routes, signal routes, one-click execution, exchange views.
- Persistence layer:
  - Supabase-backed sessions, trades, queue, API keys.
- Exchange adapter:
  - Bitunix signing and endpoint mapping.

## Fidelity checks to run

1. Swing loop can open orders with attached TP/SL and queue status updates.
2. Scalping loop enforces anti-flip and hold-time closure branches.
3. Risk sizing uses equity-based formula where documented.
4. Web one-click execution recomputes live signal at execution time.
5. Mark-price relation checks veto invalid TP/SL side.
6. Position source segregation (`autotrade` vs `1_click`) functions in web route.

## Ambiguity handling

For every ambiguous point listed in `known_gaps_and_uncertainties.md`:
- Implement confirmed behavior.
- Add `TODO(manual-confirmation)` marker referencing the exact ambiguity item.
- Do not invent replacement behavior.

## Output format expected from rebuild agent

1. File/module tree.
2. Mapping table from exported module interfaces to rebuilt modules.
3. Explicit list of preserved behaviors and any unresolved ambiguities.
4. Test/verification report against fidelity checks above.
