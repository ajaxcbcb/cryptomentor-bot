# Known Gaps and Uncertainties

## Scope

Ambiguities, possible dead code, hidden assumptions, and validation gaps found while tracing the current runtime.

---

## 1) Ambiguous Logic

1. Confluence vs static confidence precedence (swing)
- Files/functions:
  - `Bismillah/app/autotrade_engine.py`
  - `_generate_confluence_signal`, `_compute_signal_pro`, `_trade_loop`
- Why ambiguous:
  - Dynamic risk profile sets `min_confidence` for confluence path, but scanning also applies static `ENGINE_CONFIG["min_confidence"]` (with sideways scan bump).
- Status: unclear from code what the intended authoritative threshold model is.

2. Web signal source at execution time
- Files/functions:
  - `website-backend/app/routes/signals.py`
  - `generate_confluence_signals`, `_build_signal`, `execute_signal`
- Why ambiguous:
  - `/dashboard/signals` can show confluence output, but `/signals/execute` re-derives live signal via ticker momentum builder.
- Status: unclear from code whether this divergence is intentional policy.

3. Engine restore ownership
- Files/functions:
  - `Bismillah/app/scheduler.py` vs `Bismillah/app/engine_restore.py`
- Why ambiguous:
  - Both contain restore-related behavior; scheduler appears primary in current runtime start path.
- Status: unclear from code whether `engine_restore.py` is legacy or secondary/manual.

---

## 2) Suspected Defects / Conflicting Rules

1. Missing import target in confluence S/R block
- File/function:
  - `Bismillah/app/autotrade_engine.py` -> `_generate_confluence_signal`
- Detail:
  - Tries `from app.analysis.range_analyzer import RangeAnalyzer`.
  - `app/analysis/range_analyzer.py` not present in inspected tree.
- Impact:
  - S/R portion likely falls back via exception branch in this path.

2. Queue sync writes non-existent `tp3` field from swing signal object
- File/function:
  - `Bismillah/app/autotrade_engine.py` queue insert section
- Detail:
  - Inserts `cand['tp3']`, while `_compute_signal_pro` returns `tp1` and `tp2` (no guaranteed `tp3`).
- Impact:
  - Potential queue sync exception and reduced web visibility for signals.

3. Trading mode manager imports undefined helper
- File/function:
  - `Bismillah/app/trading_mode_manager.py` -> `switch_mode`
- Detail:
  - Imports `get_engine` from `app.autotrade_engine`; no `get_engine` found in inspected `autotrade_engine.py`.
- Impact:
  - Mode-switch flow may fail on that branch.

4. Bitunix web service trade-history symbol parameter mismatch
- File/function:
  - `website-backend/app/services/bitunix.py` -> `fetch_trade_history`
- Detail:
  - Passes symbol argument to `client.get_trade_history` whose signature appears `(user_id, limit=10)`.
- Impact:
  - Symbol filtering likely ineffective.

---

## 3) Dead Code Candidates

1. StackMentor TP2/TP3 handlers under unified full-close config
- File:
  - `Bismillah/app/stackmentor.py`
- Detail:
  - Config sets 100% close at TP1; TP2/TP3 qty defaults zero, but handlers remain.
- Candidate status:
  - Compatibility/legacy branches likely not used in normal unified mode.

2. Scalping helper not on primary live path
- File/function:
  - `Bismillah/app/scalping_engine.py` -> `calculate_scalping_tp_sl`
- Detail:
  - Contains slippage/spread buffering math; live order path primarily uses signal-derived levels + unified executor.
- Candidate status:
  - Possibly legacy or auxiliary.

---

## 4) Unused/Weakly-Used Config Signals

- `ENGINE_CONFIG.max_trades_per_day` set high and not effectively limiting behavior under current flow.
- Daily-loss breaker semantics in swing are tracked but commented/handled as monitoring-only.

---

## 5) Hidden Coupling

1. Bot and web backend are tightly coupled
- Web route `engine.py` dynamically imports bot modules and writes into shared DB control fields.

2. Shared mutable state split between memory and DB
- In-memory maps control queue/flip/positions behavior.
- DB tables simultaneously act as UI/source-of-truth and control flags.

3. Exchange state reconciliation is distributed
- Swing/scalping/stackmentor/trade_history each contain partial reconciliation logic.

---

## 6) Missing Tests / Verification Gaps

Observed from repository runtime path (no robust test harness discovered for these exact flows):
- End-to-end parity tests for bot signal vs web execute signal are missing.
- Regression tests for queue sync payload schema (including tp fields) are missing.
- Tests covering mode switch and restore edge cases are missing.
- Tests for reconciliation emergency-close branch are missing.

---

## 7) Explicitly Unclear from Code

- Whether flash-crash/dislocation/liquidity specific protections are intentionally absent or implemented elsewhere outside core runtime.
- Whether web 1-click and autotrade are expected to coexist on same symbols without arbitration policy.
- Whether current `main` deployment branch strategy is intended to mirror `ajax/master` exactly in production.

---

## 8) Manual Confirmation Checklist

1. Confirm canonical signal source for web execution.
2. Confirm intended confluence import path for S/R analyzer in swing confluence.
3. Confirm whether `tp3` is required in `signal_queue` inserts for swing signals.
4. Confirm intended state machine for mode switching (`get_engine` expectation).
5. Confirm final StackMentor policy (single target vs multi-tier legacy semantics).
