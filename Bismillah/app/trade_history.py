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
