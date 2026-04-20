"""
AutoTrade Engine — Professional Grade Trading Loop
Strategy: Multi-timeframe confluence + SMC + Risk Management
- Min R:R 1:2, dynamic SL via ATR
- Drawdown circuit breaker (stop if -5% daily)
- Volatility filter (no trade in low-volatility ranging market)
- Confidence threshold >= 68 (only high-quality setups)
- Max 1 position per symbol, max 3 concurrent positions
- StackMentor: 3-tier TP strategy (50%/40%/10% at R:R 1:2/1:3/1:10)
"""
import asyncio
import logging
import os
import time
from html import escape
from typing import Any, Dict, Optional, List, Set
from datetime import datetime, date, timezone
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

logger = logging.getLogger(__name__)

WEB_DASHBOARD_URL = os.getenv("WEB_DASHBOARD_URL", "https://cryptomentor.id")


def _env_flag(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "true" if default else "false") or "").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}

def _dashboard_keyboard():
    """Returns an InlineKeyboardMarkup with a Dashboard button."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", url=WEB_DASHBOARD_URL)]
    ])


def _build_trade_url(trade_id: Optional[int] = None, order_id: str = "", symbol: str = "") -> str:
    """Build dashboard URL with trade-specific query parameters."""
    try:
        parsed = urlsplit(WEB_DASHBOARD_URL)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["tab"] = "portfolio"
        if trade_id:
            query["trade_id"] = str(trade_id)
        if order_id and order_id != "-":
            query["order_id"] = str(order_id)
        if symbol:
            query["symbol"] = symbol
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", urlencode(query), parsed.fragment))
    except Exception:
        return WEB_DASHBOARD_URL


def _trade_detail_keyboard(trade_id: Optional[int] = None, order_id: str = "", symbol: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 View Trade Details", url=_build_trade_url(trade_id=trade_id, order_id=order_id, symbol=symbol))]
    ])


def _fmt_price(v: float) -> str:
    s = f"{float(v):,.6f}"
    return s.rstrip("0").rstrip(".")

# Import StackMentor system
from app.stackmentor import (
    STACKMENTOR_CONFIG,
    calculate_stackmentor_levels,
    calculate_qty_splits,
    monitor_stackmentor_positions,
)
from app.trade_execution import MIN_QTY_MAP, open_managed_position, validate_entry_prices
from app.symbol_coordinator import (
    get_coordinator,
    StrategyOwner,
    PositionSide,
)
from app.engine_execution_shared import (
    coordinator_clear_pending,
    coordinator_confirm_closed,
    coordinator_confirm_open,
    coordinator_set_pending,
    evaluate_and_apply_playbook_risk,
    format_and_emit_order_open_risk_audit,
)
from app.engine_runtime_shared import (
    get_top_volume_pairs,
    is_ttl_cooldown_active as _shared_is_ttl_cooldown_active,
    normalize_pending_lock_context,
    pending_lock_age_label,
    refresh_runtime_snapshot,
    sanitize_startup_pending_locks,
    set_ttl_cooldown as _shared_set_ttl_cooldown,
    should_notify_blocked_pending as _shared_should_notify_blocked_pending,
    should_stop_engine,
)
from app.leverage_policy import get_auto_max_safe_leverage
from app.pair_strategy_router import get_mixed_pair_assignments
from app.volume_pair_selector import mark_runtime_untradable_symbol

_running_tasks: Dict[int, asyncio.Task] = {}
_mixed_component_tasks: Dict[int, Dict[str, asyncio.Task]] = {}
_runtime_modes: Dict[int, str] = {}
_engine_lifecycle_locks: Dict[int, asyncio.Lock] = {}
_scalping_engines: Dict[int, Any] = {}
_blocked_pending_notify_ts: Dict[tuple, float] = {}
_stale_price_cooldown_ts: Dict[tuple, float] = {}
_BLOCKED_PENDING_NOTIFY_TTL_SECONDS = 600.0
_STALE_PRICE_COOLDOWN_SECONDS = 120.0
_SWING_QUEUE_MAX_AGE_SECONDS = 90.0
_SIGNAL_MARK_PROXY_CACHE: Dict[str, tuple[float, float]] = {}
_SIGNAL_MARK_PROXY_TTL_SECONDS = 5.0

# Multi-user symbol coordinator
_coordinator = None

def _get_coordinator():
    """Get or initialize the global coordinator instance."""
    global _coordinator
    if _coordinator is None:
        _coordinator = get_coordinator()
    return _coordinator


def get_engine(user_id: int):
    """Return running scalping engine instance for this user when available."""
    return _scalping_engines.get(int(user_id))


def get_scalping_engine(user_id: int):
    """
    Backward-compatible alias for control-plane/runtime callers.
    """
    return get_engine(user_id)


def _get_lifecycle_lock(user_id: int) -> asyncio.Lock:
    uid = int(user_id)
    if uid not in _engine_lifecycle_locks:
        _engine_lifecycle_locks[uid] = asyncio.Lock()
    return _engine_lifecycle_locks[uid]


def _should_notify_blocked_pending(user_id: int, symbol: str) -> bool:
    key = (int(user_id), str(symbol).upper())
    return _shared_should_notify_blocked_pending(
        _blocked_pending_notify_ts,
        key=key,
        ttl_sec=_BLOCKED_PENDING_NOTIFY_TTL_SECONDS,
    )


def _mark_stale_price_cooldown(user_id: int, symbol: str, ttl_sec: float = _STALE_PRICE_COOLDOWN_SECONDS) -> float:
    key = (int(user_id), str(symbol).upper())
    return _shared_set_ttl_cooldown(
        _stale_price_cooldown_ts,
        key=key,
        ttl_sec=float(ttl_sec),
    )


def _is_stale_price_cooldown_active(user_id: int, symbol: str) -> bool:
    key = (int(user_id), str(symbol).upper())
    return _shared_is_ttl_cooldown_active(
        _stale_price_cooldown_ts,
        key=key,
    )

# Track posisi yang sudah hit TP1 (breakeven mode): user_id → set of symbols
_tp1_hit_positions: Dict[int, set] = {}

# Signal queue system: user_id → list of signals (volume-rank first, confidence tie-break)
_signal_queues: Dict[int, List[Dict]] = {}

# Symbol execution locks: user_id → {symbol → asyncio.Lock}
_symbol_locks: Dict[int, Dict[str, asyncio.Lock]] = {}

# Track signals being processed: user_id → set of symbols currently being executed
_signals_being_processed: Dict[int, set] = {}
# Track swing signal confirmation streaks: user_id -> {symbol -> {direction,count,ts}}
_swing_signal_streaks: Dict[int, Dict[str, Dict[str, float]]] = {}
# Track swing timeout protection runtime state per symbol.
_swing_timeout_state: Dict[int, Dict[str, Dict[str, Any]]] = {}

# ─────────────────────────────────────────────
#  Engine config (professional defaults)
# ─────────────────────────────────────────────
ENGINE_CONFIG = {
    "symbols":            ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "DOT", "LINK", "UNI", "ATOM", "XAU", "CL", "QQQ"],  # 15 pairs (expanded)
    "scan_interval":      45,       # detik antar scan
    "min_confidence":     68,       # hanya sinyal berkualitas tinggi
    "max_trades_per_day": 999,       # unlimited — push trading volume
    "max_concurrent":     4,        # max 4 posisi bersamaan (tetap 4 untuk risk management)
    "min_rr_ratio":       2.0,      # minimum Risk:Reward 1:2 (untuk validasi entry)
    "daily_loss_limit":   0.05,     # circuit breaker: stop jika -5% dari modal
    "atr_sl_multiplier":  2.0,      # SL = 2.0x ATR (lebih lebar, tahan manipulasi candle)
    "use_stackmentor":    True,     # Enable StackMentor 3-tier TP for ALL users
    "atr_tp1_multiplier": 4.0,      # TP1 = 4.0x ATR → R:R 1:2 (ambil 75% posisi) [LEGACY]
    "atr_tp2_multiplier": 6.0,      # TP2 = 6.0x ATR → R:R 1:3 (sisa 25% posisi) [LEGACY]
    "tp1_close_pct":      0.75,     # tutup 75% posisi di TP1 [LEGACY]
    "min_atr_pct":        0.4,      # filter: skip jika ATR < 0.4% (market flat)
    "max_atr_pct":        8.0,      # filter: skip jika ATR > 8% (terlalu volatile)
    "rsi_long_max":       65,       # jangan LONG jika RSI > 65 (overbought)
    "rsi_short_min":      35,       # jangan SHORT jika RSI < 35 (oversold)
    "volume_spike_min":   1.1,      # volume harus > 1.1x rata-rata
    "wick_rejection_max": 0.60,     # skip entry jika wick > 60% dari candle range (manipulasi)
    # Swing adaptive parity controls
    "swing_signal_confirmations_required": int(os.getenv("SWING_SIGNAL_CONFIRMATIONS_REQUIRED", "1")),
    "swing_signal_confirmation_max_gap_seconds": int(os.getenv("SWING_SIGNAL_CONFIRMATION_MAX_GAP_SECONDS", "45")),
    "swing_emergency_candidate_mode": os.getenv("SWING_EMERGENCY_CANDIDATE_MODE", "true").lower() == "true",
    "swing_emergency_conf_relax": int(os.getenv("SWING_EMERGENCY_CONF_RELAX", "8")),
    "swing_emergency_min_confidence": int(os.getenv("SWING_EMERGENCY_MIN_CONFIDENCE", "50")),
    "swing_adaptive_timeout_protection_enabled": os.getenv(
        "SWING_ADAPTIVE_TIMEOUT_PROTECTION_ENABLED",
        os.getenv("SWING_TIMEOUT_PROTECTION_ENABLED", "false"),
    ).lower() == "true",
    "swing_timeout_be_trigger_pct": float(os.getenv("SWING_TIMEOUT_BE_TRIGGER_PCT", "0.20")),
    "swing_timeout_trailing_trigger_pct": float(os.getenv("SWING_TIMEOUT_TRAILING_TRIGGER_PCT", "0.35")),
    "swing_timeout_late_tighten_multiplier": float(os.getenv("SWING_TIMEOUT_LATE_TIGHTEN_MULTIPLIER", "1.4")),
    "swing_timeout_protection_min_update_seconds": int(os.getenv("SWING_TIMEOUT_PROTECTION_MIN_UPDATE_SECONDS", "45")),
    "swing_timeout_near_flat_usdt_threshold": float(os.getenv("SWING_TIMEOUT_NEAR_FLAT_USDT_THRESHOLD", "0.02")),
    "swing_dynamic_max_hold_enabled": os.getenv("SWING_DYNAMIC_MAX_HOLD_ENABLED", "false").lower() == "true",
    "swing_max_hold_default_seconds": int(os.getenv("SWING_MAX_HOLD_DEFAULT_SECONDS", "1800")),
}

QTY_PRECISION = {
    "BTCUSDT": 3, "ETHUSDT": 2, "SOLUSDT": 1, "BNBUSDT": 2,
    "XRPUSDT": 0, "ADAUSDT": 0, "DOGEUSDT": 0, "AVAXUSDT": 2,
    "DOTUSDT": 1, "LINKUSDT": 1, "UNIUSDT": 1, "ATOMUSDT": 1,
    "XAUUSDT": 2, "CLUSDT": 2, "QQQUSDT": 1,
}

RISK_MIN_PCT = 0.25
RISK_MAX_PCT = 5.0
EFFECTIVE_RISK_MAX_PCT = 10.0


def _normalize_risk_pct(raw_value: Any, default: float = 1.0) -> float:
    """Clamp incoming risk to supported autotrade range [0.25, 5.0]."""
    try:
        risk = float(raw_value)
    except Exception:
        return float(default)
    return max(RISK_MIN_PCT, min(RISK_MAX_PCT, risk))


def _normalize_effective_risk_pct(raw_value: Any, default: float = 1.0) -> float:
    """Clamp runtime effective risk to [0.25, 10.0] for overlay sizing."""
    try:
        risk = float(raw_value)
    except Exception:
        return float(default)
    return max(RISK_MIN_PCT, min(EFFECTIVE_RISK_MAX_PCT, risk))


def _risk_profile(user_risk_pct: float) -> Dict[str, float]:
    """
    Map user risk% to confluence selectivity and TP width.
    Risk > 1% is intentionally treated as high-risk mode.
    """
    risk = _normalize_risk_pct(user_risk_pct, default=1.0)
    if risk <= 0.25:
        return {"min_confidence": 60, "atr_multiplier": 0.5}
    if risk <= 0.5:
        return {"min_confidence": 50, "atr_multiplier": 1.0}
    if risk <= 0.75:
        return {"min_confidence": 45, "atr_multiplier": 1.25}
    if risk <= 1.0:
        return {"min_confidence": 40, "atr_multiplier": 1.5}
    if risk <= 2.0:
        return {"min_confidence": 38, "atr_multiplier": 1.75}
    if risk <= 3.0:
        return {"min_confidence": 36, "atr_multiplier": 2.0}
    if risk <= 4.0:
        return {"min_confidence": 34, "atr_multiplier": 2.25}
    return {"min_confidence": 32, "atr_multiplier": 2.5}

# Cooldown tracker: symbol → timestamp terakhir flip
_flip_cooldown: Dict[str, float] = {}
FLIP_COOLDOWN_SECONDS        = 1800  # 30 menit antar flip per simbol (trending market)
FLIP_COOLDOWN_SIDEWAYS_SECS  = 900   # 15 menit saat BTC sideways (lebih responsif)
FLIP_MIN_CONFIDENCE          = 75    # flip hanya jika sinyal baru sangat kuat
FLIP_MIN_CONFIDENCE_SIDEWAYS = 70    # threshold lebih rendah saat sideways (range trading)


def _cleanup_signal_queue(user_id: int, symbol: str, success: bool = True):
    """
    Helper: Clean up signal from queue and sync to Supabase.
    Removes from local queue, unmarks as processing, and syncs status.
    """
    # Remove from local queue
    if user_id in _signal_queues:
        _signal_queues[user_id] = [s for s in _signal_queues[user_id] if s['symbol'] != symbol]

    # Unmark from processing
    if user_id in _signals_being_processed:
        _signals_being_processed[user_id].discard(symbol)

    # Sync to Supabase
    try:
        from app.supabase_repo import _client
        s = _client()
        status = "executed" if success else "failed"
        s.table("signal_queue").update({
            "status": status,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).eq(
            "symbol", symbol
        ).eq("status", "executing").execute()
        logger.debug(f"[Engine:{user_id}] Synced {symbol} as {status} to Supabase")
    except Exception as _sync_err:
        logger.warning(f"[Engine:{user_id}] Failed to sync cleanup status: {_sync_err}")


def _upsert_signal_queue_entry(
    user_id: int,
    signal: Dict[str, Any],
    now_ts: Optional[float] = None,
) -> str:
    """
    Insert or refresh a queued signal for this user.
    Returns one of: inserted, updated, skipped_inflight, ignored.
    """
    symbol = str(signal.get("symbol", "")).upper()
    if not symbol:
        return "ignored"

    queued_entry = dict(signal)
    queued_entry["symbol"] = symbol
    queued_entry["_queued_at_ts"] = float(time.time() if now_ts is None else now_ts)

    user_queue = _signal_queues.setdefault(int(user_id), [])
    processing = _signals_being_processed.setdefault(int(user_id), set())

    for idx, existing in enumerate(user_queue):
        if str(existing.get("symbol", "")).upper() != symbol:
            continue
        if symbol in processing:
            return "skipped_inflight"
        user_queue[idx] = queued_entry
        return "updated"

    user_queue.append(queued_entry)
    return "inserted"


def _drop_expired_signal_queue_entries(
    user_id: int,
    max_age_sec: float = _SWING_QUEUE_MAX_AGE_SECONDS,
    now_ts: Optional[float] = None,
) -> List[str]:
    """
    Drop queued (non-processing) signals older than max_age_sec.
    Signals missing queue timestamp are treated as expired.
    """
    uid = int(user_id)
    if uid not in _signal_queues:
        return []

    now = float(time.time() if now_ts is None else now_ts)
    processing = _signals_being_processed.get(uid, set())
    fresh_queue: List[Dict[str, Any]] = []
    expired_symbols: List[str] = []

    for queued in _signal_queues[uid]:
        symbol = str(queued.get("symbol", "")).upper()
        if symbol in processing:
            fresh_queue.append(queued)
            continue

        try:
            queued_at = float(queued.get("_queued_at_ts", 0.0) or 0.0)
        except Exception:
            queued_at = 0.0
        age_sec = now - queued_at
        if queued_at <= 0.0 or age_sec > float(max_age_sec):
            if symbol:
                expired_symbols.append(symbol)
            continue
        fresh_queue.append(queued)

    _signal_queues[uid] = fresh_queue
    return expired_symbols


def _build_queued_remaining_symbols(
    queue: List[Dict[str, Any]],
    active_idx: int,
    active_symbol: str,
) -> List[str]:
    """Build display list excluding the active entry."""
    active_symbol_u = str(active_symbol).upper()
    remaining: List[str] = []
    for idx, queued in enumerate(queue):
        symbol = str(queued.get("symbol", "")).upper()
        if idx == int(active_idx):
            continue
        if symbol == active_symbol_u:
            continue
        if symbol:
            remaining.append(symbol)
    return remaining


def _sync_pending_signal_queue_row(user_id: int, signal: Dict[str, Any]):
    """Insert or refresh pending signal_queue row for web visibility."""
    try:
        symbol = str(signal.get("symbol", "")).upper()
        if not symbol:
            return
        tp1_val = signal.get("tp1")
        tp2_val = signal.get("tp2")
        if tp2_val in (None, ""):
            tp2_val = tp1_val
        tp3_val = signal.get("tp3")
        if tp3_val in (None, ""):
            tp3_val = tp2_val if tp2_val not in (None, "") else tp1_val
        payload = {
            "direction": signal.get("side"),
            "confidence": signal.get("confidence"),
            "entry_price": signal.get("entry_price"),
            "tp1": tp1_val,
            "tp2": tp2_val,
            "tp3": tp3_val,
            "sl": signal.get("sl"),
            "generated_at": datetime.utcnow().isoformat(),
            "reason": signal.get("reason", ""),
            "source": "autotrade",
        }
        from app.supabase_repo import _client
        s = _client()
        existing = s.table("signal_queue").select("id").eq(
            "user_id", user_id
        ).eq("symbol", symbol).eq(
            "status", "pending"
        ).limit(1).execute()
        if existing.data:
            row_id = existing.data[0].get("id")
            update_q = s.table("signal_queue").update(payload)
            if row_id is not None:
                update_q = update_q.eq("id", row_id)
            else:
                update_q = update_q.eq("user_id", user_id).eq("symbol", symbol).eq("status", "pending")
            update_q.execute()
            logger.debug(f"[Engine:{user_id}] Refreshed pending signal_queue row for {symbol}")
            return
        s.table("signal_queue").insert({
            "user_id": user_id,
            "symbol": symbol,
            "status": "pending",
            **payload,
        }).execute()
        logger.info(f"[Engine:{user_id}] Synced {symbol} to signal_queue (web visibility)")
    except Exception as _sync_err:
        logger.warning(f"[Engine:{user_id}] Failed to sync signal to Supabase: {_sync_err}")


def _cleanup_inflight_signal_marker(user_id: int, symbol: Optional[str]) -> bool:
    """Clear leaked in-flight marker when loop exits unexpectedly."""
    symbol_u = str(symbol or "").upper()
    if not symbol_u:
        return False
    processing = _signals_being_processed.get(int(user_id), set())
    if symbol_u not in processing:
        return False
    _cleanup_signal_queue(int(user_id), symbol_u, success=False)
    return True


def _resolve_signal_mark_price(symbol: str, now_ts: Optional[float] = None) -> Optional[float]:
    """
    Best-effort live mark proxy for preflight signal staleness checks.
    Uses 1m close from provider chain with short TTL cache to avoid request bursts.
    """
    symbol_u = str(symbol or "").upper()
    if not symbol_u:
        return None
    now = float(time.time() if now_ts is None else now_ts)
    cached = _SIGNAL_MARK_PROXY_CACHE.get(symbol_u)
    if cached:
        cached_px, cached_ts = cached
        if (now - float(cached_ts)) <= _SIGNAL_MARK_PROXY_TTL_SECONDS and float(cached_px) > 0:
            return float(cached_px)
    try:
        from app.providers.alternative_klines_provider import alternative_klines_provider
        base = symbol_u.replace("USDT", "")
        klines = alternative_klines_provider.get_klines(
            base,
            interval="1m",
            limit=2,
            preferred_sources=["bitunix", "binance", "cryptocompare", "coingecko"],
        )
        if klines:
            mark_px = float(klines[-1][4])
            if mark_px > 0:
                _SIGNAL_MARK_PROXY_CACHE[symbol_u] = (mark_px, now)
                return mark_px
    except Exception as _mark_err:
        logger.debug(f"[Signal] {symbol_u} mark proxy fetch failed: {_mark_err}")
    return None


def _signal_prices_pass_live_mark(
    symbol: str,
    side: str,
    entry_price: float,
    tp1_price: float,
    sl_price: float,
    stale_cooldown_user_id: Optional[int] = None,
    stale_cooldown_ttl_sec: float = _STALE_PRICE_COOLDOWN_SECONDS,
) -> bool:
    """
    Reject stale signal levels before queueing when live mark already violates
    strict execution validation rules. No price mutation is performed.
    """
    symbol_u = str(symbol or "").upper()
    mark_px = _resolve_signal_mark_price(symbol_u)
    if mark_px is None or mark_px <= 0:
        return True
    ok, _, err = validate_entry_prices(
        side=str(side or "").upper(),
        entry=float(entry_price),
        tp1=float(tp1_price),
        sl=float(sl_price),
        mark_price=float(mark_px),
    )
    if ok:
        return True
    if stale_cooldown_user_id is not None:
        try:
            _mark_stale_price_cooldown(
                int(stale_cooldown_user_id),
                symbol_u,
                ttl_sec=float(stale_cooldown_ttl_sec),
            )
        except Exception as _cd_err:
            logger.debug(f"[Signal] {symbol_u} preflight cooldown mark failed: {_cd_err}")
    logger.info(
        f"[Signal] {symbol_u} preflight stale reject: {err} "
        f"(entry={float(entry_price):.6f} tp1={float(tp1_price):.6f} sl={float(sl_price):.6f})"
    )
    return False


def _passes_swing_confirmation_gate(user_id: int, signal: Dict[str, Any], cfg: Dict[str, Any]) -> bool:
    """
    Consecutive-direction confirmation gate for swing entries.
    Helps reduce rapid direction flip churn on noisy intervals.
    """
    try:
        symbol = str(signal.get("symbol") or "").upper()
        direction = str(signal.get("side") or "").upper()
        if not symbol or direction not in {"LONG", "SHORT"}:
            return False
        required = max(1, int(cfg.get("swing_signal_confirmations_required", 1) or 1))
        max_gap = max(5, int(cfg.get("swing_signal_confirmation_max_gap_seconds", 45) or 45))
        now_ts = time.time()

        user_streaks = _swing_signal_streaks.setdefault(int(user_id), {})
        streak = user_streaks.get(symbol)
        if not streak:
            user_streaks[symbol] = {"direction": direction, "count": 1, "ts": now_ts}
            return required <= 1

        last_dir = str(streak.get("direction") or "")
        last_count = int(streak.get("count", 0) or 0)
        last_ts = float(streak.get("ts", 0.0) or 0.0)

        if direction == last_dir and (now_ts - last_ts) <= max_gap:
            new_count = last_count + 1
            user_streaks[symbol] = {"direction": direction, "count": new_count, "ts": now_ts}
        else:
            user_streaks[symbol] = {"direction": direction, "count": 1, "ts": now_ts}
            new_count = 1

        if new_count < required:
            logger.info(
                f"[Engine:{user_id}] {symbol} confirmation gate: {new_count}/{required}, waiting"
            )
            return False

        # Consume streak for this execution cycle
        user_streaks.pop(symbol, None)
        return True
    except Exception as e:
        logger.warning(f"[Engine:{user_id}] Swing confirmation gate error: {e}")
        return False


def _generate_swing_emergency_candidate(
    base_symbol: str,
    btc_bias: Optional[Dict[str, Any]],
    user_risk_pct: float,
    adaptive_overrides: Optional[Dict[str, Any]],
    cfg: Dict[str, Any],
    stale_cooldown_user_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Build an emergency fallback candidate for swing mode by relaxing adaptive
    strictness only when normal candidate generation returns none.
    """
    try:
        relaxed = dict(adaptive_overrides or {})
        relax_conf = max(0, int(cfg.get("swing_emergency_conf_relax", 8) or 8))
        relaxed["conf_delta"] = int((relaxed.get("conf_delta", 0) or 0) - relax_conf)
        relaxed["volume_min_ratio_delta"] = float((relaxed.get("volume_min_ratio_delta", 0.0) or 0.0) - 0.2)
        relaxed["ob_fvg_requirement_mode"] = "soft"
        sig = _compute_signal_pro(
            base_symbol,
            btc_bias,
            user_risk_pct,
            relaxed,
            stale_cooldown_user_id=stale_cooldown_user_id,
        )
        if not sig:
            return None
        min_conf = max(0, min(100, int(cfg.get("swing_emergency_min_confidence", 50) or 50)))
        if float(sig.get("confidence", 0) or 0) < min_conf:
            return None
        sig["is_emergency"] = True
        sig["emergency_score"] = (
            float(sig.get("confidence", 0) or 0)
            + (float(sig.get("rr_ratio", 0) or 0) * 8.0)
            + (float(sig.get("vol_ratio", 1.0) or 1.0) * 4.0)
        )
        return sig
    except Exception as e:
        logger.warning(f"[Signal] Emergency candidate error {base_symbol}: {e}")
        return None


def _is_reversal(open_side: str, new_signal: Dict, btc_is_sideways: bool = False) -> bool:
    """
    Cek apakah sinyal baru adalah reversal dari posisi aktif.

    Mode TRENDING (default):
    - Confidence >= 75%, 1H trend flip, CHoCH market structure

    Mode SIDEWAYS (BTC ranging):
    - Confidence >= 70%, EMA cross cukup (tidak perlu full CHoCH)
    - Cocok untuk range trading: flip di support/resistance
    """
    import time
    symbol   = new_signal.get("symbol", "?")
    new_side = new_signal.get("side")

    if not new_side:
        return False

    # Arah harus berlawanan
    if open_side == "BUY" and new_side != "SHORT":
        logger.debug(f"[Reversal:{symbol}] No flip — signal same direction ({new_side})")
        return False
    if open_side == "SELL" and new_side != "LONG":
        logger.debug(f"[Reversal:{symbol}] No flip — signal same direction ({new_side})")
        return False

    conf = new_signal.get("confidence", 0)
    min_conf = FLIP_MIN_CONFIDENCE_SIDEWAYS if btc_is_sideways else FLIP_MIN_CONFIDENCE

    if conf < min_conf:
        logger.info(f"[Reversal:{symbol}] No flip — confidence {conf}% < {min_conf}%")
        return False

    trend_1h = new_signal.get("trend_1h", "NEUTRAL")
    struct   = new_signal.get("market_structure", "ranging")

    if btc_is_sideways:
        # Mode sideways: cukup EMA cross + RSI extreme (tidak perlu full CHoCH)
        # Ini untuk range trading — flip di area support/resistance
        rsi_15 = new_signal.get("rsi_15", 50)
        smc_ok = struct in ("uptrend", "downtrend", "ranging")  # accept semua struktur

        if open_side == "BUY":
            # Flip ke SHORT: butuh RSI overbought atau trend sudah SHORT
            rsi_extreme = rsi_15 > 60
            trend_ok    = trend_1h in ("SHORT", "NEUTRAL")
            if not (rsi_extreme or trend_ok):
                logger.info(f"[Reversal:{symbol}] Sideways no flip SHORT — RSI={rsi_15:.0f} trend={trend_1h}")
                return False
        else:
            # Flip ke LONG: butuh RSI oversold atau trend sudah LONG
            rsi_extreme = rsi_15 < 40
            trend_ok    = trend_1h in ("LONG", "NEUTRAL")
            if not (rsi_extreme or trend_ok):
                logger.info(f"[Reversal:{symbol}] Sideways no flip LONG — RSI={rsi_15:.0f} trend={trend_1h}")
                return False

        cooldown_secs = FLIP_COOLDOWN_SIDEWAYS_SECS
        logger.info(f"[Reversal:{symbol}] Sideways mode — relaxed flip check passed")
    else:
        # Mode trending: syarat ketat (CHoCH)
        if open_side == "BUY" and trend_1h != "SHORT":
            logger.info(f"[Reversal:{symbol}] No flip — 1H trend not SHORT yet ({trend_1h})")
            return False
        if open_side == "SELL" and trend_1h != "LONG":
            logger.info(f"[Reversal:{symbol}] No flip — 1H trend not LONG yet ({trend_1h})")
            return False

        if open_side == "BUY" and struct != "downtrend":
            logger.info(f"[Reversal:{symbol}] No flip — structure not downtrend ({struct})")
            return False
        if open_side == "SELL" and struct != "uptrend":
            logger.info(f"[Reversal:{symbol}] No flip — structure not uptrend ({struct})")
            return False

        cooldown_secs = FLIP_COOLDOWN_SECONDS

    # Cooldown check
    last_flip = _flip_cooldown.get(symbol, 0)
    elapsed   = time.time() - last_flip
    if elapsed < cooldown_secs:
        logger.info(f"[Reversal:{symbol}] No flip — cooldown {int(cooldown_secs - elapsed)}s remaining")
        return False

    mode_label = "SIDEWAYS" if btc_is_sideways else "TRENDING"
    logger.warning(
        f"[Reversal:{symbol}] ✅ FLIP APPROVED [{mode_label}] — "
        f"{open_side} → {new_side} | conf={conf}% | 1H={trend_1h} | struct={struct}"
    )
    return True


# ─────────────────────────────────────────────
#  BTC Bias Filter — Market Leader Analysis
# ─────────────────────────────────────────────
def _get_btc_bias() -> Dict:
    """
    Analisis BTC sebagai market leader untuk filter altcoin signals.
    Return: {"bias": "BULLISH"/"BEARISH"/"NEUTRAL", "strength": 0-100, "reasons": [...]}
    
    Professional logic:
    - BTC harus punya directional bias yang jelas sebelum trade altcoin
    - Kalau BTC ranging/indecisive → skip semua altcoin (avoid whipsaw)
    - Altcoin signal harus align dengan BTC bias
    """
    try:
        from app.providers.alternative_klines_provider import alternative_klines_provider
        
        # Fetch BTC multi-timeframe data
        klines_4h  = alternative_klines_provider.get_klines("BTC", interval='4h',  limit=50)
        klines_1h  = alternative_klines_provider.get_klines("BTC", interval='1h',  limit=100)
        klines_15m = alternative_klines_provider.get_klines("BTC", interval='15m', limit=60)
        
        if not klines_4h or not klines_1h or not klines_15m:
            logger.warning("[BTCBias] Insufficient data")
            return {"bias": "NEUTRAL", "strength": 0, "reasons": ["Insufficient BTC data"]}
        
        # ── 4H: Higher timeframe trend (most important) ────────────────
        c4h = [float(k[4]) for k in klines_4h]
        h4h = [float(k[2]) for k in klines_4h]
        l4h = [float(k[3]) for k in klines_4h]
        v4h = [float(k[5]) for k in klines_4h]
        
        ema21_4h = _calc_ema(c4h, 21)
        ema50_4h = _calc_ema(c4h, 50)
        price_4h = c4h[-1]
        
        # 4H trend direction
        if price_4h > ema21_4h > ema50_4h:
            trend_4h = "BULLISH"
        elif price_4h < ema21_4h < ema50_4h:
            trend_4h = "BEARISH"
        else:
            trend_4h = "NEUTRAL"
        
        # ── 1H: Intermediate trend confirmation ────────────────────────
        c1h = [float(k[4]) for k in klines_1h]
        h1h = [float(k[2]) for k in klines_1h]
        l1h = [float(k[3]) for k in klines_1h]
        v1h = [float(k[5]) for k in klines_1h]
        
        ema21_1h = _calc_ema(c1h, 21)
        ema50_1h = _calc_ema(c1h, 50)
        price_1h = c1h[-1]
        rsi_1h   = _calc_rsi(c1h)
        
        if price_1h > ema21_1h > ema50_1h:
            trend_1h = "BULLISH"
        elif price_1h < ema21_1h < ema50_1h:
            trend_1h = "BEARISH"
        else:
            trend_1h = "NEUTRAL"
        
        # ── 15M: Short-term momentum ───────────────────────────────────
        c15 = [float(k[4]) for k in klines_15m]
        h15 = [float(k[2]) for k in klines_15m]
        l15 = [float(k[3]) for k in klines_15m]
        v15 = [float(k[5]) for k in klines_15m]
        
        ema9_15  = _calc_ema(c15, 9)
        ema21_15 = _calc_ema(c15, 21)
        rsi_15   = _calc_rsi(c15)
        
        if ema9_15 > ema21_15:
            trend_15m = "BULLISH"
        elif ema9_15 < ema21_15:
            trend_15m = "BEARISH"
        else:
            trend_15m = "NEUTRAL"
        
        # ── Volume confirmation ────────────────────────────────────────
        vol_ratio_1h = _calc_volume_ratio(v1h, 20)
        has_volume   = vol_ratio_1h >= 1.2  # Volume harus > 1.2x average
        
        # ── Market structure (swing highs/lows) ────────────────────────
        swing_highs, swing_lows = [], []
        w = 3
        for i in range(w, len(c1h) - w):
            if h1h[i] == max(h1h[i - w:i + w + 1]):
                swing_highs.append(h1h[i])
            if l1h[i] == min(l1h[i - w:i + w + 1]):
                swing_lows.append(l1h[i])
        
        structure = "ranging"
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                structure = "uptrend"  # HH + HL
            elif swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
                structure = "downtrend"  # LH + LL
        
        # ── Decision logic: require multi-timeframe alignment ──────────
        reasons = []
        strength = 50  # base strength
        
        # BULLISH bias requirements
        if trend_4h == "BULLISH" and trend_1h == "BULLISH":
            bias = "BULLISH"
            strength += 20
            reasons.append(f"4H+1H bullish alignment")
            
            if trend_15m == "BULLISH":
                strength += 10
                reasons.append(f"15M momentum bullish")
            
            if structure == "uptrend":
                strength += 10
                reasons.append(f"BOS: HH+HL (uptrend)")
            
            if has_volume:
                strength += 10
                reasons.append(f"Volume confirmation {vol_ratio_1h:.1f}x")
            
            if rsi_1h < 70:  # Not overbought
                strength += 5
            else:
                strength -= 10
                reasons.append(f"⚠️ RSI overbought {rsi_1h:.0f}")
        
        # BEARISH bias requirements
        elif trend_4h == "BEARISH" and trend_1h == "BEARISH":
            bias = "BEARISH"
            strength += 20
            reasons.append(f"4H+1H bearish alignment")
            
            if trend_15m == "BEARISH":
                strength += 10
                reasons.append(f"15M momentum bearish")
            
            if structure == "downtrend":
                strength += 10
                reasons.append(f"BOS: LH+LL (downtrend)")
            
            if has_volume:
                strength += 10
                reasons.append(f"Volume confirmation {vol_ratio_1h:.1f}x")
            
            if rsi_1h > 30:  # Not oversold
                strength += 5
            else:
                strength -= 10
                reasons.append(f"⚠️ RSI oversold {rsi_1h:.0f}")
        
        # NEUTRAL — conflicting signals or ranging
        else:
            bias = "NEUTRAL"
            strength = 30  # Low strength
            reasons.append(f"Conflicting timeframes: 4H={trend_4h} 1H={trend_1h} 15M={trend_15m}")
            if structure == "ranging":
                reasons.append(f"Market structure: ranging (no clear HH/HL or LH/LL)")
        
        # Cap strength
        strength = int(min(max(strength, 0), 100))
        
        logger.info(
            f"[BTCBias] {bias} strength={strength}% | "
            f"4H={trend_4h} 1H={trend_1h} 15M={trend_15m} | "
            f"struct={structure} vol={vol_ratio_1h:.1f}x RSI={rsi_1h:.0f}"
        )
        
        return {
            "bias": bias,
            "strength": strength,
            "reasons": reasons,
            "trend_4h": trend_4h,
            "trend_1h": trend_1h,
            "structure": structure,
            "rsi_1h": round(rsi_1h, 1),
        }
    
    except Exception as e:
        logger.warning(f"_get_btc_bias error: {e}", exc_info=True)
        return {"bias": "NEUTRAL", "strength": 0, "reasons": [f"Error: {e}"]}
def _calc_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    trs = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return sum(trs[-period:]) / period if len(trs) >= period else sum(trs) / len(trs) if trs else 0.0


def _calc_ema(data: List[float], period: int) -> float:
    if len(data) < period:
        return sum(data) / len(data)
    k = 2 / (period + 1)
    e = sum(data[:period]) / period
    for v in data[period:]:
        e = v * k + e * (1 - k)
    return e


def _calc_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100.0
    return 100 - (100 / (1 + ag / al))


def _calc_volume_ratio(volumes: List[float], period: int = 20) -> float:
    if len(volumes) < period + 1:
        return 1.0
    avg = sum(volumes[-period - 1:-1]) / period
    return volumes[-1] / avg if avg > 0 else 1.0


# ─────────────────────────────────────────────
#  Confluence Signal Generation (Multi-factor)
# ─────────────────────────────────────────────
def _calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calculate ATR for confluence signal system"""
    trs = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return sum(trs[-period:]) / period if len(trs) >= period else sum(trs) / len(trs) if trs else 0.0


def _generate_confluence_signal(
    symbol: str,
    candles_1h: List,
    user_risk_pct: float = 0.5,
    btc_bias: Optional[Dict] = None,
    adaptive_overrides: Optional[Dict[str, Any]] = None,
) -> Optional[Dict]:
    """
    Generate confluence-based signal using multiple confluence factors.

    Factors:
    - S/R bounce: price near support/resistance ±1% = +30 pts
    - RSI extremes: < 30 or > 70 = +25 pts
    - Volume spike: > 1.5× MA = +20 pts
    - Trending regime: ATR > 0.3% = +15 pts
    - Trend alignment: price > MA50 = +10 pts

    Min score: 50 points (requires 2+ factors)
    Adaptive thresholds based on user risk tolerance.
    """

    user_risk_pct = _normalize_risk_pct(user_risk_pct, default=1.0)
    config = _risk_profile(user_risk_pct)
    adaptive_conf_delta = int((adaptive_overrides or {}).get("conf_delta", 0) or 0)
    adaptive_vol_delta = float((adaptive_overrides or {}).get("volume_min_ratio_delta", 0.0) or 0.0)
    min_confidence = int(max(0, min(100, config["min_confidence"] + adaptive_conf_delta)))
    atr_multiplier = config["atr_multiplier"]

    try:
        # Extract OHLCV from candles
        opens = [float(c[1]) for c in candles_1h]
        highs = [float(c[2]) for c in candles_1h]
        lows = [float(c[3]) for c in candles_1h]
        closes = [float(c[4]) for c in candles_1h]
        volumes = [float(c[5]) for c in candles_1h]

        current_price = closes[-1]

        # 1. Support/Resistance Detection
        try:
            from app.analysis.range_analyzer import RangeAnalyzer
            ra = RangeAnalyzer()
            sr_result = ra.analyze(highs[-50:], lows[-50:])

            if sr_result:
                support = sr_result.get('support_level', current_price * 0.97)
                resistance = sr_result.get('resistance_level', current_price * 1.03)
                near_sr = (abs(current_price - support) / support <= 0.01 or
                          abs(current_price - resistance) / resistance <= 0.01)
            else:
                support = current_price * 0.97
                resistance = current_price * 1.03
                near_sr = False
        except Exception as e:
            logger.debug(f"[Confluence] S/R analysis failed: {e}")
            support = current_price * 0.97
            resistance = current_price * 1.03
            near_sr = False

        # 2. RSI Extremes
        try:
            from app.rsi_divergence_detector import RSIDivergenceDetector
            rsi_detector = RSIDivergenceDetector()
            rsi_values = rsi_detector._calculate_rsi_series(closes)

            if rsi_values:
                last_rsi = rsi_values[-1]
                is_rsi_extreme = last_rsi < 30 or last_rsi > 70
            else:
                last_rsi = 50.0
                is_rsi_extreme = False
        except Exception as e:
            logger.debug(f"[Confluence] RSI detection failed: {e}")
            last_rsi = _calc_rsi(closes)
            is_rsi_extreme = last_rsi < 30 or last_rsi > 70

        # 3. Volume Spike
        vol_ma = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        confluence_vol_ratio = 1.5 + max(0.0, adaptive_vol_delta)
        vol_spike = volumes[-1] > vol_ma * confluence_vol_ratio if vol_ma > 0 else False

        # 4. Market Regime (Trending Check)
        atr = _calc_atr(highs[-30:], lows[-30:], closes[-30:], 14)
        atr_pct = (atr / current_price * 100) if current_price > 0 else 0
        is_trending = atr_pct > 0.3  # > 0.3% = trending

        # 5. Trend Alignment (Price > MA50)
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sum(closes) / len(closes)
        price_above_ma = current_price > ma50

        # Confluence Scoring
        score = 0
        reasons = []

        if near_sr:
            score += 30
            reasons.append("S/R bounce")

        if is_rsi_extreme:
            rsi_dir = "Oversold" if last_rsi < 30 else "Overbought"
            score += 25
            reasons.append(f"RSI {rsi_dir} ({last_rsi:.0f})")

        if vol_spike:
            score += 20
            reasons.append("Volume spike")

        if is_trending:
            score += 15
            reasons.append(f"Trend (ATR {atr_pct:.2f}%)")

        if price_above_ma:
            score += 10
            reasons.append("Above MA50")

        # Check minimum confluence score (adaptive)
        if score < min_confidence:
            logger.debug(
                f"[Confluence] {symbol} score={score} < {min_confidence} "
                f"(risk={user_risk_pct}%) — insufficient confluence"
            )
            return None

        # Direction: LONG if RSI < 30, SHORT if RSI > 70, else LONG by default
        direction = 'LONG' if last_rsi < 30 else ('SHORT' if last_rsi > 70 else 'LONG')

        # Calculate TP with ATR scaling (adaptive)
        if direction == 'LONG':
            entry = support
            tp1 = entry + (atr * 0.75 * atr_multiplier)
            tp2 = entry + (atr * 1.25 * atr_multiplier)
            sl = support - (atr * 0.5)
        else:
            entry = resistance
            tp1 = entry - (atr * 0.75 * atr_multiplier)
            tp2 = entry - (atr * 1.25 * atr_multiplier)
            sl = resistance + (atr * 0.5)

        # Validate R:R ratio (minimum 1:1.5)
        rr = abs(tp1 - entry) / abs(entry - sl) if (entry - sl) != 0 else 0
        if rr < 1.0:
            logger.debug(f"[Confluence] {symbol} RR {rr:.2f} < 1.0 — weak setup")
            return None

        logger.info(
            f"[Confluence] {symbol} {direction} — conf={score} entry={entry:.4f} "
            f"tp1={tp1:.4f} sl={sl:.4f} RR={rr:.2f} | {' + '.join(reasons)}"
        )

        return {
            "symbol": symbol,
            "side": direction,
            "confidence": score,
            "entry_price": entry,
            "tp1": tp1,
            "tp2": tp2,
            "sl": sl,
            "rr_ratio": rr,
            "atr_pct": atr_pct,
            "vol_ratio": volumes[-1] / vol_ma if vol_ma > 0 else 1.0,
            "reasons": reasons,
            "market_structure": "uptrend" if current_price > ma50 else "downtrend",
            "trend_1h": direction,
            "rsi_15": round(last_rsi, 1),
            "rsi_1h": round(last_rsi, 1),
            "btc_is_sideways": False if btc_bias is None else (btc_bias.get("strength", 0) < 50),
        }

    except Exception as e:
        logger.warning(f"[Confluence] Signal generation failed for {symbol}: {e}", exc_info=True)
        return None


# ─────────────────────────────────────────────
#  Professional Signal Engine (Hybrid Mode)
# ─────────────────────────────────────────────
def _compute_signal_pro(
    base_symbol: str,
    btc_bias: Optional[Dict] = None,
    user_risk_pct: float = 1.0,
    adaptive_overrides: Optional[Dict[str, Any]] = None,
    stale_cooldown_user_id: Optional[int] = None,
) -> Optional[Dict]:
    """
    Hybrid signal generation:
    - PRIMARY: Confluence-based multi-factor detection (S/R + RSI + Volume + Trend)
    - SECONDARY: SMC analysis for reversals and market structure
    - FILTER: BTC bias + volatility + risk alignment

    Adaptive thresholds based on user_risk_pct:
    - 0.25% (conservative): min conf 60, tight TPs (0.5×ATR)
    - 0.5% (moderate): min conf 50, standard TPs (0.75-1.5×ATR)
    - 0.75% (aggressive): min conf 45, wider TPs (1.25×ATR)
    - 1.0% (very aggressive): min conf 40, widest TPs (1.5×ATR)
    - >1.0% to 5.0% (amber-red risk zone): progressively lower min conf, wider TPs
    """
    symbol = base_symbol.upper() + "USDT"
    cfg = dict(ENGINE_CONFIG)
    adaptive_conf_delta = int((adaptive_overrides or {}).get("conf_delta", 0) or 0)
    adaptive_vol_delta = float((adaptive_overrides or {}).get("volume_min_ratio_delta", 0.0) or 0.0)
    adaptive_ob_mode = str((adaptive_overrides or {}).get("ob_fvg_requirement_mode", "soft") or "soft")
    internal_min_confidence = int(max(0, min(100, _risk_profile(user_risk_pct)["min_confidence"] + adaptive_conf_delta)))
    cfg["volume_spike_min"] = max(1.0, cfg["volume_spike_min"] + adaptive_vol_delta)
    
    # ── BTC Bias Filter ──────────────────────────────────────
    btc_is_sideways = False
    if btc_bias:
        btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
        btc_strength = btc_bias.get("strength", 0)
        btc_is_sideways = (btc_bias_dir == "NEUTRAL" or btc_strength < 50)

    # Only skip altcoins if BTC is VERY weak (strength < 40)
    if base_symbol.upper() != "BTC" and btc_bias and btc_bias.get("strength", 100) < 40:
        logger.info(
            f"[Signal] {symbol} SKIPPED — BTC very weak "
            f"(bias={btc_bias.get('bias','?')} strength={btc_bias.get('strength',0)}%)"
        )
        return None

    try:
        from app.providers.alternative_klines_provider import alternative_klines_provider

        # ── Data fetch: 1H (primary) + 15M (secondary) ───────────────
        klines_1h  = alternative_klines_provider.get_klines(base_symbol.upper(), interval='1h',  limit=100)
        klines_15m = alternative_klines_provider.get_klines(base_symbol.upper(), interval='15m', limit=60)

        if not klines_1h or len(klines_1h) < 50:
            logger.warning(f"[Signal] {symbol} insufficient 1H data")
            return None
        if not klines_15m or len(klines_15m) < 30:
            logger.warning(f"[Signal] {symbol} insufficient 15M data")
            return None

        # ── TRY CONFLUENCE SIGNAL FIRST (primary system) ───────────────
        # This uses multi-factor analysis with adaptive thresholds based on user risk
        confluence_signal = _generate_confluence_signal(
            symbol=symbol,
            candles_1h=klines_1h,
            user_risk_pct=user_risk_pct,
            btc_bias=btc_bias,
            adaptive_overrides=adaptive_overrides,
        )

        if confluence_signal and confluence_signal.get('confidence', 0) >= internal_min_confidence:
            # Confluence signal passed thresholds — use it with SMC enhancement
            logger.info(
                f"[Signal] {symbol} using CONFLUENCE signal "
                f"(conf={confluence_signal['confidence']}, risk={user_risk_pct}%)"
            )

            # Enhance with SMC analysis from 15M data (for reversal detection)
            sig = confluence_signal
            sig["is_confluence_based"] = True

            # Add BTC bias bonus to confidence if aligned
            if base_symbol.upper() != "BTC" and btc_bias:
                btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
                btc_strength = btc_bias.get("strength", 0)

                if (btc_bias_dir == "BULLISH" and sig["side"] == "LONG") or \
                   (btc_bias_dir == "BEARISH" and sig["side"] == "SHORT"):
                    bonus = int(btc_strength * 0.15)
                    sig["confidence"] += bonus
                    sig["reasons"].append(f"BTC {btc_bias_dir} aligned (+{bonus}%)")

            if not _signal_prices_pass_live_mark(
                symbol=symbol,
                side=sig.get("side", ""),
                entry_price=float(sig.get("entry_price", 0.0) or 0.0),
                tp1_price=float(sig.get("tp1", 0.0) or 0.0),
                sl_price=float(sig.get("sl", 0.0) or 0.0),
                stale_cooldown_user_id=stale_cooldown_user_id,
            ):
                return None

            return sig

        # ── FALLBACK: Original SMC-based signal system ────────────────
        # If confluence signal fails or is too weak, try the original system
        logger.debug(
            f"[Signal] {symbol} confluence signal failed/weak — falling back to SMC system "
            f"(conf={confluence_signal['confidence'] if confluence_signal else 0}, user_risk={user_risk_pct}%)"
        )

        # ── 1H: Trend direction ────────────────────────────────────────
        c1h = [float(k[4]) for k in klines_1h]
        h1h = [float(k[2]) for k in klines_1h]
        l1h = [float(k[3]) for k in klines_1h]
        v1h = [float(k[5]) for k in klines_1h]

        ema21_1h  = _calc_ema(c1h, 21)
        ema50_1h  = _calc_ema(c1h, 50)
        rsi_1h    = _calc_rsi(c1h)
        atr_1h    = _calc_atr(h1h, l1h, c1h, 14)
        price     = c1h[-1]
        atr_pct   = (atr_1h / price) * 100

        # Volatility filter
        if atr_pct < cfg["min_atr_pct"]:
            logger.info(f"[Signal] {symbol} ATR too low ({atr_pct:.2f}%) — market flat, skip")
            return None
        if atr_pct > cfg["max_atr_pct"]:
            logger.info(f"[Signal] {symbol} ATR too high ({atr_pct:.2f}%) — too volatile, skip")
            return None

        # 1H trend bias
        if price > ema21_1h > ema50_1h:
            trend_1h = "LONG"
        elif price < ema21_1h < ema50_1h:
            trend_1h = "SHORT"
        else:
            trend_1h = "NEUTRAL"
        
        # ── BTC Alignment Check (altcoin must follow BTC) ──────────────
        if base_symbol.upper() != "BTC" and btc_bias:
            btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
            
            # Altcoin trend must align with BTC bias
            if btc_bias_dir == "BULLISH" and trend_1h == "SHORT":
                logger.info(
                    f"[Signal] {symbol} SKIPPED — BTC bullish but {symbol} bearish "
                    f"(counter-trend not allowed)"
                )
                return None
            elif btc_bias_dir == "BEARISH" and trend_1h == "LONG":
                logger.info(
                    f"[Signal] {symbol} SKIPPED — BTC bearish but {symbol} bullish "
                    f"(counter-trend not allowed)"
                )
                return None

        # ── 15M: Entry trigger ─────────────────────────────────────────
        c15 = [float(k[4]) for k in klines_15m]
        h15 = [float(k[2]) for k in klines_15m]
        l15 = [float(k[3]) for k in klines_15m]
        v15 = [float(k[5]) for k in klines_15m]

        ema9_15   = _calc_ema(c15, 9)
        ema21_15  = _calc_ema(c15, 21)
        ema9_prev = _calc_ema(c15[:-1], 9)
        ema21_prev= _calc_ema(c15[:-1], 21)
        rsi_15    = _calc_rsi(c15)
        atr_15    = _calc_atr(h15, l15, c15, 14)
        vol_ratio = _calc_volume_ratio(v15)

        # ── SMC: Market structure (swing highs/lows) ───────────────────
        swing_highs, swing_lows = [], []
        w = 3
        for i in range(w, len(c15) - w):
            if h15[i] == max(h15[i - w:i + w + 1]):
                swing_highs.append(h15[i])
            if l15[i] == min(l15[i - w:i + w + 1]):
                swing_lows.append(l15[i])

        market_structure = "ranging"
        smc_bonus = 0
        smc_reasons = []

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                market_structure = "uptrend"
                smc_reasons.append("📈 BOS: HH+HL (Uptrend)")
                smc_bonus += 10
            elif swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
                market_structure = "downtrend"
                smc_reasons.append("📉 BOS: LH+LL (Downtrend)")
                smc_bonus += 10

        # Order Block detection
        for i in range(max(0, len(c15) - 15), len(c15) - 2):
            body_pct = abs(c15[i] - float(klines_15m[i][1])) / float(klines_15m[i][1]) * 100
            if body_pct > 0.8:
                if c15[i] > float(klines_15m[i][1]) and l15[i] <= price <= h15[i] * 1.003:
                    smc_reasons.append(f"🟩 Bullish OB: {l15[i]:.4f}–{h15[i]:.4f}")
                    smc_bonus += 8
                elif c15[i] < float(klines_15m[i][1]) and l15[i] * 0.997 <= price <= h15[i]:
                    smc_reasons.append(f"🟥 Bearish OB: {l15[i]:.4f}–{h15[i]:.4f}")
                    smc_bonus += 8

        # FVG detection
        for i in range(1, min(8, len(c15) - 1)):
            idx = len(c15) - 1 - i
            if idx < 2:
                break
            if l15[idx + 1] > h15[idx - 1] and h15[idx - 1] <= price <= l15[idx + 1]:
                smc_reasons.append(f"⬆️ Bullish FVG: {h15[idx-1]:.4f}–{l15[idx+1]:.4f}")
                smc_bonus += 6
                break
            elif h15[idx + 1] < l15[idx - 1] and h15[idx + 1] <= price <= l15[idx - 1]:
                smc_reasons.append(f"⬇️ Bearish FVG: {h15[idx+1]:.4f}–{l15[idx-1]:.4f}")
                smc_bonus += 6
                break

        # ── Signal decision: require 1H + 15M alignment ───────────────
        side = None
        confidence = 50
        reasons = []

        # EMA crossover on 15M
        ema_cross_long  = ema9_15 > ema21_15 and ema9_prev <= ema21_prev
        ema_cross_short = ema9_15 < ema21_15 and ema9_prev >= ema21_prev
        ema_trend_long  = ema9_15 > ema21_15
        ema_trend_short = ema9_15 < ema21_15

        if trend_1h == "LONG":
            if ema_cross_long:
                side = "LONG"; confidence = 75
                reasons.append(f"✅ 1H uptrend + 15M EMA cross LONG (RSI {rsi_15:.0f})")
            elif ema_trend_long and rsi_15 < 55:
                side = "LONG"; confidence = 68
                reasons.append(f"✅ 1H uptrend + 15M EMA aligned + RSI {rsi_15:.0f}")
        elif trend_1h == "SHORT":
            if ema_cross_short:
                side = "SHORT"; confidence = 75
                reasons.append(f"✅ 1H downtrend + 15M EMA cross SHORT (RSI {rsi_15:.0f})")
            elif ema_trend_short and rsi_15 > 45:
                side = "SHORT"; confidence = 68
                reasons.append(f"✅ 1H downtrend + 15M EMA aligned + RSI {rsi_15:.0f}")

        # Neutral 1H: only take if strong SMC confluence
        if side is None and smc_bonus >= 18:
            if ema_trend_long and market_structure == "uptrend":
                side = "LONG"; confidence = 65
                reasons.append(f"SMC confluence LONG (1H neutral)")
            elif ema_trend_short and market_structure == "downtrend":
                side = "SHORT"; confidence = 65
                reasons.append(f"SMC confluence SHORT (1H neutral)")

        if side is None:
            logger.info(f"[Signal] {symbol} no confluence — 1H={trend_1h}, struct={market_structure}")
            return None
        
        # ── BTC Bias Bonus (altcoin gets confidence boost if aligned) ──
        if base_symbol.upper() != "BTC" and btc_bias:
            btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
            btc_strength = btc_bias.get("strength", 0)
            
            if (btc_bias_dir == "BULLISH" and side == "LONG") or \
               (btc_bias_dir == "BEARISH" and side == "SHORT"):
                bonus = int(btc_strength * 0.15)  # Up to +15% confidence
                confidence += bonus
                reasons.append(f"🔥 BTC {btc_bias_dir} bias aligned (+{bonus}%)")

        # ── RSI filter: avoid overbought/oversold entries ──────────────
        if side == "LONG"  and rsi_15 > cfg["rsi_long_max"]:
            logger.info(f"[Signal] {symbol} LONG blocked — RSI {rsi_15:.0f} overbought")
            return None
        if side == "SHORT" and rsi_15 < cfg["rsi_short_min"]:
            logger.info(f"[Signal] {symbol} SHORT blocked — RSI {rsi_15:.0f} oversold")
            return None

        # ── Volume confirmation ────────────────────────────────────────
        if vol_ratio >= cfg["volume_spike_min"]:
            confidence += 5
            reasons.append(f"📊 Volume spike {vol_ratio:.1f}x")
        else:
            confidence -= 3  # penalize low volume

        # ── SMC bonus ─────────────────────────────────────────────────
        if market_structure == ("uptrend" if side == "LONG" else "downtrend"):
            confidence += smc_bonus
        elif market_structure == ("downtrend" if side == "LONG" else "uptrend"):
            confidence -= 8  # counter-trend penalty

        # ── Adaptive OB/FVG confluence requirement (high-risk + borderline entries) ──
        if adaptive_ob_mode == "required_when_risk_high":
            is_high_risk = _normalize_risk_pct(user_risk_pct, default=1.0) > 1.0
            is_borderline = confidence < (internal_min_confidence + 8)
            has_ob_fvg = any(("OB" in str(r)) or ("FVG" in str(r)) for r in smc_reasons)
            if is_high_risk and is_borderline and not has_ob_fvg:
                logger.info(
                    f"[Signal] {symbol} adaptive skip — high-risk borderline entry without OB/FVG "
                    f"(conf={confidence}, min_conf={internal_min_confidence}, user_risk={user_risk_pct}%)"
                )
                return None

        # ── ATR-based SL/TP (professional sizing) ─────────────────────
        # Use 1H ATR for SL/TP to avoid noise from 15M
        sl_dist  = atr_1h * cfg["atr_sl_multiplier"]
        tp1_dist = atr_1h * cfg["atr_tp1_multiplier"]   # R:R 1:2 — ambil 75%
        tp2_dist = atr_1h * cfg["atr_tp2_multiplier"]   # R:R 1:3 — sisa 25%

        if side == "LONG":
            sl  = price - sl_dist
            tp1 = price + tp1_dist
            tp2 = price + tp2_dist
        else:
            sl  = price + sl_dist
            tp1 = price - tp1_dist
            tp2 = price - tp2_dist

        # ── R:R validation (pakai TP1 sebagai basis minimum) ──────────
        rr = tp1_dist / sl_dist
        if rr < cfg["min_rr_ratio"]:
            logger.info(f"[Signal] {symbol} R:R {rr:.2f} < {cfg['min_rr_ratio']} — skip")
            return None

        # ── Candle manipulation filter (wick rejection) ───────────────
        # Skip entry jika candle terakhir punya wick dominan ke arah entry
        # Ini tanda manipulasi / stop hunt sebelum reversal
        last_open  = float(klines_15m[-1][1])
        last_close = c15[-1]
        last_high  = h15[-1]
        last_low   = l15[-1]
        candle_range = last_high - last_low
        if candle_range > 0:
            if side == "LONG":
                # Wick bawah besar = stop hunt ke bawah, tapi close di atas = OK
                # Wick atas besar = rejection dari atas = BAHAYA untuk LONG
                upper_wick = last_high - max(last_open, last_close)
                wick_ratio = upper_wick / candle_range
                if wick_ratio > cfg["wick_rejection_max"]:
                    logger.info(
                        f"[Signal] {symbol} LONG blocked — upper wick {wick_ratio:.0%} "
                        f"(manipulation candle, wait for clean close)"
                    )
                    return None
            else:  # SHORT
                # Wick bawah besar = rejection dari bawah = BAHAYA untuk SHORT
                lower_wick = min(last_open, last_close) - last_low
                wick_ratio = lower_wick / candle_range
                if wick_ratio > cfg["wick_rejection_max"]:
                    logger.info(
                        f"[Signal] {symbol} SHORT blocked — lower wick {wick_ratio:.0%} "
                        f"(manipulation candle, wait for clean close)"
                    )
                    return None

        confidence = int(min(max(confidence, 50), 95))
        if confidence < internal_min_confidence:
            logger.info(
                f"[Signal] {symbol} confidence {confidence}% < internal_min_conf {internal_min_confidence}% "
                f"(adaptive conf_delta={adaptive_conf_delta})"
            )
            return None

        if not _signal_prices_pass_live_mark(
            symbol=symbol,
            side=side,
            entry_price=price,
            tp1_price=tp1,
            sl_price=sl,
            stale_cooldown_user_id=stale_cooldown_user_id,
        ):
            return None

        logger.info(
            f"[Signal] {symbol} {side} conf={confidence}% "
            f"entry={price:.4f} sl={sl:.4f} tp={tp1:.4f} "
            f"RR={rr:.1f} ATR={atr_pct:.2f}% vol={vol_ratio:.1f}x "
            f"(adaptive conf_delta={adaptive_conf_delta} vol_delta={adaptive_vol_delta:.2f} ob_mode={adaptive_ob_mode})"
        )

        return {
            "symbol":           symbol,
            "side":             side,
            "confidence":       confidence,
            "entry_price":      price,
            "tp1":              round(tp1, 6),
            "tp2":              round(tp2, 6),
            "sl":               round(sl, 6),
            "rr_ratio":         round(rr, 2),
            "atr_pct":          round(atr_pct, 2),
            "vol_ratio":        round(vol_ratio, 2),
            "reasons":          reasons + smc_reasons,
            "market_structure": market_structure,
            "trend_1h":         trend_1h,
            "rsi_15":           round(rsi_15, 1),
            "rsi_1h":           round(rsi_1h, 1),
            "btc_is_sideways":  btc_is_sideways,
        }

    except Exception as e:
        logger.warning(f"_compute_signal_pro error {base_symbol}: {e}", exc_info=True)
        return None


# ─────────────────────────────────────────────
#  Engine lifecycle
# ─────────────────────────────────────────────
def is_running(user_id: int) -> bool:
    uid = int(user_id)
    t = _running_tasks.get(uid)
    if t is None or t.done():
        return False
    components = _mixed_component_tasks.get(uid)
    if components:
        swing_task = components.get("swing")
        scalp_task = components.get("scalp")
        return bool(
            swing_task
            and not swing_task.done()
            and scalp_task
            and not scalp_task.done()
        )
    return True


async def _set_engine_active_flag(user_id: int, active: bool) -> None:
    try:
        from app.supabase_repo import _client
        s = _client()
        await asyncio.to_thread(
            lambda: s.table("autotrade_sessions").upsert({
                "telegram_id": int(user_id),
                "engine_active": bool(active)
            }, on_conflict="telegram_id").execute()
        )
    except Exception as e:
        logger.warning(f"[Engine:{user_id}] Failed to update engine_active flag: {e}")


def _clear_runtime_state(user_id: int) -> None:
    uid = int(user_id)
    _running_tasks.pop(uid, None)
    _mixed_component_tasks.pop(uid, None)
    _runtime_modes.pop(uid, None)
    _scalping_engines.pop(uid, None)


def _mark_engine_inactive_if_stopped_sync(user_id: int) -> None:
    try:
        from app.supabase_repo import _client
        s = _client()
        sess = s.table("autotrade_sessions").select("status").eq(
            "telegram_id", int(user_id)
        ).limit(1).execute()
        current_status = (sess.data or [{}])[0].get("status", "")
        if current_status == "stopped":
            s.table("autotrade_sessions").upsert({
                "telegram_id": int(user_id),
                "engine_active": False
            }, on_conflict="telegram_id").execute()
    except Exception as e:
        logger.warning(f"[Engine:{user_id}] Failed to update engine_active flag: {e}")


def _log_task_result(user_id: int, task: asyncio.Task, label: str) -> None:
    if task.cancelled():
        logger.info(f"[AutoTrade:{user_id}] {label} cancelled")
        return
    exc = task.exception()
    if exc:
        logger.error(f"[AutoTrade:{user_id}] {label} crashed: {exc}", exc_info=exc)


async def _run_mixed_supervisor(
    user_id: int,
    swing_task: asyncio.Task,
    scalp_task: asyncio.Task,
) -> None:
    """
    Mixed runtime supervisor.
    Ends (and tears down sibling task) when either component ends.
    """
    tasks: Set[asyncio.Task] = {swing_task, scalp_task}
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for pending_task in pending:
            pending_task.cancel()
        for pending_task in pending:
            try:
                await pending_task
            except asyncio.CancelledError:
                pass
            except Exception:
                pass
        first_done = next(iter(done)) if done else None
        if first_done is not None:
            await first_done
    finally:
        for child in tasks:
            if not child.done():
                child.cancel()


async def _stop_engine_locked(user_id: int, mark_inactive: bool) -> None:
    uid = int(user_id)
    current = asyncio.current_task()
    primary_task = _running_tasks.get(uid)
    component_tasks = _mixed_component_tasks.get(uid, {})
    current_is_component = any(task is current for task in component_tasks.values())

    tasks_to_cancel: List[asyncio.Task] = []
    seen: Set[int] = set()
    for task in [primary_task, *component_tasks.values()]:
        if task is None:
            continue
        if task.done():
            continue
        tid = id(task)
        if tid in seen:
            continue
        seen.add(tid)
        tasks_to_cancel.append(task)

    for task in tasks_to_cancel:
        if task is current:
            logger.info(f"[Engine:{uid}] stop requested from current task, using graceful self-stop")
            continue
        task.cancel()

    for task in tasks_to_cancel:
        if task is current:
            continue
        # Avoid awaiting the mixed supervisor from inside one of its child tasks,
        # otherwise cancellation can self-interrupt this stop path.
        if current_is_component and task is primary_task:
            continue
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=12.0)
        except asyncio.TimeoutError:
            logger.warning(f"[Engine:{uid}] stop timeout waiting cancelled task")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"[Engine:{uid}] stop wait raised: {e}")

    if tasks_to_cancel:
        logger.info(f"AutoTrade stopped for user {uid}")

    _clear_runtime_state(uid)

    try:
        cleared = await _get_coordinator().clear_all_pending_without_position_for_user(
            int(uid), reason="engine_stop_cleanup"
        )
        if cleared:
            logger.warning(f"[Engine:{uid}] Cleared {cleared} pending lock(s) during stop cleanup")
    except Exception as e:
        logger.warning(f"[Engine:{uid}] stop cleanup pending clear failed: {e}")

    if mark_inactive:
        await _set_engine_active_flag(uid, False)


async def stop_engine_async(user_id: int, mark_inactive: bool = True) -> None:
    lock = _get_lifecycle_lock(int(user_id))
    async with lock:
        await _stop_engine_locked(int(user_id), mark_inactive=mark_inactive)


def stop_engine(user_id: int):
    """
    Backward-compatible sync wrapper.
    Schedules stop on the running loop when available.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(stop_engine_async(user_id, mark_inactive=True))
    except RuntimeError:
        asyncio.run(stop_engine_async(user_id, mark_inactive=True))


async def start_engine_async(bot, user_id: int, api_key: str, api_secret: str,
                             amount: float, leverage: int, notify_chat_id: int,
                             is_premium: bool = False, silent: bool = False, exchange_id: str = "bitunix"):
    lock = _get_lifecycle_lock(int(user_id))
    async with lock:
        # Restart path: wait for full stop + cleanup before new task starts.
        await _stop_engine_locked(int(user_id), mark_inactive=False)
    
    # Load trading mode
    from app.trading_mode_manager import TradingModeManager, TradingMode
    trading_mode = TradingModeManager.get_mode(user_id)
    
    # Get exchange client
    from app.exchange_registry import get_client
    client = get_client(exchange_id, api_key, api_secret)

    uid = int(user_id)

    def _component_done_cb(label: str):
        def _cb(task: asyncio.Task):
            _log_task_result(uid, task, label)
        return _cb

    def _primary_done_cb(task: asyncio.Task):
        _mark_engine_inactive_if_stopped_sync(uid)
        _log_task_result(uid, task, "runtime")
        _clear_runtime_state(uid)

    # Start appropriate engine based on mode
    if trading_mode == TradingMode.SCALPING:
        from app.scalping_engine import ScalpingEngine
        engine = ScalpingEngine(
            user_id=user_id,
            client=client,
            bot=bot,
            notify_chat_id=notify_chat_id,
        )
        task = asyncio.create_task(engine.run())
        _runtime_modes[uid] = TradingMode.SCALPING.value
        _mixed_component_tasks.pop(uid, None)
        _scalping_engines[uid] = engine
        logger.info(f"[AutoTrade:{user_id}] Started SCALPING engine (exchange={exchange_id})")
    elif trading_mode == TradingMode.MIXED:
        from app.scalping_engine import ScalpingEngine

        engine = ScalpingEngine(
            user_id=user_id,
            client=client,
            bot=bot,
            notify_chat_id=notify_chat_id,
            mixed_mode=True,
            startup_notification=False,
        )
        swing_task = asyncio.create_task(
            _trade_loop(
                bot,
                user_id,
                api_key,
                api_secret,
                amount,
                leverage,
                notify_chat_id,
                is_premium,
                True,  # suppress component startup notification
                exchange_id,
                mixed_mode=True,
                symbol_owner="swing",
            )
        )
        scalp_task = asyncio.create_task(engine.run())
        swing_task.add_done_callback(_component_done_cb("mixed_swing_component"))
        scalp_task.add_done_callback(_component_done_cb("mixed_scalp_component"))

        task = asyncio.create_task(_run_mixed_supervisor(uid, swing_task=swing_task, scalp_task=scalp_task))
        _mixed_component_tasks[uid] = {"swing": swing_task, "scalp": scalp_task}
        _runtime_modes[uid] = TradingMode.MIXED.value
        _scalping_engines[uid] = engine
        logger.info(f"[AutoTrade:{user_id}] Started MIXED engine (parallel swing+scalp) (exchange={exchange_id})")
    else:
        # Existing swing trading logic
        task = asyncio.create_task(
            _trade_loop(
                bot,
                user_id,
                api_key,
                api_secret,
                amount,
                leverage,
                notify_chat_id,
                is_premium,
                silent,
                exchange_id,
                mixed_mode=False,
                symbol_owner="swing",
            )
        )
        _runtime_modes[uid] = TradingMode.SWING.value
        _mixed_component_tasks.pop(uid, None)
        _scalping_engines.pop(uid, None)
        logger.info(f"[AutoTrade:{user_id}] Started SWING engine (exchange={exchange_id}, amount={amount}, leverage={leverage}x, premium={is_premium})")

    task.add_done_callback(_primary_done_cb)
    _running_tasks[uid] = task
    
    # Update engine_active flag in database
    await _set_engine_active_flag(user_id, True)

    if trading_mode == TradingMode.MIXED and not silent:
        try:
            assignments = await get_mixed_pair_assignments(
                user_id=uid,
                limit=10,
                fallback_pairs=list(ENGINE_CONFIG.get("symbols", [])),
                logger_override=logger,
                label=f"[Engine:{uid}]",
            )
            swing_pairs = list(assignments.get("swing") or [])
            scalp_pairs = list(assignments.get("scalp") or [])
            swing_preview = ", ".join(swing_pairs[:5]) if swing_pairs else "-"
            scalp_preview = ", ".join(scalp_pairs[:5]) if scalp_pairs else "-"
            await bot.send_message(
                chat_id=notify_chat_id,
                text=(
                    "🤖 <b>Mixed Engine Active!</b>\n\n"
                    "⚖️ <b>Mode: Mixed (Top 10 Auto-Routed)</b>\n"
                    "• Routing cadence: <b>10 minutes (sticky)</b>\n"
                    "• Concurrent cap: <b>Swing 4 + Scalping 4</b>\n"
                    f"• Base leverage setting: <b>{int(leverage)}x</b>\n"
                    "• Applied leverage: <b>Auto max-safe per pair</b>\n\n"
                    f"📊 Swing pairs ({len(swing_pairs)}): <code>{escape(swing_preview)}</code>\n"
                    f"⚡ Scalping pairs ({len(scalp_pairs)}): <code>{escape(scalp_preview)}</code>\n\n"
                    "Bot will keep re-evaluating top-volume assignments on cadence."
                ),
                parse_mode="HTML",
            )
        except Exception as mixed_notify_err:
            logger.warning(f"[AutoTrade:{uid}] Mixed startup notification failed: {mixed_notify_err}")
    return task


def start_engine(bot, user_id: int, api_key: str, api_secret: str,
                 amount: float, leverage: int, notify_chat_id: int,
                 is_premium: bool = False, silent: bool = False, exchange_id: str = "bitunix"):
    """
    Backward-compatible sync wrapper.
    Schedules async serialized start.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            start_engine_async(
                bot=bot,
                user_id=user_id,
                api_key=api_key,
                api_secret=api_secret,
                amount=amount,
                leverage=leverage,
                notify_chat_id=notify_chat_id,
                is_premium=is_premium,
                silent=silent,
                exchange_id=exchange_id,
            )
        )
    except RuntimeError:
        asyncio.run(
            start_engine_async(
                bot=bot,
                user_id=user_id,
                api_key=api_key,
                api_secret=api_secret,
                amount=amount,
                leverage=leverage,
                notify_chat_id=notify_chat_id,
                is_premium=is_premium,
                silent=silent,
                exchange_id=exchange_id,
            )
        )


# ─────────────────────────────────────────────
#  Main trading loop
# ─────────────────────────────────────────────
async def _trade_loop(bot, user_id: int, api_key: str, api_secret: str,
                      amount: float, leverage: int, notify_chat_id: int,
                      is_premium: bool = False, silent: bool = False, exchange_id: str = "bitunix",
                      mixed_mode: bool = False, symbol_owner: str = "swing"):
    import sys, os
    bismillah_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if bismillah_root not in sys.path:
        sys.path.insert(0, bismillah_root)

    from app.exchange_registry import get_client, get_exchange
    from app.supabase_repo import _client
    from app.bitunix_ws_pnl import start_pnl_tracker, stop_pnl_tracker, is_tracking
    from app.adaptive_confluence import (
        refresh_global_adaptive_state,
        get_adaptive_overrides,
    )
    from app.win_playbook import (
        refresh_global_win_playbook_state,
        get_win_playbook_snapshot,
        compute_playbook_match_from_reasons,
    )
    from app.sideways_governor import (
        refresh_sideways_governor_state,
        get_sideways_governor_snapshot,
        resolve_dynamic_max_hold_seconds,
    )
    from app.confidence_adaptation import (
        apply_confidence_risk_brake,
        get_confidence_adaptation,
        get_confidence_adaptation_snapshot,
        refresh_global_confidence_adaptation_state,
    )

    # Get exchange-specific client
    ex_cfg = get_exchange(exchange_id)
    client = get_client(exchange_id, api_key, api_secret)
    cfg    = ENGINE_CONFIG

    logger.info(f"[Engine:{user_id}] Using exchange: {ex_cfg['name']} ({exchange_id})")
    await sanitize_startup_pending_locks(
        _get_coordinator(),
        int(user_id),
        logger,
        label=f"[Engine:{user_id}]",
    )

    # Premium user: RR 1:3 dengan dual TP (75%/25%) + breakeven SL
    # Free user: RR 1:2 single TP (behaviour lama)
    if is_premium:
        cfg = dict(ENGINE_CONFIG)  # copy agar tidak mutate global
        # Dual TP sudah di ENGINE_CONFIG, tidak perlu override
        # Flag untuk aktifkan dual TP logic
    _dual_tp_enabled = is_premium

    trades_today      = 0
    last_trade_date   = date.today()
    had_open_position = False
    daily_pnl_usdt    = 0.0   # track realized PnL for circuit breaker
    daily_loss_limit  = amount * cfg["daily_loss_limit"]

    # Init TP1 tracker untuk user ini
    if user_id not in _tp1_hit_positions:
        _tp1_hit_positions[user_id] = set()

    def calc_qty(symbol: str, notional: float, price: float) -> float:
        """Legacy position sizing (fixed margin) - kept for backward compatibility"""
        precision = QTY_PRECISION.get(symbol, 3)
        qty = round(notional / price, precision)
        min_qty = 10 ** (-precision) if precision > 0 else 1
        return qty if qty >= min_qty else 0.0
    
    async def calc_qty_with_risk(
        symbol: str,
        entry: float,
        sl: float,
        leverage: int,
        effective_risk_pct_override: Optional[float] = None,
    ) -> tuple:
        """
        Calculate position size using risk-based sizing with EQUITY (not balance).

        CRITICAL: Uses equity = balance + unrealized_pnl for accurate risk calculation.
        If SL hits, user loses EXACTLY risk_percentage of equity.
        Leverage is used for margin calculation, NOT to amplify position size.

        Formula:
        1. Equity = Balance + Unrealized PnL
        2. Risk Amount = Equity * Risk%
        3. SL Distance = |Entry - SL|
        4. Position Size (in base currency) = Risk Amount / SL Distance
        5. Margin Required = (Position Size * Entry Price) / Leverage

        Returns:
            (qty, used_risk_sizing): tuple of (quantity, whether risk sizing was used)
        """
        try:
            # Runtime-only risk overlay can override base risk for sizing.
            risk_pct = _normalize_effective_risk_pct(
                effective_risk_pct_override if effective_risk_pct_override is not None else user_risk_pct,
                default=user_risk_pct,
            )

            # Get account info: available, frozen, and unrealized PnL
            acc_result = await asyncio.to_thread(client.get_account_info)
            if not acc_result.get('success'):
                raise Exception(f"Account info fetch failed: {acc_result.get('error')}")

            # Total balance = available (free) + frozen (in positions)
            available = float(acc_result.get('available', 0) or 0)
            frozen = float(acc_result.get('frozen', 0) or 0)
            balance = available + frozen

            # Unrealized P&L from all positions
            unrealized_pnl = float(acc_result.get('total_unrealized_pnl', 0) or 0)

            # Equity = Total Balance + Unrealized P&L
            equity = balance + unrealized_pnl

            if equity <= 0:
                raise Exception(
                    f"Invalid equity: available={available:.2f} + frozen={frozen:.2f} + "
                    f"unrealized={unrealized_pnl:.2f} = {equity:.2f}"
                )
            
            # Calculate risk amount using EQUITY (not balance)
            risk_amount = equity * (risk_pct / 100)

            # Calculate SL distance
            sl_distance = abs(entry - sl)
            if sl_distance <= 0:
                raise Exception(f"Invalid SL distance: {sl_distance}")

            # Calculate position size: how much can we trade if SL distance hits
            # position_size = risk_amount / sl_distance
            position_size = risk_amount / sl_distance

            # Round to exchange precision
            precision = QTY_PRECISION.get(symbol, 3)
            qty = round(position_size, precision)

            # Validate minimum quantity
            min_qty = 10 ** (-precision) if precision > 0 else 1
            if qty < min_qty:
                raise Exception(f"Quantity {qty} below minimum {min_qty}")

            # Calculate margin required for this position
            position_value = qty * entry
            margin_required = position_value / leverage

            # Validate margin available (should not exceed 95% of balance for safety)
            max_margin = balance * 0.95  # Keep 5% buffer
            if margin_required > max_margin:
                raise Exception(
                    f"Insufficient margin: need ${margin_required:.2f}, "
                    f"balance=${balance:.2f}, max_usable=${max_margin:.2f}. "
                    f"Reduce risk % or increase balance."
                )

            logger.info(
                f"[RiskCalc:{user_id}] {symbol} - "
                f"Equity=${equity:.2f} (Available=${available:.2f} + Frozen=${frozen:.2f} + "
                f"Unrealized=${unrealized_pnl:.2f}), "
                f"Risk={risk_pct}% (~${risk_amount:.2f}), "
                f"Entry=${entry:.2f}, SL=${sl:.2f} (Distance={sl_distance:.2f}), "
                f"Position_Size={position_size:.8f}, Qty={qty}, "
                f"Position_Value=${position_value:.2f}, "
                f"Margin_Required=${margin_required:.2f}/{max_margin:.2f} (Leverage={leverage}x), "
                f"Max_Loss_If_SL=${risk_amount:.2f}"
            )
            
            return qty, True  # Success - used risk-based sizing
            
        except Exception as e:
            logger.warning(
                f"[RiskSizing:{user_id}] FAILED: {e} - Falling back to fixed margin system"
            )
            
            # FALLBACK: Use old fixed margin system for backward compatibility
            qty_fallback = calc_qty(symbol, amount * leverage, entry)
            
            logger.info(
                f"[RiskSizing:{user_id}] FALLBACK - Using fixed margin: "
                f"amount=${amount}, leverage={leverage}x, qty={qty_fallback}"
            )
            
            return qty_fallback, False  # Fallback used

    # ── Fetch user's risk_per_trade setting ───────────────────────────
    user_risk_pct = 1.0  # Default (1% risk)
    try:
        from app.supabase_repo import get_risk_per_trade
        fetched_risk = get_risk_per_trade(user_id)

        if fetched_risk is not None:
            user_risk_pct = _normalize_risk_pct(fetched_risk, default=1.0)
            logger.info(f"[Engine:{user_id}] Loaded user risk_per_trade: {user_risk_pct}%")
    except Exception as e:
        logger.warning(f"[Engine:{user_id}] Failed to load user risk_pct, using default 1.0%: {e}")

    risk_profile_cfg = _risk_profile(user_risk_pct)
    dynamic_min_confidence = int(risk_profile_cfg["min_confidence"])
    cfg = dict(cfg)
    cfg["min_confidence"] = dynamic_min_confidence
    adaptive_state: Dict[str, Any] = {
        "conf_delta": 0,
        "volume_min_ratio_delta": 0.0,
        "ob_fvg_requirement_mode": "soft",
        "strategy_loss_rate": 0.0,
        "ops_reconcile_rate": 0.0,
        "trade_count_per_day": 0.0,
        "strategy_sample_size": 0,
        "decision_reason": "bootstrap",
        "updated_at": None,
    }
    adaptive_next_refresh_ts = 0.0
    sideways_governor_state: Dict[str, Any] = {
        "mode": "normal",
        "decision_reason": "bootstrap",
        "dynamic_hold_non_sideways_seconds": int(cfg.get("swing_max_hold_default_seconds", 1800) or 1800),
        "symbol_non_sideways_hold_seconds": {},
    }
    sideways_governor_next_refresh_ts = 0.0
    win_playbook_state: Dict[str, Any] = {
        "risk_overlay_pct": 0.0,
        "rolling_win_rate": 0.0,
        "rolling_expectancy": 0.0,
        "sample_size": 0,
        "active_tags": [],
        "guardrails_healthy": False,
    }
    win_playbook_next_refresh_ts = 0.0
    confidence_adapt_state: Dict[str, Any] = {
        "enabled": False,
        "modes": {"swing": {"sample_size": 0, "active_adaptations": []}},
    }
    confidence_adapt_next_refresh_ts = 0.0
    stale_reconcile_enabled = _env_flag("STALE_RECONCILE_ENABLED", True)
    swing_stale_reconcile_interval_seconds = max(
        30,
        int(float(os.getenv("SWING_STALE_RECONCILE_INTERVAL_SECONDS", "300") or 300)),
    )
    swing_stale_reconcile_next_ts = 0.0

    async def _run_swing_stale_reconcile(reconcile_reason: str) -> Dict[str, Any]:
        from app.trade_history import inspect_open_trade_drift, apply_open_trade_reconcile

        drift = await asyncio.to_thread(
            inspect_open_trade_drift,
            user_id,
            client,
            "swing",
        )
        result = await asyncio.to_thread(
            apply_open_trade_reconcile,
            user_id,
            client,
            "swing",
            drift,
        )
        marker = (
            f"[Engine:{user_id}] stale_reconcile trade_type=swing "
            f"reconcile_reason={reconcile_reason} "
            f"db_open_count={int(result.get('db_open_count', 0) or 0)} "
            f"exchange_open_count={int(result.get('exchange_open_count', 0) or 0)} "
            f"healed_count={int(result.get('healed_count', 0) or 0)} "
            f"stale_symbols={list(result.get('stale_symbols') or [])}"
        )
        if not bool(result.get("exchange_fetch_ok", True)):
            logger.warning(f"{marker} exchange_fetch_ok=false error={result.get('exchange_error')}")
        else:
            logger.info(marker)
        return result

    try:
        await asyncio.to_thread(refresh_global_confidence_adaptation_state)
        confidence_adapt_state = await asyncio.to_thread(get_confidence_adaptation_snapshot)
    except Exception as conf_bootstrap_err:
        logger.warning(f"[Engine:{user_id}] Initial confidence adaptation load failed: {conf_bootstrap_err}")

    logger.info(
        f"[Engine:{user_id}] PRO ENGINE STARTED — symbols_mode=dynamic_top10_volume "
        f"{'(mixed_owner=swing) ' if mixed_mode else ''}"
        f"(bootstrap={cfg['symbols']}), min_conf={cfg['min_confidence']} (risk-profile dynamic), "
        f"min_rr={cfg['min_rr_ratio']}, user_risk={user_risk_pct}%, daily_loss_limit_DISABLED"
    )

    try:
        if not silent:
            await asyncio.sleep(1)
            await bot.send_message(
                chat_id=notify_chat_id,
                text=(
                    "🤖 <b>AutoTrade PRO Engine Active!</b>\n\n"
                    f"📊 Strategy: Confluence-based multi-factor detection\n"
                    f"🎯 Min Confidence: {cfg['min_confidence']}% (risk-profile dynamic)\n"
                    f"💰 Risk Per Trade: {user_risk_pct}%\n"
                    + (
                        f"⚖️ R:R: 1:2 (TP1, 75%) → 1:3 (TP2, 25%)\n"
                        f"🔒 Breakeven: SL moves to entry after TP1 hit\n"
                        f"👑 Mode: <b>PREMIUM</b>\n"
                        if is_premium else
                        f"⚖️ Min R:R Ratio: 1:{cfg['min_rr_ratio']}\n"
                    )
                    + f"📈 Mode: <b>Unlimited trades/day (no daily loss limit)</b>\n"
                    f"✅ Continuous trading enabled for opportunity maximization\n\n"
                    f"🧠 Adaptive conf delta: <b>{int(adaptive_state.get('conf_delta', 0)):+d}</b>\n"
                    f"🧠 Adaptive vol delta: <b>{float(adaptive_state.get('volume_min_ratio_delta', 0.0)):+.2f}</b>\n"
                    f"🛡️ Sideways governor mode: <b>{str(sideways_governor_state.get('mode', 'normal')).upper()}</b>\n"
                    f"🏆 Win playbook tags: <b>{len(win_playbook_state.get('active_tags', []) or [])}</b>\n"
                    f"⚡ Runtime risk overlay: <b>{float(win_playbook_state.get('risk_overlay_pct', 0.0)):+.2f}%</b>\n"
                    f"🎚️ Confidence adaptation: <b>{'ON' if bool(confidence_adapt_state.get('enabled', False)) else 'OFF'}</b>\n\n"
                    "High-probability setups only. Risk per trade: fixed dollar amount."
                ),
                parse_mode='HTML',
                reply_markup=_dashboard_keyboard()
            )
    except Exception as _startup_err:
        logger.warning(f"[Engine:{user_id}] Startup notification failed (non-fatal): {_startup_err}")

    if stale_reconcile_enabled:
        try:
            await _run_swing_stale_reconcile("startup")
            swing_stale_reconcile_next_ts = time.time() + float(swing_stale_reconcile_interval_seconds)
        except Exception as stale_err:
            logger.warning(f"[Engine:{user_id}] startup stale reconcile failed: {stale_err}")

    while True:
        try:
            now_ts = datetime.now(timezone.utc).timestamp()
            adaptive_next_refresh_ts, adaptive_state, adaptive_refreshed, adaptive_err = await refresh_runtime_snapshot(
                now_ts=now_ts,
                next_refresh_ts=adaptive_next_refresh_ts,
                refresh_fn=refresh_global_adaptive_state,
                snapshot_fn=get_adaptive_overrides,
                current_snapshot=adaptive_state,
                interval_sec=600.0,
            )
            if adaptive_refreshed:
                logger.info(
                    f"[Engine:{user_id}] Adaptive overlay refreshed — "
                    f"conf_delta={adaptive_state.get('conf_delta')} "
                    f"vol_delta={adaptive_state.get('volume_min_ratio_delta'):.2f} "
                    f"ob_mode={adaptive_state.get('ob_fvg_requirement_mode')} "
                    f"loss_rate={adaptive_state.get('strategy_loss_rate'):.3f} "
                    f"ops_rate={adaptive_state.get('ops_reconcile_rate'):.3f} "
                    f"sample={adaptive_state.get('strategy_sample_size')} "
                    f"decision={adaptive_state.get('decision_reason')}"
                )
            elif adaptive_err:
                logger.warning(f"[Engine:{user_id}] Adaptive refresh failed, using last state: {adaptive_err}")

            win_playbook_next_refresh_ts, win_playbook_state, playbook_refreshed, playbook_err = await refresh_runtime_snapshot(
                now_ts=now_ts,
                next_refresh_ts=win_playbook_next_refresh_ts,
                refresh_fn=refresh_global_win_playbook_state,
                snapshot_fn=get_win_playbook_snapshot,
                current_snapshot=win_playbook_state,
                interval_sec=600.0,
            )
            if playbook_refreshed:
                logger.info(
                    f"[Engine:{user_id}] Win playbook refreshed — "
                    f"sample={win_playbook_state.get('sample_size')} "
                    f"wr={float(win_playbook_state.get('rolling_win_rate', 0.0)):.3f} "
                    f"exp={float(win_playbook_state.get('rolling_expectancy', 0.0)):+.4f} "
                    f"overlay={float(win_playbook_state.get('risk_overlay_pct', 0.0)):.2f}% "
                    f"active_tags={len(win_playbook_state.get('active_tags', []) or [])} "
                    f"guardrails={bool(win_playbook_state.get('guardrails_healthy', False))}"
                )
            elif playbook_err:
                logger.warning(f"[Engine:{user_id}] Win playbook refresh failed, using last snapshot: {playbook_err}")

            confidence_adapt_next_refresh_ts, confidence_adapt_state, conf_adapt_refreshed, conf_adapt_err = await refresh_runtime_snapshot(
                now_ts=now_ts,
                next_refresh_ts=confidence_adapt_next_refresh_ts,
                refresh_fn=refresh_global_confidence_adaptation_state,
                snapshot_fn=get_confidence_adaptation_snapshot,
                current_snapshot=confidence_adapt_state,
                interval_sec=600.0,
            )
            if conf_adapt_refreshed:
                mode_state = ((confidence_adapt_state.get("modes") or {}).get("swing") or {})
                logger.info(
                    f"[Engine:{user_id}] Confidence adaptation refreshed — "
                    f"enabled={bool(confidence_adapt_state.get('enabled', False))} "
                    f"sample={int(mode_state.get('sample_size', 0) or 0)} "
                    f"active_buckets={len(mode_state.get('active_adaptations', []) or [])} "
                    f"top={((mode_state.get('top_bucket') or {}).get('bucket') or '-')}"
                )
            elif conf_adapt_err:
                logger.warning(f"[Engine:{user_id}] Confidence adaptation refresh failed, using last snapshot: {conf_adapt_err}")

            sideways_governor_next_refresh_ts, sideways_governor_state, governor_refreshed, governor_err = await refresh_runtime_snapshot(
                now_ts=now_ts,
                next_refresh_ts=sideways_governor_next_refresh_ts,
                refresh_fn=refresh_sideways_governor_state,
                snapshot_fn=get_sideways_governor_snapshot,
                current_snapshot=sideways_governor_state,
                interval_sec=600.0,
            )
            if governor_refreshed:
                logger.info(
                    f"[Engine:{user_id}] Sideways governor refreshed (swing non-sideways hook) — "
                    f"mode={sideways_governor_state.get('mode')} "
                    f"non_sideways_hold={sideways_governor_state.get('dynamic_hold_non_sideways_seconds')} "
                    f"reason={sideways_governor_state.get('decision_reason')}"
                )
            elif governor_err:
                logger.warning(f"[Engine:{user_id}] Sideways governor refresh failed, using last snapshot: {governor_err}")

            # ── Initialize btc_bias for this iteration ────────────────
            btc_bias = {"bias": "NEUTRAL", "strength": 0, "reasons": []}
            
            # ── Check if engine stop requested ────────────────────────
            try:
                if asyncio.current_task().cancelled():
                    logger.info(f"[Engine:{user_id}] Task cancelled, exiting loop")
                    break
            except Exception:
                pass  # Ignore check errors

            if await should_stop_engine(user_id, logger=logger, label=f"[Engine:{user_id}]"):
                logger.info(f"[Engine:{user_id}] Stop signal from Supabase, exiting loop")
                try:
                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text="🛑 <b>AutoTrade stopped.</b>\n\nUse /autotrade to restart.",
                        parse_mode='HTML',
                        reply_markup=_dashboard_keyboard()
                    )
                except Exception:
                    pass
                return

            if stale_reconcile_enabled and now_ts >= float(swing_stale_reconcile_next_ts or 0.0):
                try:
                    await _run_swing_stale_reconcile("periodic")
                except Exception as stale_err:
                    logger.warning(f"[Engine:{user_id}] periodic stale reconcile failed: {stale_err}")
                swing_stale_reconcile_next_ts = now_ts + float(swing_stale_reconcile_interval_seconds)
            
            # ── Reset harian ──────────────────────────────────────────
            today = date.today()
            if today != last_trade_date:
                trades_today    = 0
                daily_pnl_usdt  = 0.0
                last_trade_date = today
                logger.info(f"[Engine:{user_id}] New day — counters reset")

            # ── Daily loss tracking (no circuit breaker limit) ──────────
            # Track daily P&L for monitoring but allow continuous trading
            if daily_pnl_usdt <= -daily_loss_limit:
                logger.warning(
                    f"[Engine:{user_id}] Daily P&L: {daily_pnl_usdt:.2f} USDT "
                    f"(note: no circuit breaker, trading continues)"
                )
                # Note: Circuit breaker disabled per user request for opportunity maximization
                # Daily P&L tracking continues for monitoring purposes

            # ── Demo user: equity cap $50 ────────────────────────────
            from app.demo_users import is_demo_user, DEMO_BALANCE_LIMIT
            if is_demo_user(user_id):
                try:
                    acc_result = await asyncio.to_thread(client.get_account_info)
                    if acc_result.get('success'):
                        demo_available = float(acc_result.get('available', 0) or 0)
                        demo_frozen = float(acc_result.get('frozen', 0) or 0)
                        demo_balance = demo_available + demo_frozen
                        demo_unrealized = float(acc_result.get('total_unrealized_pnl', 0) or 0)
                        demo_equity = demo_balance + demo_unrealized
                        # Only stop if equity significantly exceeds limit (10% buffer)
                        if demo_equity > (DEMO_BALANCE_LIMIT * 1.1):
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    "⚠️ <b>Demo Limit Reached</b>\n\n"
                                    f"Your equity has exceeded the <b>${DEMO_BALANCE_LIMIT:.0f} demo limit</b>.\n\n"
                                    "This is a <b>special demo account</b> — the bot has been stopped automatically.\n\n"
                                    "To increase your equity limit, contact @yongdnf3 🙂"
                                ),
                                parse_mode='HTML'
                            )
                            await stop_engine_async(user_id, mark_inactive=True)
                            logger.info(f"[Engine:{user_id}] Demo user stopped: equity ${demo_equity:.2f} > ${DEMO_BALANCE_LIMIT:.0f}")
                            return
                except Exception as e:
                    logger.warning(f"[Engine:{user_id}] Failed to check demo equity: {e}")

            # ── Cek posisi terbuka ────────────────────────────────────
            pos_result     = await asyncio.to_thread(client.get_positions)
            open_positions = pos_result.get('positions', []) if pos_result.get('success') else []
            occupied_syms  = {p['symbol'] for p in open_positions}
            # ── Swing adaptive timeout protection + dynamic max-hold hooks ───────
            if open_positions and (
                bool(cfg.get("swing_dynamic_max_hold_enabled", False))
                or bool(cfg.get("swing_adaptive_timeout_protection_enabled", False))
            ):
                try:
                    from app.trade_history import (
                        get_open_trades,
                        close_open_trades_by_symbol,
                        build_loss_reasoning,
                        build_win_reasoning,
                    )
                    open_rows = await asyncio.to_thread(get_open_trades, user_id, "swing")
                    open_row_by_symbol = {
                        str(r.get("symbol") or "").upper(): r
                        for r in (open_rows or [])
                        if str(r.get("symbol") or "").upper()
                    }
                    timeout_state_user = _swing_timeout_state.setdefault(int(user_id), {})
                    for pos in open_positions:
                        symbol_open = str(pos.get("symbol") or "").upper()
                        if not symbol_open:
                            continue
                        db_row = open_row_by_symbol.get(symbol_open)
                        if not db_row:
                            continue
                        side_open = str(db_row.get("side") or pos.get("side") or "LONG").upper()
                        entry_open = float(db_row.get("entry_price") or 0)
                        if entry_open <= 0:
                            continue
                        qty_open = float(pos.get("qty") or pos.get("size") or db_row.get("qty") or 0)
                        if qty_open <= 0:
                            continue
                        mark_open = float(pos.get("mark_price") or pos.get("markPrice") or 0)
                        if mark_open <= 0:
                            ticker_res = await asyncio.to_thread(client.get_ticker, symbol_open)
                            if ticker_res.get("success"):
                                mark_open = float(
                                    ticker_res.get("mark_price")
                                    or ticker_res.get("last_price")
                                    or ticker_res.get("price")
                                    or 0
                                )
                        if mark_open <= 0:
                            continue
                        sl_open = float(db_row.get("sl_price") or 0)
                        if sl_open <= 0:
                            continue
                        opened_at_raw = str(db_row.get("opened_at") or "")
                        opened_at_ts = 0.0
                        try:
                            opened_txt = opened_at_raw.replace("Z", "+00:00")
                            opened_at_ts = datetime.fromisoformat(opened_txt).timestamp()
                        except Exception:
                            opened_at_ts = 0.0
                        if opened_at_ts <= 0:
                            continue
                        elapsed_open = max(0.0, time.time() - opened_at_ts)
                        hold_limit = int(cfg.get("swing_max_hold_default_seconds", 1800) or 1800)
                        if bool(cfg.get("swing_dynamic_max_hold_enabled", False)):
                            hold_limit = int(
                                resolve_dynamic_max_hold_seconds(
                                    symbol=symbol_open,
                                    is_sideways=False,
                                    snapshot=sideways_governor_state,
                                    default_non_sideways=int(cfg.get("swing_max_hold_default_seconds", 1800) or 1800),
                                )
                            )
                        if (
                            bool(cfg.get("swing_dynamic_max_hold_enabled", False))
                            and hold_limit > 0
                            and elapsed_open >= float(hold_limit)
                        ):
                            close_res = await asyncio.to_thread(client.close_position, symbol_open)
                            if close_res.get("success"):
                                raw_pnl = (mark_open - entry_open) if side_open == "LONG" else (entry_open - mark_open)
                                pnl_est = raw_pnl * qty_open
                                loss_reason = ""
                                win_metadata = None
                                if pnl_est < 0:
                                    near_flat_thr = float(cfg.get("swing_timeout_near_flat_usdt_threshold", 0.02) or 0.02)
                                    near_flat = abs(float(pnl_est)) <= near_flat_thr
                                    if near_flat:
                                        pnl_est = 0.0
                                    loss_reason = (
                                        "timeout_exit; timeout_protection=max_hold; "
                                        f"phase=late; near_flat={1 if near_flat else 0}; "
                                        f"pnl={float(pnl_est):+.6f}; symbol={symbol_open}; side={side_open}"
                                    )
                                else:
                                    match_meta = await asyncio.to_thread(
                                        compute_playbook_match_from_reasons,
                                        db_row.get("entry_reasons", []),
                                        win_playbook_state,
                                    )
                                    win_metadata = {
                                        "playbook_match_score": match_meta.get("playbook_match_score"),
                                        "win_reason_tags": match_meta.get("matched_tags", []),
                                        "effective_risk_pct": db_row.get("effective_risk_pct"),
                                        "risk_overlay_pct": db_row.get("risk_overlay_pct"),
                                        "win_reasoning": build_win_reasoning(
                                            db_row,
                                            current_signal=None,
                                            playbook_tags=match_meta.get("matched_tags", []),
                                            playbook_score=match_meta.get("playbook_match_score"),
                                        ),
                                    }
                                await asyncio.to_thread(
                                    close_open_trades_by_symbol,
                                    user_id,
                                    symbol_open,
                                    mark_open,
                                    pnl_est,
                                    "max_hold_time_exceeded",
                                    loss_reason,
                                    win_metadata,
                                    "swing",
                                )
                                try:
                                    await _get_coordinator().confirm_closed(
                                        user_id=user_id, symbol=symbol_open, now_ts=time.time()
                                    )
                                except Exception:
                                    pass
                                timeout_state_user.pop(symbol_open, None)
                                logger.info(
                                    f"[Engine:{user_id}] Swing dynamic max-hold close: {symbol_open} "
                                    f"elapsed={elapsed_open:.1f}s limit={hold_limit}s pnl={pnl_est:+.4f}"
                                )
                                continue

                        if not bool(cfg.get("swing_adaptive_timeout_protection_enabled", False)):
                            continue

                        state = timeout_state_user.setdefault(
                            symbol_open,
                            {
                                "initial_sl": sl_open,
                                "last_sl_update_ts": 0.0,
                                "phase": "early",
                                "applied": False,
                            },
                        )
                        initial_sl = float(state.get("initial_sl", sl_open) or sl_open)
                        last_sl_update_ts = float(state.get("last_sl_update_ts", 0.0) or 0.0)
                        min_update_gap = float(cfg.get("swing_timeout_protection_min_update_seconds", 45) or 45)
                        if (time.time() - last_sl_update_ts) < min_update_gap:
                            continue
                        denom = float(hold_limit if hold_limit > 0 else max(1, int(cfg.get("swing_max_hold_default_seconds", 1800) or 1800)))
                        ratio = max(0.0, min(1.0, float(elapsed_open) / denom))
                        phase = "early" if ratio < 0.50 else ("mid" if ratio < 0.80 else "late")
                        state["phase"] = phase
                        if phase == "early":
                            continue
                        favorable_pct = (
                            ((mark_open - entry_open) / entry_open) * 100.0
                            if side_open == "LONG"
                            else ((entry_open - mark_open) / entry_open) * 100.0
                        )
                        be_trigger = float(cfg.get("swing_timeout_be_trigger_pct", 0.20) or 0.20)
                        trailing_trigger = float(cfg.get("swing_timeout_trailing_trigger_pct", 0.35) or 0.35)
                        tighten = float(cfg.get("swing_timeout_late_tighten_multiplier", 1.4) or 1.4)
                        if phase == "late":
                            tighten *= 1.2
                        new_sl = sl_open
                        if favorable_pct >= be_trigger:
                            new_sl = entry_open
                        if favorable_pct >= trailing_trigger:
                            risk_gap = abs(entry_open - initial_sl)
                            if risk_gap > 0:
                                trail_gap = risk_gap / max(1.0, tighten)
                                if side_open == "LONG":
                                    new_sl = max(new_sl, max(entry_open, mark_open - trail_gap))
                                else:
                                    new_sl = min(new_sl, min(entry_open, mark_open + trail_gap))
                        eps = max(1e-8, abs(entry_open) * 1e-6)
                        improved = (new_sl > sl_open + eps) if side_open == "LONG" else (new_sl < sl_open - eps)
                        if not improved:
                            continue
                        if side_open == "LONG" and new_sl >= mark_open:
                            continue
                        if side_open == "SHORT" and new_sl <= mark_open:
                            continue
                        sl_update_res = await asyncio.to_thread(client.set_position_sl, symbol_open, float(new_sl))
                        if not sl_update_res.get("success"):
                            continue
                        try:
                            _client().table("autotrade_trades").update({
                                "sl_price": float(new_sl)
                            }).eq("id", db_row.get("id")).eq("status", "open").execute()
                        except Exception as sl_db_err:
                            logger.warning(f"[Engine:{user_id}] Failed to persist swing timeout SL update: {sl_db_err}")
                        state["last_sl_update_ts"] = time.time()
                        state["applied"] = True
                        logger.info(
                            f"[Engine:{user_id}] Swing timeout protection applied: "
                            f"{symbol_open} phase={phase} old_sl={sl_open:.6f} new_sl={new_sl:.6f}"
                        )
                except Exception as swing_timeout_err:
                    logger.warning(f"[Engine:{user_id}] Swing timeout/max-hold hook failed: {swing_timeout_err}")

            # Deteksi posisi baru tutup (TP/SL hit) — estimasi PnL
            if had_open_position and not open_positions:
                had_open_position = False
                # Bersihkan TP1 tracker karena semua posisi sudah tutup
                _tp1_hit_positions[user_id] = set()
                _swing_timeout_state.pop(int(user_id), None)
                if is_tracking(user_id):
                    stop_pnl_tracker(user_id)

                # ── Update trade history: posisi ditutup ──────────────
                try:
                    from app.trade_history import (
                        get_open_trades,
                        save_trade_close,
                        build_loss_reasoning,
                        build_win_reasoning,
                    )
                    from app.providers.alternative_klines_provider import alternative_klines_provider
                    open_db_trades = get_open_trades(user_id, "swing")
                    for db_trade in open_db_trades:
                        sym_base = db_trade["symbol"].replace("USDT", "")
                        # Prefer exchange-realized roundtrip financials (close realized + fees).
                        # Fallback to mark/klines estimation only when exchange history is unavailable.
                        fin = {}
                        try:
                            fin = await asyncio.to_thread(
                                client.get_roundtrip_financials,
                                db_trade["symbol"],
                                str(db_trade.get("order_id") or ""),
                                str(db_trade.get("side") or ""),
                                str(db_trade.get("opened_at") or ""),
                                200,
                            )
                        except Exception as _fin_err:
                            logger.warning(
                                f"[Engine:{user_id}] roundtrip financial lookup failed for "
                                f"{db_trade.get('symbol')}: {_fin_err}"
                            )

                        # Ambil harga terakhir untuk estimasi exit jika tidak ada close avg price dari history.
                        try:
                            if fin.get("success") and fin.get("close_avg_price"):
                                exit_px = float(fin.get("close_avg_price"))
                            else:
                                # Try mark price from exchange
                                ticker_result = await asyncio.to_thread(client.get_ticker, db_trade["symbol"])
                                if ticker_result.get('success') and ticker_result.get('mark_price'):
                                    exit_px = float(ticker_result['mark_price'])
                                else:
                                    # Fallback to klines
                                    klines = alternative_klines_provider.get_klines(sym_base, interval='1m', limit=2)
                                    exit_px = float(klines[-1][4]) if klines else float(db_trade.get("entry_price", 0))
                        except Exception as e:
                            logger.warning(f"[Engine:{user_id}] Failed to get exit price for {sym_base}: {e}")
                            # Last resort: use entry price (will result in 0 PnL)
                            exit_px = float(db_trade.get("entry_price", 0))

                        entry_px = float(db_trade.get("entry_price", 0))
                        db_side  = db_trade.get("side", "LONG")
                        raw_pnl  = (exit_px - entry_px) if db_side == "LONG" else (entry_px - exit_px)
                        est_pnl_usdt = raw_pnl * float(db_trade.get("qty", 0))

                        if fin.get("success") and fin.get("net_pnl") is not None:
                            pnl_usdt = float(fin.get("net_pnl"))
                        else:
                            pnl_usdt = est_pnl_usdt

                        win_metadata = None
                        if pnl_usdt < 0:
                            # Loss — generate reasoning
                            try:
                                curr_sig = await asyncio.to_thread(
                                    _compute_signal_pro, sym_base, None, user_risk_pct, adaptive_state
                                )
                            except Exception:
                                curr_sig = None
                            loss_reason = build_loss_reasoning(db_trade, curr_sig)
                            close_status = "closed_sl"
                        else:
                            loss_reason  = ""
                            close_status = "closed_tp"
                            match_meta = await asyncio.to_thread(
                                compute_playbook_match_from_reasons,
                                db_trade.get("entry_reasons", []),
                                win_playbook_state,
                            )
                            win_metadata = {
                                "playbook_match_score": match_meta.get("playbook_match_score"),
                                "win_reason_tags": match_meta.get("matched_tags", []),
                                "effective_risk_pct": db_trade.get("effective_risk_pct"),
                                "risk_overlay_pct": db_trade.get("risk_overlay_pct"),
                                "win_reasoning": build_win_reasoning(
                                    db_trade,
                                    current_signal=None,
                                    playbook_tags=match_meta.get("matched_tags", []),
                                    playbook_score=match_meta.get("playbook_match_score"),
                                ),
                            }

                        save_trade_close(
                            trade_id=db_trade["id"],
                            exit_price=exit_px,
                            pnl_usdt=pnl_usdt,
                            close_reason=close_status,
                            loss_reasoning=loss_reason,
                            win_metadata=win_metadata,
                        )

                        # Confirm position closed with coordinator
                        try:
                            coordinator = _get_coordinator()
                            await coordinator.confirm_closed(
                                user_id=user_id,
                                symbol=db_trade.get("symbol", ""),
                                now_ts=time.time()
                            )
                            _swing_timeout_state.get(int(user_id), {}).pop(str(db_trade.get("symbol", "")).upper(), None)
                        except Exception as _cc_err:
                            logger.warning(f"[Engine:{user_id}] confirm_closed failed: {_cc_err}")

                        daily_pnl_usdt += pnl_usdt

                        # Broadcast profit besar ke semua user (social proof)
                        if pnl_usdt >= 5.0 and close_status == "closed_tp":
                            try:
                                from app.social_proof import broadcast_profit
                                from app.supabase_repo import get_user_by_tid
                                user_data = get_user_by_tid(user_id)
                                fname = user_data.get("first_name", "User") if user_data else "User"
                                asyncio.create_task(broadcast_profit(
                                    bot=bot,
                                    user_id=user_id,
                                    first_name=fname,
                                    symbol=db_trade.get("symbol", ""),
                                    side=db_trade.get("side", "LONG"),
                                    pnl_usdt=pnl_usdt,
                                    leverage=db_trade.get("leverage", leverage),
                                ))
                            except Exception as _bp_err:
                                logger.warning(f"[Engine:{user_id}] broadcast_profit failed: {_bp_err}")

                except Exception as _he:
                    logger.warning(f"[Engine:{user_id}] trade_history close failed: {_he}")
                await bot.send_message(
                    chat_id=notify_chat_id,
                    text=(
                        f"🔔 <b>Position Closed</b> (TP/SL hit)\n\n"
                        f"📊 Trades today: <b>{trades_today}</b>\n"
                        f"🔄 Looking for next setup..."
                    ),
                    parse_mode='HTML',
                    reply_markup=_dashboard_keyboard()
                )

            if open_positions:
                had_open_position = True

            # ── StackMentor Monitor: Check TP2/TP3 hits ──────────────
            if cfg.get("use_stackmentor", True):
                try:
                    await monitor_stackmentor_positions(
                        bot=bot,
                        user_id=user_id,
                        client=client,
                        notify_chat_id=notify_chat_id
                    )
                except Exception as _sm_err:
                    logger.warning(f"[StackMentor:{user_id}] Monitor error: {_sm_err}")

            # ── TP1 Monitor: cek apakah harga sudah melewati TP1 ─────
            # Hanya untuk premium user (dual TP mode) [LEGACY - will be replaced by StackMentor]
            if _dual_tp_enabled and open_positions and user_id in _tp1_hit_positions:
                for pos in open_positions:
                    pos_symbol = pos.get("symbol", "")
                    if pos_symbol in _tp1_hit_positions.get(user_id, set()):
                        continue  # sudah di breakeven mode, skip

                    # Cari data trade yang sesuai untuk tahu TP1 dan entry
                    try:
                        from app.trade_history import get_open_trades
                        db_trades = get_open_trades(user_id, "swing")
                        for db_t in db_trades:
                            if db_t["symbol"] != pos_symbol:
                                continue
                            db_entry  = float(db_t.get("entry_price", 0))
                            db_tp1    = float(db_t.get("tp_price", 0))
                            db_side   = db_t.get("side", "LONG")
                            db_qty    = float(db_t.get("qty", 0))
                            mark_px   = float(pos.get("mark_price", 0)) or db_entry

                            tp1_hit = (db_side == "LONG"  and mark_px >= db_tp1 and db_tp1 > 0) or \
                                      (db_side == "SHORT" and mark_px <= db_tp1 and db_tp1 > 0)

                            if not tp1_hit:
                                continue

                            logger.info(f"[Engine:{user_id}] TP1 HIT {pos_symbol} @ {mark_px:.4f} — closing 75%, moving SL to breakeven")

                            # Close 75% posisi
                            close_side_tp1 = "SELL" if db_side == "LONG" else "BUY"
                            prec_tp1       = QTY_PRECISION.get(pos_symbol, 3)
                            qty_to_close   = round(db_qty * cfg["tp1_close_pct"], prec_tp1)

                            if qty_to_close > 0:
                                partial_result = await asyncio.to_thread(
                                    client.close_partial, pos_symbol, close_side_tp1, qty_to_close, db_side
                                )
                                if not partial_result.get("success"):
                                    logger.warning(f"[Engine:{user_id}] Partial close failed: {partial_result.get('error')}")
                                    continue

                            await asyncio.sleep(1)

                            # Geser SL ke entry (breakeven)
                            be_result = await asyncio.to_thread(
                                client.set_position_sl, pos_symbol, db_entry
                            )

                            # Tandai sudah breakeven
                            _tp1_hit_positions[user_id].add(pos_symbol)

                            tp1_profit_pct = abs(mark_px - db_entry) / db_entry * 100
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    f"🎯 <b>TP1 HIT — {pos_symbol}</b>\n\n"
                                    f"✅ Closed 75% position @ <code>{mark_px:.4f}</code>\n"
                                    f"💰 Profit locked: +{tp1_profit_pct:.2f}%\n\n"
                                    f"🔒 <b>SL moved to entry (breakeven)</b>\n"
                                    f"📍 Breakeven: <code>{db_entry:.4f}</code>\n\n"
                                    f"⏳ Remaining 25% running to TP2...\n"
                                    f"{'✅ SL updated' if be_result.get('success') else '⚠️ SL update failed — check manually'}"
                                ),
                                parse_mode='HTML',
                                reply_markup=_dashboard_keyboard()
                            )
                            break
                    except Exception as _tp1e:
                        logger.warning(f"[Engine:{user_id}] TP1 monitor error: {_tp1e}")

            # ── Reversal check: apakah struktur pasar flip? ───────────
            if open_positions:
                for pos in open_positions:
                    pos_symbol  = pos.get("symbol", "")
                    pos_side    = pos.get("side", "").upper()   # BUY / SELL
                    pos_qty     = float(pos.get("qty", 0))
                    base_symbol = pos_symbol.replace("USDT", "")

                    if not pos_qty:
                        continue

                    # Scan sinyal baru untuk simbol ini
                    try:
                        rev_sig = await asyncio.to_thread(
                            _compute_signal_pro, base_symbol, btc_bias, user_risk_pct, adaptive_state
                        )
                    except Exception:
                        continue

                    if not rev_sig or not _is_reversal(pos_side, rev_sig, rev_sig.get("btc_is_sideways", False)):
                        continue
                    flip_conf_adapt = get_confidence_adaptation(
                        mode="swing",
                        confidence=float(rev_sig.get("confidence", 0.0) or 0.0),
                        is_emergency=False,
                        snapshot=confidence_adapt_state,
                    )
                    flip_base_min_conf = (
                        FLIP_MIN_CONFIDENCE_SIDEWAYS
                        if bool(rev_sig.get("btc_is_sideways", False))
                        else FLIP_MIN_CONFIDENCE
                    )
                    flip_effective_min_conf = int(
                        max(
                            0,
                            min(
                                100,
                                int(flip_base_min_conf)
                                + int(flip_conf_adapt.get("bucket_penalty", 0) or 0),
                            ),
                        )
                    )
                    if float(rev_sig.get("confidence", 0) or 0) < float(flip_effective_min_conf):
                        logger.info(
                            f"[Engine:{user_id}] Flip rejected by confidence adaptation "
                            f"trade_type=swing symbol={pos_symbol} conf={float(rev_sig.get('confidence', 0) or 0):.2f} "
                            f"min_conf={float(flip_effective_min_conf):.2f} "
                            f"conf_bucket={flip_conf_adapt.get('bucket')} "
                            f"bucket_penalty={int(flip_conf_adapt.get('bucket_penalty', 0) or 0)} "
                            f"bucket_risk_scale={float(flip_conf_adapt.get('bucket_risk_scale', 1.0) or 1.0):.2f} "
                            f"edge_adj={float(flip_conf_adapt.get('edge_adj', 0.0) or 0.0):+.4f}"
                        )
                        continue
                    rev_sig["confidence_bucket"] = str(flip_conf_adapt.get("bucket", ""))
                    rev_sig["confidence_bucket_penalty"] = int(flip_conf_adapt.get("bucket_penalty", 0) or 0)
                    rev_sig["confidence_bucket_risk_scale"] = float(flip_conf_adapt.get("bucket_risk_scale", 1.0) or 1.0)
                    rev_sig["confidence_bucket_edge_adj"] = float(flip_conf_adapt.get("edge_adj", 0.0) or 0.0)
                    rev_sig["confidence_effective_min_conf"] = float(flip_effective_min_conf)

                    # ── CHoCH terdeteksi — eksekusi flip ─────────────
                    new_side    = rev_sig["side"]
                    new_entry   = rev_sig["entry_price"]
                    new_tp      = rev_sig["tp1"]
                    new_sl      = rev_sig["sl"]
                    new_conf    = rev_sig["confidence"]
                    new_struct  = rev_sig["market_structure"]
                    new_trend   = rev_sig["trend_1h"]

                    logger.warning(
                        f"[Engine:{user_id}] CHoCH DETECTED {pos_symbol}: "
                        f"{pos_side} → {new_side} | conf={new_conf}% | "
                        f"struct={new_struct} | 1H={new_trend}"
                    )

                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text=(
                            f"🔄 <b>CHoCH Detected — Reversal {pos_symbol}</b>\n\n"
                            f"Active position: <b>{'LONG' if pos_side=='BUY' else 'SHORT'}</b>\n"
                            f"New signal: <b>{new_side}</b>\n\n"
                            f"📊 1H Trend: <b>{new_trend}</b>\n"
                            f"🏗 Structure: <b>{new_struct}</b> (CHoCH)\n"
                            f"🧠 Confidence: <b>{new_conf}%</b>\n"
                            f"{'🔀 Mode: <b>SIDEWAYS FLIP</b> (range trading)' if rev_sig.get('btc_is_sideways') else '📈 Mode: <b>TREND FLIP</b> (CHoCH confirmed)'}\n\n"
                            f"⚡ Closing position and flipping to {new_side}..."
                        ),
                        parse_mode='HTML',
                        reply_markup=_dashboard_keyboard()
                    )

                    # Step 1: Close posisi aktif
                    close_side  = "SELL" if pos_side == "BUY" else "BUY"
                    close_result = await asyncio.to_thread(
                        client.place_order, pos_symbol, close_side, pos_qty,
                        order_type='market', reduce_only=True
                    )

                    if not close_result.get("success"):
                        close_err = close_result.get("error", "Unknown")
                        logger.error(f"[Engine:{user_id}] Flip close FAILED: {close_err}")
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=f"⚠️ <b>Failed to close position for flip:</b> {close_err}\nReversal cancelled.",
                            parse_mode='HTML'
                        )
                        continue

                    await asyncio.sleep(1)  # beri waktu exchange proses close

                    # Step 2: Open posisi baru arah berlawanan (auto max-safe leverage)
                    flip_effective_leverage = get_auto_max_safe_leverage(
                        symbol=pos_symbol,
                        entry_price=new_entry,
                        sl_price=new_sl,
                        baseline_leverage=leverage,
                    )
                    logger.info(
                        f"[Engine:{user_id}] leverage_mode=auto_max_safe symbol={pos_symbol} "
                        f"baseline_leverage={leverage} effective_leverage={flip_effective_leverage}"
                    )

                    flip_risk_eval = await evaluate_and_apply_playbook_risk(
                        signal=rev_sig,
                        base_risk_pct=user_risk_pct,
                        raw_reasons=rev_sig.get("reasons", []),
                        logger=logger,
                        label=f"[Engine:{user_id}] Flip",
                    )
                    flip_playbook_effective_risk_pct = float(flip_risk_eval.get("effective_risk_pct", user_risk_pct))
                    flip_risk_overlay_pct = float(flip_risk_eval.get("risk_overlay_pct", 0.0))
                    flip_playbook_score = float(flip_risk_eval.get("playbook_match_score", 0.0))
                    flip_playbook_tags = list(flip_risk_eval.get("playbook_match_tags", []))
                    flip_conf_scale = float(rev_sig.get("confidence_bucket_risk_scale", 1.0) or 1.0)
                    flip_effective_risk_pct = apply_confidence_risk_brake(
                        playbook_effective_risk_pct=flip_playbook_effective_risk_pct,
                        bucket_risk_scale=flip_conf_scale,
                    )
                    rev_sig["effective_risk_pct"] = float(flip_effective_risk_pct)
                    rev_sig["risk_overlay_pct"] = float(flip_risk_overlay_pct)
                    logger.info(
                        f"[Engine:{user_id}] Flip risk eval — "
                        f"score={flip_playbook_score:.3f} tags={flip_playbook_tags[:3]} "
                        f"overlay={flip_risk_overlay_pct:.2f}% -> playbook_risk={flip_playbook_effective_risk_pct:.2f}% "
                        f"trade_type=swing conf_bucket={rev_sig.get('confidence_bucket', '-')} "
                        f"conf_scale={flip_conf_scale:.2f} "
                        f"edge_adj={float(rev_sig.get('confidence_bucket_edge_adj', 0.0) or 0.0):+.4f} "
                        f"-> final_effective_risk={flip_effective_risk_pct:.2f}% "
                        f"action={flip_risk_eval.get('overlay_action')}"
                    )
                    flip_qty, _ = await calc_qty_with_risk(
                        pos_symbol,
                        new_entry,
                        new_sl,
                        flip_effective_leverage,
                        effective_risk_pct_override=flip_effective_risk_pct,
                    )
                    if flip_qty <= 0:
                        logger.warning(f"[Engine:{user_id}] Flip qty=0 for {pos_symbol}, skip open")
                        continue

                    # Position is now closed on exchange. Clear coordinator ownership
                    # before opening the new flipped side.
                    try:
                        coordinator = _get_coordinator()
                        await coordinator_confirm_closed(
                            coordinator,
                            user_id=user_id,
                            symbol=pos_symbol,
                            now_ts=time.time(),
                        )
                        _swing_timeout_state.get(int(user_id), {}).pop(str(pos_symbol).upper(), None)
                    except Exception as _cc_err:
                        logger.warning(f"[Engine:{user_id}] confirm_closed (flip pre-open) failed: {_cc_err}")

                    # Persist old position close before opening flipped side.
                    try:
                        from app.trade_history import (
                            save_trade_close,
                            build_loss_reasoning,
                            build_win_reasoning,
                            get_open_trades,
                        )
                        old_trades = get_open_trades(user_id, "swing")
                        for ot in old_trades:
                            if ot["symbol"] != pos_symbol:
                                continue
                            old_entry = float(ot.get("entry_price", new_entry))
                            old_side = ot.get("side", "LONG")
                            raw_pnl = (new_entry - old_entry) if old_side == "LONG" else (old_entry - new_entry)
                            pnl_est = raw_pnl * float(ot.get("qty", 0))
                            loss_r = build_loss_reasoning(ot, rev_sig) if pnl_est < 0 else ""
                            win_meta = None
                            if pnl_est >= 0:
                                old_match = await asyncio.to_thread(
                                    compute_playbook_match_from_reasons,
                                    ot.get("entry_reasons", []),
                                    win_playbook_state,
                                )
                                win_meta = {
                                    "playbook_match_score": old_match.get("playbook_match_score"),
                                    "win_reason_tags": old_match.get("matched_tags", []),
                                    "effective_risk_pct": ot.get("effective_risk_pct"),
                                    "risk_overlay_pct": ot.get("risk_overlay_pct"),
                                    "win_reasoning": build_win_reasoning(
                                        ot,
                                        current_signal=rev_sig,
                                        playbook_tags=old_match.get("matched_tags", []),
                                        playbook_score=old_match.get("playbook_match_score"),
                                    ),
                                }
                            save_trade_close(
                                trade_id=ot["id"],
                                exit_price=new_entry,
                                pnl_usdt=pnl_est,
                                close_reason="closed_flip",
                                loss_reasoning=loss_r,
                                win_metadata=win_meta,
                            )
                    except Exception as _close_old_err:
                        logger.warning(f"[Engine:{user_id}] flip old-trade close persistence failed: {_close_old_err}")

                    open_result = await open_managed_position(
                        client=client,
                        user_id=user_id,
                        symbol=pos_symbol,
                        side=new_side,
                        entry_price=new_entry,
                        sl_price=new_sl,
                        tp_price=new_tp,
                        quantity=flip_qty,
                        leverage=flip_effective_leverage,
                        reconcile=True,
                    )

                    if open_result.success:
                        if open_result.levels:
                            new_tp = float(open_result.levels.tp1)
                            new_sl = float(open_result.levels.sl)
                        _flip_cooldown[pos_symbol] = time.time()
                        trades_today += 1
                        sl_pct = abs(new_entry - new_sl) / new_entry * 100
                        tp_pct = abs(new_tp - new_entry) / new_entry * 100

                        # Register new flipped position ownership for coordinator.
                        try:
                            coordinator = _get_coordinator()
                            await coordinator_confirm_open(
                                coordinator,
                                user_id=user_id,
                                symbol=pos_symbol,
                                strategy=StrategyOwner.SWING,
                                side=PositionSide.LONG if new_side == "LONG" else PositionSide.SHORT,
                                size=flip_qty,
                                entry_price=new_entry,
                                exchange_position_id=open_result.order_id,
                            )
                        except Exception as _co_open_err:
                            logger.warning(f"[Engine:{user_id}] confirm_open (flip) failed: {_co_open_err}")

                        # ── Update history: close trade lama, buka trade baru ──
                        try:
                            from app.trade_history import save_trade_open

                            # Simpan trade baru hasil flip
                            save_trade_open(
                                telegram_id=user_id,
                                symbol=pos_symbol,
                                side=new_side,
                                entry_price=new_entry,
                                qty=flip_qty,
                                leverage=flip_effective_leverage,
                                tp_price=new_tp,
                                sl_price=new_sl,
                                signal=rev_sig,
                                order_id=open_result.order_id or "",
                                is_flip=True,
                                tp1_price=float(open_result.levels.tp1) if open_result.levels else new_tp,
                                tp2_price=float(open_result.levels.tp2) if open_result.levels else new_tp,
                                tp3_price=float(open_result.levels.tp3) if open_result.levels else new_tp,
                                qty_tp1=float(open_result.levels.qty_tp1) if open_result.levels else flip_qty,
                                qty_tp2=float(open_result.levels.qty_tp2) if open_result.levels else 0.0,
                                qty_tp3=float(open_result.levels.qty_tp3) if open_result.levels else 0.0,
                                strategy="stackmentor",
                                execution_meta={
                                    "playbook_match_score": flip_playbook_score,
                                    "effective_risk_pct": flip_effective_risk_pct,
                                    "risk_overlay_pct": flip_risk_overlay_pct,
                                },
                            )
                        except Exception as _he:
                            logger.warning(f"[Engine:{user_id}] flip trade_history failed: {_he}")
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=(
                                f"✅ <b>FLIP SUCCESSFUL — {pos_symbol}</b>\n\n"
                                f"{'LONG' if pos_side=='BUY' else 'SHORT'} → <b>{new_side}</b>\n"
                                f"💵 Entry: <code>{new_entry:.4f}</code>\n"
                                f"🎯 TP: <code>{new_tp:.4f}</code> (+{tp_pct:.1f}%)\n"
                                f"🛑 SL: <code>{new_sl:.4f}</code> (-{sl_pct:.1f}%)\n"
                                f"📦 Qty: {flip_qty} | {flip_effective_leverage}x\n"
                                f"🧠 Confidence: {new_conf}%\n"
                                f"⚖️ R:R: 1:{rev_sig['rr_ratio']:.1f}"
                            ),
                            parse_mode='HTML'
                        )
                        logger.info(f"[Engine:{user_id}] Flip SUCCESS {pos_symbol} → {new_side}")
                    else:
                        flip_err = str(open_result.error or "Unknown")
                        flip_code = str(open_result.error_code or "order_failed")
                        logger.error(f"[Engine:{user_id}] Flip open FAILED [{flip_code}]: {flip_err}")
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=(
                                f"⚠️ <b>Old position closed but failed to open {new_side}:</b>\n"
                                f"{flip_err}\n\nBot is still running, looking for next setup."
                            ),
                            parse_mode='HTML'
                        )

            # ── Concurrent positions limit ─────────────────────────────
            if len(open_positions) >= cfg["max_concurrent"]:
                logger.info(f"[Engine:{user_id}] Max concurrent positions ({cfg['max_concurrent']}) reached")
                await asyncio.sleep(cfg["scan_interval"])
                continue

            # ── Scan symbols (dynamic top-10 by volume, highest first) ─────
            if mixed_mode:
                assignments = await get_mixed_pair_assignments(
                    user_id=int(user_id),
                    limit=10,
                    fallback_pairs=list(cfg.get("symbols", [])),
                    logger_override=logger,
                    label=f"[Engine:{user_id}]",
                )
                ranked_pairs = list(assignments.get("swing") or [])
            else:
                ranked_pairs = await get_top_volume_pairs(
                    limit=10,
                    fallback_pairs=list(cfg.get("symbols", [])),
                    logger=logger,
                    label=f"[Engine:{user_id}]",
                )
            ranked_bases = []
            for pair in ranked_pairs:
                base = str(pair).upper().replace("USDT", "")
                if base and base not in ranked_bases:
                    ranked_bases.append(base)
            volume_rank = {b: idx for idx, b in enumerate(ranked_bases, start=1)}
            available = [s for s in ranked_bases if (s + "USDT") not in occupied_syms]
            available = [
                s for s in available
                if not _is_stale_price_cooldown_active(user_id, f"{str(s).upper()}USDT")
            ]
            if not available:
                await asyncio.sleep(cfg["scan_interval"])
                continue
            logger.info(
                f"[Engine:{user_id}] Top-volume focus: "
                + ", ".join([f"{s}(#{volume_rank.get(s, 0)})" for s in available])
            )
            
            # ── Get BTC bias first (market leader analysis) ───────────
            btc_bias = await asyncio.to_thread(_get_btc_bias)
            btc_bias_dir = btc_bias.get("bias", "NEUTRAL")
            btc_strength = btc_bias.get("strength", 0)
            
            logger.info(
                f"[Engine:{user_id}] BTC Bias: {btc_bias_dir} ({btc_strength}%) — "
                f"{', '.join(btc_bias.get('reasons', [])[:2])}"
            )

            # Saat BTC sideways: hanya scan BTC sendiri (altcoin diblokir di _compute_signal_pro)
            # BTC bisa range trade dengan confidence lebih tinggi
            btc_sideways_mode = (btc_bias_dir == "NEUTRAL" or btc_strength < 60)
            effective_min_conf = int(
                max(0, min(100, cfg["min_confidence"] + int(adaptive_state.get("conf_delta", 0) or 0)))
            )
            min_conf_scan = effective_min_conf + 5 if btc_sideways_mode else effective_min_conf

            candidates: List[Dict] = []
            for sym in available:
                try:
                    sig = await asyncio.to_thread(
                        _compute_signal_pro,
                        sym,
                        btc_bias,
                        user_risk_pct,
                        adaptive_state,
                        user_id,
                    )
                    if sig:
                        conf_adapt = get_confidence_adaptation(
                            mode="swing",
                            confidence=float(sig.get("confidence", 0.0) or 0.0),
                            is_emergency=False,
                            snapshot=confidence_adapt_state,
                        )
                        bucket_penalty = int(conf_adapt.get("bucket_penalty", 0) or 0)
                        min_conf_effective = int(max(0, min(100, min_conf_scan + bucket_penalty)))
                        if float(sig.get('confidence', 0) or 0) < float(min_conf_effective):
                            logger.info(
                                f"[Engine:{user_id}] Candidate rejected by confidence gate "
                                f"trade_type=swing symbol={sym} conf={float(sig.get('confidence', 0) or 0):.2f} "
                                f"min_conf={float(min_conf_effective):.2f} conf_bucket={conf_adapt.get('bucket')} "
                                f"bucket_penalty={bucket_penalty} "
                                f"bucket_risk_scale={float(conf_adapt.get('bucket_risk_scale', 1.0) or 1.0):.2f} "
                                f"edge_adj={float(conf_adapt.get('edge_adj', 0.0) or 0.0):+.4f}"
                            )
                            continue
                        if not _passes_swing_confirmation_gate(user_id, sig, cfg):
                            continue
                        match_meta = await asyncio.to_thread(
                            compute_playbook_match_from_reasons,
                            sig.get("reasons", []),
                            win_playbook_state,
                        )
                        sig["playbook_match_score"] = float(match_meta.get("playbook_match_score", 0.0))
                        sig["playbook_match_tags"] = list(match_meta.get("matched_tags", []))
                        sig["is_emergency"] = False
                        sig["confidence_bucket"] = str(conf_adapt.get("bucket", ""))
                        sig["confidence_bucket_penalty"] = int(conf_adapt.get("bucket_penalty", 0) or 0)
                        sig["confidence_bucket_risk_scale"] = float(conf_adapt.get("bucket_risk_scale", 1.0) or 1.0)
                        sig["confidence_bucket_edge_adj"] = float(conf_adapt.get("edge_adj", 0.0) or 0.0)
                        sig["confidence_effective_min_conf"] = float(min_conf_effective)
                        sig["_volume_rank"] = volume_rank.get(sym, 9999)
                        candidates.append(sig)
                        logger.info(f"[Engine:{user_id}] Candidate: {sym} {sig['side']} "
                                    f"conf={sig['confidence']}% RR={sig['rr_ratio']} rank={sig['_volume_rank']} "
                                    f"playbook={sig.get('playbook_match_score', 0.0):.3f} "
                                    f"trade_type=swing conf_bucket={sig.get('confidence_bucket')} "
                                    f"bucket_penalty={sig.get('confidence_bucket_penalty', 0)} "
                                    f"bucket_risk_scale={float(sig.get('confidence_bucket_risk_scale', 1.0) or 1.0):.2f} "
                                    f"edge_adj={float(sig.get('confidence_bucket_edge_adj', 0.0) or 0.0):+.4f}"
                                    f"{' [SIDEWAYS]' if sig.get('btc_is_sideways') else ''}")
                except Exception as e:
                    logger.warning(f"[Engine:{user_id}] Scan error {sym}: {e}")

            if not candidates:
                if bool(cfg.get("swing_emergency_candidate_mode", True)):
                    emergency_candidates: List[Dict] = []
                    for sym in available:
                        try:
                            emer_sig = await asyncio.to_thread(
                                _generate_swing_emergency_candidate,
                                sym,
                                btc_bias,
                                user_risk_pct,
                                adaptive_state,
                                cfg,
                                user_id,
                            )
                            if not emer_sig:
                                continue
                            conf_adapt = get_confidence_adaptation(
                                mode="swing",
                                confidence=float(emer_sig.get("confidence", 0.0) or 0.0),
                                is_emergency=True,
                                snapshot=confidence_adapt_state,
                            )
                            emergency_base_min = max(0, min(100, int(cfg.get("swing_emergency_min_confidence", 50) or 50)))
                            min_conf_effective = int(
                                max(
                                    0,
                                    min(
                                        100,
                                        emergency_base_min + int(conf_adapt.get("bucket_penalty", 0) or 0),
                                    ),
                                )
                            )
                            if float(emer_sig.get("confidence", 0) or 0) < float(min_conf_effective):
                                logger.info(
                                    f"[Engine:{user_id}] Emergency candidate rejected by confidence gate "
                                    f"trade_type=swing symbol={sym} conf={float(emer_sig.get('confidence', 0) or 0):.2f} "
                                    f"min_conf={float(min_conf_effective):.2f} conf_bucket={conf_adapt.get('bucket')} "
                                    f"bucket_penalty={int(conf_adapt.get('bucket_penalty', 0) or 0)} "
                                    f"bucket_risk_scale={float(conf_adapt.get('bucket_risk_scale', 1.0) or 1.0):.2f} "
                                    f"edge_adj={float(conf_adapt.get('edge_adj', 0.0) or 0.0):+.4f}"
                                )
                                continue
                            if not _passes_swing_confirmation_gate(user_id, emer_sig, cfg):
                                continue
                            match_meta = await asyncio.to_thread(
                                compute_playbook_match_from_reasons,
                                emer_sig.get("reasons", []),
                                win_playbook_state,
                            )
                            emer_sig["playbook_match_score"] = float(match_meta.get("playbook_match_score", 0.0))
                            emer_sig["playbook_match_tags"] = list(match_meta.get("matched_tags", []))
                            emer_sig["confidence_bucket"] = str(conf_adapt.get("bucket", ""))
                            emer_sig["confidence_bucket_penalty"] = int(conf_adapt.get("bucket_penalty", 0) or 0)
                            emer_sig["confidence_bucket_risk_scale"] = float(conf_adapt.get("bucket_risk_scale", 1.0) or 1.0)
                            emer_sig["confidence_bucket_edge_adj"] = float(conf_adapt.get("edge_adj", 0.0) or 0.0)
                            emer_sig["confidence_effective_min_conf"] = float(min_conf_effective)
                            emer_sig["_volume_rank"] = volume_rank.get(sym, 9999)
                            emergency_candidates.append(emer_sig)
                        except Exception as emergency_err:
                            logger.warning(f"[Engine:{user_id}] Emergency scan error {sym}: {emergency_err}")
                    if emergency_candidates:
                        candidates = emergency_candidates
                        logger.info(
                            f"[Engine:{user_id}] Emergency candidate mode activated: {len(candidates)} fallback setups"
                        )
                if not candidates:
                    logger.info(f"[Engine:{user_id}] No quality setups found, waiting...")
                    await asyncio.sleep(cfg["scan_interval"])
                    continue

            # ── Signal Queue System: Sort by volume-rank first, then quality ────────
            # Highest-volume pair is top priority, confidence and RR resolve ties.
            candidates.sort(
                key=lambda s: (
                    int(s.get("_volume_rank", 9999)),
                    -float(s.get("confidence", 0)),
                    -float(s.get("playbook_match_score", 0.0)),
                    -float(s.get("rr_ratio", 0)),
                )
            )

            logger.info(f"[Engine:{user_id}] Signal Queue System: {len(candidates)} candidates generated (sorted by volume-rank then confidence)")
            queue_msg = "📋 <b>Signal Queue (by volume priority):</b>\n"
            for idx, cand in enumerate(candidates, 1):
                logger.info(
                    f"  [{idx}] {cand['symbol']}: rank={cand.get('_volume_rank', '?')} "
                    f"{cand['side']} conf={cand['confidence']}% RR={cand['rr_ratio']:.1f} "
                    f"PB={float(cand.get('playbook_match_score', 0.0)):.3f}"
                )
                queue_msg += (
                    f"{idx}. <b>{cand['symbol']}</b> (Vol Rank #{cand.get('_volume_rank', '?')}) "
                    f"{cand['side']} | Conf: {cand['confidence']}% | R:R: 1:{cand['rr_ratio']:.1f} "
                    f"| PB: {float(cand.get('playbook_match_score', 0.0)):.2f}\n"
                )

            if user_id not in _signal_queues:
                _signal_queues[user_id] = []
            if user_id not in _signals_being_processed:
                _signals_being_processed[user_id] = set()

            queue_now_ts = time.time()
            for cand in candidates:
                queue_action = _upsert_signal_queue_entry(user_id, cand, now_ts=queue_now_ts)
                if queue_action == "skipped_inflight":
                    logger.debug(f"[Engine:{user_id}] Skip queue refresh for in-flight {cand.get('symbol')}")
                    continue
                if queue_action in {"inserted", "updated"}:
                    _sync_pending_signal_queue_row(user_id, cand)

            # Keep queue globally ordered by current volume priority then signal quality.
            _signal_queues[user_id].sort(
                key=lambda s: (
                    int(s.get("_volume_rank", 9999)),
                    -float(s.get("confidence", 0)),
                    -float(s.get("rr_ratio", 0)),
                )
            )
            _signal_queues[user_id] = [
                queued for queued in _signal_queues[user_id]
                if not _is_stale_price_cooldown_active(
                    user_id,
                    str(queued.get("symbol", "")).upper(),
                )
            ]
            expired_from_age = _drop_expired_signal_queue_entries(
                user_id,
                max_age_sec=_SWING_QUEUE_MAX_AGE_SECONDS,
            )
            if expired_from_age:
                logger.info(
                    f"[Engine:{user_id}] Dropped stale queued signals (> {_SWING_QUEUE_MAX_AGE_SECONDS:.0f}s): "
                    + ", ".join(expired_from_age)
                )

            # ── Process next signal from queue ──────────────────────────────────
            if not _signal_queues[user_id]:
                await asyncio.sleep(cfg["scan_interval"])
                continue

            # Initialize symbol locks for this user if not exists
            if user_id not in _symbol_locks:
                _symbol_locks[user_id] = {}
            # Get next signal from queue (highest volume priority first)
            sig = None
            for idx, candidate in enumerate(_signal_queues[user_id]):
                if candidate['symbol'] not in _signals_being_processed[user_id]:
                    sig = candidate
                    queued_idx = idx
                    break

            if not sig:
                # All symbols in queue are being processed, wait for next iteration
                logger.info(f"[Engine:{user_id}] All queued signals are being processed, waiting...")
                await asyncio.sleep(cfg["scan_interval"])
                continue

            symbol     = sig['symbol']
            side       = sig['side']
            entry      = sig['entry_price']
            tp1        = sig['tp1']
            tp2        = sig['tp2']
            sl         = sig['sl']
            confidence = sig['confidence']
            rr_ratio   = sig['rr_ratio']
            pending_marked = False

            queued_at_ts = float(sig.get("_queued_at_ts", 0.0) or 0.0)
            queue_age_sec = (max(0.0, time.time() - queued_at_ts) if queued_at_ts > 0 else -1.0)
            queue_age_text = f"{queue_age_sec:.1f}s" if queue_age_sec >= 0 else "n/a"
            stale_cd_active = _is_stale_price_cooldown_active(user_id, symbol)
            logger.info(
                f"[Engine:{user_id}] Processing signal from queue: {symbol} {side} "
                f"conf={confidence}% RR={rr_ratio:.1f} "
                f"(Queue position: #{queued_idx + 1}/{len(_signal_queues[user_id])}, "
                f"selected_idx={queued_idx}, queue_age={queue_age_text}, "
                f"stale_cd_active={stale_cd_active})"
            )

            if not _signal_prices_pass_live_mark(
                symbol=symbol,
                side=side,
                entry_price=float(entry),
                tp1_price=float(tp1),
                sl_price=float(sl),
            ):
                expiry_ts = _mark_stale_price_cooldown(user_id, symbol)
                cooldown_sec = max(1, int(round(expiry_ts - time.time())))
                logger.info(
                    f"[Engine:{user_id}] Queue pre-exec stale reject: {symbol} "
                    f"(cooldown={cooldown_sec}s)"
                )
                _cleanup_signal_queue(user_id, symbol, success=False)
                await asyncio.sleep(cfg["scan_interval"])
                continue

            # ── Mark symbol as being processed (prevent concurrent execution) ──
            _signals_being_processed[user_id].add(symbol)

            # Sync execution status to Supabase (web visibility)
            try:
                from app.supabase_repo import _client
                s = _client()
                s.table("signal_queue").update({
                    "status": "executing",
                    "started_at": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).eq(
                    "symbol", symbol
                ).eq("status", "pending").execute()
                logger.debug(f"[Engine:{user_id}] Synced {symbol} as executing to Supabase")
            except Exception as _sync_err:
                logger.warning(f"[Engine:{user_id}] Failed to sync executing status: {_sync_err}")

            # Send queue status update to user
            try:
                queued_remaining = _build_queued_remaining_symbols(
                    _signal_queues[user_id],
                    active_idx=queued_idx,
                    active_symbol=symbol,
                )
                if queued_remaining:
                    queue_status = f"📊 <b>Signal Queue Status:</b>\n\n"
                    queue_status += f"<b>⚙️ Now Processing:</b>\n{symbol} | {side} | Conf: {confidence}%\n\n"
                    queue_status += f"<b>📋 Queued ({len(queued_remaining)} remaining):</b>\n"
                    for q_sym in queued_remaining:
                        queue_status += f"  • {q_sym}\n"
                    queue_status += f"\n<i>Higher volume priority signals execute first (confidence breaks ties)</i>"
                    await bot.send_message(chat_id=notify_chat_id, text=queue_status, parse_mode='HTML')
            except Exception as _qst_err:
                logger.debug(f"[Engine:{user_id}] Queue status notification failed: {_qst_err}")

            # ── Auto Max Pair Leverage Calculation ──
            effective_leverage = get_auto_max_safe_leverage(
                symbol=symbol,
                entry_price=entry,
                sl_price=sl,
                baseline_leverage=leverage,
            )
            logger.info(
                f"[Engine:{user_id}] leverage_mode=auto_max_safe symbol={symbol} "
                f"baseline_leverage={leverage} effective_leverage={effective_leverage}"
            )
            risk_eval = await evaluate_and_apply_playbook_risk(
                signal=sig,
                base_risk_pct=user_risk_pct,
                raw_reasons=sig.get("reasons", []),
                logger=logger,
                label=f"[Engine:{user_id}] {symbol}",
            )
            playbook_effective_risk_pct = float(risk_eval.get("effective_risk_pct", user_risk_pct))
            risk_overlay_pct = float(risk_eval.get("risk_overlay_pct", 0.0))
            playbook_match_score = float(risk_eval.get("playbook_match_score", sig.get("playbook_match_score", 0.0)))
            playbook_match_tags = list(risk_eval.get("playbook_match_tags", sig.get("playbook_match_tags", [])))
            confidence_risk_scale = float(sig.get("confidence_bucket_risk_scale", 1.0) or 1.0)
            confidence_bucket = str(sig.get("confidence_bucket", "-") or "-")
            confidence_edge_adj = float(sig.get("confidence_bucket_edge_adj", 0.0) or 0.0)
            effective_risk_pct = apply_confidence_risk_brake(
                playbook_effective_risk_pct=playbook_effective_risk_pct,
                bucket_risk_scale=confidence_risk_scale,
            )
            sig["effective_risk_pct"] = float(effective_risk_pct)
            sig["risk_overlay_pct"] = float(risk_overlay_pct)
            logger.info(
                f"[Engine:{user_id}] Win playbook eval {symbol} — "
                f"score={playbook_match_score:.3f} tags={playbook_match_tags[:3]} "
                f"guardrails={bool(risk_eval.get('guardrails_healthy', False))} "
                f"overlay={risk_overlay_pct:.2f}% -> playbook_risk={playbook_effective_risk_pct:.2f}% "
                f"trade_type=swing conf_bucket={confidence_bucket} conf_scale={confidence_risk_scale:.2f} "
                f"edge_adj={confidence_edge_adj:+.4f} -> final_effective_risk={effective_risk_pct:.2f}% "
                f"action={risk_eval.get('overlay_action')}"
            )

            # Sync signal execution update to Supabase including effective leverage
            try:
                from app.supabase_repo import _client
                s = _client()
                s.table("signal_queue").update({
                    "reason": f"Executed with Auto Max Pair Leverage: {effective_leverage}x"
                }).eq("user_id", user_id).eq("symbol", symbol).eq("status", "executing").execute()
            except Exception:
                pass

            # ── Hitung qty dengan risk-based sizing (Phase 2) ─────────────
            # Try risk-based position sizing first, fallback to fixed margin if fails
            qty, used_risk_sizing = await calc_qty_with_risk(
                symbol,
                entry,
                sl,
                effective_leverage,
                effective_risk_pct_override=effective_risk_pct,
            )
            
            if qty <= 0:
                logger.warning(f"[Engine:{user_id}] qty=0 for {symbol}, skip")
                _cleanup_signal_queue(user_id, symbol, success=False)
                await asyncio.sleep(cfg["scan_interval"])
                continue
            
            # Log which method was used
            if used_risk_sizing:
                logger.info(f"[Engine:{user_id}] Using RISK-BASED position sizing for {symbol}")
            else:
                logger.info(f"[Engine:{user_id}] Using FIXED MARGIN position sizing for {symbol} (fallback)")

            # ── StackMentor: Calculate 3-tier TP levels ───────────────
            # All users are eligible for StackMentor (no minimum equity)
            from app.supabase_repo import is_stackmentor_eligible_by_balance

            stackmentor_enabled = False
            try:
                # Get user's current equity from exchange (available + frozen + unrealized PnL)
                acc_result = await asyncio.to_thread(client.get_account_info)
                if acc_result.get('success'):
                    user_available = float(acc_result.get('available', 0) or 0)
                    user_frozen = float(acc_result.get('frozen', 0) or 0)
                    user_balance = user_available + user_frozen
                    user_unrealized = float(acc_result.get('total_unrealized_pnl', 0) or 0)
                    user_equity = user_balance + user_unrealized
                else:
                    user_equity = 0

                # All users are eligible for StackMentor
                stackmentor_enabled = cfg.get("use_stackmentor", True) and is_stackmentor_eligible_by_balance(user_equity)

                if stackmentor_enabled:
                    logger.info(f"[StackMentor:{user_id}] Enabled for equity ${user_equity:.2f} ✅")
                else:
                    logger.info(f"[StackMentor:{user_id}] Disabled in config (equity: ${user_equity:.2f})")
            except Exception as _sm_check_err:
                logger.warning(f"[StackMentor:{user_id}] Equity check failed: {_sm_check_err}")
                stackmentor_enabled = False
            
            precision  = QTY_PRECISION.get(symbol, 3)
            if stackmentor_enabled:
                # StackMentor: 3-tier TP strategy (50%/40%/10%)
                tp1_sm, tp2_sm, tp3_sm = calculate_stackmentor_levels(
                    entry_price=entry,
                    sl_price=sl,
                    side=side
                )
                min_qty = MIN_QTY_MAP.get(symbol, 0.001)
                qty_tp1, qty_tp2, qty_tp3 = calculate_qty_splits(qty, min_qty=min_qty, precision=precision)

                # Override signal TP with StackMentor levels
                tp1 = tp1_sm
                tp2 = tp2_sm
                tp3 = tp3_sm

                logger.info(
                    f"[StackMentor:{user_id}] {symbol} {side} — "
                    f"TP1={tp1:.4f}(60%) TP2={tp2:.4f}(30%) TP3={tp3:.4f}(10%) "
                    f"qty_splits={qty_tp1}/{qty_tp2}/{qty_tp3}"
                )
            elif _dual_tp_enabled:
                # Legacy premium: 75%/25% split
                qty_tp1 = round(qty * cfg["tp1_close_pct"], precision)
                qty_tp2 = round(qty - qty_tp1, precision)
                qty_tp3 = 0
                tp3 = tp2
                if qty_tp1 <= 0 or qty_tp2 <= 0:
                    qty_tp1 = qty
                    qty_tp2 = 0
                    qty_tp3 = 0
            else:
                # Legacy free: single TP
                qty_tp1 = qty
                qty_tp2 = 0
                qty_tp3 = 0
                tp3 = tp1

            # ── Multi-user symbol coordination check ───────────────────
            # Check if this user can enter this symbol (no conflicting owner)
            coordinator = _get_coordinator()
            can_enter, block_reason = await coordinator.can_enter(
                user_id=user_id,
                symbol=symbol,
                strategy=StrategyOwner.SWING,
                now_ts=time.time()
            )
            if not can_enter:
                logger.warning(f"[Coordinator:{user_id}] Entry BLOCKED for {symbol}: {block_reason}")
                should_notify = True
                pending_ctx: Dict[str, Any] = {}
                pending_diag: Dict[str, Any] = {}
                if "blocked_pending_order" in str(block_reason):
                    pending_ctx = await coordinator.get_pending_lock_context(
                        user_id=user_id,
                        symbol=symbol,
                        now_ts=time.time(),
                    )
                    pending_diag = normalize_pending_lock_context(pending_ctx)
                    logger.warning(
                        "[Coordinator:%s] blocked_pending_diagnostics symbol=%s "
                        "pending_owner=%s owner=%s pending_age=%s pending_ttl=%.1fs "
                        "has_position=%s stale_candidate=%s last_clear_reason=%s",
                        user_id,
                        symbol,
                        pending_diag.get("pending_owner") or "-",
                        pending_diag.get("owner") or "-",
                        pending_lock_age_label(pending_diag.get("pending_age_seconds")),
                        float(pending_diag.get("pending_ttl_seconds", 90.0) or 90.0),
                        bool(pending_diag.get("has_position", False)),
                        bool(pending_diag.get("stale_candidate", False)),
                        pending_diag.get("last_pending_clear_reason") or "-",
                    )
                    should_notify = _should_notify_blocked_pending(user_id, symbol)
                if should_notify:
                    diag_text = ""
                    if pending_diag:
                        pending_owner = escape(str(pending_diag.get("pending_owner") or pending_diag.get("owner") or "unknown"))
                        pending_age = pending_lock_age_label(pending_diag.get("pending_age_seconds"))
                        ttl_sec = int(round(float(pending_diag.get("pending_ttl_seconds", 90.0) or 90.0)))
                        has_position_txt = "YES" if bool(pending_diag.get("has_position", False)) else "NO"
                        last_clear_reason = escape(str(pending_diag.get("last_pending_clear_reason") or "-"))
                        diag_text = (
                            f"<b>Pending owner:</b> {pending_owner}\n"
                            f"<b>Pending age:</b> {pending_age} (TTL {ttl_sec}s)\n"
                            f"<b>Open position on symbol:</b> {has_position_txt}\n"
                            f"<b>Last pending clear:</b> {last_clear_reason}\n\n"
                            f"<i>Safety hint:</i> stale auto-clear applies only when pending exists "
                            f"without open position and age exceeds TTL."
                        )
                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text=(
                            f"⚠️ <b>Trade skipped on {symbol}</b>\n\n"
                            f"<b>Reason:</b> {block_reason}\n\n"
                            + (
                                f"{diag_text}\n\n"
                                if diag_text else
                                "Another strategy may own this symbol right now.\n\n"
                            )
                            + "Bot will continue scanning for other opportunities."
                        ),
                        parse_mode='HTML'
                    )
                _cleanup_signal_queue(user_id, symbol, success=False)
                await asyncio.sleep(cfg["scan_interval"])
                continue

            # Final stale guard with fully computed levels (post sizing/StackMentor path).
            if not _signal_prices_pass_live_mark(
                symbol=symbol,
                side=side,
                entry_price=float(entry),
                tp1_price=float(tp1),
                sl_price=float(sl),
            ):
                expiry_ts = _mark_stale_price_cooldown(user_id, symbol)
                cooldown_sec = max(1, int(round(expiry_ts - time.time())))
                logger.info(
                    f"[Engine:{user_id}] Final pre-open stale reject: {symbol} "
                    f"(cooldown={cooldown_sec}s)"
                )
                _cleanup_signal_queue(user_id, symbol, success=False)
                await asyncio.sleep(cfg["scan_interval"])
                continue

            # Mark pending (order about to be submitted)
            await coordinator_set_pending(coordinator, user_id, symbol, StrategyOwner.SWING)
            pending_marked = True

            # ── Unified managed entry path (shared with scalping) ────────────
            exec_result = await open_managed_position(
                client=client,
                user_id=user_id,
                symbol=symbol,
                side=side,
                entry_price=entry,
                sl_price=sl,
                tp_price=tp1,
                quantity=qty,
                leverage=effective_leverage,
                reconcile=True,
            )

            if not exec_result.success:
                err = str(exec_result.error or "Unknown")
                err_code = str(exec_result.error_code or "order_failed")
                logger.error(f"[Engine:{user_id}] Order FAILED [{err_code}]: {err}")

                await coordinator_clear_pending(coordinator, user_id, symbol)
                pending_marked = False

                if err_code == "invalid_prices":
                    expiry_ts = _mark_stale_price_cooldown(user_id, symbol)
                    cooldown_sec = max(1, int(round(expiry_ts - time.time())))
                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text=(
                            f"⚠️ <b>Trade skipped: stale signal</b>\n\n"
                            f"{err}\n\n"
                            f"Market moved before entry validation.\n"
                            f"Cooldown on {symbol}: {cooldown_sec}s to avoid repeated stale entries.\n\n"
                            f"Bot will look for next setup."
                        ),
                        parse_mode='HTML'
                    )
                    _cleanup_signal_queue(user_id, symbol, success=False)
                    await asyncio.sleep(cfg["scan_interval"])
                    continue
                if err_code == "invalid_sl_price":
                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text=(
                            f"⚠️ <b>Trade skipped</b>\n\n"
                            f"{err}\n\n"
                            f"Bot will look for next setup."
                        ),
                        parse_mode='HTML'
                    )
                    _cleanup_signal_queue(user_id, symbol, success=False)
                    await asyncio.sleep(cfg["scan_interval"])
                    continue
                if err_code == "unsupported_symbol_api":
                    quarantine_expiry = mark_runtime_untradable_symbol(symbol, ttl_sec=21600.0)
                    quarantine_sec = max(1, int(round(quarantine_expiry - time.time())))
                    quarantine_hours = max(1, int(round(quarantine_sec / 3600.0)))
                    await bot.send_message(
                        chat_id=notify_chat_id,
                        text=(
                            f"⚠️ <b>Trade skipped on {symbol}</b>\n\n"
                            f"{err}\n\n"
                            f"Bitunix OpenAPI does not support this symbol right now.\n"
                            f"Runtime quarantine applied: {quarantine_hours}h.\n"
                            f"Bot will continue scanning other top-volume pairs."
                        ),
                        parse_mode='HTML'
                    )
                    _cleanup_signal_queue(user_id, symbol, success=False)
                    await asyncio.sleep(cfg["scan_interval"])
                    continue

                if err_code in {"auth", "ip_blocked"}:
                    logger.warning(f"[Engine:{user_id}] Auth/IP error, retrying once in 15s: {err}")
                    await asyncio.sleep(15)
                    retry_result = await open_managed_position(
                        client=client,
                        user_id=user_id,
                        symbol=symbol,
                        side=side,
                        entry_price=entry,
                        sl_price=sl,
                        tp_price=tp1,
                        quantity=qty,
                        leverage=effective_leverage,
                        reconcile=True,
                    )
                    if retry_result.success:
                        exec_result = retry_result
                    else:
                        retry_err = str(retry_result.error or "")
                        retry_code = str(retry_result.error_code or "order_failed")
                        if retry_code == "auth":
                            _cleanup_signal_queue(user_id, symbol, success=False)
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    "❌ <b>AutoTrade Dihentikan - API Key Salah</b>\n\n"
                                    "⚠️ <b>Masalah:</b> API Key atau Secret Key yang Anda masukkan salah atau tidak valid.\n\n"
                                    "🔧 <b>Penyebab Umum:</b>\n"
                                    "• API Key/Secret Key salah saat input\n"
                                    "• API Key memiliki IP restriction (harus tanpa IP)\n"
                                    "• API Key sudah expired atau dihapus\n"
                                    "• Permissions tidak lengkap (harus ada Futures Trading)\n\n"
                                    "✅ <b>Cara Memperbaiki:</b>\n"
                                    "1. Buka Bitunix → API Management\n"
                                    "2. Hapus API Key lama\n"
                                    "3. Buat API Key baru:\n"
                                    "   • <b>TANPA IP Restriction</b>\n"
                                    "   • Enable <b>Futures Trading</b>\n"
                                    "   • Copy API Key & Secret Key dengan benar\n"
                                    "4. Ketik /autotrade → Change API Key\n"
                                    "5. Paste API Key & Secret Key yang baru\n\n"
                                    "❓ <b>Butuh Bantuan?</b>\n"
                                    "Hubungi Admin: @BillFarr\n"
                                    "Admin akan membantu Anda setup API Key dengan benar."
                                ),
                                parse_mode='HTML'
                            )
                            return
                        if retry_code == "ip_blocked":
                            _cleanup_signal_queue(user_id, symbol, success=False)
                            await bot.send_message(
                                chat_id=notify_chat_id,
                                text=(
                                    "⚠️ <b>Server IP blocked by Bitunix</b>\n\n"
                                    "Bot will retry in 5 minutes.\n"
                                    "Make sure <b>PROXY_URL</b> is set in Railway Variables."
                                ),
                                parse_mode='HTML'
                            )
                            await asyncio.sleep(300)
                            continue
                        _cleanup_signal_queue(user_id, symbol, success=False)
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=f"⚠️ <b>Order failed (2x):</b> {retry_err}\n\nBot is still running.",
                            parse_mode='HTML'
                        )
                        await asyncio.sleep(cfg["scan_interval"])
                        continue
                else:
                    _cleanup_signal_queue(user_id, symbol, success=False)
                    if err_code == "insufficient_balance":
                        bal_result = await asyncio.to_thread(client.get_account_info)
                        bal_usdt = 0.0
                        if bal_result.get('success'):
                            bal_usdt = float(bal_result.get('available', 0) or 0) + float(bal_result.get('frozen', 0) or 0)
                        margin_needed = round(amount, 2)
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=(
                                f"⚠️ <b>Order failed: Insufficient balance</b>\n\n"
                                f"💰 Your futures balance: <b>{bal_usdt:.2f} USDT</b>\n"
                                f"📦 Required margin: <b>~{margin_needed:.2f} USDT</b>\n\n"
                                f"Solutions:\n"
                                f"• Transfer USDT from <b>Spot → Futures</b> on Bitunix\n"
                                f"• Or reduce your autotrade equity target\n\n"
                                f"Bot is still running and will retry."
                            ),
                            parse_mode='HTML'
                        )
                    elif err_code == "reconcile_failed":
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=(
                                f"🚨 <b>Position auto-closed: {symbol}</b>\n\n"
                                f"Self-healing check found the live position mismatch.\n\n"
                                f"<code>{escape(err)}</code>"
                            ),
                            parse_mode='HTML'
                        )
                    else:
                        await bot.send_message(
                            chat_id=notify_chat_id,
                            text=f"⚠️ <b>Order failed:</b> {err}\n\nBot is still running.",
                            parse_mode='HTML'
                        )
                    await asyncio.sleep(cfg["scan_interval"])
                    continue

                if not exec_result.success:
                    _cleanup_signal_queue(user_id, symbol, success=False)
                    await asyncio.sleep(cfg["scan_interval"])
                    continue

            # Sync levels from unified execution so risk math/persistence matches
            if exec_result.levels:
                tp1 = float(exec_result.levels.tp1)
                tp2 = float(exec_result.levels.tp2)
                tp3 = float(exec_result.levels.tp3)
                sl = float(exec_result.levels.sl)
                qty_tp1 = float(exec_result.levels.qty_tp1)
                qty_tp2 = float(exec_result.levels.qty_tp2)
                qty_tp3 = float(exec_result.levels.qty_tp3)

            # ── Order SUCCESS: Clean up from queue and mark execution complete ──
            _cleanup_signal_queue(user_id, symbol, success=True)

            # Confirm with coordinator that position is now open
            coordinator = _get_coordinator()
            await coordinator_confirm_open(
                coordinator,
                user_id=user_id,
                symbol=symbol,
                strategy=StrategyOwner.SWING,
                side=PositionSide.LONG if side == "LONG" else PositionSide.SHORT,
                size=qty,
                entry_price=entry,
                exchange_position_id=exec_result.order_id,
            )
            pending_marked = False

            order_id = exec_result.order_id or '-'
            trades_today += 1
            had_open_position = True

            # Tandai posisi ini belum hit TP1
            if user_id not in _tp1_hit_positions:
                _tp1_hit_positions[user_id] = set()
            _tp1_hit_positions[user_id].discard(symbol)

            # StackMentor registration now happens inside open_managed_position().

            # ── Simpan ke trade history ───────────────────────────────
            trade_id = None
            try:
                from app.trade_history import save_trade_open
                trade_id = save_trade_open(
                    telegram_id=user_id,
                    symbol=symbol,
                    side=side,
                    entry_price=entry,
                    qty=qty,
                    leverage=effective_leverage,
                    tp_price=tp1,
                    sl_price=sl,
                    signal=sig,
                    order_id=order_id,
                    is_flip=False,
                    # StackMentor fields
                    tp1_price=tp1,
                    tp2_price=tp2,
                    tp3_price=tp3,
                    qty_tp1=qty_tp1,
                    qty_tp2=qty_tp2,
                    qty_tp3=qty_tp3,
                    strategy="stackmentor" if stackmentor_enabled else "legacy",
                    execution_meta={
                        "playbook_match_score": sig.get("playbook_match_score"),
                        "effective_risk_pct": sig.get("effective_risk_pct"),
                        "risk_overlay_pct": sig.get("risk_overlay_pct"),
                    },
                )
            except Exception as _he:
                logger.warning(f"[Engine:{user_id}] trade_history save failed: {_he}")

            # ── Trade-open notification (compact + web deep-link) ─────
            acc_result = await asyncio.to_thread(client.get_account_info)
            if acc_result.get('success'):
                current_available = float(acc_result.get('available', 0) or 0)
                current_frozen = float(acc_result.get('frozen', 0) or 0)
                current_balance = current_available + current_frozen
                current_unrealized = float(acc_result.get('total_unrealized_pnl', 0) or 0)
                current_equity = current_balance + current_unrealized
            else:
                current_equity = 0

            risk_amount = qty * abs(entry - sl)
            base_risk_pct = float(user_risk_pct)
            overlay_pct = float(sig.get("risk_overlay_pct", 0.0) or 0.0)
            effective_risk_pct = float(sig.get("effective_risk_pct", base_risk_pct) or base_risk_pct)
            risk_audit_line = format_and_emit_order_open_risk_audit(
                logger=logger,
                user_id=user_id,
                symbol=symbol,
                side=side,
                order_id=str(order_id or "-"),
                base_risk_pct=base_risk_pct,
                overlay_pct=overlay_pct,
                effective_risk_pct=effective_risk_pct,
                implied_risk_usdt=risk_amount,
            )
            risk_pct_equity = (risk_amount / current_equity * 100) if current_equity > 0 else None
            direction = "Long" if side.upper() in ("LONG", "BUY") else "Short"
            opened_at = datetime.utcnow().strftime("%d %b %Y %H:%M:%S UTC")
            order_id_text = escape(str(order_id or "-"))
            runner_active = float(qty_tp3 or 0) > 0 and abs(float(tp3 or 0) - float(tp1 or 0)) > 1e-9
            tp_block = (
                f"<b>TP1 (Partial):</b> {_fmt_price(tp1)}\n"
                f"<b>Runner TP (TP3):</b> {_fmt_price(tp3)}\n"
                f"<b>Split:</b> {((qty_tp1 / qty) * 100) if qty > 0 else 0:.0f}% / {((qty_tp3 / qty) * 100) if qty > 0 else 0:.0f}%\n"
            ) if runner_active else f"<b>TP:</b> {_fmt_price(tp1)}\n"

            await bot.send_message(
                chat_id=notify_chat_id,
                text=(
                    "🤖 <b>Cryptomentor AI Autotrade</b>\n\n"
                    f"<b>Direction:</b> {direction}\n"
                    f"<b>Trading Pair:</b> {symbol}\n"
                    f"<b>Entry:</b> {_fmt_price(entry)}\n"
                    + tp_block
                    + f"<b>SL:</b> {_fmt_price(sl)}\n"
                    + f"<b>Risk PNL:</b> ${risk_amount:.2f}\n"
                    + (
                        f"<b>Risk % on equity:</b> {risk_pct_equity:.2f}%\n"
                        if risk_pct_equity is not None else
                        "<b>Risk % on equity:</b> N/A\n"
                    )
                    + f"<b>{risk_audit_line}</b>\n"
                    + f"<b>Order ID:</b> <code>{order_id_text}</code>\n"
                    + f"<b>Date and time:</b> {opened_at}"
                ),
                parse_mode='HTML',
                reply_markup=_trade_detail_keyboard(trade_id=trade_id, order_id=order_id, symbol=symbol),
            )

            # ── Start PnL tracker ─────────────────────────────────────
            start_pnl_tracker(user_id=user_id, api_key=api_key, api_secret=api_secret,
                               bot=bot, chat_id=notify_chat_id)

            # ── Update session ────────────────────────────────────────
            try:
                _client().table("autotrade_sessions").update({
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("telegram_id", user_id).execute()
            except Exception:
                pass

            await asyncio.sleep(cfg["scan_interval"])

        except asyncio.CancelledError:
            # Safety: avoid stale pending lock if cancellation happens mid-entry.
            try:
                if 'pending_marked' in locals() and pending_marked:
                    await _get_coordinator().clear_pending(user_id, symbol)
            except Exception:
                pass
            try:
                _cleanup_inflight_signal_marker(user_id, locals().get("symbol"))
            except Exception:
                pass
            stop_pnl_tracker(user_id)
            try:
                await bot.send_message(chat_id=notify_chat_id,
                                       text="🛑 <b>AutoTrade stopped.</b>",
                                       parse_mode='HTML',
                                       reply_markup=_dashboard_keyboard())
            except Exception:
                pass
            return

        except Exception as e:
            # Safety: release pending lock on unexpected loop errors.
            try:
                if 'pending_marked' in locals() and pending_marked:
                    await _get_coordinator().clear_pending(user_id, symbol)
            except Exception:
                pass
            try:
                _cleanup_inflight_signal_marker(user_id, locals().get("symbol"))
            except Exception:
                pass
            err_str = str(e)
            logger.error(f"[Engine:{user_id}] Loop error: {e}", exc_info=True)
            # Jangan stop engine karena network/timeout error — hanya retry
            if any(x in err_str for x in ['TOKEN_INVALID', 'SIGNATURE_ERROR']):
                # Auth error di luar order placement — kemungkinan transient, retry 3x
                logger.warning(f"[Engine:{user_id}] Auth error in loop, will retry: {err_str}")
                await asyncio.sleep(60)  # tunggu lebih lama sebelum retry
            else:
                await asyncio.sleep(30)
