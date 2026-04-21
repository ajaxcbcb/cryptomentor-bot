"""
Scalping Engine
High-frequency trading engine for 5-minute scalping with 30-minute max hold time
"""

import asyncio
import logging
import os
import time
from typing import Any, Optional, Dict, List
from datetime import datetime
from html import escape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from app.trading_mode import ScalpingConfig, ScalpingSignal, ScalpingPosition
from app.supabase_repo import _client
from app.symbol_coordinator import (
    get_coordinator,
    StrategyOwner,
    PositionSide,
)
from app.engine_execution_shared import (
    build_cumulative_close_update_payload,
    coordinator_clear_pending,
    coordinator_confirm_closed,
    coordinator_confirm_open,
    coordinator_set_pending,
    evaluate_and_apply_playbook_risk,
    format_and_emit_order_open_risk_audit,
)
from app.engine_runtime_shared import (
    apply_scalping_confidence_relief,
    evaluate_adaptive_daily_circuit_breaker,
    get_scalping_risk_parity_controls,
    get_scalping_risk_parity_snapshot,
    get_top_volume_pairs,
    is_ttl_cooldown_active as _shared_is_ttl_cooldown_active,
    normalize_pending_lock_context,
    pending_lock_age_label,
    refresh_scalping_risk_parity_state,
    refresh_runtime_snapshot,
    sanitize_startup_pending_locks,
    set_ttl_cooldown as _shared_set_ttl_cooldown,
    should_notify_blocked_pending as _shared_should_notify_blocked_pending,
    should_stop_engine,
)
from app.adaptive_confluence import refresh_global_adaptive_state, get_adaptive_overrides
from app.confidence_adaptation import (
    apply_confidence_risk_brake,
    get_confidence_adaptation,
    get_confidence_adaptation_snapshot,
    refresh_global_confidence_adaptation_state,
)
from app.sideways_governor import (
    refresh_sideways_governor_state,
    get_sideways_governor_snapshot,
    get_sideways_entry_overrides,
    resolve_dynamic_max_hold_seconds,
)
from app.leverage_policy import get_auto_max_safe_leverage
from app.pair_strategy_router import get_mixed_pair_assignments
from app.win_playbook import (
    compute_playbook_match_from_reasons,
    refresh_global_win_playbook_state,
    get_win_playbook_snapshot,
)
from app.volume_pair_selector import mark_runtime_untradable_symbol
from app.close_alerts import format_trade_close_alert

logger = logging.getLogger(__name__)
WEB_DASHBOARD_URL = os.getenv("WEB_DASHBOARD_URL", "https://cryptomentor.id")


def _env_flag(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, "true" if default else "false") or "").strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


STALE_RECONCILE_ENABLED = _env_flag("STALE_RECONCILE_ENABLED", True)
SCALPING_STALE_RECONCILE_INTERVAL_SECONDS = max(
    30,
    int(float(os.getenv("SCALPING_STALE_RECONCILE_INTERVAL_SECONDS", "120") or 120)),
)
STALE_RECONCILE_JIT_ON_CAPACITY = _env_flag("STALE_RECONCILE_JIT_ON_CAPACITY", True)


def _fmt_price(v: float) -> str:
    s = f"{float(v):,.6f}"
    return s.rstrip("0").rstrip(".")


def _derive_rr_ratio(entry_price: float, sl_price: float, tp_price: float, fallback_rr: float = 0.0) -> float:
    """Derive R:R from executed levels and fallback to signal R:R when invalid."""
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
    try:
        return float(fallback_rr)
    except Exception:
        return 0.0


def _build_trade_url(trade_id: Optional[int] = None, order_id: str = "", symbol: str = "") -> str:
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


class ScalpingEngine:
    """
    High-frequency trading engine for 5-minute scalping
    
    Features:
    - 5M timeframe with 15M trend validation
    - Single TP at 1.5R
    - 30-minute max hold time
    - 5-minute cooldown between signals
    - 72% minimum confidence
    """
    
    def __init__(
        self,
        user_id: int,
        client,
        bot,
        notify_chat_id: int,
        config: Optional[ScalpingConfig] = None,
        mixed_mode: bool = False,
        startup_notification: bool = True,
    ):
        """
        Initialize scalping engine
        
        Args:
            user_id: Telegram user ID
            client: Exchange client instance
            bot: Telegram bot instance
            notify_chat_id: Chat ID for notifications
            config: ScalpingConfig (optional, uses defaults if None)
        """
        self.user_id = user_id
        self.client = client
        self.bot = bot
        self.notify_chat_id = notify_chat_id
        self.config = config or ScalpingConfig()
        self._mixed_mode = bool(mixed_mode)
        self._startup_notification = bool(startup_notification)
        
        # Position tracking
        self.positions: Dict[str, ScalpingPosition] = {}
        self._closing_symbols = set()
        self._recent_close_notifications: Dict[str, float] = {}
        
        # Cooldown tracking
        self.cooldown_tracker: Dict[str, float] = {}
        
        # Sideways error counter per symbol
        self.sideways_error_counter: Dict[str, int] = {}
        self.signal_streaks: Dict[str, Dict[str, float]] = {}
        self.last_closed_meta: Dict[str, Dict[str, float]] = {}
        self._blocked_pending_notify_ts: Dict[str, float] = {}
        self._stale_price_cooldown_ts: Dict[str, float] = {}
        
        # Running state
        self.running = False
        self._adaptive_overlay: Dict[str, float] = {
            "conf_delta": 0,
            "volume_min_ratio_delta": 0.0,
            "ob_fvg_requirement_mode": "soft",
            "strategy_loss_rate": 0.0,
            "ops_reconcile_rate": 0.0,
            "trade_count_per_day": 0.0,
            "strategy_sample_size": 0,
            "decision_reason": "bootstrap",
        }
        self._adaptive_next_refresh = 0.0
        self._active_scan_pairs = list(self.config.pairs)
        self._sideways_governor_snapshot: Dict[str, Any] = {
            "mode": "normal",
            "allow_sideways_entries": True,
            "allow_sideways_fallback": True,
            "sideways_min_rr_override": None,
            "sideways_min_volume_floor": 0.9,
            "sideways_confidence_bonus": 0,
            "sideways_confirmations_required": 1,
            "sideways_expectancy_24h": 0.0,
            "sideways_timeout_loss_rate_24h": 0.0,
            "sample_size_24h": 0,
            "decision_reason": "bootstrap",
            "dynamic_hold_sideways_seconds": 120,
            "dynamic_hold_non_sideways_seconds": int(self.config.max_hold_time),
        }
        self._sideways_governor_next_refresh = 0.0
        self._sideways_hourly_kpi_next = 0.0
        self._win_playbook_snapshot: Dict[str, Any] = {
            "risk_overlay_pct": 0.0,
            "rolling_win_rate": 0.0,
            "rolling_expectancy": 0.0,
            "sample_size": 0,
            "active_tags": [],
            "guardrails_healthy": False,
        }
        self._win_playbook_next_refresh = 0.0
        self._confidence_adapt_snapshot: Dict[str, Any] = {
            "enabled": False,
            "modes": {"scalping": {"active_adaptations": [], "sample_size": 0}},
        }
        self._confidence_adapt_next_refresh = 0.0
        self._scalp_risk_parity_snapshot: Dict[str, Any] = {
            "enabled": False,
            "regime": "disabled",
            "ratio": 1.0,
            "controls": {
                "time_profile": {"best": 1.0, "good": 0.7, "neutral": 0.5, "avoid": 0.0},
                "cap_pct": 0.50,
            },
        }
        self._scalp_risk_parity_next_refresh = 0.0
        self._stale_reconcile_enabled = bool(STALE_RECONCILE_ENABLED)
        self._stale_reconcile_interval_seconds = int(SCALPING_STALE_RECONCILE_INTERVAL_SECONDS)
        self._stale_reconcile_jit_on_capacity = bool(STALE_RECONCILE_JIT_ON_CAPACITY)
        self._stale_reconcile_next_ts = 0.0
        self._stale_reconcile_lock = asyncio.Lock()
        self._last_jit_reconcile_ts = 0.0

        # Multi-user symbol coordinator
        self.coordinator = get_coordinator()

        logger.info(f"[Scalping:{user_id}] Engine initialized with config: {self.config}")

    @staticmethod
    def _is_scalping_trade_row(row: Dict[str, Any]) -> bool:
        trade_type = str(row.get("trade_type") or "").strip().lower()
        if trade_type:
            return trade_type == "scalping"
        timeframe = str(row.get("timeframe") or "").strip().lower()
        if timeframe == "5m":
            return True
        strategy = str(row.get("strategy") or "").strip().lower()
        return strategy in {"scalping", "micro_scalp", "sideways_scalp"}

    def _should_notify_blocked_pending(self, symbol: str, ttl_sec: int = 600) -> bool:
        return _shared_should_notify_blocked_pending(
            self._blocked_pending_notify_ts,
            key=str(symbol).upper(),
            ttl_sec=float(ttl_sec),
        )

    def _mark_stale_price_cooldown(
        self,
        symbol: str,
        ttl_sec: float = 120.0,
        now_ts: Optional[float] = None,
    ) -> float:
        key = str(symbol).upper()
        expiry = _shared_set_ttl_cooldown(
            self.cooldown_tracker,
            key=key,
            ttl_sec=float(ttl_sec),
            now_ts=now_ts,
        )
        _shared_set_ttl_cooldown(
            self._stale_price_cooldown_ts,
            key=key,
            ttl_sec=float(ttl_sec),
            now_ts=now_ts,
        )
        return expiry

    def _is_stale_price_cooldown_active(self, symbol: str, now_ts: Optional[float] = None) -> bool:
        return _shared_is_ttl_cooldown_active(
            self._stale_price_cooldown_ts,
            key=str(symbol).upper(),
            now_ts=now_ts,
        )

    def _apply_generic_failure_cooldown(
        self,
        symbol: str,
        ttl_sec: float = 300.0,
        now_ts: Optional[float] = None,
    ) -> bool:
        if self._is_stale_price_cooldown_active(symbol, now_ts=now_ts):
            return False
        _shared_set_ttl_cooldown(
            self.cooldown_tracker,
            key=str(symbol).upper(),
            ttl_sec=float(ttl_sec),
            now_ts=now_ts,
        )
        return True

    async def _prune_stale_local_positions(self) -> int:
        """
        Remove in-memory tracked positions that no longer have open DB rows.
        Keeps capacity checks aligned immediately after reconcile heals.
        """
        removed = 0
        for symbol in list(self.positions.keys()):
            open_row = await self._get_open_trade_row(symbol)
            if open_row:
                continue
            self.positions.pop(symbol, None)
            removed += 1
        if removed > 0:
            logger.info(
                f"[Scalping:{self.user_id}] stale_reconcile trade_type=scalping "
                f"action=prune_local removed={removed}"
            )
        return removed

    async def _run_stale_reconcile(self, reconcile_reason: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "exchange_fetch_ok": True,
            "db_open_count": 0,
            "exchange_open_count": 0,
            "stale_symbols": [],
            "healed_count": 0,
            "healed_trade_ids": [],
            "healed_closes": [],
            "pruned_local_count": 0,
        }
        if not self._stale_reconcile_enabled:
            return out

        now_ts = time.time()
        if reconcile_reason == "jit_capacity" and (now_ts - self._last_jit_reconcile_ts) < 8.0:
            return out

        async with self._stale_reconcile_lock:
            now_ts = time.time()
            if reconcile_reason == "jit_capacity":
                if (now_ts - self._last_jit_reconcile_ts) < 8.0:
                    return out
                self._last_jit_reconcile_ts = now_ts

            from app.trade_history import inspect_open_trade_drift, apply_open_trade_reconcile

            drift = await asyncio.to_thread(
                inspect_open_trade_drift,
                self.user_id,
                self.client,
                "scalping",
            )
            out = await asyncio.to_thread(
                apply_open_trade_reconcile,
                self.user_id,
                self.client,
                "scalping",
                drift,
            )
            for payload in list(out.get("healed_closes") or []):
                try:
                    trade_id = int(payload.get("trade_id") or 0)
                except Exception:
                    trade_id = 0
                dedupe_key = f"reconcile_close:scalping:{trade_id}" if trade_id > 0 else (
                    f"reconcile_close:scalping:{str(payload.get('symbol') or '').upper()}:"
                    f"{str(payload.get('close_reason') or '').lower()}"
                )
                await self._notify_user_once(
                    dedupe_key=dedupe_key,
                    message=format_trade_close_alert(
                        symbol=payload.get("symbol"),
                        side=payload.get("side"),
                        close_reason=payload.get("close_reason"),
                        entry_price=payload.get("entry_price"),
                        exit_price=payload.get("exit_price"),
                        pnl_usdt=payload.get("pnl_usdt"),
                    ),
                    ttl_sec=600,
                )
            pruned_local_count = 0
            if int(out.get("healed_count", 0) or 0) > 0 or reconcile_reason == "jit_capacity":
                pruned_local_count = await self._prune_stale_local_positions()
            out["pruned_local_count"] = int(pruned_local_count)

            marker = (
                f"[Scalping:{self.user_id}] stale_reconcile trade_type=scalping "
                f"reconcile_reason={reconcile_reason} "
                f"db_open_count={int(out.get('db_open_count', 0) or 0)} "
                f"exchange_open_count={int(out.get('exchange_open_count', 0) or 0)} "
                f"healed_count={int(out.get('healed_count', 0) or 0)} "
                f"pruned_local_count={int(out.get('pruned_local_count', 0) or 0)} "
                f"stale_symbols={list(out.get('stale_symbols') or [])}"
            )
            if not bool(out.get("exchange_fetch_ok", True)):
                logger.warning(f"{marker} exchange_fetch_ok=false error={out.get('exchange_error')}")
            else:
                logger.info(marker)
            return out

    async def _ensure_capacity_for_entry(self) -> bool:
        if len(self.positions) < self.config.max_concurrent_positions:
            return True
        if self._stale_reconcile_enabled and self._stale_reconcile_jit_on_capacity:
            rec = await self._run_stale_reconcile("jit_capacity")
            if int(rec.get("healed_count", 0) or 0) > 0 or int(rec.get("pruned_local_count", 0) or 0) > 0:
                if len(self.positions) < self.config.max_concurrent_positions:
                    logger.info(
                        f"[Scalping:{self.user_id}] Capacity unblocked after JIT stale reconcile "
                        f"(max={self.config.max_concurrent_positions}, now={len(self.positions)})"
                    )
                    return True
        return len(self.positions) < self.config.max_concurrent_positions

    async def _open_managed_position_safe(self, open_managed_position_fn, **kwargs):
        """
        Compatibility guard for mixed deployments:
        retry without tp_price if remote/runtime function signature is older.
        """
        try:
            return await open_managed_position_fn(**kwargs)
        except TypeError as te:
            msg = str(te)
            if "unexpected keyword argument 'tp_price'" not in msg:
                raise
            retry_kwargs = dict(kwargs)
            retry_kwargs.pop("tp_price", None)
            logger.warning(
                "[Scalping:%s] open_managed_position tp_price unsupported in runtime; retrying without tp_price for %s",
                self.user_id,
                retry_kwargs.get("symbol", "?"),
            )
            return await open_managed_position_fn(**retry_kwargs)

    def _fmt_pnl_usdt(self, pnl: float) -> str:
        """Format PnL with higher precision for tiny values."""
        try:
            p = float(pnl)
        except Exception:
            p = 0.0
        if abs(p) < 0.01:
            return f"{p:+.4f}"
        return f"{p:+.2f}"

    async def _resolve_exit_price(self, symbol: str, fallback: float, order_result: Optional[dict] = None) -> tuple[float, bool]:
        """
        Resolve exit price for PnL calculation.
        Returns (price, is_estimated_from_ticker).
        """
        try:
            if isinstance(order_result, dict):
                fp = order_result.get("fill_price")
                if fp is not None:
                    fpv = float(fp)
                    if fpv > 0:
                        return fpv, False
        except Exception:
            pass

        try:
            ticker = await asyncio.to_thread(self.client.get_ticker, symbol)
            if ticker and ticker.get("success"):
                px = float(
                    ticker.get("mark_price")
                    or ticker.get("last_price")
                    or ticker.get("price")
                    or fallback
                )
                if px > 0:
                    return px, True
        except Exception:
            pass

        return float(fallback), True

    async def _resolve_net_pnl(
        self,
        symbol: str,
        gross_pnl: float,
        open_order_id: str = "",
        close_order_id: str = "",
    ) -> tuple[float, float, float, bool]:
        """
        Best-effort net PnL estimation using exchange order fees/details.
        Returns: (net_pnl, open_fee, close_fee, used_exchange_data)
        """
        open_fee = 0.0
        close_fee = 0.0
        used_exchange_data = False
        close_realized = None

        get_fin = getattr(self.client, "get_order_financials", None)
        if not callable(get_fin):
            return gross_pnl, open_fee, close_fee, used_exchange_data

        try:
            if open_order_id:
                o = await asyncio.to_thread(get_fin, open_order_id, symbol)
                if o.get("success"):
                    open_fee = abs(float(o.get("fee", 0) or 0))
                    used_exchange_data = True
        except Exception:
            pass

        try:
            if close_order_id:
                c = await asyncio.to_thread(get_fin, close_order_id, symbol)
                if c.get("success"):
                    close_fee = abs(float(c.get("fee", 0) or 0))
                    if c.get("realized_pnl") is not None:
                        close_realized = float(c.get("realized_pnl"))
                    used_exchange_data = True
        except Exception:
            pass

        base = close_realized if close_realized is not None else gross_pnl
        net = base - open_fee - close_fee
        return net, open_fee, close_fee, used_exchange_data

    async def _get_open_trade_row(self, symbol: str) -> Dict[str, Any]:
        try:
            s = _client()
            res = (
                s.table("autotrade_trades")
                .select("*")
                .eq("telegram_id", self.user_id)
                .eq("symbol", symbol)
                .eq("status", "open")
                .order("opened_at", desc=True)
                .limit(10)
                .execute()
            )
            for row in (res.data or []):
                row_dict = dict(row)
                if self._is_scalping_trade_row(row_dict):
                    return row_dict
        except Exception as e:
            logger.warning(f"[Scalping:{self.user_id}] Failed open trade fetch for {symbol}: {e}")
        return {}

    async def _resolve_close_quantity(self, position: ScalpingPosition) -> float:
        """
        Determine safest close quantity for reduce-only close.
        Priority:
        1) DB remaining quantity snapshot (if partial TP already happened)
        2) Live exchange position quantity
        3) Local in-memory position quantity
        """
        open_row = await self._get_open_trade_row(position.symbol)
        for key in ("remaining_quantity", "quantity", "qty"):
            try:
                q = float(open_row.get(key) or 0.0)
                if q > 0:
                    return q
            except Exception:
                continue

        try:
            pos_resp = await asyncio.to_thread(self.client.get_positions)
            if pos_resp and pos_resp.get("success"):
                for p in pos_resp.get("positions", []):
                    if str(p.get("symbol")) != str(position.symbol):
                        continue
                    q = abs(float(p.get("qty") or p.get("size") or 0.0))
                    if q > 0:
                        return q
        except Exception:
            pass

        return max(0.0, float(getattr(position, "quantity", 0.0) or 0.0))
    
    async def run(self):
        """Main trading loop - scans every 15 seconds"""
        self.running = True
        logger.info(f"[Scalping:{self.user_id}] Engine started")
        
        # ── Recover existing state ───────────────────────────────────────────
        # 1) Startup stale-open reconcile (DB vs exchange)
        try:
            await self._run_stale_reconcile("startup")
            self._stale_reconcile_next_ts = time.time() + float(self._stale_reconcile_interval_seconds)
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Startup stale reconcile failed: {e}")

        # 2. Load open positions from DB to resume monitoring
        await self._load_existing_positions()
        await sanitize_startup_pending_locks(
            self.coordinator,
            int(self.user_id),
            logger,
            label=f"[Scalping:{self.user_id}]",
        )
        
        # Send startup notification
        try:
            # Best-effort initial adaptive load.
            try:
                await asyncio.to_thread(refresh_global_adaptive_state)
                self._adaptive_overlay = await asyncio.to_thread(get_adaptive_overrides)
            except Exception as adapt_err:
                logger.warning(f"[Scalping:{self.user_id}] Initial adaptive load failed: {adapt_err}")
            try:
                await asyncio.to_thread(refresh_sideways_governor_state)
                self._sideways_governor_snapshot = await asyncio.to_thread(get_sideways_governor_snapshot)
            except Exception as governor_err:
                logger.warning(f"[Scalping:{self.user_id}] Initial sideways governor load failed: {governor_err}")
            try:
                await asyncio.to_thread(refresh_global_win_playbook_state)
                self._win_playbook_snapshot = await asyncio.to_thread(get_win_playbook_snapshot)
            except Exception as playbook_err:
                logger.warning(f"[Scalping:{self.user_id}] Initial win-playbook load failed: {playbook_err}")
            try:
                await asyncio.to_thread(refresh_global_confidence_adaptation_state)
                self._confidence_adapt_snapshot = await asyncio.to_thread(get_confidence_adaptation_snapshot)
            except Exception as conf_adapt_err:
                logger.warning(f"[Scalping:{self.user_id}] Initial confidence adaptation load failed: {conf_adapt_err}")
            try:
                await asyncio.to_thread(refresh_scalping_risk_parity_state)
                self._scalp_risk_parity_snapshot = await asyncio.to_thread(get_scalping_risk_parity_snapshot)
            except Exception as risk_parity_err:
                logger.warning(f"[Scalping:{self.user_id}] Initial risk parity load failed: {risk_parity_err}")
            if self._mixed_mode:
                assignments = await get_mixed_pair_assignments(
                    user_id=int(self.user_id),
                    limit=10,
                    fallback_pairs=list(self.config.pairs),
                    logger_override=logger,
                    label=f"[Scalping:{self.user_id}]",
                )
                self._active_scan_pairs = list(assignments.get("scalp") or [])
            else:
                self._active_scan_pairs = await get_top_volume_pairs(
                    limit=10,
                    fallback_pairs=list(self.config.pairs),
                    logger=logger,
                    label=f"[Scalping:{self.user_id}]",
                )

            if self._startup_notification:
                await self.bot.send_message(
                    chat_id=self.notify_chat_id,
                    text=(
                        ("🤖 <b>Scalping Engine Active!</b>\n\n" if not self._mixed_mode else "🤖 <b>Mixed Component Active (Scalping)</b>\n\n")
                        + ("⚡ <b>Mode: Scalping (5M)</b>\n\n" if not self._mixed_mode else "⚖️ <b>Mode: Mixed (Scalp Partition)</b>\n\n")
                        + "📊 Configuration:\n"
                        + f"• Timeframe: {self.config.timeframe}\n"
                        + f"• Scan interval: {self.config.scan_interval}s\n"
                        + f"• Min confidence: {self.config.min_confidence * 100:.0f}%\n"
                        + f"• Min R:R: 1:{self.config.min_rr}\n"
                        + f"• Max hold time: {self.config.max_hold_time // 60} minutes\n"
                        + f"• Max concurrent: {self.config.max_concurrent_positions} positions\n"
                        + f"• Assigned pairs: {len(self._active_scan_pairs)}\n\n"
                        + f"• Adaptive conf delta: {int(self._adaptive_overlay.get('conf_delta', 0)):+d}\n"
                        + f"• Adaptive vol delta: {float(self._adaptive_overlay.get('volume_min_ratio_delta', 0.0)):+.2f}\n"
                        + f"• Sideways governor: {str(self._sideways_governor_snapshot.get('mode', 'normal')).upper()}\n"
                        + f"• Win playbook tags: {len(self._win_playbook_snapshot.get('active_tags', []) or [])}\n"
                        + f"• Runtime risk overlay: {float(self._win_playbook_snapshot.get('risk_overlay_pct', 0.0)):+.2f}%\n"
                        + f"• Confidence adaptation: {'ON' if bool(self._confidence_adapt_snapshot.get('enabled', False)) else 'OFF'}\n"
                        + f"• Confidence active buckets: "
                        + f"{len((((self._confidence_adapt_snapshot.get('modes') or {}).get('scalping') or {}).get('active_adaptations') or []))}\n"
                        + f"• Risk parity regime: {str(self._scalp_risk_parity_snapshot.get('regime', 'disabled')).upper()} "
                        + f"(ratio={float(self._scalp_risk_parity_snapshot.get('ratio', 1.0) or 1.0):.3f})\n\n"
                        + f"Bot will scan for high-probability setups every {self.config.scan_interval} seconds.\n"
                        + "Patience = profit. 🎯"
                    ),
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.warning(f"[Scalping:{self.user_id}] Startup notification failed: {e}")
        
        scan_count = 0
        self._sideways_hourly_kpi_next = time.time() + 3600.0
        try:
            while self.running:
                try:
                    # ── Check Supabase stop signal ────────────────────────────
                    # Only stop if status is explicitly "stopped" AND engine_active=False
                    # This prevents race conditions where status briefly shows "stopped"
                    # during user restart flow
                    if await should_stop_engine(
                        self.user_id,
                        logger=logger,
                        label=f"[Scalping:{self.user_id}]",
                    ):
                        logger.info(f"[Scalping:{self.user_id}] Stop signal from Supabase (status=stopped, engine_active=False)")
                        self.running = False
                        try:
                            await self.bot.send_message(
                                chat_id=self.notify_chat_id,
                                text="🛑 <b>AutoTrade stopped.</b>\n\nUse /autotrade to restart.",
                                parse_mode='HTML'
                            )
                        except Exception:
                            pass
                        break

                    scan_count += 1
                    now_ts = time.time()
                    self._adaptive_next_refresh, self._adaptive_overlay, adaptive_refreshed, adaptive_err = await refresh_runtime_snapshot(
                        now_ts=now_ts,
                        next_refresh_ts=self._adaptive_next_refresh,
                        refresh_fn=refresh_global_adaptive_state,
                        snapshot_fn=get_adaptive_overrides,
                        current_snapshot=self._adaptive_overlay,
                        interval_sec=600.0,
                    )
                    if adaptive_refreshed:
                        logger.info(
                            f"[Scalping:{self.user_id}] Adaptive overlay refreshed — "
                            f"conf_delta={self._adaptive_overlay.get('conf_delta')} "
                            f"vol_delta={self._adaptive_overlay.get('volume_min_ratio_delta'):.2f} "
                            f"mode={self._adaptive_overlay.get('ob_fvg_requirement_mode')} "
                            f"loss_rate={self._adaptive_overlay.get('strategy_loss_rate'):.3f} "
                            f"sample={self._adaptive_overlay.get('strategy_sample_size')}"
                        )
                    elif adaptive_err:
                        logger.warning(f"[Scalping:{self.user_id}] Adaptive refresh failed: {adaptive_err}")

                    self._sideways_governor_next_refresh, self._sideways_governor_snapshot, governor_refreshed, governor_err = await refresh_runtime_snapshot(
                        now_ts=now_ts,
                        next_refresh_ts=self._sideways_governor_next_refresh,
                        refresh_fn=refresh_sideways_governor_state,
                        snapshot_fn=get_sideways_governor_snapshot,
                        current_snapshot=self._sideways_governor_snapshot,
                        interval_sec=600.0,
                    )
                    if governor_refreshed:
                        policy = get_sideways_entry_overrides(self._sideways_governor_snapshot)
                        logger.info(
                            f"[Scalping:{self.user_id}] Sideways governor refreshed | "
                            f"mode={policy.get('mode')} sample={policy.get('sample_size_24h')} "
                            f"exp={float(policy.get('sideways_expectancy_24h', 0.0)):+.6f} "
                            f"timeout_loss_rate={float(policy.get('sideways_timeout_loss_rate_24h', 0.0)):.3f} "
                            f"reason={policy.get('decision_reason')}"
                        )
                    elif governor_err:
                        logger.warning(f"[Scalping:{self.user_id}] Sideways governor refresh failed: {governor_err}")

                    self._win_playbook_next_refresh, self._win_playbook_snapshot, playbook_refreshed, playbook_err = await refresh_runtime_snapshot(
                        now_ts=now_ts,
                        next_refresh_ts=self._win_playbook_next_refresh,
                        refresh_fn=refresh_global_win_playbook_state,
                        snapshot_fn=get_win_playbook_snapshot,
                        current_snapshot=self._win_playbook_snapshot,
                        interval_sec=600.0,
                    )
                    if playbook_refreshed:
                        logger.info(
                            f"[Scalping:{self.user_id}] Win playbook refreshed — "
                            f"sample={self._win_playbook_snapshot.get('sample_size')} "
                            f"wr={float(self._win_playbook_snapshot.get('rolling_win_rate', 0.0)):.3f} "
                            f"exp={float(self._win_playbook_snapshot.get('rolling_expectancy', 0.0)):+.4f} "
                            f"overlay={float(self._win_playbook_snapshot.get('risk_overlay_pct', 0.0)):.2f}% "
                            f"active_tags={len(self._win_playbook_snapshot.get('active_tags', []) or [])}"
                        )
                    elif playbook_err:
                        logger.warning(f"[Scalping:{self.user_id}] Win playbook refresh failed: {playbook_err}")
                    self._confidence_adapt_next_refresh, self._confidence_adapt_snapshot, conf_adapt_refreshed, conf_adapt_err = await refresh_runtime_snapshot(
                        now_ts=now_ts,
                        next_refresh_ts=self._confidence_adapt_next_refresh,
                        refresh_fn=refresh_global_confidence_adaptation_state,
                        snapshot_fn=get_confidence_adaptation_snapshot,
                        current_snapshot=self._confidence_adapt_snapshot,
                        interval_sec=600.0,
                    )
                    if conf_adapt_refreshed:
                        mode_state = ((self._confidence_adapt_snapshot.get("modes") or {}).get("scalping") or {})
                        logger.info(
                            f"[Scalping:{self.user_id}] Confidence adaptation refreshed — "
                            f"enabled={bool(self._confidence_adapt_snapshot.get('enabled', False))} "
                            f"sample={int(mode_state.get('sample_size', 0) or 0)} "
                            f"active_buckets={len(mode_state.get('active_adaptations', []) or [])} "
                            f"top={((mode_state.get('top_bucket') or {}).get('bucket') or '-')}"
                        )
                    elif conf_adapt_err:
                        logger.warning(f"[Scalping:{self.user_id}] Confidence adaptation refresh failed: {conf_adapt_err}")
                    self._scalp_risk_parity_next_refresh, self._scalp_risk_parity_snapshot, parity_refreshed, parity_err = await refresh_runtime_snapshot(
                        now_ts=now_ts,
                        next_refresh_ts=self._scalp_risk_parity_next_refresh,
                        refresh_fn=refresh_scalping_risk_parity_state,
                        snapshot_fn=get_scalping_risk_parity_snapshot,
                        current_snapshot=self._scalp_risk_parity_snapshot,
                        interval_sec=600.0,
                    )
                    if parity_refreshed:
                        parity_controls = get_scalping_risk_parity_controls(self._scalp_risk_parity_snapshot)
                        logger.info(
                            f"[Scalping:{self.user_id}] Risk parity refreshed — "
                            f"enabled={bool(parity_controls.get('enabled', False))} "
                            f"regime={parity_controls.get('regime')} "
                            f"ratio={float(parity_controls.get('ratio', 1.0) or 1.0):.3f} "
                            f"target={float(parity_controls.get('target_min', 0.85) or 0.85):.2f}-"
                            f"{float(parity_controls.get('target_max', 1.0) or 1.0):.2f} "
                            f"cap_pct={float(parity_controls.get('cap_pct', 0.50) or 0.50):.2f}"
                        )
                    elif parity_err:
                        logger.warning(f"[Scalping:{self.user_id}] Risk parity refresh failed: {parity_err}")

                    if self._stale_reconcile_enabled and now_ts >= float(self._stale_reconcile_next_ts or 0.0):
                        await self._run_stale_reconcile("periodic")
                        self._stale_reconcile_next_ts = now_ts + float(self._stale_reconcile_interval_seconds)

                    if now_ts >= self._sideways_hourly_kpi_next:
                        policy = get_sideways_entry_overrides(self._sideways_governor_snapshot)
                        logger.info(
                            f"[Scalping:{self.user_id}] Sideways KPI hourly | "
                            f"mode={policy.get('mode')} "
                            f"expectancy_24h={float(policy.get('sideways_expectancy_24h', 0.0)):+.6f} "
                            f"timeout_loss_rate_24h={float(policy.get('sideways_timeout_loss_rate_24h', 0.0)):.3f} "
                            f"sample_24h={int(policy.get('sample_size_24h', 0) or 0)}"
                        )
                        self._sideways_hourly_kpi_next = now_ts + 3600.0
                    logger.info(f"[Scalping:{self.user_id}] Scan cycle #{scan_count} starting...")

                    # Monitor existing positions first (priority)
                    logger.info(f"[Scalping:{self.user_id}] Monitoring positions...")
                    await self._process_expired_positions()
                    await self.monitor_positions()
                    
                    # Scan for new signals in PARALLEL (dynamic top-volume universe).
                    if self._mixed_mode:
                        assignments = await get_mixed_pair_assignments(
                            user_id=int(self.user_id),
                            limit=10,
                            fallback_pairs=list(self.config.pairs),
                            logger_override=logger,
                            label=f"[Scalping:{self.user_id}]",
                        )
                        ranked_pairs = list(assignments.get("scalp") or [])
                    else:
                        ranked_pairs = await get_top_volume_pairs(
                            limit=10,
                            fallback_pairs=list(self.config.pairs),
                            logger=logger,
                            label=f"[Scalping:{self.user_id}]",
                        )
                    self._active_scan_pairs = ranked_pairs if self._mixed_mode else (ranked_pairs or list(self.config.pairs))
                    logger.info(
                        f"[Scalping:{self.user_id}] Scanning {len(self._active_scan_pairs)} "
                        + ("mixed scalp-routed" if self._mixed_mode else "top-volume")
                        + " pairs: "
                        + ", ".join(self._active_scan_pairs)
                    )
                    signals_found = 0
                    signals_validated = 0
                    
                    scan_tasks = []
                    for symbol in self._active_scan_pairs:
                        scan_tasks.append(self._scan_single_symbol(symbol))
                        
                    if scan_tasks and self.running:
                        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
                        
                        candidate_signals = []
                        for r in results:
                            if isinstance(r, Exception):
                                logger.error(f"[Scalping:{self.user_id}] Gathered exception: {r}")
                            elif r is not None:
                                candidate_signals.append(r)

                        normal_signals = [s for s in candidate_signals if not getattr(s, "is_emergency", False)]
                        emergency_signals = [s for s in candidate_signals if getattr(s, "is_emergency", False)]

                        if normal_signals:
                            valid_signals = normal_signals
                        elif emergency_signals:
                            best_emergency = max(
                                emergency_signals,
                                key=lambda s: float(getattr(s, "emergency_score", getattr(s, "confidence", 0)))
                            )
                            valid_signals = [best_emergency]
                            logger.info(
                                f"[Scalping:{self.user_id}] Emergency candidate selected: "
                                f"{best_emergency.symbol} {best_emergency.side} "
                                f"(score={getattr(best_emergency, 'emergency_score', best_emergency.confidence):.2f})"
                            )
                        else:
                            valid_signals = []

                        v2_mode = "legacy"
                        try:
                            from app.decision_tree_v2_config import get_v2_mode, should_apply
                            from app.decision_coordinator import evaluate_scalping_signal

                            v2_mode = str(get_v2_mode() or "legacy")
                            apply_v2 = bool(valid_signals) and should_apply("scalping", mixed_mode=self._mixed_mode)
                            if valid_signals:
                                logger.info(
                                    f"[Scalping:{self.user_id}] Decision Tree V2 "
                                    f"mode={v2_mode} apply={apply_v2} candidates={len(valid_signals)}"
                                )
                            if apply_v2:
                                evaluated_signals = []
                                for signal in valid_signals:
                                    decision = await evaluate_scalping_signal(
                                        user_id=int(self.user_id),
                                        signal=signal,
                                        client=self.client,
                                        runtime_snapshots={
                                            "adaptive": self._adaptive_overlay,
                                            "win_playbook": self._win_playbook_snapshot,
                                            "confidence_adaptation": self._confidence_adapt_snapshot,
                                            "sideways_governor": self._sideways_governor_snapshot,
                                            "risk_parity": self._scalp_risk_parity_snapshot,
                                        },
                                        mixed_mode=bool(self._mixed_mode),
                                    )
                                    setattr(signal, "decision_trace_id", decision.candidate.decision_trace_id)
                                    setattr(signal, "decision_mode_version", "decision_tree_v2")
                                    setattr(signal, "decision_regime", decision.candidate.regime)
                                    setattr(signal, "decision_final_score", float(decision.candidate.final_score or 0.0))
                                    setattr(signal, "decision_quality_score", float(decision.candidate.metadata.get("decision_quality_score", 0.0) or 0.0))
                                    setattr(signal, "decision_community_score", float(decision.candidate.community_score or 0.0))
                                    setattr(signal, "decision_user_segment_score", float(decision.candidate.user_segment_score or 0.0))
                                    setattr(signal, "decision_display_reason", str(decision.display_reason or ""))
                                    setattr(signal, "decision_reject_reason", str(decision.reject_reason or ""))
                                    setattr(signal, "participation_bucket", str(decision.candidate.participation_bucket or ""))
                                    setattr(signal, "quality_bucket", str(decision.candidate.quality_bucket or ""))
                                    if float(decision.candidate.recommended_risk_pct or 0.0) > 0.0:
                                        setattr(signal, "effective_risk_pct", float(decision.candidate.recommended_risk_pct))
                                    if decision.approved or v2_mode != "live":
                                        evaluated_signals.append(signal)
                                    else:
                                        logger.info(
                                            f"[Scalping:{self.user_id}] V2 rejected signal "
                                            f"symbol={signal.symbol} reason={decision.reject_reason or '-'} "
                                            f"score={float(decision.candidate.final_score or 0.0):.3f}"
                                        )
                                valid_signals = evaluated_signals
                        except Exception as v2_exc:
                            logger.warning(f"[Scalping:{self.user_id}] Decision Tree V2 evaluation skipped: {v2_exc}")

                        signals_found += len(valid_signals)
                        
                        # Sequentially process the returned valid signals
                        for signal in valid_signals:
                            if not self.running:
                                break
                                
                            # Re-check concurrent safety limits safely in the sequential block
                            if not await self._ensure_capacity_for_entry():
                                break
                            
                            if signal.symbol in self.positions:
                                continue
                                
                            signals_validated += 1
                            logger.info(f"[Scalping:{self.user_id}] {signal.symbol} - Signal validated! Placing order...")
                            
                            success = await self.place_scalping_order(signal)
                            
                            if success:
                                self.mark_cooldown(signal.symbol)
                                logger.info(f"[Scalping:{self.user_id}] {signal.symbol} - Order placed successfully!")
                            else:
                                # Avoid hammering non-executable symbols in emergency mode.
                                # Preserve stale-price cooldown when already set.
                                self._apply_generic_failure_cooldown(signal.symbol, ttl_sec=300.0)
                                logger.warning(f"[Scalping:{self.user_id}] {signal.symbol} - Order placement failed")
                    
                    logger.info(
                        f"[Scalping:{self.user_id}] Scan #{scan_count} complete: "
                        f"{signals_found} signals found, {signals_validated} validated"
                    )
                    
                    # Wait for next scan
                    logger.debug(f"[Scalping:{self.user_id}] Sleeping for {self.config.scan_interval}s...")
                    await asyncio.sleep(self.config.scan_interval)
                
                except Exception as e:
                    logger.error(f"[Scalping:{self.user_id}] Error in main loop: {e}")
                    import traceback
                    traceback.print_exc()
                    await asyncio.sleep(self.config.scan_interval)
        
        finally:
            self.running = False
            logger.info(f"[Scalping:{self.user_id}] Engine stopped after {scan_count} scan cycles")
    
    def stop(self):
        """Stop the trading loop"""
        self.running = False
        logger.info(f"[Scalping:{self.user_id}] Stop requested")

    
    async def _scan_single_symbol(self, symbol: str) -> Optional[ScalpingSignal]:
        try:
            if len(self.positions) >= self.config.max_concurrent_positions:
                if not await self._ensure_capacity_for_entry():
                    return None
            if self.check_cooldown(symbol):
                return None
                
            signal = await self.generate_scalping_signal(symbol)
            if signal is not None:
                if not self.validate_scalping_entry(signal):
                    signal = None
                elif not self._passes_anti_flip_filters(signal):
                    signal = None
                else:
                    setattr(signal, "is_emergency", False)
                    if not getattr(signal, "trade_subtype", ""):
                        setattr(signal, "trade_subtype", "trend_scalp")
                    return signal

            if not getattr(self.config, "emergency_candidate_mode", False):
                return None

            emergency_signal = await self._generate_emergency_candidate(symbol)
            if emergency_signal is None:
                return None
            if not self.validate_scalping_entry(emergency_signal):
                return None
            if not self._passes_anti_flip_filters(emergency_signal):
                return None

            setattr(emergency_signal, "is_emergency", True)
            if not getattr(emergency_signal, "trade_subtype", ""):
                setattr(emergency_signal, "trade_subtype", "trend_scalp")
            setattr(
                emergency_signal,
                "emergency_score",
                float(emergency_signal.confidence) + (float(emergency_signal.rr_ratio) * 8.0) + (float(getattr(emergency_signal, "volume_ratio", 1.0)) * 4.0),
            )
            return emergency_signal
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error in _scan_single_symbol for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
            
    async def generate_scalping_signal(self, symbol: str) -> Optional[ScalpingSignal]:
        """
        Generate 5M scalping signal with 15M trend validation (ASYNC with caching)
        
        Algorithm:
        1. Check trading mode — sideways pipeline only in SCALPING mode
        2. If SCALPING mode, try sideways signal first
        3. Fall through to trending signal (existing logic unchanged)
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            ScalpingSignal or MicroScalpSignal object, or None
        """
        try:
            # Check trading mode — sideways only for scalping mode
            from app.trading_mode_manager import TradingModeManager
            from app.trading_mode import TradingMode
            mode = TradingModeManager.get_mode(self.user_id)
            sideways_policy = get_sideways_entry_overrides(self._sideways_governor_snapshot)

            if mode in (TradingMode.SCALPING, TradingMode.MIXED):
                if bool(sideways_policy.get("allow_sideways_entries", True)):
                    # Try sideways detection first
                    sideways_signal = await self._try_sideways_signal(symbol)
                    if sideways_signal is not None:
                        return sideways_signal
                else:
                    logger.info(
                        f"[Scalping:{self.user_id}] {symbol} sideways entry paused by governor "
                        f"(mode={sideways_policy.get('mode')})"
                    )

            # Fall through to trending signal (existing logic unchanged)
            from app.autosignal_async import compute_signal_scalping_async

            # Generate signal using async version with caching
            signal_dict = await compute_signal_scalping_async(symbol.replace("USDT", ""))
            
            if not signal_dict:
                return None
            
            # Convert dict to ScalpingSignal object
            signal = ScalpingSignal(
                symbol=signal_dict["symbol"],
                side=signal_dict["side"],
                confidence=signal_dict["confidence"],
                entry_price=signal_dict["entry_price"],
                tp_price=signal_dict["tp"],
                sl_price=signal_dict["sl"],
                rr_ratio=signal_dict["rr_ratio"],
                atr_pct=signal_dict["atr_pct"],
                volume_ratio=signal_dict["vol_ratio"],
                rsi_5m=signal_dict["rsi_5m"],
                trend_15m=signal_dict["trend_15m"],
                reasons=signal_dict["reasons"]
            )
            setattr(signal, "trade_subtype", "trend_scalp")
            
            logger.info(
                f"[Scalping:{self.user_id}] Signal generated: {symbol} {signal.side} "
                f"@ {signal.entry_price:.4f} (confidence: {signal.confidence}%)"
            )
            
            return signal
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error generating signal for {symbol}: {e}")
            return None

    async def _generate_emergency_candidate(self, symbol: str) -> Optional[ScalpingSignal]:
        """
        Emergency candidate mode:
        Build a conservative fallback candidate when normal logic produces nothing.
        Safety checks are still enforced by validate_scalping_entry().
        """
        try:
            from app.candle_cache import get_candles_cached
            from app.providers.alternative_klines_provider import alternative_klines_provider

            base_symbol = symbol.replace("USDT", "").upper()

            async def fetch_klines_async(sym, interval, limit):
                source_orders = [
                    ["bitunix", "binance", "cryptocompare", "coingecko"],
                    ["binance", "bitunix", "cryptocompare", "coingecko"],
                ]
                for order in source_orders:
                    data = await asyncio.to_thread(
                        alternative_klines_provider.get_klines,
                        sym, interval, limit, order
                    )
                    if data:
                        return data
                return []

            raw_5m = await get_candles_cached(fetch_klines_async, base_symbol, "5m", 80)
            if not raw_5m or len(raw_5m) < 40:
                return None

            closes = [float(k[4]) for k in raw_5m]
            highs = [float(k[2]) for k in raw_5m]
            lows = [float(k[3]) for k in raw_5m]
            vols = [float(k[5]) for k in raw_5m]
            price = closes[-1]
            if price <= 0:
                return None

            def _ema(values, period):
                if len(values) < period:
                    return values[-1]
                k = 2 / (period + 1)
                e = sum(values[:period]) / period
                for v in values[period:]:
                    e = v * k + e * (1 - k)
                return e

            def _rsi(values, period=14):
                if len(values) < period + 1:
                    return 50.0
                gains = []
                losses = []
                for i in range(1, len(values)):
                    d = values[i] - values[i - 1]
                    gains.append(max(d, 0.0))
                    losses.append(max(-d, 0.0))
                avg_gain = sum(gains[-period:]) / period
                avg_loss = sum(losses[-period:]) / period
                if avg_loss == 0:
                    return 100.0
                rs = avg_gain / avg_loss
                return 100 - (100 / (1 + rs))

            ema21 = _ema(closes, 21)
            ema50 = _ema(closes, 50)
            rsi_5m = _rsi(closes, 14)

            tr = []
            for i in range(1, len(closes)):
                tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
            atr = (sum(tr[-14:]) / 14) if len(tr) >= 14 else 0.0
            atr_pct = (atr / price) * 100 if price > 0 else 0.0
            if atr_pct < max(0.08, self.config.min_atr_pct * 0.6):
                return None

            avg_vol = sum(vols[-21:-1]) / 20 if len(vols) >= 21 else (sum(vols[:-1]) / max(1, len(vols) - 1))
            vol_ratio = (vols[-1] / avg_vol) if avg_vol > 0 else 0.0
            if vol_ratio < getattr(self.config, "emergency_min_volume_ratio", 0.9):
                return None

            side = None
            if ema21 >= ema50 and rsi_5m <= 62:
                side = "LONG"
            elif ema21 <= ema50 and rsi_5m >= 38:
                side = "SHORT"
            if side is None:
                return None

            sl_distance = max(atr * 1.15, price * 0.0025)
            tp_distance = sl_distance * 1.6
            if side == "LONG":
                sl = price - sl_distance
                tp = price + tp_distance
                trend_15m = "LONG"
            else:
                sl = price + sl_distance
                tp = price - tp_distance
                trend_15m = "SHORT"

            rr = tp_distance / sl_distance if sl_distance > 0 else 0.0
            confidence = min(82, max(72, int(72 + max(0.0, (vol_ratio - 1.0) * 8.0) + (2 if atr_pct > 0.4 else 0))))

            signal = ScalpingSignal(
                symbol=symbol,
                side=side,
                confidence=confidence,
                entry_price=price,
                tp_price=tp,
                sl_price=sl,
                rr_ratio=rr,
                atr_pct=atr_pct,
                volume_ratio=vol_ratio,
                rsi_5m=rsi_5m,
                trend_15m=trend_15m,
                reasons=[
                    "Emergency candidate mode (top-ranked fallback)",
                    f"EMA21/50={ema21:.4f}/{ema50:.4f}, RSI={rsi_5m:.1f}",
                    f"ATR={atr_pct:.2f}%, Volume={vol_ratio:.2f}x",
                ],
            )
            return signal
        except Exception as e:
            logger.debug(f"[Scalping:{self.user_id}] Emergency candidate error for {symbol}: {e}")
            return None

    async def _try_sideways_signal(self, symbol: str):
        """
        Try to generate a sideways micro-scalp signal.
        Returns MicroScalpSignal if valid, None otherwise (fall through to trending).
        """
        try:
            from app.candle_cache import get_candles_cached
            from app.providers.alternative_klines_provider import alternative_klines_provider
            from app.sideways_detector import SidewaysDetector
            from app.range_analyzer import RangeAnalyzer
            from app.bounce_detector import BounceDetector
            from app.rsi_divergence_detector import RSIDivergenceDetector
            from app.trading_mode import MicroScalpSignal
            sideways_policy = get_sideways_entry_overrides(self._sideways_governor_snapshot)
            allow_fallback = bool(sideways_policy.get("allow_sideways_fallback", True))

            base_symbol = symbol.replace("USDT", "").upper()

            # Wrap sync get_klines in async with cache
            async def fetch_klines_async(sym, interval, limit):
                source_orders = [
                    ["bitunix", "binance", "cryptocompare", "coingecko"],
                    ["binance", "bitunix", "cryptocompare", "coingecko"],
                    ["binance", "cryptocompare", "bitunix", "coingecko"],
                ]
                for order in source_orders:
                    data = await asyncio.to_thread(
                        alternative_klines_provider.get_klines,
                        sym, interval, limit, order
                    )
                    if data:
                        return data
                return []

            # Fetch klines (list format: [timestamp, open, high, low, close, volume, ...])
            raw_5m = await get_candles_cached(fetch_klines_async, base_symbol, "5m", 50)
            raw_15m = await get_candles_cached(fetch_klines_async, base_symbol, "15m", 60)

            if not raw_5m or not raw_15m:
                logger.warning(
                    f"[Scalping:{self.user_id}] {symbol} partial feed outage in sideways path "
                    f"(5m={len(raw_5m) if raw_5m else 0}, 15m={len(raw_15m) if raw_15m else 0})"
                )
                return None

            # Convert list format to dict format expected by detectors
            def to_dict_candles(raw):
                result = []
                for k in raw:
                    result.append({
                        'open':   float(k[1]),
                        'high':   float(k[2]),
                        'low':    float(k[3]),
                        'close':  float(k[4]),
                        'volume': float(k[5]),
                    })
                return result

            candles_5m = to_dict_candles(raw_5m)
            candles_15m = to_dict_candles(raw_15m)

            price = candles_5m[-1]['close']
            if price == 0:
                return None

            # Step 1: Detect sideways
            try:
                sideways_result = SidewaysDetector().detect(candles_5m, candles_15m, price)
            except Exception as e:
                self._increment_sideways_error(symbol)
                logger.error(f"[Scalping:{self.user_id}] SidewaysDetector error for {symbol}: {e}")
                return None

            if not sideways_result.is_sideways:
                return None  # Market is trending, use trending logic

            logger.info(f"[Scalping:{self.user_id}] {symbol} SIDEWAYS detected: {sideways_result.reason}")

            # Step 2: Identify range S/R (optional — used for room check)
            try:
                range_result = RangeAnalyzer().analyze(candles_5m, price)
            except Exception as e:
                self._increment_sideways_error(symbol)
                logger.error(f"[Scalping:{self.user_id}] RangeAnalyzer error for {symbol}: {e}")
                range_result = None

            support = range_result.support if range_result else None
            resistance = range_result.resistance if range_result else None

            # Step 3: Try bounce signal first (classic S/R bounce)
            bounce_result = None
            if range_result:
                try:
                    bounce_result = BounceDetector().detect(
                        last_candle=candles_5m[-1],
                        support=range_result.support,
                        resistance=range_result.resistance,
                        price=price,
                    )
                except Exception as e:
                    self._increment_sideways_error(symbol)
                    logger.error(f"[Scalping:{self.user_id}] BounceDetector error for {symbol}: {e}")

            # Step 3b: If no bounce, try micro momentum (1M/3M EMA crossover)
            if bounce_result is None:
                try:
                    from app.micro_momentum_detector import MicroMomentumDetector
                    raw_1m = await get_candles_cached(fetch_klines_async, base_symbol, "1m", 30)
                    raw_3m = await get_candles_cached(fetch_klines_async, base_symbol, "3m", 15)

                    if raw_1m and raw_3m:
                        candles_1m = to_dict_candles(raw_1m)
                        candles_3m = to_dict_candles(raw_3m)

                        momentum_signal = MicroMomentumDetector().detect(
                            candles_1m=candles_1m,
                            candles_3m=candles_3m,
                            candles_5m=candles_5m,
                            price=price,
                            support=support,
                            resistance=resistance,
                        )

                        if momentum_signal:
                            logger.info(
                                f"[Scalping:{self.user_id}] {symbol} MICRO MOMENTUM signal: "
                                f"{momentum_signal.direction} | {momentum_signal.reason}"
                            )
                            # Return as MicroScalpSignal
                            reasons = [
                                f"Sideways market: {sideways_result.reason}",
                                f"Micro momentum: {momentum_signal.reason}",
                            ]
                            if range_result:
                                reasons.insert(1, f"Range: {range_result.support:.4f} - {range_result.resistance:.4f}")

                            signal = MicroScalpSignal(
                                symbol=symbol,
                                side=momentum_signal.direction,
                                entry_price=momentum_signal.entry_price,
                                tp_price=momentum_signal.tp_price,
                                sl_price=momentum_signal.sl_price,
                                rr_ratio=momentum_signal.rr_ratio,
                                range_support=support or price * 0.995,
                                range_resistance=resistance or price * 1.005,
                                range_width_pct=range_result.range_width_pct if range_result else 0.5,
                                confidence=momentum_signal.confidence,
                                bounce_confirmed=False,
                                rsi_divergence_detected=False,
                                volume_ratio=1.0,
                                reasons=reasons,
                            )
                            setattr(signal, "trade_subtype", "sideways_scalp")
                            return signal
                except Exception as e:
                    logger.warning(f"[Scalping:{self.user_id}] MicroMomentum error for {symbol}: {e}")

            if bounce_result is None:
                if not allow_fallback:
                    logger.debug(
                        f"[Scalping:{self.user_id}] {symbol} sideways fallback disabled "
                        f"(mode={sideways_policy.get('mode')})"
                    )
                    return None
                logger.info(
                    f"[Scalping:{self.user_id}] {symbol} sideways fallback retired after loss review; "
                    "waiting for confirmed bounce or momentum trigger"
                )
                logger.debug(f"[Scalping:{self.user_id}] {symbol} No bounce/momentum signal")
                return None

            direction = bounce_result.direction  # "LONG" or "SHORT"

            # Step 4: RSI divergence (optional bonus, don't fail if error)
            divergence_bonus = 0
            rsi_divergence_detected = False
            divergence_reason = ""
            try:
                div_result = RSIDivergenceDetector().detect(candles_5m, direction)
                divergence_bonus = div_result.confidence_bonus
                rsi_divergence_detected = div_result.detected
                divergence_reason = div_result.reason
            except Exception as e:
                logger.warning(f"[Scalping:{self.user_id}] RSIDivergenceDetector error (continuing): {e}")

            # Step 5: Calculate confidence
            base_confidence = 70

            # Volume bonus: current volume > 1.5x average of last 20 candles
            volume_bonus = 0
            volume_ratio = 0
            try:
                volumes = [float(c.get('volume', 0)) for c in candles_5m[-21:-1]]
                avg_volume = sum(volumes) / len(volumes) if volumes else 0
                current_volume = float(candles_5m[-1].get('volume', 0))
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                if volume_ratio > 1.5:
                    volume_bonus = 5
            except Exception:
                volume_ratio = 0

            # Range width bonus: 1.0% - 2.0% is ideal
            range_bonus = 5 if 1.0 <= range_result.range_width_pct <= 2.0 else 0

            confidence = min(95, base_confidence + divergence_bonus + volume_bonus + range_bonus)

            # Relaxed confidence threshold for sideways (70% vs 75%)
            if confidence < 70:
                logger.debug(f"[Scalping:{self.user_id}] {symbol} Sideways confidence too low: {confidence}")
                return None

            # Calculate ATR (14 periods) to dynamically pad SL buffer
            atr = 0
            if len(candles_5m) > 14:
                tr_list = []
                for i in range(1, len(candles_5m)):
                    c = candles_5m[i]
                    p = candles_5m[i-1]
                    high = c['high']
                    low = c['low']
                    prev_close = p['close']
                    tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                    tr_list.append(tr)
                atr = sum(tr_list[-14:]) / 14 if len(tr_list) >= 14 else 0

            # Step 6: Calculate TP/SL
            entry = price
            # Dynamic volatility buffer: 0.75x ATR. If ATR fails, fallback to 0.35%
            sl_buffer_price = (atr * 0.75) if atr > 0 else (entry * 0.0035)

            if direction == "LONG":
                tp = entry + 0.70 * (range_result.resistance - entry)
                sl = range_result.support - sl_buffer_price
            else:  # SHORT
                tp = entry - 0.70 * (entry - range_result.support)
                sl = range_result.resistance + sl_buffer_price

            # Step 7: Validate R:R
            if direction == "LONG":
                rr = (tp - entry) / (entry - sl) if (entry - sl) > 0 else 0
            else:
                rr = (entry - tp) / (sl - entry) if (sl - entry) > 0 else 0

            if rr < 1.0:
                logger.debug(f"[Scalping:{self.user_id}] {symbol} Sideways R:R too low: {rr:.2f}")
                return None

            # Build reasons
            reasons = [
                f"Sideways market: {sideways_result.reason}",
                f"Range: {range_result.support:.4f} - {range_result.resistance:.4f} ({range_result.range_width_pct:.2f}%)",
                bounce_result.reason,
            ]
            if divergence_reason:
                reasons.append(divergence_reason)

            # Reset error counter on success
            self.sideways_error_counter[symbol] = 0

            signal = MicroScalpSignal(
                symbol=symbol,
                side=direction,
                entry_price=entry,
                tp_price=round(tp, 6),
                sl_price=round(sl, 6),
                rr_ratio=round(rr, 2),
                range_support=range_result.support,
                range_resistance=range_result.resistance,
                range_width_pct=range_result.range_width_pct,
                confidence=confidence,
                bounce_confirmed=True,
                rsi_divergence_detected=rsi_divergence_detected,
                volume_ratio=volume_ratio,
                reasons=reasons,
            )
            setattr(signal, "trade_subtype", "sideways_scalp")
            return signal

        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] _try_sideways_signal error for {symbol}: {e}")
            return None

    def _increment_sideways_error(self, symbol: str):
        """Increment error counter and apply cooldown if threshold reached."""
        self.sideways_error_counter[symbol] = self.sideways_error_counter.get(symbol, 0) + 1
        if self.sideways_error_counter[symbol] >= 3:
            self.cooldown_tracker[symbol] = time.time() + 300  # 5 min cooldown
            self.sideways_error_counter[symbol] = 0
            logger.warning(
                f"[Scalping:{self.user_id}] {symbol} sideways error threshold reached, cooldown 5min"
            )

    def _passes_anti_flip_filters(self, signal) -> bool:
        """Require directional stability + block rapid opposite re-entry."""
        now = time.time()
        symbol = signal.symbol
        direction = signal.side  # LONG / SHORT
        is_sideways = bool(getattr(signal, "is_sideways", False))
        sideways_policy = get_sideways_entry_overrides(self._sideways_governor_snapshot)

        # 1) Consecutive confirmation gate (stability filter)
        required = int(getattr(self.config, "signal_confirmations_required", 2))
        if is_sideways:
            required = max(required, int(sideways_policy.get("sideways_confirmations_required", 1) or 1))
        max_gap = int(getattr(self.config, "signal_confirmation_max_gap_seconds", 45))
        streak = self.signal_streaks.get(symbol)
        if not isinstance(streak, dict):
            streak = None
            self.signal_streaks[symbol] = None
        if not streak:
            self.signal_streaks[symbol] = {"direction": direction, "count": 1, "ts": now}
            if required > 1:
                logger.info(f"[Scalping:{self.user_id}] {symbol} anti-flip: first {direction} signal seen, waiting confirmation")
                return False
            streak = self.signal_streaks[symbol]

        last_dir = streak.get("direction")
        last_ts = float(streak.get("ts", 0))
        last_count = int(streak.get("count", 0))
        if direction == last_dir and now - last_ts <= max_gap:
            new_count = last_count + 1
            self.signal_streaks[symbol] = {"direction": direction, "count": new_count, "ts": now}
            if new_count < required:
                logger.info(f"[Scalping:{self.user_id}] {symbol} anti-flip: streak {new_count}/{required}, waiting")
                return False
        else:
            self.signal_streaks[symbol] = {"direction": direction, "count": 1, "ts": now}
            if required > 1:
                logger.info(f"[Scalping:{self.user_id}] {symbol} anti-flip: direction changed/reset to {direction}, waiting confirmation")
                return False

        # 2) Opposite-direction re-entry cooldown after close
        closed = self.last_closed_meta.get(symbol)
        if closed:
            closed_ts = float(closed.get("ts", 0))
            closed_side = closed.get("side")  # BUY / SELL
            closed_reason = str(closed.get("reason", ""))
            opposite_block = int(getattr(self.config, "anti_flip_opposite_seconds", 600))
            if "sideways" in closed_reason:
                opposite_block = max(opposite_block, int(getattr(self.config, "sideways_reentry_cooldown_seconds", 420)))

            is_opposite = (closed_side == "BUY" and direction == "SHORT") or (closed_side == "SELL" and direction == "LONG")
            if is_opposite and (now - closed_ts) < opposite_block:
                wait_left = int(opposite_block - (now - closed_ts))
                logger.info(
                    f"[Scalping:{self.user_id}] {symbol} anti-flip: blocked opposite re-entry "
                    f"{direction} for {wait_left}s after close_reason={closed_reason}"
                )
                return False

        # Streak consumed for this execution cycle
        self.signal_streaks.pop(symbol, None)
        return True

    @staticmethod
    def _effective_risk_pct_from_qty(
        *,
        entry_price: float,
        sl_price: float,
        quantity: float,
        equity: float,
    ) -> float:
        try:
            eq = float(equity or 0.0)
            if eq <= 0:
                return 0.0
            risk_amount = abs(float(entry_price) - float(sl_price)) * max(0.0, float(quantity or 0.0))
            return max(0.0, (risk_amount / eq) * 100.0)
        except Exception:
            return 0.0

    def calculate_position_size_pro(
        self,
        symbol: str,
        entry_price: float,
        sl_price: float,
        capital: float,
        leverage: int,
        effective_risk_pct_override: Optional[float] = None,
        notional_cap_pct: Optional[float] = None,
    ) -> tuple:
        """
        Calculate position size based on risk % per trade (PRO TRADER METHOD)
        
        SCALPING MODE: MAXIMUM 5% RISK PER TRADE (SAFETY FIRST!)
        
        Args:
            entry_price: Entry price
            sl_price: Stop loss price
            capital: Total trading capital
            leverage: Leverage multiplier (will be capped at 10x for scalping)
            
        Returns:
            (position_size, used_risk_sizing, sizing_meta)
        """
        try:
            # Auto Max-Safe leverage is passed in from caller
            # leverage = min(leverage, 10)  # Removed hardcoded cap
            
            # Get base risk percentage from database
            from app.supabase_repo import get_risk_per_trade
            base_risk_pct = float(get_risk_per_trade(self.user_id) or 1.0)
            base_risk_pct = max(0.25, min(base_risk_pct, 5.0))
            if effective_risk_pct_override is None:
                risk_pct = base_risk_pct
            else:
                risk_pct = max(0.25, min(float(effective_risk_pct_override), 10.0))
            
            # Get current balance from exchange
            acc_result = self.client.get_account_info()
            if not acc_result.get('success'):
                raise Exception(f"Account info fetch failed: {acc_result.get('error')}")

            available = float(acc_result.get('available', 0) or 0)
            frozen = float(acc_result.get('frozen', 0) or 0)
            unrealized = float(acc_result.get('total_unrealized_pnl', 0) or 0)
            equity = available + frozen + unrealized
            if equity <= 0:
                raise Exception(
                    f"Invalid equity: available={available:.2f} + frozen={frozen:.2f} + "
                    f"unrealized={unrealized:.2f} = {equity:.2f}"
                )
            
            # Calculate position size using risk-based formula
            from app.position_sizing import calculate_position_size
            sizing = calculate_position_size(
                balance=equity,
                risk_pct=risk_pct,
                entry_price=entry_price,
                sl_price=sl_price,
                leverage=leverage,
                symbol=symbol,
            )
            
            if not sizing['valid']:
                raise Exception(f"Position sizing invalid: {sizing['error']}")
            
            qty = sizing['qty']
            
            # SAFETY CHECK: Ensure position size is reasonable
            position_value = qty * entry_price
            cap_pct = max(0.10, min(float(notional_cap_pct or 0.50), 1.00))
            max_position_value = equity * cap_pct
            cap_hit = False
            
            if position_value > max_position_value:
                logger.warning(
                    f"[Scalping:{self.user_id}] Position too large! "
                    f"${position_value:.2f} > ${max_position_value:.2f} ({cap_pct*100:.1f}% of equity). "
                    f"Reducing to safe size."
                )
                qty = (max_position_value / entry_price) * 0.9  # 90% of max for safety margin
                cap_hit = True

            applied_risk_pct = self._effective_risk_pct_from_qty(
                entry_price=entry_price,
                sl_price=sl_price,
                quantity=qty,
                equity=equity,
            )
            sizing_meta = {
                "equity": float(equity),
                "risk_target_pct": float(risk_pct),
                "applied_risk_pct": float(applied_risk_pct),
                "notional_cap_pct": float(cap_pct),
                "cap_hit": bool(cap_hit),
                "fallback_mode": "",
            }
            
            logger.info(
                f"[Scalping:{self.user_id}] RISK-BASED sizing: "
                f"Equity=${equity:.2f} (Available=${available:.2f} + Frozen=${frozen:.2f} + Unrealized=${unrealized:.2f}), "
                f"BaseRisk={base_risk_pct}% EffectiveRisk={risk_pct}%, "
                f"Leverage={leverage}x (Auto Max-Safe), "
                f"Entry=${entry_price:.2f}, SL=${sl_price:.2f}, "
                f"SL_Dist={sizing['sl_distance_pct']:.2f}%, "
                f"Position=${sizing['position_size_usdt']:.2f}, "
                f"Margin=${sizing['margin_required']:.2f}, "
                f"Qty={qty}, Risk_Amt=${sizing['risk_amount']:.2f}, "
                f"CapPct={cap_pct*100:.1f}% CapHit={cap_hit} AppliedRisk={applied_risk_pct:.3f}%"
            )
            
            return qty, True, sizing_meta  # Success - used risk-based sizing
            
        except Exception as e:
            logger.warning(
                f"[Scalping:{self.user_id}] Risk sizing FAILED: {e} - "
                f"Falling back to ULTRA-SAFE 2% method"
            )
            
            # FALLBACK: Use ULTRA-SAFE 2% risk method
            risk_per_trade_pct = 0.02  # 2% ONLY
            risk_amount = capital * risk_per_trade_pct
            
            # Calculate SL distance in %
            sl_distance_pct = abs(entry_price - sl_price) / entry_price
            
            # Position size = Risk Amount / SL Distance
            position_size_usdt = risk_amount / sl_distance_pct
            
            # SAFETY: Hard fallback cap at max 20% capital
            fallback_cap_pct = min(max(0.10, min(float(notional_cap_pct or 0.50), 1.00)), 0.20)
            max_position_usdt = capital * fallback_cap_pct
            cap_hit = False
            if position_size_usdt > max_position_usdt:
                logger.warning(
                    f"[Scalping:{self.user_id}] Fallback position too large! "
                    f"${position_size_usdt:.2f} > ${max_position_usdt:.2f}. Capping."
                )
                position_size_usdt = max_position_usdt
                cap_hit = True
            
            # Convert to base currency
            position_size = position_size_usdt / entry_price
            applied_risk_pct = self._effective_risk_pct_from_qty(
                entry_price=entry_price,
                sl_price=sl_price,
                quantity=position_size,
                equity=capital,
            )
            sizing_meta = {
                "equity": float(capital),
                "risk_target_pct": float(risk_per_trade_pct * 100.0),
                "applied_risk_pct": float(applied_risk_pct),
                "notional_cap_pct": float(fallback_cap_pct),
                "cap_hit": bool(cap_hit),
                "fallback_mode": "fixed_2pct",
            }
            
            logger.info(
                f"[Scalping:{self.user_id}] FALLBACK sizing: "
                f"Capital=${capital:.2f}, Risk=${risk_amount:.2f} (2%), "
                f"SL Distance={sl_distance_pct:.2%}, "
                f"Position=${position_size_usdt:.2f} (cap={fallback_cap_pct*100:.1f}%), "
                f"Quantity={position_size:.6f}, AppliedRisk={applied_risk_pct:.3f}%"
            )
            
            return position_size, False, sizing_meta  # Fallback used
    
    def is_optimal_trading_time(
        self,
        parity_controls: Optional[Dict[str, Any]] = None,
        hour_utc: Optional[int] = None,
    ) -> tuple:
        """
        Check if current time is optimal for scalping
        
        Crypto has high/low volatility hours:
        - Best: 12:00-20:00 UTC (EU + US overlap) - High volume, clear trends
        - Good: 08:00-12:00 UTC (EU open) - Good volume
        - Avoid: 00:00-06:00 UTC (Asian session) - Low volume, whipsaw
        
        Returns:
            (should_trade: bool, position_size_multiplier: float)
        """
        if hour_utc is None:
            hour_utc = datetime.utcnow().hour
        controls = parity_controls or {}
        profile = dict((controls.get("time_profile") or {}))
        mult_best = max(0.0, min(float(profile.get("best", 1.0) or 1.0), 1.0))
        mult_good = max(0.0, min(float(profile.get("good", 0.7) or 0.7), 1.0))
        mult_neutral = max(0.0, min(float(profile.get("neutral", 0.5) or 0.5), 1.0))
        mult_avoid = max(0.0, min(float(profile.get("avoid", 0.0) or 0.0), 1.0))
        
        # Best hours: 12:00-20:00 UTC (EU + US overlap)
        if 12 <= hour_utc < 20:
            return mult_best > 0.0, mult_best
        
        # Good hours: 08:00-12:00 UTC (EU open)
        elif 8 <= hour_utc < 12:
            return mult_good > 0.0, mult_good
        
        # Avoid: 00:00-06:00 UTC (Asian session)
        elif 0 <= hour_utc < 6:
            if mult_avoid <= 0.0:
                logger.info(f"[Scalping:{self.user_id}] Skipping trade - Asian session (low volume)")
            return mult_avoid > 0.0, mult_avoid
        
        # Neutral: Other hours
        else:
            return mult_neutral > 0.0, mult_neutral
    
    def calculate_scalping_tp_sl(self, entry: float, direction: str, atr: float) -> tuple:
        """
        Calculate single TP at 1.5R and SL using ATR with slippage buffer
        
        Formula:
        - SL distance = 1.5 * ATR (5M)
        - TP distance = 1.5 * SL distance (R:R 1:1.5)
        - Slippage buffer = 0.05% (0.03% slippage + 0.02% spread)
        
        Args:
            entry: Entry price
            direction: "LONG" or "SHORT"
            atr: ATR value (5M timeframe)
            
        Returns:
            Tuple of (tp_price, sl_price)
        """
        sl_distance = atr * self.config.atr_sl_multiplier  # 1.5 * ATR
        tp_distance = sl_distance * self.config.single_tp_multiplier  # 1.5 * SL
        
        # Slippage & spread buffer for realistic fills
        slippage_pct = 0.0003  # 0.03% average slippage
        spread_pct = 0.0002    # 0.02% spread
        buffer_pct = slippage_pct + spread_pct  # 0.05% total
        
        if direction == "LONG":
            # SL: Trigger earlier to avoid worse fill
            sl = entry - sl_distance
            sl_adjusted = sl * (1 + buffer_pct)  # Trigger 0.05% earlier
            
            # TP: Need to go further to account for slippage
            tp = entry + tp_distance
            tp_adjusted = tp * (1 + buffer_pct)  # Go 0.05% further
        else:  # SHORT
            # SL: Trigger earlier
            sl = entry + sl_distance
            sl_adjusted = sl * (1 - buffer_pct)
            
            # TP: Go further
            tp = entry - tp_distance
            tp_adjusted = tp * (1 - buffer_pct)
        
        # Round to 8 decimals (exchange precision)
        tp_final = round(tp_adjusted, 8)
        sl_final = round(sl_adjusted, 8)
        
        logger.debug(
            f"[Scalping:{self.user_id}] TP/SL calculated: "
            f"Entry={entry:.4f}, TP={tp_final:.4f}, SL={sl_final:.4f} "
            f"(buffer={buffer_pct:.2%})"
        )
        
        return (tp_final, sl_final)
    
    def validate_scalping_entry(self, signal) -> bool:
        """
        Validate signal meets all scalping requirements.
        MicroScalpSignal (sideways) bypasses ATR checks — already validated in pipeline.
        """
        from app.trading_mode import MicroScalpSignal as _MicroScalpSignal
        is_sideways = isinstance(signal, _MicroScalpSignal)
        is_emergency = bool(getattr(signal, "is_emergency", False))
        sideways_policy = get_sideways_entry_overrides(self._sideways_governor_snapshot)
        conf_delta = int(self._adaptive_overlay.get("conf_delta", 0) or 0)
        vol_delta = float(self._adaptive_overlay.get("volume_min_ratio_delta", 0.0) or 0.0)
        conf_adapt = get_confidence_adaptation(
            mode="scalping",
            confidence=float(getattr(signal, "confidence", 0.0) or 0.0),
            is_emergency=is_emergency,
            snapshot=self._confidence_adapt_snapshot,
        )
        conf_adapt_base = dict(conf_adapt or {})
        parity_controls = get_scalping_risk_parity_controls(self._scalp_risk_parity_snapshot)
        conf_adapt = apply_scalping_confidence_relief(conf_adapt, parity_controls)
        setattr(signal, "confidence_bucket", str(conf_adapt.get("bucket", "")))
        setattr(signal, "confidence_bucket_penalty_base", int(conf_adapt_base.get("bucket_penalty", 0) or 0))
        setattr(signal, "confidence_bucket_penalty", int(conf_adapt.get("bucket_penalty", 0) or 0))
        setattr(signal, "confidence_bucket_risk_scale_base", float(conf_adapt_base.get("bucket_risk_scale", 1.0) or 1.0))
        setattr(signal, "confidence_bucket_risk_scale", float(conf_adapt.get("bucket_risk_scale", 1.0) or 1.0))
        setattr(signal, "confidence_bucket_edge_adj", float(conf_adapt.get("edge_adj", 0.0) or 0.0))
        setattr(signal, "confidence_bucket_sample_size", int(conf_adapt.get("bucket_sample_size", 0) or 0))
        setattr(signal, "confidence_adapt_reason", str(conf_adapt.get("reason", "")))
        setattr(signal, "parity_conf_relief_applied", bool(conf_adapt.get("parity_conf_relief_applied", False)))
        setattr(signal, "scalp_risk_parity_regime", str(parity_controls.get("regime", "disabled")))
        setattr(signal, "scalp_risk_parity_ratio", float(parity_controls.get("ratio", 1.0) or 1.0))
        if not getattr(signal, "trade_subtype", ""):
            setattr(signal, "trade_subtype", "sideways_scalp" if is_sideways else "trend_scalp")

        # Check confidence
        min_conf_pct = max(0.0, min(100.0, (self.config.min_confidence * 100.0) + conf_delta))
        if is_sideways:
            min_conf_pct = max(
                0.0,
                min(
                    100.0,
                    min_conf_pct + int(sideways_policy.get("sideways_confidence_bonus", 0) or 0),
                ),
            )
        min_conf_pct = max(
            0.0,
            min(100.0, min_conf_pct + int(conf_adapt.get("bucket_penalty", 0) or 0)),
        )
        setattr(signal, "confidence_effective_min_conf", float(min_conf_pct))
        if signal.confidence < min_conf_pct:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"Confidence {signal.confidence}% < {min_conf_pct}% "
                f"(adaptive conf_delta={conf_delta}, trade_type=scalping "
                f"conf_bucket={conf_adapt.get('bucket')} "
                f"bucket_penalty={int(conf_adapt.get('bucket_penalty', 0) or 0)} "
                f"bucket_penalty_base={int(conf_adapt_base.get('bucket_penalty', 0) or 0)} "
                f"bucket_risk_scale={float(conf_adapt.get('bucket_risk_scale', 1.0) or 1.0):.2f} "
                f"bucket_risk_scale_base={float(conf_adapt_base.get('bucket_risk_scale', 1.0) or 1.0):.2f} "
                f"parity_regime={parity_controls.get('regime')} "
                f"parity_ratio={float(parity_controls.get('ratio', 1.0) or 1.0):.3f} "
                f"edge_adj={float(conf_adapt.get('edge_adj', 0.0) or 0.0):+.4f})"
            )
            return False

        if is_sideways and not bool(getattr(signal, "bounce_confirmed", False)):
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: sideways entry requires bounce_confirmed "
                f"(symbol={signal.symbol} trade_subtype={getattr(signal, 'trade_subtype', 'sideways_scalp')})"
            )
            return False
        
        # Check R:R (sideways uses a dedicated temporary floor)
        required_rr = self.config.sideways_min_rr if is_sideways else self.config.min_rr
        if is_sideways and sideways_policy.get("sideways_min_rr_override") is not None:
            required_rr = max(required_rr, float(sideways_policy.get("sideways_min_rr_override") or required_rr))
        if signal.rr_ratio < required_rr:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"R:R {signal.rr_ratio} < {required_rr}"
            )
            return False

        # Adaptive volume-quality gate for both trending and sideways.
        # Keep conservative defaults to avoid abrupt behavior shifts.
        base_vol_req = 0.9 if is_sideways else 1.0
        required_vol = max(0.8, min(2.0, base_vol_req + vol_delta))
        if is_sideways:
            required_vol = max(required_vol, float(sideways_policy.get("sideways_min_volume_floor", 0.9) or 0.9))
        signal_vol = float(getattr(signal, "volume_ratio", 0.0) or 0.0)
        if signal_vol < required_vol:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"Volume {signal_vol:.2f}x < {required_vol:.2f}x "
                f"(adaptive vol_delta={vol_delta:.2f})"
            )
            return False
        
        # Check symbol in allowed list
        allowed_symbols = set(self._active_scan_pairs or ([] if self._mixed_mode else self.config.pairs))
        if self._mixed_mode and not allowed_symbols:
            logger.info(f"[Scalping:{self.user_id}] Mixed mode has no assigned scalp symbols, skipping signal.")
            return False
        if signal.symbol not in allowed_symbols:
            logger.debug(f"[Scalping:{self.user_id}] Signal rejected: Symbol {signal.symbol} not allowed")
            return False
        
        # Check no existing position
        if signal.symbol in self.positions:
            logger.debug(f"[Scalping:{self.user_id}] Signal rejected: Position already open on {signal.symbol}")
            return False
        
        # Check max concurrent positions
        if len(self.positions) >= self.config.max_concurrent_positions:
            logger.debug(
                f"[Scalping:{self.user_id}] Signal rejected: "
                f"Max positions reached ({self.config.max_concurrent_positions})"
            )
            return False
        
        # ATR checks — skip for sideways signals (no atr_pct field)
        if not is_sideways:
            if signal.atr_pct < self.config.min_atr_pct:
                logger.debug(
                    f"[Scalping:{self.user_id}] Signal rejected: "
                    f"ATR {signal.atr_pct:.2f}% too low (market flat)"
                )
                return False
            
            if signal.atr_pct > self.config.max_atr_pct:
                logger.debug(
                    f"[Scalping:{self.user_id}] Signal rejected: "
                    f"ATR {signal.atr_pct:.2f}% too high (too volatile)"
                )
                return False
        
        # Adaptive daily circuit breaker gate (UTC day, full bypass only for strong opportunities).
        playbook_strong_match = bool(getattr(signal, "playbook_strong_match", False))
        match_meta: Dict[str, Any] = {}
        try:
            match_meta = compute_playbook_match_from_reasons(
                getattr(signal, "reasons", []) or [],
                self._win_playbook_snapshot,
                mode_hint="scalping",
            )
            setattr(
                signal,
                "playbook_match_score",
                float(match_meta.get("playbook_match_score", getattr(signal, "playbook_match_score", 0.0)) or 0.0),
            )
            setattr(
                signal,
                "playbook_match_tags",
                list(match_meta.get("matched_tags", getattr(signal, "playbook_match_tags", [])) or []),
            )
            playbook_strong_match = bool(match_meta.get("strong_match", False))
            setattr(signal, "playbook_strong_match", bool(playbook_strong_match))
        except Exception as playbook_match_err:
            logger.debug(f"[Scalping:{self.user_id}] Playbook strong-match precheck failed: {playbook_match_err}")

        if not is_sideways and not bool(self._win_playbook_snapshot.get("guardrails_healthy", False)):
            effective_confidence = float(getattr(signal, "confidence", 0.0) or 0.0)
            if effective_confidence < 75.0:
                reason_tags = set(match_meta.get("reason_tags", []) or [])
                has_volume_confirmation = "volume_confirmation" in reason_tags
                playbook_match_score = float(getattr(signal, "playbook_match_score", 0.0) or 0.0)
                if (not has_volume_confirmation) or playbook_match_score < 0.20:
                    logger.info(
                        f"[Scalping:{self.user_id}] Signal rejected: weak trend scalp under unhealthy playbook "
                        f"requires volume_confirmation + playbook_match_score>=0.20 "
                        f"(symbol={signal.symbol} confidence={effective_confidence:.1f} "
                        f"playbook_score={playbook_match_score:.3f} "
                        f"has_volume_confirmation={has_volume_confirmation})"
                    )
                    return False

        min_conf_for_breaker = float(
            getattr(signal, "confidence_effective_min_conf", self.config.min_confidence * 100.0)
            or (self.config.min_confidence * 100.0)
        )
        breaker_eval = evaluate_adaptive_daily_circuit_breaker(
            mode="scalping",
            user_id=int(self.user_id),
            signal=signal,
            supabase_client=_client(),
            playbook_snapshot=self._win_playbook_snapshot,
            min_confidence_pct=min_conf_for_breaker,
            min_rr_ratio=float(required_rr),
            playbook_strong_match=bool(playbook_strong_match),
        )
        setattr(signal, "daily_breaker_override_applied", bool(breaker_eval.get("override_applied", False)))
        setattr(signal, "daily_breaker_decision_reason", str(breaker_eval.get("decision_reason", "")))
        logger.info(
            f"[Scalping:{self.user_id}] Adaptive breaker decision "
            f"trade_type=scalping symbol={signal.symbol} "
            f"threshold_source={breaker_eval.get('threshold_source', 'adaptive_win_playbook')} "
            f"loss_pct_today={float(breaker_eval.get('loss_pct_today', 0.0)):.4f} "
            f"adaptive_limit_pct={float(breaker_eval.get('adaptive_limit_pct', 0.0)):.4f} "
            f"base_limit_pct={float(breaker_eval.get('base_limit_pct', 0.0)):.4f} "
            f"step={int(breaker_eval.get('adaptive_step', 0))} "
            f"step_reason={breaker_eval.get('adaptive_step_reason')} "
            f"sample_size={int(breaker_eval.get('sample_size', 0) or 0)} "
            f"wr={float(breaker_eval.get('rolling_win_rate', 0.0)):.3f} "
            f"exp={float(breaker_eval.get('rolling_expectancy', 0.0)):+.4f} "
            f"strong_opportunity={bool(breaker_eval.get('strong_opportunity', False))} "
            f"override_applied={bool(breaker_eval.get('override_applied', False))} "
            f"blocked={bool(breaker_eval.get('blocked', False))} "
            f"reason={breaker_eval.get('decision_reason')}"
        )
        if bool(breaker_eval.get("blocked", False)):
            logger.warning(
                f"[Scalping:{self.user_id}] Signal rejected by adaptive breaker: "
                f"symbol={signal.symbol} reason={breaker_eval.get('decision_reason')} "
                f"loss_pct_today={float(breaker_eval.get('loss_pct_today', 0.0)):.4f} "
                f"adaptive_limit_pct={float(breaker_eval.get('adaptive_limit_pct', 0.0)):.4f}"
            )
            return False
        logger.info(
            f"[Scalping:{self.user_id}] Entry gate passed "
            f"trade_type=scalping symbol={signal.symbol} conf={float(signal.confidence):.2f} "
            f"min_conf={float(getattr(signal, 'confidence_effective_min_conf', 0.0)):.2f} "
            f"conf_bucket={str(getattr(signal, 'confidence_bucket', '-'))} "
            f"bucket_penalty={int(getattr(signal, 'confidence_bucket_penalty', 0) or 0)} "
            f"bucket_risk_scale={float(getattr(signal, 'confidence_bucket_risk_scale', 1.0) or 1.0):.2f} "
            f"edge_adj={float(getattr(signal, 'confidence_bucket_edge_adj', 0.0) or 0.0):+.4f} "
            f"is_emergency={is_emergency}"
        )
        return True

    
    async def place_scalping_order(self, signal: ScalpingSignal) -> bool:
        """
        Place scalping order with PROPER position sizing and time-of-day filter
        
        Args:
            signal: ScalpingSignal to execute
            
        Returns:
            True if order placed successfully
        """
        parity_controls = get_scalping_risk_parity_controls(self._scalp_risk_parity_snapshot)
        cap_pct = float(parity_controls.get("cap_pct", 0.50) or 0.50)
        # Check optimal trading time
        should_trade, size_multiplier = self.is_optimal_trading_time(parity_controls=parity_controls)
        
        if not should_trade:
            logger.info(
                f"[Scalping:{self.user_id}] Skipping {signal.symbol} - "
                f"Non-optimal trading hours"
            )
            return False
        
        max_retries = 3
        base_delay = 1.0
        pending_marked = False
        
        for attempt in range(max_retries):
            try:
                # Get account info
                session = _client().table("autotrade_sessions").select(
                    "initial_deposit", "leverage"
                ).eq("telegram_id", self.user_id).limit(1).execute()
                
                if not session.data:
                    logger.error(f"[Scalping:{self.user_id}] No session found")
                    return False
                
                capital = float(session.data[0].get("initial_deposit", 100))
                leverage = int(session.data[0].get("leverage", 10))
                
                # ── Auto Max Pair Leverage Calculation ──
                effective_leverage = get_auto_max_safe_leverage(
                    symbol=signal.symbol,
                    entry_price=signal.entry_price,
                    sl_price=signal.sl_price,
                    baseline_leverage=leverage,
                )
                logger.info(
                    f"[Scalping:{self.user_id}] leverage_mode=auto_max_safe symbol={signal.symbol} "
                    f"baseline_leverage={leverage} effective_leverage={effective_leverage}"
                )
                from app.supabase_repo import get_risk_per_trade
                base_risk_pct = float(get_risk_per_trade(self.user_id) or 1.0)
                risk_eval = await evaluate_and_apply_playbook_risk(
                    signal=signal,
                    base_risk_pct=base_risk_pct,
                    raw_reasons=getattr(signal, "reasons", []),
                    logger=logger,
                    label=f"[Scalping:{self.user_id}] {signal.symbol}",
                )
                playbook_effective_risk_pct = float(risk_eval.get("effective_risk_pct", 1.0))
                risk_overlay_pct = float(risk_eval.get("risk_overlay_pct", 0.0))
                playbook_match_score = float(risk_eval.get("playbook_match_score", 0.0))
                playbook_match_tags = list(risk_eval.get("playbook_match_tags", []))
                confidence_risk_scale = float(getattr(signal, "confidence_bucket_risk_scale", 1.0) or 1.0)
                confidence_risk_scale_base = float(getattr(signal, "confidence_bucket_risk_scale_base", confidence_risk_scale) or confidence_risk_scale)
                confidence_bucket = str(getattr(signal, "confidence_bucket", "-") or "-")
                confidence_edge_adj = float(getattr(signal, "confidence_bucket_edge_adj", 0.0) or 0.0)
                effective_risk_pct = apply_confidence_risk_brake(
                    playbook_effective_risk_pct=playbook_effective_risk_pct,
                    bucket_risk_scale=confidence_risk_scale,
                )
                effective_risk_target_pct = min(float(playbook_effective_risk_pct), float(effective_risk_pct), 10.0)
                setattr(signal, "effective_risk_pct", effective_risk_pct)
                setattr(signal, "risk_overlay_pct", risk_overlay_pct)
                setattr(signal, "base_risk_pct", base_risk_pct)
                setattr(signal, "effective_risk_target_pct", float(effective_risk_target_pct))
                logger.info(
                    f"[Scalping:{self.user_id}] Win playbook eval {signal.symbol} — "
                    f"score={playbook_match_score:.3f} tags={playbook_match_tags[:3]} "
                    f"guardrails={bool(risk_eval.get('guardrails_healthy', False))} "
                    f"overlay={risk_overlay_pct:.2f}% -> playbook_risk={playbook_effective_risk_pct:.2f}% "
                    f"conf_bucket={confidence_bucket} conf_scale={confidence_risk_scale:.2f} "
                    f"conf_scale_base={confidence_risk_scale_base:.2f} "
                    f"parity_regime={parity_controls.get('regime')} "
                    f"parity_ratio={float(parity_controls.get('ratio', 1.0) or 1.0):.3f} "
                    f"edge_adj={confidence_edge_adj:+.4f} -> final_effective_risk={effective_risk_pct:.2f}% "
                    f"action={risk_eval.get('overlay_action')} trade_type=scalping"
                )
                
                # CRITICAL: Calculate position size based on risk (Phase 2)
                quantity, used_risk_sizing, sizing_meta = self.calculate_position_size_pro(
                    symbol=signal.symbol,
                    entry_price=signal.entry_price,
                    sl_price=signal.sl_price,
                    capital=capital,
                    leverage=effective_leverage,
                    effective_risk_pct_override=effective_risk_pct,
                    notional_cap_pct=cap_pct,
                )
                
                if used_risk_sizing:
                    logger.info(f"[Scalping:{self.user_id}] Using RISK-BASED position sizing for {signal.symbol}")
                else:
                    logger.info(f"[Scalping:{self.user_id}] Using FIXED 2% position sizing for {signal.symbol} (fallback)")
                
                # Apply time-of-day multiplier
                quantity_adjusted = quantity * size_multiplier
                qty_pre_time = float(quantity)
                
                if size_multiplier < 1.0:
                    logger.info(
                        f"[Scalping:{self.user_id}] Time-of-day adjustment: "
                        f"{size_multiplier:.0%} position size (hour={datetime.utcnow().hour} UTC)"
                    )

                equity_for_risk = float(sizing_meta.get("equity", 0.0) or 0.0)
                applied_risk_pct_raw = self._effective_risk_pct_from_qty(
                    entry_price=float(signal.entry_price),
                    sl_price=float(signal.sl_price),
                    quantity=float(quantity_adjusted),
                    equity=equity_for_risk,
                )
                if (
                    equity_for_risk > 0.0
                    and applied_risk_pct_raw > float(effective_risk_target_pct) + 1e-9
                    and quantity_adjusted > 0.0
                ):
                    scale_down = float(effective_risk_target_pct) / max(applied_risk_pct_raw, 1e-9)
                    quantity_adjusted *= max(0.0, min(scale_down, 1.0))
                    applied_risk_pct_raw = self._effective_risk_pct_from_qty(
                        entry_price=float(signal.entry_price),
                        sl_price=float(signal.sl_price),
                        quantity=float(quantity_adjusted),
                        equity=equity_for_risk,
                    )
                applied_risk_pct = min(
                    float(applied_risk_pct_raw),
                    float(playbook_effective_risk_pct),
                    float(effective_risk_target_pct),
                    10.0,
                )
                if applied_risk_pct < 0.25:
                    logger.warning(
                        f"[Scalping:{self.user_id}] Trade skipped: effective risk below floor "
                        f"trade_type=scalping symbol={signal.symbol} applied={applied_risk_pct:.4f}% "
                        f"target={effective_risk_target_pct:.4f}% ratio={float(parity_controls.get('ratio', 1.0) or 1.0):.3f}"
                    )
                    return False
                setattr(signal, "effective_risk_pct", float(applied_risk_pct))
                setattr(signal, "effective_risk_target_pct", float(effective_risk_target_pct))
                setattr(signal, "effective_risk_raw_pct", float(applied_risk_pct_raw))
                setattr(signal, "scalp_risk_cap_pct", float(cap_pct))
                setattr(signal, "scalp_risk_cap_hit", bool(sizing_meta.get("cap_hit", False)))
                setattr(signal, "scalp_risk_time_multiplier", float(size_multiplier))
                setattr(signal, "scalp_risk_qty_pre_time", float(qty_pre_time))
                logger.info(
                    f"[Scalping:{self.user_id}] scalp_risk_parity "
                    f"trade_type=scalping symbol={signal.symbol} "
                    f"ratio={float(parity_controls.get('ratio', 1.0) or 1.0):.3f} "
                    f"regime={parity_controls.get('regime')} "
                    f"conf_scale_base={confidence_risk_scale_base:.2f} "
                    f"conf_scale_final={confidence_risk_scale:.2f} "
                    f"time_multiplier={float(size_multiplier):.2f} "
                    f"cap_pct={float(cap_pct):.2f} "
                    f"cap_hit={bool(sizing_meta.get('cap_hit', False))} "
                    f"effective_risk_target={float(effective_risk_target_pct):.3f} "
                    f"effective_risk_applied={float(applied_risk_pct):.3f} "
                    f"fallback={str(sizing_meta.get('fallback_mode') or '-')}"
                )
                
                # ── Minimum qty validation (NO AUTO-LEVERAGE for risk management) ──
                # Minimum qty per pair (Bitunix standard minimums)
                MIN_QTY_MAP = {
                    "BTCUSDT": 0.001, "ETHUSDT": 0.01, "SOLUSDT": 0.1,
                    "BNBUSDT": 0.01,  "XRPUSDT": 1.0,  "DOGEUSDT": 10.0,
                    "ADAUSDT": 1.0,   "AVAXUSDT": 0.1, "DOTUSDT": 0.1,
                    "LINKUSDT": 0.1,  "UNIUSDT": 0.1,  "ATOMUSDT": 0.1,
                    "XAUUSDT": 0.01,  "CLUSDT": 0.01,  "QQQUSDT": 0.1
                }
                min_qty = MIN_QTY_MAP.get(signal.symbol, 0.001)
                
                # CRITICAL: Skip trade if qty too small - NEVER auto-raise leverage
                # Auto-raising leverage breaks risk management (user set leverage for specific risk %)
                if quantity_adjusted < min_qty:
                    logger.warning(
                        f"[Scalping:{self.user_id}] {signal.symbol} qty={quantity_adjusted:.6f} "
                        f"< min={min_qty}. Skipping - balance too small for this pair."
                    )
                    return False  # Silent skip, engine will try other pairs
                
                # ═══════════════════════════════════════════════════════════
                # Multi-user symbol coordination check
                # ═══════════════════════════════════════════════════════════
                can_enter, block_reason = await self.coordinator.can_enter(
                    user_id=self.user_id,
                    symbol=signal.symbol,
                    strategy=StrategyOwner.SCALP,
                    now_ts=time.time()
                )
                if not can_enter:
                    logger.warning(f"[Coordinator:{self.user_id}] Entry BLOCKED for {signal.symbol}: {block_reason}")
                    should_notify = True
                    pending_diag: Dict[str, Any] = {}
                    if "blocked_pending_order" in str(block_reason):
                        pending_ctx = await self.coordinator.get_pending_lock_context(
                            user_id=self.user_id,
                            symbol=signal.symbol,
                            now_ts=time.time(),
                        )
                        pending_diag = normalize_pending_lock_context(pending_ctx)
                        logger.warning(
                            "[Coordinator:%s] blocked_pending_diagnostics symbol=%s "
                            "pending_owner=%s owner=%s pending_age=%s pending_ttl=%.1fs "
                            "has_position=%s stale_candidate=%s last_clear_reason=%s",
                            self.user_id,
                            signal.symbol,
                            pending_diag.get("pending_owner") or "-",
                            pending_diag.get("owner") or "-",
                            pending_lock_age_label(pending_diag.get("pending_age_seconds")),
                            float(pending_diag.get("pending_ttl_seconds", 90.0) or 90.0),
                            bool(pending_diag.get("has_position", False)),
                            bool(pending_diag.get("stale_candidate", False)),
                            pending_diag.get("last_pending_clear_reason") or "-",
                        )
                        should_notify = self._should_notify_blocked_pending(signal.symbol, ttl_sec=600)
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
                        await self._notify_user(
                            f"⚠️ <b>Trade skipped on {signal.symbol}</b>\n\n"
                            f"<b>Reason:</b> {block_reason}\n\n"
                            + (
                                f"{diag_text}\n\n"
                                if diag_text else
                                "Another strategy may own this symbol.\n\n"
                            )
                            + "Bot will continue scanning."
                        )
                    return False

                # Mark pending
                await coordinator_set_pending(self.coordinator, self.user_id, signal.symbol, StrategyOwner.SCALP)
                pending_marked = True

                # ═══════════════════════════════════════════════════════════
                # Unified entry path — see app/trade_execution.py
                # Atomic order with TP1 + SL on exchange + StackMentor register
                # ═══════════════════════════════════════════════════════════
                from app.trade_execution import open_managed_position
                from app.trading_mode import MicroScalpSignal as _MicroScalpSignalCheck
                _is_sideways_signal = isinstance(signal, _MicroScalpSignalCheck)

                exec_result = await self._open_managed_position_safe(
                    open_managed_position,
                    client=self.client,
                    user_id=self.user_id,
                    symbol=signal.symbol,
                    side=signal.side,                # "LONG" / "SHORT"
                    entry_price=signal.entry_price,
                    sl_price=signal.sl_price,
                    tp_price=signal.tp_price,
                    quantity=quantity_adjusted,
                    leverage=effective_leverage,
                    # Sideways positions have very tight TP/SL — skip reconcile
                    # to avoid false emergency closes. Engine monitors via max_hold.
                    reconcile=not _is_sideways_signal,
                )

                if exec_result.success:
                    levels = exec_result.levels
                    side_str = "BUY" if signal.side == "LONG" else "SELL"

                    # Register position for local tracking
                    position = ScalpingPosition(
                        user_id=self.user_id,
                        symbol=signal.symbol,
                        side=side_str,
                        entry_price=signal.entry_price,
                        quantity=quantity_adjusted,
                        leverage=effective_leverage,
                        open_order_id=exec_result.order_id or "",
                        tp_price=levels.tp1,
                        sl_price=levels.sl,
                        opened_at=time.time(),
                        breakeven_set=False,
                    )
                    setattr(position, "entry_reasons", list(getattr(signal, "reasons", []) or []))
                    setattr(position, "playbook_match_score", float(getattr(signal, "playbook_match_score", 0.0) or 0.0))
                    setattr(position, "playbook_match_tags", list(getattr(signal, "playbook_match_tags", []) or []))
                    setattr(position, "effective_risk_pct", float(getattr(signal, "effective_risk_pct", 0.0) or 0.0))
                    setattr(position, "risk_overlay_pct", float(getattr(signal, "risk_overlay_pct", 0.0) or 0.0))
                    setattr(position, "initial_sl_price", float(levels.sl))
                    setattr(position, "timeout_protection_applied", False)
                    setattr(position, "timeout_protection_phase", "early")
                    setattr(position, "timeout_last_sl_update_ts", 0.0)
                    self.positions[signal.symbol] = position

                    # Mark as sideways position if signal is MicroScalpSignal
                    from app.trading_mode import MicroScalpSignal as _MicroScalpSignal
                    if isinstance(signal, _MicroScalpSignal):
                        position.is_sideways = True

                    # Save to database + notify user
                    trade_id = await self._save_position_to_db(position, signal, order_id=exec_result.order_id or "")
                    await self._notify_stackmentor_opened(
                        position,
                        signal,
                        levels,
                        order_id=exec_result.order_id or "-",
                        trade_id=trade_id,
                    )

                    # Confirm position with coordinator
                    position_side = PositionSide.LONG if signal.side == "LONG" else PositionSide.SHORT
                    await coordinator_confirm_open(
                        self.coordinator,
                        user_id=self.user_id,
                        symbol=signal.symbol,
                        strategy=StrategyOwner.SCALP,
                        side=position_side,
                        size=quantity_adjusted,
                        entry_price=signal.entry_price,
                        exchange_position_id=getattr(exec_result, 'position_id', None),
                    )
                    pending_marked = False

                    logger.info(
                        f"[Scalping:{self.user_id}] StackMentor position opened: "
                        f"{signal.symbol} {side_str} @ {signal.entry_price:.4f}, "
                        f"Qty: {quantity_adjusted:.6f}, "
                        f"TP1={levels.tp1:.4f} TP2={levels.tp2:.4f} TP3={levels.tp3:.4f}"
                    )
                    return True
                else:
                    error_msg = exec_result.error or "Unknown error"
                    error_code = exec_result.error_code or ""
                    logger.warning(
                        f"[Scalping:{self.user_id}] Order failed (attempt {attempt+1}) "
                        f"[{error_code}]: {error_msg}"
                    )

                    # Non-retryable conditions — clear pending before returning
                    if error_code == "insufficient_balance":
                        await self._notify_user("❌ Order failed: Insufficient balance")
                        await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if error_code == "invalid_prices":
                        expiry_ts = self._mark_stale_price_cooldown(signal.symbol, ttl_sec=120.0)
                        cooldown_sec = max(1, int(round(expiry_ts - time.time())))
                        await self._notify_user(
                            f"⚠️ <b>Trade skipped: {signal.symbol}</b>\n\n"
                            f"Market moved before entry: {error_msg}\n\n"
                            f"Cooldown on {signal.symbol}: {cooldown_sec}s to avoid repeated stale entries."
                        )
                        await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if error_code in ("auth", "ip_blocked"):
                        await self._notify_user(
                            f"⚠️ Exchange auth/IP error: {error_msg}\n"
                            f"Engine continues; check API key & proxy."
                        )
                        await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if error_code == "reconcile_failed":
                        await self._notify_user(
                            f"🚨 <b>Position auto-closed: {signal.symbol}</b>\n\n"
                            f"Self-healing check found the live position did not match "
                            f"expected qty/TP/SL and could not be repaired. Position was "
                            f"closed to protect your capital.\n\n"
                            f"<code>{error_msg}</code>"
                        )
                        await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if error_code == "unsupported_symbol_api":
                        quarantine_expiry = mark_runtime_untradable_symbol(signal.symbol, ttl_sec=21600.0)
                        quarantine_sec = max(1, int(round(quarantine_expiry - time.time())))
                        quarantine_hours = max(1, int(round(quarantine_sec / 3600.0)))
                        await self._notify_user(
                            f"⚠️ <b>Trade skipped: {signal.symbol}</b>\n\n"
                            f"{error_msg}\n\n"
                            f"Bitunix OpenAPI does not support this pair right now.\n"
                            f"Runtime quarantine applied: {quarantine_hours}h.\n"
                            f"Engine will continue scanning other top-volume pairs."
                        )
                        await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                        pending_marked = False
                        return False
                    if 'invalid symbol' in error_msg.lower():
                        await self._notify_user(f"❌ Order failed: Invalid symbol {signal.symbol}")
                        await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                        pending_marked = False
                        return False

                    # Retryable error — backoff
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
            
            except asyncio.TimeoutError:
                logger.warning(f"[Scalping:{self.user_id}] Order timeout (attempt {attempt+1})")
                if attempt == max_retries - 1 and pending_marked:
                    await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                    pending_marked = False
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
            
            except Exception as e:
                logger.error(f"[Scalping:{self.user_id}] Order exception (attempt {attempt+1}): {e}")
                if attempt == max_retries - 1 and pending_marked:
                    await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
                    pending_marked = False
                if attempt < max_retries - 1:
                    await asyncio.sleep(base_delay * (2 ** attempt))
        
        # All retries failed — set cooldown to prevent spam
        if pending_marked:
            await coordinator_clear_pending(self.coordinator, self.user_id, signal.symbol)
            pending_marked = False
        self.mark_cooldown(signal.symbol)
        await self._notify_user(
            f"❌ Failed to place order for {signal.symbol} after {max_retries} attempts.\n"
            f"Signal skipped. Engine continues monitoring."
        )
        return False
    
    async def monitor_positions(self):
        """
        Monitor open positions using StackMentor system
        StackMentor handles 3-tier TP and auto-breakeven automatically
        """
        if not self.positions:
            return
        
        # Use StackMentor monitoring for all positions
        from app.stackmentor import monitor_stackmentor_positions

        try:
            # monitor_stackmentor_positions is async (bot, user_id, client, chat_id)
            await monitor_stackmentor_positions(
                self.bot,
                self.user_id,
                self.client,
                self.notify_chat_id,
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error in StackMentor monitoring: {e}")
        
        # Check for positions that need to be removed from local tracking
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            
            try:
                if bool(getattr(self.config, "adaptive_timeout_protection_enabled", False)):
                    try:
                        await self._apply_timeout_protection(position)
                    except Exception as protect_err:
                        logger.warning(
                            f"[Scalping:{self.user_id}] timeout protection check failed for "
                            f"{position.symbol}: {protect_err}"
                        )

                # Check dynamic max hold by subtype/symbol performance.
                elapsed = max(0.0, time.time() - float(position.opened_at))
                max_hold_seconds = self._max_hold_seconds_for_position(position)
                if elapsed >= float(max_hold_seconds):
                    if getattr(position, 'is_sideways', False):
                        await self._close_sideways_max_hold(position, max_hold_seconds=max_hold_seconds)
                    else:
                        await self._close_position_max_hold(position, max_hold_seconds=max_hold_seconds)
                    continue

                # Remove stale local tracker if DB row is no longer open.
                open_row = await self._get_open_trade_row(symbol)
                if not open_row:
                    logger.info(
                        f"[Scalping:{self.user_id}] Removing stale local position tracker for {symbol} "
                        f"(no open DB row)"
                    )
                    self.positions.pop(symbol, None)
                    continue
             
            except Exception as e:
                logger.error(f"[Scalping:{self.user_id}] Error checking {symbol}: {e}")
                continue

    async def _process_expired_positions(self):
        """
        Close positions that already exceeded dynamic max-hold before scanning.
        This keeps timeout exits ahead of new-entry decisions in each cycle.
        """
        if not self.positions:
            return
        for symbol in list(self.positions.keys()):
            position = self.positions.get(symbol)
            if not position:
                continue
            try:
                elapsed = max(0.0, time.time() - float(position.opened_at))
                max_hold_seconds = self._max_hold_seconds_for_position(position)
                if elapsed < float(max_hold_seconds):
                    continue
                if getattr(position, "is_sideways", False):
                    await self._close_sideways_max_hold(position, max_hold_seconds=max_hold_seconds)
                else:
                    await self._close_position_max_hold(position, max_hold_seconds=max_hold_seconds)
            except Exception as e:
                logger.error(f"[Scalping:{self.user_id}] Error in pre-scan max-hold close for {symbol}: {e}")

    def _max_hold_seconds_for_position(self, position: ScalpingPosition) -> int:
        snapshot = getattr(self, "_sideways_governor_snapshot", {}) or {}
        return resolve_dynamic_max_hold_seconds(
            symbol=str(getattr(position, "symbol", "") or ""),
            is_sideways=bool(getattr(position, "is_sideways", False)),
            snapshot=snapshot,
            default_non_sideways=int(self.config.max_hold_time),
        )

    def _timeout_phase(self, elapsed_seconds: float, max_hold_seconds: int) -> str:
        if max_hold_seconds <= 0:
            return "late"
        ratio = max(0.0, min(1.0, float(elapsed_seconds) / float(max_hold_seconds)))
        if ratio < 0.50:
            return "early"
        if ratio < 0.80:
            return "mid"
        return "late"

    def _build_timeout_loss_reasoning(
        self,
        position: ScalpingPosition,
        pnl: float,
        phase: str,
        protected: bool,
        near_flat: bool,
    ) -> str:
        return (
            f"timeout_exit; timeout_protection={'applied' if protected else 'none'}; "
            f"phase={phase}; near_flat={1 if near_flat else 0}; pnl={float(pnl):+.6f}; "
            f"symbol={position.symbol}; side={position.side}"
        )

    async def _apply_timeout_protection(self, position: ScalpingPosition):
        """
        Apply phased timeout protection:
        - mid phase: breakeven promotion when unrealized progress is sufficient
        - late phase: tighten trailing SL (more aggressive for sideways trades)
        """
        max_hold = self._max_hold_seconds_for_position(position)
        now_ts = time.time()
        elapsed = max(0.0, now_ts - float(position.opened_at))
        phase = self._timeout_phase(elapsed, max_hold)
        setattr(position, "timeout_protection_phase", phase)

        if phase == "early":
            return

        last_update_ts = float(getattr(position, "timeout_last_sl_update_ts", 0.0) or 0.0)
        min_update_gap = float(getattr(self.config, "timeout_protection_min_update_seconds", 45) or 45)
        if now_ts - last_update_ts < min_update_gap:
            return

        ticker = await asyncio.to_thread(self.client.get_ticker, position.symbol)
        if not ticker or not ticker.get("success"):
            return
        current_price = float(ticker.get("mark_price") or ticker.get("last_price") or ticker.get("price") or 0)
        if current_price <= 0:
            return

        entry = float(position.entry_price)
        old_sl = float(position.sl_price)
        initial_sl = float(getattr(position, "initial_sl_price", old_sl) or old_sl)
        if initial_sl <= 0:
            initial_sl = old_sl
            setattr(position, "initial_sl_price", initial_sl)

        if position.side == "BUY":
            favorable_pct = ((current_price - entry) / entry) * 100.0 if entry > 0 else 0.0
            unrealized_pnl = (current_price - entry) * float(position.quantity)
        else:
            favorable_pct = ((entry - current_price) / entry) * 100.0 if entry > 0 else 0.0
            unrealized_pnl = (entry - current_price) * float(position.quantity)

        be_trigger = float(getattr(self.config, "timeout_be_trigger_pct", 0.20) or 0.20)
        trailing_trigger = float(getattr(self.config, "timeout_trailing_trigger_pct", 0.35) or 0.35)
        tighten = float(getattr(self.config, "timeout_late_tighten_multiplier", 1.4) or 1.4)
        if phase == "late" and bool(getattr(position, "is_sideways", False)):
            tighten *= 1.5
        elif phase == "late":
            tighten *= 1.2

        new_sl = old_sl
        reason = None
        if favorable_pct >= be_trigger and not bool(getattr(position, "breakeven_set", False)):
            new_sl = entry
            reason = "breakeven"

        if favorable_pct >= trailing_trigger:
            risk_gap = abs(entry - initial_sl)
            if risk_gap > 0:
                trail_gap = risk_gap / max(1.0, tighten)
                if position.side == "BUY":
                    trail_target = max(entry, current_price - trail_gap)
                    if trail_target > new_sl:
                        new_sl = trail_target
                        reason = "soft_trailing"
                else:
                    trail_target = min(entry, current_price + trail_gap)
                    if trail_target < new_sl:
                        new_sl = trail_target
                        reason = "soft_trailing"

        eps = max(1e-8, abs(entry) * 1e-6)
        improve = (new_sl > old_sl + eps) if position.side == "BUY" else (new_sl < old_sl - eps)
        if not improve:
            return

        if position.side == "BUY" and new_sl >= current_price:
            return
        if position.side == "SELL" and new_sl <= current_price:
            return

        result = await asyncio.to_thread(self.client.set_position_sl, position.symbol, float(new_sl))
        if not result.get("success"):
            logger.warning(
                f"[Scalping:{self.user_id}] timeout_protection_apply_failed "
                f"symbol={position.symbol} phase={phase} old_sl={old_sl:.6f} new_sl={new_sl:.6f} "
                f"reason={reason} err={result.get('error')}"
            )
            return

        position.sl_price = float(new_sl)
        if reason == "breakeven" or (position.side == "BUY" and new_sl >= entry) or (position.side == "SELL" and new_sl <= entry):
            position.breakeven_set = True
        setattr(position, "timeout_last_sl_update_ts", now_ts)
        setattr(position, "timeout_protection_applied", True)

        logger.info(
            f"[Scalping:{self.user_id}] timeout_protection_applied symbol={position.symbol} "
            f"phase={phase} old_sl={old_sl:.6f} new_sl={new_sl:.6f} reason={reason} "
            f"unrealized_pnl={unrealized_pnl:+.6f} minutes_open={elapsed/60.0:.2f}"
        )
    
    async def _move_sl_to_breakeven(self, position: ScalpingPosition, current_price: float):
        """Move stop loss to breakeven (entry price) to protect profits"""
        try:
            # Update position SL to entry price
            old_sl = position.sl_price
            result = await asyncio.to_thread(
                self.client.set_position_sl, position.symbol, float(position.entry_price)
            )
            if not result.get("success"):
                logger.warning(
                    f"[Scalping:{self.user_id}] breakeven_sl_update_failed symbol={position.symbol} "
                    f"old_sl={old_sl:.6f} new_sl={position.entry_price:.6f} err={result.get('error')}"
                )
                return
            position.sl_price = position.entry_price
            position.breakeven_set = True
            setattr(position, "timeout_last_sl_update_ts", time.time())
            setattr(position, "timeout_protection_applied", True)
            setattr(position, "timeout_protection_phase", "mid")
            
            # Notify user
            await self._notify_user(
                f"🔒 <b>Breakeven Protection Activated</b>\n\n"
                f"Symbol: {position.symbol}\n"
                f"Entry: {position.entry_price:.4f}\n"
                f"Old SL: {old_sl:.4f}\n"
                f"New SL: {position.sl_price:.4f} (Breakeven)\n\n"
                f"Position is now risk-free! 🎉"
            )
            
            logger.info(
                f"[Scalping:{self.user_id}] SL moved to breakeven: "
                f"{position.symbol} @ {position.entry_price:.4f}"
            )
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error moving SL to breakeven: {e}")
    
    async def _close_position_max_hold(
        self,
        position: ScalpingPosition,
        max_hold_seconds: Optional[int] = None,
    ):
        """Force close position at market price when dynamic max hold is exceeded."""
        try:
            if max_hold_seconds is None:
                max_hold_seconds = self._max_hold_seconds_for_position(position)
            logger.info(
                f"[Scalping:{self.user_id}] Max hold time exceeded for {position.symbol} "
                f"(elapsed: {int(time.time() - position.opened_at)}s / max={int(max_hold_seconds)}s)"
            )
            
            close_qty = await self._resolve_close_quantity(position)
            if close_qty <= 0:
                logger.warning(
                    f"[Scalping:{self.user_id}] Max-hold close skipped for {position.symbol}: qty<=0"
                )
                self.positions.pop(position.symbol, None)
                return

            # Close entire position at market
            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=close_qty,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                close_order_id = str(result.get("order_id") or "")
                fill_price, px_estimated = await self._resolve_exit_price(
                    position.symbol, position.entry_price, result
                )
                
                # Calculate PnL
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * close_qty
                else:
                    pnl = (position.entry_price - fill_price) * close_qty
                
                pnl_usdt = pnl
                pnl_net, open_fee, close_fee, used_exchange = await self._resolve_net_pnl(
                    symbol=position.symbol,
                    gross_pnl=pnl_usdt,
                    open_order_id=getattr(position, "open_order_id", "") or "",
                    close_order_id=close_order_id,
                )
                timeout_phase = str(getattr(position, "timeout_protection_phase", "late"))
                timeout_protected = bool(getattr(position, "timeout_protection_applied", False))
                near_flat_thr = float(getattr(self.config, "timeout_near_flat_usdt_threshold", 0.02) or 0.02)
                near_flat = abs(float(pnl_net)) <= near_flat_thr
                loss_reasoning = self._build_timeout_loss_reasoning(
                    position=position,
                    pnl=pnl_net,
                    phase=timeout_phase,
                    protected=timeout_protected,
                    near_flat=near_flat,
                )
                
                # Update database
                await self._update_position_closed(
                    position,
                    fill_price,
                    pnl_net,
                    "max_hold_time_exceeded",
                    loss_reasoning=loss_reasoning,
                )

                logger.info(
                    f"[Scalping:{self.user_id}] "
                    f"{'timeout_exit_with_protection' if timeout_protected else 'timeout_exit_without_protection'} "
                    f"symbol={position.symbol} reason=max_hold_time_exceeded phase={timeout_phase} "
                    f"near_flat={int(near_flat)} pnl={pnl_net:+.6f}"
                )

                # Confirm position closed with coordinator
                await coordinator_confirm_closed(
                    self.coordinator,
                    user_id=self.user_id,
                    symbol=position.symbol,
                    now_ts=time.time(),
                )

                # Update StackMentor tracking
                try:
                    from app.stackmentor import remove_stackmentor_position
                    remove_stackmentor_position(self.user_id, position.symbol)
                except Exception as sm_err:
                    logger.warning(f"[Scalping:{self.user_id}] Failed to update StackMentor: {sm_err}")

                # Notify user
                hold_label = (
                    f"{int(max_hold_seconds) // 60} minutes"
                    if int(max_hold_seconds) >= 120
                    else f"{int(max_hold_seconds)} seconds"
                )
                await self._notify_user(
                    f"⏰ <b>Position Closed (Max Hold Time)</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Entry: {_fmt_price(position.entry_price)}\n"
                    f"Exit: {_fmt_price(fill_price)}{' (estimated)' if px_estimated else ''}\n"
                    f"Hold Time: {hold_label}\n"
                    f"PnL (net): <b>{self._fmt_pnl_usdt(pnl_net)} USDT</b>\n"
                    f"PnL (gross): <b>{self._fmt_pnl_usdt(pnl_usdt)} USDT</b>"
                    + (f"\nFees: {self._fmt_pnl_usdt(-(open_fee + close_fee))} USDT" if used_exchange else "")
                )

                # Remove from tracking
                del self.positions[position.symbol]
            else:
                logger.error(
                    f"[Scalping:{self.user_id}] Failed to close position: {result.get('error')}"
                )
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing max hold position: {e}")
    
    async def _close_sideways_max_hold(
        self,
        position: ScalpingPosition,
        max_hold_seconds: Optional[int] = None,
    ):
        """Force close sideways position when dynamic max hold is exceeded."""
        if position.symbol in self._closing_symbols:
            logger.info(f"[Scalping:{self.user_id}] Skip duplicate close attempt for {position.symbol}")
            return
        self._closing_symbols.add(position.symbol)
        try:
            if max_hold_seconds is None:
                max_hold_seconds = self._max_hold_seconds_for_position(position)
            elapsed = int(time.time() - position.opened_at)
            logger.info(
                f"[Scalping:{self.user_id}] Sideways max hold exceeded for {position.symbol} "
                f"(elapsed: {elapsed}s / max={int(max_hold_seconds)}s)"
            )

            close_qty = await self._resolve_close_quantity(position)
            if close_qty <= 0:
                logger.warning(
                    f"[Scalping:{self.user_id}] Sideways close skipped for {position.symbol}: qty<=0"
                )
                self.positions.pop(position.symbol, None)
                return
            
            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=close_qty,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                close_order_id = str(result.get("order_id") or "")
                fill_price = float(result.get('fill_price', 0))
                # If exchange doesn't return fill_price, get current mark price
                if fill_price <= 0:
                    try:
                        ticker = await asyncio.to_thread(self.client.get_ticker, position.symbol)
                        if ticker.get('success'):
                            fill_price = float(ticker.get('mark_price', position.entry_price))
                        else:
                            fill_price = position.entry_price
                    except Exception:
                        fill_price = position.entry_price

                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * close_qty
                else:
                    pnl = (position.entry_price - fill_price) * close_qty

                pnl_usdt = pnl
                pnl_net, open_fee, close_fee, used_exchange = await self._resolve_net_pnl(
                    symbol=position.symbol,
                    gross_pnl=pnl_usdt,
                    open_order_id=getattr(position, "open_order_id", "") or "",
                    close_order_id=close_order_id,
                )
                timeout_phase = str(getattr(position, "timeout_protection_phase", "late"))
                timeout_protected = bool(getattr(position, "timeout_protection_applied", False))
                near_flat_thr = float(getattr(self.config, "timeout_near_flat_usdt_threshold", 0.02) or 0.02)
                near_flat = abs(float(pnl_net)) <= near_flat_thr
                loss_reasoning = self._build_timeout_loss_reasoning(
                    position=position,
                    pnl=pnl_net,
                    phase=timeout_phase,
                    protected=timeout_protected,
                    near_flat=near_flat,
                )

                closed_now = await self._update_position_closed(
                    position,
                    fill_price,
                    pnl_net,
                    "sideways_max_hold_exceeded",
                    loss_reasoning=loss_reasoning,
                )
                if closed_now:
                    logger.info(
                        f"[Scalping:{self.user_id}] "
                        f"{'timeout_exit_with_protection' if timeout_protected else 'timeout_exit_without_protection'} "
                        f"symbol={position.symbol} reason=sideways_max_hold_exceeded phase={timeout_phase} "
                        f"near_flat={int(near_flat)} pnl={pnl_net:+.6f}"
                    )
                    # Confirm position closed with coordinator
                    await coordinator_confirm_closed(
                        self.coordinator,
                        user_id=self.user_id,
                        symbol=position.symbol,
                        now_ts=time.time(),
                    )

                    self.last_closed_meta[position.symbol] = {
                        "ts": time.time(),
                        "side": position.side,
                        "reason": "sideways_max_hold_exceeded",
                    }
                    await self._notify_user_once(
                        dedupe_key=f"sideways_max_hold:{position.symbol}:{position.entry_price:.4f}",
                        message=(
                            f"⏰ <b>SIDEWAYS Closed (Max Hold)</b>\n\n"
                            f"Symbol: {position.symbol}\n"
                            f"Entry: {_fmt_price(position.entry_price)}\n"
                            f"Exit: {_fmt_price(fill_price)}\n"
                            f"Hold Time: {elapsed}s (max {int(max_hold_seconds)}s)\n"
                            f"PnL (net): <b>{self._fmt_pnl_usdt(pnl_net)} USDT</b>\n"
                            f"PnL (gross): <b>{self._fmt_pnl_usdt(pnl_usdt)} USDT</b>"
                            + (f"\nFees: {self._fmt_pnl_usdt(-(open_fee + close_fee))} USDT" if used_exchange else "")
                        ),
                        ttl_sec=600,
                    )
                    # Prevent rapid churn on the same sideways pair.
                    sideways_cd = int(getattr(self.config, "sideways_reentry_cooldown_seconds", 420))
                    self.cooldown_tracker[position.symbol] = time.time() + max(self.config.cooldown_seconds, sideways_cd)
                    logger.info(
                        f"[Scalping:{self.user_id}] Applied sideways re-entry cooldown for "
                        f"{position.symbol}: {max(self.config.cooldown_seconds, sideways_cd)}s"
                    )
                self.positions.pop(position.symbol, None)
            else:
                logger.error(
                    f"[Scalping:{self.user_id}] Failed to close sideways position: {result.get('error')}"
                )
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing sideways max hold: {e}")
        finally:
            self._closing_symbols.discard(position.symbol)
    
    async def _close_position_tp(self, position: ScalpingPosition, fill_price: float):
        """Close position when TP hit"""
        try:
            close_qty = await self._resolve_close_quantity(position)
            if close_qty <= 0:
                logger.warning(
                    f"[Scalping:{self.user_id}] TP close skipped for {position.symbol}: qty<=0"
                )
                self.positions.pop(position.symbol, None)
                return

            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=close_qty,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                # Calculate PnL
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * close_qty
                else:
                    pnl = (position.entry_price - fill_price) * close_qty
                
                pnl_usdt = pnl
                
                closed_now = await self._update_position_closed(position, fill_price, pnl_usdt, "closed_tp")
                if closed_now:
                    # Confirm position closed with coordinator
                    await coordinator_confirm_closed(
                        self.coordinator,
                        user_id=self.user_id,
                        symbol=position.symbol,
                        now_ts=time.time(),
                    )

                    self.last_closed_meta[position.symbol] = {
                        "ts": time.time(),
                        "side": position.side,
                        "reason": "closed_tp",
                    }
                    if position.is_sideways:
                        await self._notify_sideways_closed(position, fill_price, pnl_usdt, "closed_tp")
                    else:
                        await self._notify_user(
                            f"✅ <b>TP Hit!</b>\n\n"
                            f"Symbol: {position.symbol}\n"
                            f"Entry: {position.entry_price:.4f}\n"
                            f"Exit: {fill_price:.4f}\n"
                            f"PnL: <b>{pnl_usdt:+.2f} USDT</b> 🎉"
                        )

                # Social proof broadcast — kirim ke semua user jika profit >= 2 USDT
                if pnl_usdt >= 2.0:
                    try:
                        from app.social_proof import broadcast_profit
                        from app.supabase_repo import get_user_by_tid
                        user_data = get_user_by_tid(self.user_id)
                        fname = user_data.get("first_name", "User") if user_data else "User"
                        import asyncio as _asyncio
                        _asyncio.create_task(broadcast_profit(
                            bot=self.bot,
                            user_id=self.user_id,
                            first_name=fname,
                            symbol=position.symbol,
                            side=position.side,
                            pnl_usdt=pnl_usdt,
                            leverage=position.leverage,
                        ))
                    except Exception as _bp_err:
                        logger.warning(f"[Scalping:{self.user_id}] broadcast_profit failed: {_bp_err}")
                
                self.positions.pop(position.symbol, None)
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing TP position: {e}")
    
    async def _close_position_sl(self, position: ScalpingPosition, fill_price: float):
        """Close position when SL hit"""
        try:
            close_qty = await self._resolve_close_quantity(position)
            if close_qty <= 0:
                logger.warning(
                    f"[Scalping:{self.user_id}] SL close skipped for {position.symbol}: qty<=0"
                )
                self.positions.pop(position.symbol, None)
                return

            close_side = "SELL" if position.side == "BUY" else "BUY"
            
            result = await asyncio.to_thread(
                self.client.place_order,
                symbol=position.symbol,
                side=close_side,
                qty=close_qty,
                order_type='market',
                reduce_only=True
            )
            
            if result.get('success'):
                # Calculate PnL
                if position.side == "BUY":
                    pnl = (fill_price - position.entry_price) * close_qty
                else:
                    pnl = (position.entry_price - fill_price) * close_qty
                
                pnl_usdt = pnl
                
                closed_now = await self._update_position_closed(position, fill_price, pnl_usdt, "closed_sl")
                if closed_now:
                    # Confirm position closed with coordinator
                    await coordinator_confirm_closed(
                        self.coordinator,
                        user_id=self.user_id,
                        symbol=position.symbol,
                        now_ts=time.time(),
                    )

                    self.last_closed_meta[position.symbol] = {
                        "ts": time.time(),
                        "side": position.side,
                        "reason": "closed_sl",
                    }
                    if position.is_sideways:
                        await self._notify_sideways_closed(position, fill_price, pnl_usdt, "closed_sl")
                    else:
                        await self._notify_user(
                            f"🛑 <b>SL Hit</b>\n\n"
                            f"Symbol: {position.symbol}\n"
                            f"Entry: {position.entry_price:.4f}\n"
                            f"Exit: {fill_price:.4f}\n"
                            f"PnL: <b>{pnl_usdt:+.2f} USDT</b>"
                        )

                self.positions.pop(position.symbol, None)
        
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error closing SL position: {e}")

    
    def check_cooldown(self, symbol: str) -> bool:
        """
        Check if symbol is in cooldown period
        
        Args:
            symbol: Trading pair
            
        Returns:
            True if in cooldown, False otherwise
        """
        if symbol not in self.cooldown_tracker:
            return False
        
        cooldown_until = self.cooldown_tracker[symbol]
        current_time = time.time()
        
        if current_time >= cooldown_until:
            # Cooldown expired, remove from tracker
            del self.cooldown_tracker[symbol]
            return False
        
        return True
    
    def mark_cooldown(self, symbol: str):
        """
        Mark symbol as in cooldown for 2.5 minutes
        
        Args:
            symbol: Trading pair
        """
        self.cooldown_tracker[symbol] = time.time() + self.config.cooldown_seconds
        logger.debug(f"[Scalping:{self.user_id}] Cooldown marked for {symbol} (2.5 minutes)")
    
    async def _save_position_to_db(self, position: ScalpingPosition, signal, order_id: str = ""):
        """Save position to database, including sideways metadata if applicable."""
        try:
            from app.trading_mode import MicroScalpSignal as _MicroScalpSignal
            s = _client()
            try:
                persist_qty = float(getattr(position, "quantity", 0.0) or 0.0)
            except Exception:
                persist_qty = 0.0
            if persist_qty <= 0:
                logger.error(
                    f"[Scalping:{self.user_id}] Refusing DB insert for {position.symbol}: non-positive quantity={persist_qty}"
                )
                return None
            fallback_rr = float(getattr(signal, "rr_ratio", 0.0) or 0.0)
            rr_ratio = _derive_rr_ratio(
                entry_price=float(position.entry_price),
                sl_price=float(position.sl_price),
                tp_price=float(position.tp_price),
                fallback_rr=fallback_rr,
            )

            row = {
                "telegram_id": self.user_id,
                "symbol": position.symbol,
                "side": position.side,
                "entry_price": position.entry_price,
                "qty": persist_qty,
                "quantity": persist_qty,
                "original_quantity": persist_qty,
                "remaining_quantity": persist_qty,
                "leverage": position.leverage,
                "tp_price": position.tp_price,
                "sl_price": position.sl_price,
                "rr_ratio": rr_ratio,
                "trade_type": "scalping",
                "trade_subtype": str(getattr(signal, "trade_subtype", "trend_scalp") or "trend_scalp"),
                "timeframe": "5m",
                "confidence": signal.confidence,
                "entry_reasons": list(getattr(signal, "reasons", []) or []),
                "playbook_match_score": float(getattr(signal, "playbook_match_score", 0.0) or 0.0),
                "effective_risk_pct": float(getattr(signal, "effective_risk_pct", 0.0) or 0.0),
                "risk_overlay_pct": float(getattr(signal, "risk_overlay_pct", 0.0) or 0.0),
                "decision_trace_id": str(getattr(signal, "decision_trace_id", "") or "") or None,
                "decision_mode_version": str(getattr(signal, "decision_mode_version", "") or "") or None,
                "decision_regime": str(getattr(signal, "decision_regime", "") or "") or None,
                "decision_final_score": float(getattr(signal, "decision_final_score", 0.0) or 0.0),
                "decision_quality_score": float(getattr(signal, "decision_quality_score", 0.0) or 0.0),
                "decision_community_score": float(getattr(signal, "decision_community_score", 0.0) or 0.0),
                "decision_user_segment_score": float(getattr(signal, "decision_user_segment_score", 0.0) or 0.0),
                "status": "open",
                "order_id": order_id or "",
                "opened_at": datetime.utcnow().isoformat(),
            }

            if isinstance(signal, _MicroScalpSignal):
                # Sideways scalp metadata
                row.update({
                    "trade_subtype": "sideways_scalp",
                    "tp_strategy": "sideways_range_70pct",
                    "max_hold_time": 120,
                    "range_support": signal.range_support,
                    "range_resistance": signal.range_resistance,
                    "range_width_pct": signal.range_width_pct,
                    "bounce_confirmed": bool(getattr(signal, "bounce_confirmed", False)),
                    "rsi_divergence_detected": signal.rsi_divergence_detected,
                })
            else:
                row.update({
                    "tp_strategy": "single_tp_1.5R",
                    "max_hold_time": 1800,
                })

            res = s.table("autotrade_trades").insert(row).execute()
            return res.data[0]["id"] if getattr(res, "data", None) else None
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error saving position to DB: {e}")
            return None
    
    async def _update_position_closed(
        self,
        position: ScalpingPosition,
        close_price: float,
        pnl: float,
        close_reason: str,
        loss_reasoning: str = "",
        win_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update position in database when closed.
        Returns True only when this call successfully closed an OPEN row.
        """
        try:
            s = _client()
            open_rows = s.table("autotrade_trades").select("*").eq(
                "telegram_id", self.user_id
            ).eq("symbol", position.symbol).eq("status", "open").order("opened_at", desc=True).limit(10).execute()
            open_row = None
            for row in (open_rows.data or []):
                row_dict = dict(row)
                if self._is_scalping_trade_row(row_dict):
                    open_row = row_dict
                    break
            if open_row is None:
                logger.info(f"[Scalping:{self.user_id}] No open DB row to close for {position.symbol} (already closed)")
                return False

            trade_id = open_row["id"]
            update_payload, cumulative_pnl, partial_realized = build_cumulative_close_update_payload(
                open_row=open_row,
                position=position,
                close_price=close_price,
                pnl=pnl,
                close_reason=close_reason,
                loss_reasoning=loss_reasoning,
                win_metadata=win_metadata,
                playbook_snapshot=self._win_playbook_snapshot,
            )

            if partial_realized > 0:
                logger.info(
                    f"[Scalping:{self.user_id}] cumulative_pnl applied for {position.symbol}: "
                    f"partial={partial_realized:+.6f} final_leg={float(pnl):+.6f} total={cumulative_pnl:+.6f}"
                )

            res = s.table("autotrade_trades").update(update_payload).eq("id", trade_id).eq("status", "open").execute()
            if not getattr(res, "data", None):
                logger.info(f"[Scalping:{self.user_id}] DB close skipped for {position.symbol} (race already closed)")
                return False
            return True
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error updating position in DB: {e}")
            return False
    
    async def _notify_sideways_opened(self, position: ScalpingPosition, signal):
        """Notify user when sideways scalp position opened"""
        try:
            reasons_text = "\n".join(f"• {r}" for r in signal.reasons)
            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    f"⚡ <b>SIDEWAYS SCALP Opened</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Side: {position.side}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"TP: {position.tp_price:.4f}\n"
                    f"SL: {position.sl_price:.4f}\n"
                    f"R:R: 1:{signal.rr_ratio:.2f}\n"
                    f"Confidence: {signal.confidence}%\n"
                    f"Range: {signal.range_support:.4f} - {signal.range_resistance:.4f}\n"
                    f"Max Hold: 2 menit\n\n"
                    f"<b>Reasons:</b>\n{reasons_text}"
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending sideways notification: {e}")

    async def _notify_sideways_closed(self, position: ScalpingPosition, fill_price: float, pnl: float, reason: str):
        """Notify user when sideways scalp position closed"""
        try:
            if reason == "closed_tp":
                label = "✅ SIDEWAYS TP Hit"
            elif reason == "closed_sl":
                label = "🛑 SIDEWAYS SL Hit"
            else:
                label = "⏰ SIDEWAYS Closed (2min)"
            
            await self._notify_user_once(
                dedupe_key=f"{reason}:{position.symbol}:{position.entry_price:.4f}",
                message=(
                    f"{label}\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"Exit: {fill_price:.4f}\n"
                    f"PnL: <b>{pnl:+.2f} USDT</b>"
                ),
                ttl_sec=600,
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending sideways close notification: {e}")

    async def _notify_position_opened(self, position: ScalpingPosition, signal: ScalpingSignal):
        """Notify user when position opened"""
        try:
            reasons_text = "\n".join(f"• {r}" for r in signal.reasons)
            risk = abs(position.entry_price - position.sl_price)
            reward = abs(position.tp_price - position.entry_price)
            rr_live = (reward / risk) if risk > 0 else 0.0
            
            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    f"⚡ <b>SCALP Trade Opened</b>\n\n"
                    f"Symbol: {position.symbol}\n"
                    f"Side: {position.side}\n"
                    f"Entry: {position.entry_price:.4f}\n"
                    f"TP: {position.tp_price:.4f} (R:R 1:{rr_live:.2f})\n"
                    f"SL: {position.sl_price:.4f}\n"
                    f"Confidence: {signal.confidence:.0f}%\n"
                    f"Max Hold: 30 minutes\n\n"
                    f"<b>Reasons:</b>\n{reasons_text}"
                ),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending notification: {e}")
    
    async def _notify_stackmentor_opened(
        self,
        position: ScalpingPosition,
        signal,
        levels,
        order_id: str = "-",
        trade_id: Optional[int] = None,
    ):
        """Notify user when StackMentor position opened.

        `levels` is a `StackMentorLevels` dataclass from app.trade_execution.
        """
        try:
            risk_amount = abs(position.entry_price - levels.sl) * position.quantity
            base_risk_pct = float(getattr(signal, "base_risk_pct", 1.0) or 1.0)
            overlay_pct = float(getattr(signal, "risk_overlay_pct", 0.0) or 0.0)
            effective_risk_pct = float(getattr(signal, "effective_risk_pct", base_risk_pct) or base_risk_pct)
            risk_audit_line = format_and_emit_order_open_risk_audit(
                logger=logger,
                user_id=self.user_id,
                symbol=position.symbol,
                side=position.side,
                order_id=str(order_id or "-"),
                base_risk_pct=base_risk_pct,
                overlay_pct=overlay_pct,
                effective_risk_pct=effective_risk_pct,
                implied_risk_usdt=risk_amount,
            )
            runner_active = float(getattr(levels, "qty_tp3", 0.0) or 0.0) > 0 and abs(
                float(getattr(levels, "tp3", 0.0) or 0.0) - float(getattr(levels, "tp1", 0.0) or 0.0)
            ) > 1e-9
            acc_result = await asyncio.to_thread(self.client.get_account_info)
            current_equity = 0.0
            if acc_result.get("success"):
                available = float(acc_result.get("available", 0) or 0)
                frozen = float(acc_result.get("frozen", 0) or 0)
                unrealized = float(acc_result.get("total_unrealized_pnl", 0) or 0)
                current_equity = available + frozen + unrealized
            risk_pct_equity = (risk_amount / current_equity * 100) if current_equity > 0 else None
            direction = "Long" if position.side.upper() in ("BUY", "LONG") else "Short"
            opened_at = datetime.utcnow().strftime("%d %b %Y %H:%M:%S UTC")
            order_id_text = escape(str(order_id or "-"))
            tp_block = (
                (
                    f"<b>TP1 (Partial):</b> {_fmt_price(levels.tp1)}\n"
                    f"<b>Runner TP (TP3):</b> {_fmt_price(levels.tp3)}\n"
                    f"<b>Split:</b> {float(levels.qty_tp1 / position.quantity * 100) if position.quantity > 0 else 0:.0f}% / "
                    f"{float(levels.qty_tp3 / position.quantity * 100) if position.quantity > 0 else 0:.0f}%\n"
                )
                if runner_active else
                f"<b>TP:</b> {_fmt_price(levels.tp1)}\n"
            )

            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=(
                    "🤖 <b>Cryptomentor AI Autotrade</b>\n\n"
                    f"<b>Direction:</b> {direction}\n"
                    f"<b>Trading Pair:</b> {position.symbol}\n"
                    f"<b>Entry:</b> {_fmt_price(position.entry_price)}\n"
                    + tp_block
                    + f"<b>SL:</b> {_fmt_price(levels.sl)}\n"
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
                reply_markup=_trade_detail_keyboard(trade_id=trade_id, order_id=order_id, symbol=position.symbol),
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending StackMentor notification: {e}")
    
    async def _notify_user(self, message: str):
        """Send notification to user"""
        try:
            await self.bot.send_message(
                chat_id=self.notify_chat_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Error sending notification: {e}")

    async def _notify_user_once(self, dedupe_key: str, message: str, ttl_sec: int = 600):
        """Best-effort in-memory dedupe for repeated close notifications."""
        now = time.time()
        last_sent = self._recent_close_notifications.get(dedupe_key, 0)
        if now - last_sent < ttl_sec:
            logger.info(f"[Scalping:{self.user_id}] Suppressed duplicate notification: {dedupe_key}")
            return
        self._recent_close_notifications[dedupe_key] = now
        await self._notify_user(message)

    async def _load_existing_positions(self):
        """Load open positions from database on startup to resume monitoring"""
        try:
            from app.supabase_repo import _client as _sc
            from app.trading_mode import ScalpingPosition
            from datetime import datetime
            
            s = _sc()
            res = s.table("autotrade_trades").select("*").eq(
                "telegram_id", self.user_id
            ).eq("status", "open").execute()
            
            if res.data:
                scalping_rows = [dict(row) for row in (res.data or []) if self._is_scalping_trade_row(dict(row))]
                logger.info(f"[Scalping:{self.user_id}] Found {len(scalping_rows)} open scalping trades in DB. Resuming tracking...")
                for row in scalping_rows:
                    symbol = row.get("symbol")
                    if not symbol or symbol in self.positions:
                        continue
                    
                    # Convert ISO string to Unix timestamp
                    opened_at_str = row.get("opened_at")
                    try:
                        if opened_at_str:
                            # Handle different ISO formats (Z vs +00:00)
                            if opened_at_str.endswith('Z'):
                                opened_at_str = opened_at_str.replace('Z', '+00:00')
                            dt = datetime.fromisoformat(opened_at_str)
                            opened_at = dt.timestamp()
                        else:
                            opened_at = time.time()
                    except Exception as parse_err:
                        logger.warning(f"[Scalping:{self.user_id}] Could not parse timestamp {opened_at_str}: {parse_err}")
                        opened_at = time.time()
                    
                    pos = ScalpingPosition(
                        user_id=self.user_id,
                        symbol=symbol,
                        side=row.get("side", "BUY"),
                        entry_price=float(row.get("entry_price", 0)),
                        quantity=float(row.get("qty", row.get("quantity", 0)) or 0),
                        leverage=int(row.get("leverage", 10)),
                        tp_price=float(row.get("tp_price", 0)),
                        sl_price=float(row.get("sl_price", 0)),
                        opened_at=opened_at
                    )
                    setattr(pos, "entry_reasons", list(row.get("entry_reasons", []) or []))
                    setattr(pos, "playbook_match_score", float(row.get("playbook_match_score", 0) or 0))
                    setattr(pos, "effective_risk_pct", float(row.get("effective_risk_pct", 0) or 0))
                    setattr(pos, "risk_overlay_pct", float(row.get("risk_overlay_pct", 0) or 0))
                    setattr(pos, "initial_sl_price", float(row.get("sl_price", 0) or 0))
                    setattr(pos, "timeout_protection_applied", False)
                    setattr(pos, "timeout_protection_phase", "early")
                    setattr(pos, "timeout_last_sl_update_ts", 0.0)
                    
                    # Check if it was a sideways trade
                    if row.get("trade_subtype") == "sideways_scalp":
                        pos.is_sideways = True
                    
                    self.positions[symbol] = pos
                    logger.info(f"[Scalping:{self.user_id}] Resumed tracking for {symbol} (opened {int(time.time() - opened_at)}s ago)")
            
        except Exception as e:
            logger.error(f"[Scalping:{self.user_id}] Failed to load existing positions: {e}")
