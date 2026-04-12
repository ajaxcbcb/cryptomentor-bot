# State Machine and Decision Tree (Plain-English)

## Scope

- Swing path: `Bismillah/app/autotrade_engine.py`
- Scalping path: `Bismillah/app/scalping_engine.py`
- Unified execution and reconciliation: `Bismillah/app/trade_execution.py`
- Position monitor: `Bismillah/app/stackmentor.py`

---

## 1) Engine-Level Decision Flow

1. Engine start requested (`start_engine`).
2. Load user trading mode (`TradingModeManager.get_mode`).
3. Branch:
   - `SCALPING` -> start `ScalpingEngine.run()`.
   - else -> start swing `_trade_loop(...)`.
4. Repeated loop while running:
   - sync state from exchange + DB,
   - evaluate existing positions and close/flip paths,
   - evaluate fresh entries,
   - sleep scan interval.

No-trade paths:
- stop signal in DB/session,
- max concurrent reached,
- no valid symbols available,
- no candidate signal after filters,
- risk sizing returns qty 0,
- SL/TP relation invalid against mark,
- cooldown/anti-flip blocks.

Defensive paths:
- auth/IP failure branches and retry,
- reconciliation failure -> emergency close path in unified executor,
- scalping circuit breaker block,
- stale position reconciliation utilities in trade-history layer.

---

## 2) Swing Decision Tree (Sequential)

1. Check stop/cancel signals.
2. Pull positions.
3. If positions exist:
   - run StackMentor monitor,
   - check TP1 legacy branch if applicable,
   - evaluate reversal (`_is_reversal`) per position:
     - if reversal approved -> close old side and open new side.
4. If concurrent position limit reached -> wait.
5. Build available symbol list (not currently occupied).
6. Compute BTC bias (`_get_btc_bias`).
7. For each available symbol:
   - compute signal (`_compute_signal_pro`),
   - apply confidence threshold,
   - collect candidates.
8. If no candidates -> wait.
9. Sort candidates by confidence and RR.
10. Sync queue to DB and choose next non-processing symbol.
11. Compute qty (`calc_qty_with_risk`, fallback fixed-margin if needed).
12. Validate prices with current mark (`get_ticker`).
13. Place order with TP/SL.
14. On success:
   - cleanup queue status,
   - register StackMentor,
   - save trade history,
   - notify user,
   - start WS PnL tracker.
15. On failure:
   - classify error,
   - retry or skip or stop depending on error class.

---

## 3) Scalping Decision Tree (Sequential)

1. Loop every scan interval.
2. Check DB stop signal.
3. Monitor current positions:
   - StackMentor monitor,
   - close sideways positions > 2m,
   - close any position > max hold (30m).
4. Scan symbols concurrently (`_scan_single_symbol`).
5. Per symbol:
   - cooldown check,
   - signal generation:
     - try sideways pipeline first,
     - fallback to async trend pipeline,
   - validation (`validate_scalping_entry`),
   - anti-flip gates (`_passes_anti_flip_filters`).
6. For valid signals (processed sequentially):
   - enforce max concurrent,
   - compute risk-based qty,
   - reject if below min qty,
   - execute through `open_managed_position`.
7. On success:
   - register local position,
   - persist open trade,
   - notify user.
8. On failure:
   - non-retryable classes fail fast,
   - retryable classes use exponential backoff.

---

## 4) Position Lifecycle Branches

Entry -> Open -> Managed -> Closed.

Major close branches (confirmed from code):
- TP hit (exchange-triggered TP / StackMentor detection).
- SL hit.
- Flip close then opposite open.
- Sideways max-hold forced close (2m).
- General max-hold forced close (30m).
- Manual 1-click close path (web bitunix routes for source `1_click`).
- Reconciliation emergency close if invariants fail.

---

## 5) Stateful vs Stateless Components

Signal engine statefulness:
- Swing signal computation is mostly stateless per symbol/timeframe fetch, but runtime behavior is stateful due to queue/cooldown/position constraints.
- Scalping is explicitly stateful (`positions`, `cooldown_tracker`, `signal_streaks`, `last_closed_meta`).

Engine model:
- Hybrid polling + event-driven (poll loops plus WS PnL tracker).

---

## 6) Confirmed Override/Veto Relationships

- Risk can veto signals: yes.
- Position management can override raw signal intent: yes (flip checks, hold-time closures, cooldowns).
- Web execution path can bypass bot confluence path: yes (`/signals/execute` re-derives live ticker-based signal).

---

## 7) Unclear / Needs Manual Confirmation

- Intended authoritative signal source for web execution (confluence vs ticker momentum) is unclear from code.
- Intended persistence contract for `signal_queue.tp3` vs swing signal payload fields is unclear from code.
- Intended lifecycle/ownership of `engine_restore.py` vs `scheduler.start_scheduler` restore logic is unclear from code.
