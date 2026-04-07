"""
Trade History — Simpan dan kelola history trade autotrade ke Supabase.
Setiap order masuk/keluar dicatat lengkap dengan reasoning.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


def _db():
    from app.supabase_repo import _client
    return _client()


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
) -> Optional[int]:
    """Simpan trade baru ke Supabase. Return trade_id."""
    try:
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
            "rr_ratio":         float(signal.get("rr_ratio", 0)),
            "trend_1h":         signal.get("trend_1h", ""),
            "market_structure": signal.get("market_structure", ""),
            "rsi_15":           float(signal.get("rsi_15", 0)),
            "atr_pct":          float(signal.get("atr_pct", 0)),
            "entry_reasons":    signal.get("reasons", []),
            "is_flip":          is_flip,
            "order_id":         order_id,
            "opened_at":        datetime.utcnow().isoformat(),
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
):
    """Update trade yang sudah ada dengan data close."""
    try:
        update = {
            "exit_price":     float(exit_price),
            "pnl_usdt":       float(pnl_usdt),
            "status":         close_reason,
            "closed_at":      datetime.utcnow().isoformat(),
        }
        if loss_reasoning:
            update["loss_reasoning"] = loss_reasoning

        _db().table("autotrade_trades").update(update).eq("id", trade_id).execute()
        logger.info(f"[TradeHistory] Closed trade #{trade_id} — {close_reason} PnL={pnl_usdt:.4f}")
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to close trade #{trade_id}: {e}")


def close_open_trades_by_symbol(
    telegram_id: int,
    symbol: str,
    exit_price: float,
    pnl_usdt: float,
    close_reason: str,
    loss_reasoning: str = "",
):
    """Close semua open trade untuk symbol tertentu (dipakai saat flip/SL hit)."""
    try:
        res = _db().table("autotrade_trades") \
            .select("id") \
            .eq("telegram_id", int(telegram_id)) \
            .eq("symbol", symbol) \
            .eq("status", "open") \
            .execute()

        for row in (res.data or []):
            save_trade_close(
                trade_id=row["id"],
                exit_price=exit_price,
                pnl_usdt=pnl_usdt,
                close_reason=close_reason,
                loss_reasoning=loss_reasoning,
            )
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to close trades for {symbol}: {e}")


# ─────────────────────────────────────────────
#  READ: Ambil open trades dari DB
# ─────────────────────────────────────────────

def get_open_trades(telegram_id: int) -> List[Dict]:
    """Ambil semua trade yang masih open untuk user."""
    try:
        res = _db().table("autotrade_trades") \
            .select("*") \
            .eq("telegram_id", int(telegram_id)) \
            .eq("status", "open") \
            .execute()
        return res.data or []
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to get open trades: {e}")
        return []


def get_all_open_trades() -> List[Dict]:
    """Ambil semua open trades dari semua user (untuk startup check)."""
    try:
        res = _db().table("autotrade_trades") \
            .select("*") \
            .eq("status", "open") \
            .execute()
        return res.data or []
    except Exception as e:
        logger.error(f"[TradeHistory] Failed to get all open trades: {e}")
        return []


def reconcile_open_trades_with_exchange(
    telegram_id: int,
    client,
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

    Returns: number of trades that were healed (closed) by this call.
    """
    healed = 0
    try:
        open_trades = get_open_trades(telegram_id)
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
            qty = float(trade.get("qty") or 0)
            leverage = int(trade.get("leverage") or 1)
            side = (trade.get("side") or "").upper()

            # Try to fetch current price for a best-effort exit value.
            exit_price = entry
            try:
                ticker = client.get_ticker(symbol)
                if ticker.get("success"):
                    exit_price = float(
                        ticker.get("mark_price") or ticker.get("last_price") or entry
                    )
            except Exception:
                pass

            # Estimate PnL from price delta * qty * leverage direction.
            if side == "LONG":
                pnl = (exit_price - entry) * qty
            else:
                pnl = (entry - exit_price) * qty
            pnl_with_lev = pnl * leverage

            # Infer close reason. Prefer StackMentor tp-hit flags if any.
            tp1_hit = bool(trade.get("tp1_hit"))
            tp2_hit = bool(trade.get("tp2_hit"))
            tp3_hit = bool(trade.get("tp3_hit"))
            if tp3_hit:
                reason = "closed_tp3"
            elif tp2_hit:
                reason = "closed_tp2"
            elif tp1_hit:
                reason = "closed_tp1"
            elif pnl_with_lev >= 0:
                reason = "closed_tp"
            else:
                reason = "closed_sl"

            save_trade_close(
                trade_id=trade["id"],
                exit_price=exit_price,
                pnl_usdt=pnl_with_lev,
                close_reason=reason,
                loss_reasoning=(
                    "Reconciled from exchange — position no longer open"
                    if pnl_with_lev < 0 else ""
                ),
            )
            healed += 1
            logger.warning(
                f"[Reconcile:{telegram_id}] Healed orphan {symbol} #{trade['id']} "
                f"as {reason} pnl={pnl_with_lev:.4f}"
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
