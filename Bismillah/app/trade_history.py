"""
Trade History — Simpan dan kelola history trade autotrade ke Supabase.
Setiap order masuk/keluar dicatat lengkap dengan reasoning.
"""
import logging
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Optional, Dict, List
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def _db():
    from app.supabase_repo import _client
    return _client()


def _partial_realized_pnl(trade_row: Dict[str, Any]) -> float:
    total = 0.0
    for key in ("profit_tp1", "profit_tp2", "profit_tp3"):
        try:
            total += float(trade_row.get(key) or 0.0)
        except Exception:
            continue
    return float(total)


def _should_enforce_win_reasoning(close_reason: str, cumulative_pnl: float) -> bool:
    if float(cumulative_pnl) > 0:
        return True
    reason = str(close_reason or "").strip().lower()
    if reason in {"closed_tp", "closed_tp3"}:
        return True
    if reason == "closed_flip" and float(cumulative_pnl) > 0:
        return True
    return False


def _normalized_win_tags(raw_tags: Any, close_reason: str) -> List[str]:
    tags: List[str] = []
    if isinstance(raw_tags, list):
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]
    elif raw_tags is not None and str(raw_tags).strip():
        tags = [str(raw_tags).strip()]
    if tags:
        return tags
    reason = str(close_reason or "").strip().lower() or "closed_unknown"
    return ["win_close", reason]


def _derive_executed_rr(entry_price: float, sl_price: float, tp_price: float, fallback_rr: float) -> float:
    """
    Derive R:R from the final executed levels.
    Falls back to signal-provided rr_ratio when inputs are invalid.
    """
    try:
        entry = float(entry_price)
        sl = float(sl_price)
        tp = float(tp_price)
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk > 0 and reward > 0:
            return round(reward / risk, 2)
    except Exception:
        pass
    return float(fallback_rr)


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _classify_trade_mode(trade: Dict[str, Any]) -> str:
    trade_type = str(trade.get("trade_type") or "").strip().lower()
    timeframe = str(trade.get("timeframe") or "").strip().lower()
    strategy = str(trade.get("strategy") or "").strip().lower()
    if trade_type == "scalping" or timeframe == "5m":
        return "scalping"
    if strategy in {"stackmentor", "legacy", "swing"}:
        return "swing"
    if trade.get("tp1_price") is not None and trade_type != "scalping":
        return "swing"
    return "unknown"


def _normalize_trade_type_filter(trade_type: Optional[str]) -> str:
    mode = str(trade_type or "").strip().lower()
    if mode in {"scalp", "scalping"}:
        return "scalping"
    if mode == "swing":
        return "swing"
    return ""


def _matches_trade_type_filter(trade: Dict[str, Any], trade_type: Optional[str]) -> bool:
    wanted = _normalize_trade_type_filter(trade_type)
    if not wanted:
        return True
    return _classify_trade_mode(trade) == wanted


def _configured_rr(trade: Dict[str, Any]) -> Optional[float]:
    rr = _to_float(trade.get("rr_ratio"), None)
    if rr is not None and rr > 0:
        return float(rr)
    entry = _to_float(trade.get("entry_price"), None)
    sl = _to_float(trade.get("sl_price"), None)
    tp = _to_float(trade.get("tp1_price"), None)
    if tp is None:
        tp = _to_float(trade.get("tp_price"), None)
    if entry is None or sl is None or tp is None:
        return None
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    if risk <= 0 or reward <= 0:
        return None
    return float(reward / risk)


def _resolve_qty_for_r_multiple(trade: Dict[str, Any]) -> Optional[float]:
    for key in ("qty", "quantity", "original_quantity"):
        q = _to_float(trade.get(key), None)
        if q is not None and abs(q) > 0:
            return float(abs(q))
    return None


def _realized_r_multiple(trade: Dict[str, Any]) -> Optional[float]:
    status = str(trade.get("status") or "").strip().lower()
    if status == "open":
        return None
    pnl = _to_float(trade.get("pnl_usdt"), None)
    entry = _to_float(trade.get("entry_price"), None)
    sl = _to_float(trade.get("sl_price"), None)
    qty = _resolve_qty_for_r_multiple(trade)
    if pnl is None or entry is None or sl is None or qty is None:
        return None
    risk_usdt = abs(entry - sl) * qty
    if risk_usdt <= 0:
        return None
    return float(pnl / risk_usdt)


# ─────────────────────────────────────────────
#  WRITE: Simpan trade baru saat order masuk
# ─────────────────────────────────────────────

def save_trade_open(
    telegram_id: int,
    symbol: str,
    side: str,           # LONG / SHORT
    entry_price: float,
    qty: float,
    leverage: int,
    tp_price: float,
    sl_price: float,
    signal: Dict,        # output dari _compute_signal_pro
    order_id: str = "",
    is_flip: bool = False,
    # StackMentor fields
    tp1_price: Optional[float] = None,
    tp2_price: Optional[float] = None,
    tp3_price: Optional[float] = None,
    qty_tp1: Optional[float] = None,
    qty_tp2: Optional[float] = None,
    qty_tp3: Optional[float] = None,
    strategy: str = "stackmentor",
    execution_meta: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """Simpan trade baru ke Supabase. Return trade_id."""
    try:
        fallback_rr = float(signal.get("rr_ratio", 0))
        executed_tp_for_rr = float(tp1_price if tp1_price is not None else tp_price)
        rr_ratio = _derive_executed_rr(
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=executed_tp_for_rr,
            fallback_rr=fallback_rr,
        )

        row = {
            "telegram_id":      int(telegram_id),
            "symbol":           symbol,
            "side":             side,
            "entry_price":      float(entry_price),
            "qty":              float(qty),
            "leverage":         int(leverage),
            "tp_price":         float(tp_price),
            "sl_price":         float(sl_price),
            "status":           "open",
            "confidence":       int(signal.get("confidence", 0)),
            "rr_ratio":         rr_ratio,
            "trend_1h":         signal.get("trend_1h", ""),
            "market_structure": signal.get("market_structure", ""),
            "rsi_15":           float(signal.get("rsi_15", 0)),
            "atr_pct":          float(signal.get("atr_pct", 0)),
            "entry_reasons":    signal.get("reasons", []),
            "is_flip":          is_flip,
            "order_id":         order_id,
            "opened_at":        datetime.utcnow().isoformat(),
            "playbook_match_score": 0.0,
            "effective_risk_pct": 0.0,
            "risk_overlay_pct": 0.0,
            "trade_type": "swing",
            "timeframe": "15m",
            # StackMentor fields
            "strategy":         strategy,
        }
        
        # Add StackMentor fields if provided
        if tp1_price is not None:
            row["tp1_price"] = float(tp1_price)
        if tp2_price is not None:
            row["tp2_price"] = float(tp2_price)
        if tp3_price is not None:
            row["tp3_price"] = float(tp3_price)
        if qty_tp1 is not None:
            row["qty_tp1"] = float(qty_tp1)
        if qty_tp2 is not None:
            row["qty_tp2"] = float(qty_tp2)
        if qty_tp3 is not None:
            row["qty_tp3"] = float(qty_tp3)
        if execution_meta:
            if execution_meta.get("playbook_match_score") is not None:
                row["playbook_match_score"] = float(execution_meta.get("playbook_match_score"))
            if execution_meta.get("effective_risk_pct") is not None:
                row["effective_risk_pct"] = float(execution_meta.get("effective_risk_pct"))
            if execution_meta.get("risk_overlay_pct") is not None:
                row["risk_overlay_pct"] = float(execution_meta.get("risk_overlay_pct"))
        
        res = _db().table("autotrade_trades").insert(row).execute()
        trade_id = res.data[0]["id"] if res.data else None
        logger.info(f"[TradeHistory] Saved open trade #{trade_id} — {symbol} {side} @ {entry_price} [{strategy}]")
        return trade_id
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to save open trade: {e}")
        return None


# ─────────────────────────────────────────────
#  WRITE: Update trade saat posisi tutup
# ─────────────────────────────────────────────

def save_trade_close(
    trade_id: int,
    exit_price: float,
    pnl_usdt: float,
    close_reason: str,   # closed_tp / closed_sl / closed_flip / closed_manual
    loss_reasoning: str = "",
    win_metadata: Optional[Dict[str, Any]] = None,
):
    """Update trade yang sudah ada dengan data close."""
    try:
        res_open = _db().table("autotrade_trades").select("*").eq("id", trade_id).limit(1).execute()
        trade_row = (res_open.data or [{}])[0] if res_open else {}
        partial_realized = _partial_realized_pnl(trade_row)
        pnl_is_total = bool((win_metadata or {}).get("pnl_is_total", False))
        final_leg_pnl = float(pnl_usdt)
        cumulative_pnl = float(final_leg_pnl if pnl_is_total else (final_leg_pnl + partial_realized))
        try:
            base_playbook = float(trade_row.get("playbook_match_score") or 0.0)
        except Exception:
            base_playbook = 0.0
        try:
            base_effective = float(trade_row.get("effective_risk_pct") or 0.0)
        except Exception:
            base_effective = 0.0
        try:
            base_overlay = float(trade_row.get("risk_overlay_pct") or 0.0)
        except Exception:
            base_overlay = 0.0

        update = {
            "exit_price":     float(exit_price),
            "pnl_usdt":       float(cumulative_pnl),
            "close_reason":   close_reason,
            "status":         close_reason,
            "remaining_quantity": 0.0,
            "closed_at":      datetime.utcnow().isoformat(),
            "playbook_match_score": base_playbook,
            "effective_risk_pct": base_effective,
            "risk_overlay_pct": base_overlay,
        }
        should_enforce_win_reasoning = _should_enforce_win_reasoning(close_reason, cumulative_pnl)

        if loss_reasoning:
            update["loss_reasoning"] = loss_reasoning
        elif (
            float(cumulative_pnl) < 0
            and not should_enforce_win_reasoning
            and not str(update.get("loss_reasoning") or "").strip()
        ):
            update["loss_reasoning"] = (
                f"auto_loss_reason: close_reason={close_reason}; pnl={float(cumulative_pnl):+.6f}"
            )
        if win_metadata:
            if win_metadata.get("playbook_match_score") is not None:
                update["playbook_match_score"] = float(win_metadata.get("playbook_match_score"))
            if win_metadata.get("effective_risk_pct") is not None:
                update["effective_risk_pct"] = float(win_metadata.get("effective_risk_pct"))
            if win_metadata.get("risk_overlay_pct") is not None:
                update["risk_overlay_pct"] = float(win_metadata.get("risk_overlay_pct"))
            tags = win_metadata.get("win_reason_tags")
            if tags is not None:
                update["win_reason_tags"] = _normalized_win_tags(tags, close_reason)
            if win_metadata.get("win_reasoning"):
                update["win_reasoning"] = str(win_metadata.get("win_reasoning"))

        if should_enforce_win_reasoning and not update.get("win_reasoning"):
            merged_trade = dict(trade_row or {})
            merged_trade.update({
                "exit_price": float(exit_price),
                "pnl_usdt": float(cumulative_pnl),
                "close_reason": close_reason,
            })
            matched_tags = []
            if win_metadata and isinstance(win_metadata.get("win_reason_tags"), list):
                matched_tags = list(win_metadata.get("win_reason_tags"))
            matched_tags = _normalized_win_tags(matched_tags, close_reason)
            update["win_reasoning"] = build_win_reasoning(
                merged_trade,
                playbook_tags=matched_tags,
                playbook_score=(win_metadata or {}).get("playbook_match_score"),
            )
            update["win_reason_tags"] = matched_tags

        if partial_realized > 0 and not pnl_is_total:
            logger.info(
                f"[TradeHistory] cumulative_pnl applied trade #{trade_id}: "
                f"partial={partial_realized:+.6f} final_leg={final_leg_pnl:+.6f} total={cumulative_pnl:+.6f}"
            )

        _db().table("autotrade_trades").update(update).eq("id", trade_id).execute()
        logger.info(f"[TradeHistory] Closed trade #{trade_id} — {close_reason} PnL={cumulative_pnl:.4f}")
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to close trade #{trade_id}: {e}")


def close_open_trades_by_symbol(
    telegram_id: int,
    symbol: str,
    exit_price: float,
    pnl_usdt: float,
    close_reason: str,
    loss_reasoning: str = "",
    win_metadata: Optional[Dict[str, Any]] = None,
    trade_type: Optional[str] = None,
):
    """Close semua open trade untuk symbol tertentu (dipakai saat flip/SL hit)."""
    try:
        res = _db().table("autotrade_trades") \
            .select("*") \
            .eq("telegram_id", int(telegram_id)) \
            .eq("symbol", symbol) \
            .eq("status", "open") \
            .execute()

        for row in (res.data or []):
            if not _matches_trade_type_filter(row, trade_type):
                continue
            save_trade_close(
                trade_id=row["id"],
                exit_price=exit_price,
                pnl_usdt=pnl_usdt,
                close_reason=close_reason,
                loss_reasoning=loss_reasoning,
                win_metadata=win_metadata,
            )
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to close trades for {symbol}: {e}")


# ─────────────────────────────────────────────
#  READ: Ambil open trades dari DB
# ─────────────────────────────────────────────

def get_open_trades(telegram_id: int, trade_type: Optional[str] = None) -> List[Dict]:
    """Ambil semua trade yang masih open untuk user."""
    try:
        res = _db().table("autotrade_trades") \
            .select("*") \
            .eq("telegram_id", int(telegram_id)) \
            .eq("status", "open") \
            .execute()
        rows = list(res.data or [])
        if trade_type:
            rows = [r for r in rows if _matches_trade_type_filter(r, trade_type)]
        return rows
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to get open trades: {e}")
        return []


def get_all_open_trades(trade_type: Optional[str] = None) -> List[Dict]:
    """Ambil semua open trades dari semua user (untuk startup check)."""
    try:
        res = _db().table("autotrade_trades") \
            .select("*") \
            .eq("status", "open") \
            .execute()
        rows = list(res.data or [])
        if trade_type:
            rows = [r for r in rows if _matches_trade_type_filter(r, trade_type)]
        return rows
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to get all open trades: {e}")
        return []


def reconcile_open_trades_with_exchange(
    telegram_id: int,
    client,
    trade_type: Optional[str] = None,
) -> int:
    """
    Self-healing reconciliation for stale "open" trades.

    Compares trades that are still marked status="open" in the DB against
    the actual open positions on the exchange. Any DB-open trade that has
    no matching live position is closed in the DB with the appropriate
    reason inferred from PnL sign and (if available) StackMentor TP-hit
    flags.

    Why this is needed
    ------------------
    The swing engine only marks trades closed inside its in-loop polling
    (autotrade_engine._trade_loop) and only when its local
    `had_open_position` flag was True. Across bot restarts, scalping-engine
    closes, manual closes from outside the bot, or any TP/SL fill that
    happened while the engine was down, the row stays stuck at "open"
    forever and the user sees "Position still open" in /history for trades
    that have actually been closed for hours/days.

    This function is safe to call from:
      * the /history command handler (lazy heal on view)
      * engine startup / restore
      * a periodic background task

    Optional:
      * trade_type filter ("swing" / "scalping") to keep reconciliation
        strategy-isolated.

    Returns: number of trades that were healed (closed) by this call.
    """
    healed = 0
    try:
        open_trades = get_open_trades(telegram_id, trade_type=trade_type)
        if not open_trades:
            return 0

        # Fetch live exchange positions ONCE for this user.
        try:
            pos_resp = client.get_positions()
        except Exception as e:
            logger.warning(
                f"[Reconcile:{telegram_id}] get_positions raised: {e}"
            )
            return 0

        if not pos_resp.get("success"):
            logger.warning(
                f"[Reconcile:{telegram_id}] get_positions failed: {pos_resp.get('error')}"
            )
            return 0

        live_symbols = {
            p.get("symbol")
            for p in pos_resp.get("positions", [])
            if float(p.get("qty") or p.get("size") or 0) > 0
        }

        for trade in open_trades:
            symbol = trade.get("symbol")
            if symbol in live_symbols:
                continue  # still open on exchange — leave alone

            # Orphan: DB says open, exchange says no position. Close it.
            entry = float(trade.get("entry_price") or 0)
            qty = float(
                trade.get("qty")
                or trade.get("quantity")
                or trade.get("original_quantity")
                or 0
            )
            side = (trade.get("side") or "").upper()
            exit_price = entry
            pnl = 0.0
            roundtrip_net_pnl = None
            roundtrip_close_price = None
            get_roundtrip = getattr(client, "get_roundtrip_financials", None)
            if callable(get_roundtrip):
                try:
                    roundtrip = get_roundtrip(
                        symbol=str(symbol or ""),
                        open_order_id=str(trade.get("order_id") or ""),
                        entry_side=str(side or ""),
                        opened_at_iso=str(trade.get("opened_at") or ""),
                    )
                    if isinstance(roundtrip, dict) and roundtrip.get("success"):
                        roundtrip_net_pnl = _to_float(roundtrip.get("net_pnl"), None)
                        roundtrip_close_price = _to_float(roundtrip.get("close_avg_price"), None)
                except Exception as e:
                    logger.warning(
                        f"[Reconcile:{telegram_id}] roundtrip financial lookup failed for {symbol}: {e}"
                    )

            # Infer close reason from execution evidence when available.
            tp1_hit = bool(trade.get("tp1_hit"))
            tp2_hit = bool(trade.get("tp2_hit"))
            tp3_hit = bool(trade.get("tp3_hit"))
            if tp3_hit:
                reason = "closed_tp3"
            elif tp2_hit:
                reason = "closed_tp2"
            elif tp1_hit:
                reason = "closed_tp1"
            else:
                reason = "stale_reconcile"

            if roundtrip_net_pnl is not None:
                pnl = float(roundtrip_net_pnl)
                if roundtrip_close_price is not None and float(roundtrip_close_price) > 0:
                    exit_price = float(roundtrip_close_price)
                source = "exchange_history"
            else:
                # Policy: never guess stale-reconcile PnL from ticker snapshots.
                reason = "stale_reconcile"
                pnl = 0.0
                source = "fallback_zero_pnl"

            reconcile_reasoning = (
                f"Reconciled from exchange — position no longer open; "
                f"reason={reason}; source={source}; "
                f"roundtrip_pnl_resolved={1 if roundtrip_net_pnl is not None else 0}; "
                f"qty={qty:.8f}; side={side}"
            )

            save_trade_close(
                trade_id=trade["id"],
                exit_price=exit_price,
                pnl_usdt=pnl,
                close_reason=reason,
                loss_reasoning=reconcile_reasoning,
            )
            healed += 1
            logger.warning(
                f"[Reconcile:{telegram_id}] Healed orphan {symbol} #{trade['id']} "
                f"as {reason} pnl={pnl:.4f}"
            )

        # Also clear stale entries from the in-memory StackMentor registry
        # so the monitor loop stops chasing dead positions.
        if healed:
            try:
                from app.stackmentor import _stackmentor_positions, remove_stackmentor_position
                user_positions = _stackmentor_positions.get(int(telegram_id), {})
                for sym in list(user_positions.keys()):
                    if sym not in live_symbols:
                        remove_stackmentor_position(int(telegram_id), sym)
            except Exception as e:
                logger.warning(
                    f"[Reconcile:{telegram_id}] StackMentor cleanup failed: {e}"
                )
    except Exception as e:
        logger.error(f"[Reconcile:{telegram_id}] Reconciliation error: {e}")
    return healed


def get_trade_history(telegram_id: int, limit: int = 20) -> List[Dict]:
    """Ambil history trade terbaru untuk user."""
    try:
        res = _db().table("autotrade_trades") \
            .select("*") \
            .eq("telegram_id", int(telegram_id)) \
            .order("opened_at", desc=True) \
            .limit(limit) \
            .execute()
        return res.data or []
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to get trade history: {e}")
        return []


def _resolve_day_window_utc(
    *,
    day_tz: str = "Asia/Singapore",
    now_utc: Optional[datetime] = None,
) -> Dict[str, datetime]:
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    tz = ZoneInfo(day_tz)
    local_now = now.astimezone(tz)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    local_end = local_start + timedelta(days=1)
    return {
        "utc_start": local_start.astimezone(timezone.utc),
        "utc_end": local_end.astimezone(timezone.utc),
        "local_start": local_start,
        "local_end": local_end,
    }


def _fetch_trades_for_window(
    *,
    time_column: str,
    utc_start: datetime,
    utc_end: datetime,
    limit: int = 5000,
) -> List[Dict[str, Any]]:
    s = _db()
    fields = (
        "id,telegram_id,symbol,status,close_reason,trade_type,timeframe,strategy,"
        "entry_price,sl_price,tp_price,tp1_price,rr_ratio,pnl_usdt,"
        "qty,quantity,original_quantity,remaining_quantity,opened_at,closed_at"
    )
    rows: List[Dict[str, Any]] = []
    page_size = min(1000, max(200, int(limit)))
    page = 0
    while len(rows) < limit:
        frm = page * page_size
        to = frm + page_size - 1
        res = (
            s.table("autotrade_trades")
            .select(fields)
            .gte(time_column, utc_start.isoformat())
            .lt(time_column, utc_end.isoformat())
            .order(time_column, desc=False)
            .range(frm, to)
            .execute()
        )
        chunk = res.data or []
        if not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        page += 1
    return rows[:limit]


def _summarize_mode_audit(opened_rows: List[Dict[str, Any]], closed_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    configured_rr = [_configured_rr(r) for r in opened_rows]
    configured_rr = [x for x in configured_rr if x is not None and x > 0]
    realized_r = [_realized_r_multiple(r) for r in closed_rows]
    realized_r = [x for x in realized_r if x is not None]

    close_reason_mix: Dict[str, int] = {}
    for row in closed_rows:
        reason = str(row.get("close_reason") or row.get("status") or "unknown").strip().lower()
        close_reason_mix[reason] = close_reason_mix.get(reason, 0) + 1

    return {
        "opened_count": len(opened_rows),
        "closed_count": len(closed_rows),
        "configured_rr_median": round(float(median(configured_rr)), 3) if configured_rr else None,
        "configured_rr_values": len(configured_rr),
        "realized_r_median": round(float(median(realized_r)), 3) if realized_r else None,
        "realized_r_values": len(realized_r),
        "close_reason_mix": close_reason_mix,
    }


def get_daily_rr_integrity_audit(
    *,
    day_tz: str = "Asia/Singapore",
    now_utc: Optional[datetime] = None,
    include_runtime_snapshots: bool = True,
) -> Dict[str, Any]:
    """
    Read-only daily audit path for R:R integrity by bot mode.

    Output includes:
    - opened/closed counts per bot (swing/scalping)
    - configured RR median (open rows)
    - realized R multiple median (closed rows)
    - close reason mix
    - runtime snapshot reason metadata (adaptive/governor/playbook)
    """
    window = _resolve_day_window_utc(day_tz=day_tz, now_utc=now_utc)
    opened_rows = _fetch_trades_for_window(
        time_column="opened_at",
        utc_start=window["utc_start"],
        utc_end=window["utc_end"],
    )
    closed_rows = _fetch_trades_for_window(
        time_column="closed_at",
        utc_start=window["utc_start"],
        utc_end=window["utc_end"],
    )

    opened_by_mode: Dict[str, List[Dict[str, Any]]] = {"swing": [], "scalping": [], "unknown": []}
    closed_by_mode: Dict[str, List[Dict[str, Any]]] = {"swing": [], "scalping": [], "unknown": []}

    for row in opened_rows:
        opened_by_mode[_classify_trade_mode(row)].append(row)
    for row in closed_rows:
        closed_by_mode[_classify_trade_mode(row)].append(row)

    per_mode = {
        mode: _summarize_mode_audit(opened_by_mode.get(mode, []), closed_by_mode.get(mode, []))
        for mode in ("swing", "scalping", "unknown")
    }

    runtime_snapshots: Dict[str, Any] = {}
    if include_runtime_snapshots:
        try:
            from app.adaptive_confluence import get_adaptive_overrides
            from app.sideways_governor import refresh_sideways_governor_state, get_sideways_governor_snapshot
            from app.win_playbook import refresh_global_win_playbook_state, get_win_playbook_snapshot

            adaptive = get_adaptive_overrides() or {}
            try:
                refresh_sideways_governor_state()
            except Exception:
                pass
            governor = get_sideways_governor_snapshot() or {}
            try:
                refresh_global_win_playbook_state()
            except Exception:
                pass
            playbook = get_win_playbook_snapshot() or {}

            runtime_snapshots = {
                "adaptive": {
                    "updated_at": adaptive.get("updated_at"),
                    "decision_reason": adaptive.get("decision_reason"),
                    "conf_delta": int(adaptive.get("conf_delta", 0) or 0),
                    "volume_min_ratio_delta": float(adaptive.get("volume_min_ratio_delta", 0.0) or 0.0),
                },
                "sideways_governor": {
                    "updated_at": governor.get("updated_at"),
                    "mode": str(governor.get("mode", "normal")).upper(),
                    "decision_reason": governor.get("decision_reason"),
                    "sample_size_24h": int(governor.get("sample_size_24h", 0) or 0),
                },
                "win_playbook": {
                    "updated_at": playbook.get("updated_at"),
                    "guardrails_healthy": bool(playbook.get("guardrails_healthy", False)),
                    "rolling_expectancy": float(playbook.get("rolling_expectancy", 0.0) or 0.0),
                    "rolling_win_rate": float(playbook.get("rolling_win_rate", 0.0) or 0.0),
                    "sample_size": int(playbook.get("sample_size", 0) or 0),
                    "risk_overlay_pct": float(playbook.get("risk_overlay_pct", 0.0) or 0.0),
                    "active_tag_count": len(playbook.get("active_tags", []) or []),
                },
            }
        except Exception as e:
            runtime_snapshots = {"error": str(e)}

    return {
        "day_tz": day_tz,
        "window": {
            "local_start": window["local_start"].isoformat(),
            "local_end": window["local_end"].isoformat(),
            "utc_start": window["utc_start"].isoformat(),
            "utc_end": window["utc_end"].isoformat(),
        },
        "totals": {
            "opened_count": len(opened_rows),
            "closed_count": len(closed_rows),
        },
        "per_mode": per_mode,
        "runtime_snapshots": runtime_snapshots,
    }


# ─────────────────────────────────────────────
#  ANALYSIS: Generate loss reasoning
# ─────────────────────────────────────────────

def build_loss_reasoning(trade: Dict, current_signal: Optional[Dict] = None) -> str:
    """
    Generate analisis kenapa trade ini loss.
    Bandingkan kondisi entry vs kondisi saat SL hit.
    """
    reasons = []

    entry_trend   = trade.get("trend_1h", "?")
    entry_struct  = trade.get("market_structure", "?")
    entry_rsi     = trade.get("rsi_15", 0)
    entry_conf    = trade.get("confidence", 0)
    side          = trade.get("side", "?")
    entry_reasons = trade.get("entry_reasons", [])

    reasons.append(f"Entry: {side} @ {trade.get('entry_price', '?')}")
    reasons.append(f"Kondisi entry — 1H: {entry_trend} | Struct: {entry_struct} | RSI: {entry_rsi} | Conf: {entry_conf}%")

    if current_signal:
        curr_trend  = current_signal.get("trend_1h", "?")
        curr_struct = current_signal.get("market_structure", "?")
        curr_rsi    = current_signal.get("rsi_15", 0)

        if entry_trend != curr_trend:
            reasons.append(f"⚠️ 1H trend berubah: {entry_trend} → {curr_trend} (reversal tidak terdeteksi tepat waktu)")
        if entry_struct != curr_struct:
            reasons.append(f"⚠️ Market structure berubah: {entry_struct} → {curr_struct}")
        if side == "LONG" and curr_rsi > 70:
            reasons.append(f"⚠️ RSI overbought saat entry ({entry_rsi}) — momentum sudah lemah")
        if side == "SHORT" and curr_rsi < 30:
            reasons.append(f"⚠️ RSI oversold saat entry ({entry_rsi}) — momentum sudah lemah")

    # Analisis dari entry reasons
    if entry_reasons:
        has_volume = any("Volume" in str(r) for r in entry_reasons)
        has_ob     = any("OB" in str(r) for r in entry_reasons)
        has_fvg    = any("FVG" in str(r) for r in entry_reasons)
        if not has_volume:
            reasons.append("⚠️ Tidak ada konfirmasi volume saat entry")
        if not has_ob and not has_fvg:
            reasons.append("⚠️ Tidak ada Order Block / FVG sebagai support/resistance")

    return " | ".join(reasons)


def build_win_reasoning(
    trade: Dict[str, Any],
    current_signal: Optional[Dict[str, Any]] = None,
    playbook_tags: Optional[List[str]] = None,
    playbook_score: Optional[float] = None,
) -> str:
    """
    Generate concise reasoning for winning closes.
    Mirrors `build_loss_reasoning` style but focuses on factors behind wins.
    """
    reasons: List[str] = []

    side = str(trade.get("side", "?"))
    entry = trade.get("entry_price", "?")
    exit_price = trade.get("exit_price", trade.get("close_price", "?"))
    pnl = float(trade.get("pnl_usdt") or 0.0)
    conf = trade.get("confidence", 0)
    trend = trade.get("trend_1h", "?")
    structure = trade.get("market_structure", "?")
    rr = trade.get("rr_ratio", "?")
    close_reason = str(trade.get("close_reason") or trade.get("status") or "")
    entry_reasons = trade.get("entry_reasons", []) or []

    reasons.append(f"Win: {side} {trade.get('symbol', '')} {entry} -> {exit_price} ({close_reason})")
    reasons.append(f"Entry quality — Conf: {conf}% | R:R: {rr} | 1H: {trend} | Struct: {structure}")

    if playbook_tags:
        reasons.append(f"Playbook tags matched: {', '.join(playbook_tags[:5])}")
    if playbook_score is not None:
        try:
            reasons.append(f"Playbook match score: {float(playbook_score):.3f}")
        except Exception:
            pass

    if entry_reasons:
        has_volume = any("volume" in str(r).lower() for r in entry_reasons)
        has_ob_fvg = any(("ob" in str(r).lower()) or ("fvg" in str(r).lower()) for r in entry_reasons)
        has_btc_align = any("btc" in str(r).lower() for r in entry_reasons)
        alignment = []
        if has_volume:
            alignment.append("volume confirmation")
        if has_ob_fvg:
            alignment.append("OB/FVG structure")
        if has_btc_align:
            alignment.append("BTC bias alignment")
        if alignment:
            reasons.append(f"Alignment factors: {', '.join(alignment)}")

    if current_signal:
        curr_trend = current_signal.get("trend_1h", "?")
        curr_struct = current_signal.get("market_structure", "?")
        if str(curr_trend) == str(trend):
            reasons.append(f"Trend persisted post-entry ({trend})")
        if str(curr_struct) == str(structure):
            reasons.append(f"Structure remained supportive ({structure})")

    if pnl > 0:
        reasons.append(f"Realized positive expectancy captured: +{pnl:.4f} USDT")

    return " | ".join([r for r in reasons if str(r).strip()])
