"""
Performance analytics endpoint — canonical dashboard performance payload.
"""

from __future__ import annotations

import importlib.util
import logging
import math
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends

from app.db.supabase import _client
from app.routes.dashboard import get_current_user
from app.services import bitunix as bsvc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["performance"])

CLOSED_STATUSES = [
    "closed",
    "closed_tp",
    "closed_sl",
    "closed_tp1",
    "closed_tp2",
    "closed_tp3",
    "closed_flip",
    "closed_manual",
]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _load_playbook_analysis_builder() -> Optional[Callable[..., Dict[str, Any]]]:
    # Preferred path when Bismillah is importable as a package.
    try:
        from Bismillah.app.playbook_analytics import build_playbook_analysis  # type: ignore

        return build_playbook_analysis
    except Exception:
        pass

    # Fallback: load analyzer by file path.
    analyzer_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "Bismillah", "app", "playbook_analytics.py")
    )
    if not os.path.exists(analyzer_path):
        return None
    try:
        spec = importlib.util.spec_from_file_location("bismillah_playbook_analytics", analyzer_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        builder = getattr(module, "build_playbook_analysis", None)
        if callable(builder):
            return builder
    except Exception as e:
        logger.warning(f"[Performance] playbook analyzer import failed: {e}")
    return None


_PLAYBOOK_ANALYSIS_BUILDER = _load_playbook_analysis_builder()


def _fallback_empty_playbook_analysis(now_utc: datetime) -> Dict[str, Any]:
    return {
        "window": {
            "policy": "max(last_300, last_14d)",
            "target_strategy_sample": 300,
            "target_lookback_days": 14,
            "sample_start": None,
            "sample_end": None,
            "strategy_rows_available": 0,
        },
        "sample_size": 0,
        "promote": [],
        "watch": [],
        "avoid": [],
        "coverage": {
            "wins_count": 0,
            "wins_with_reasoning_count": 0,
            "wins_with_reasoning_pct": 100.0,
            "closed_with_usable_tags_count": 0,
            "closed_with_usable_tags_pct": 0.0,
            "weak_or_missing_playbook_match_wins_count": 0,
            "weak_or_missing_playbook_match_wins_pct": 100.0,
            "strong_match_threshold": 0.55,
        },
        "generated_at": now_utc.isoformat(),
        "sparse_data": True,
    }


async def build_performance_payload(tg_id: int) -> Dict[str, Any]:
    s = _client()
    now_utc = datetime.now(timezone.utc)
    since_90d = (now_utc - timedelta(days=90)).isoformat()
    since_30d = (now_utc - timedelta(days=30)).isoformat()

    trades_res = (
        s.table("autotrade_trades")
        .select(
            "symbol,pnl_usdt,status,close_reason,opened_at,closed_at,entry_reasons,trade_type,timeframe,"
            "confidence,entry_price,sl_price,qty,quantity,original_quantity,win_reasoning,playbook_match_score"
        )
        .eq("telegram_id", int(tg_id))
        .in_("status", CLOSED_STATUSES)
        .gte("closed_at", since_90d)
        .order("closed_at")
        .execute()
    )
    trades = trades_res.data or []

    sess = (
        s.table("autotrade_sessions")
        .select("initial_deposit,current_balance")
        .eq("telegram_id", int(tg_id))
        .limit(1)
        .execute()
    )
    sess_row = (sess.data or [{}])[0]
    start_equity = _as_float(sess_row.get("initial_deposit"), 0.0)
    if start_equity <= 0:
        start_equity = _as_float(sess_row.get("current_balance"), 0.0)
    if start_equity <= 0:
        try:
            acc = await bsvc.fetch_account(int(tg_id))
            if acc.get("success"):
                start_equity = _as_float(acc.get("available"), 0.0)
        except Exception:
            pass
    if start_equity <= 0:
        start_equity = 10000.0

    if not trades:
        analysis = _fallback_empty_playbook_analysis(now_utc=now_utc)
        if _PLAYBOOK_ANALYSIS_BUILDER is not None:
            try:
                analysis = _PLAYBOOK_ANALYSIS_BUILDER([], now_utc=now_utc)
            except Exception:
                pass
        return {
            "metrics": {
                "sharpe": 0.0,
                "max_drawdown_pct": 0.0,
                "win_rate_pct": 0.0,
                "total_trades": 0,
                "volatility_pct": 0.0,
            },
            "equity_curve": [],
            "pnl_30d": 0.0,
            "start_equity": round(start_equity, 2),
            "playbook_analysis": analysis,
        }

    total_trades = len(trades)
    pnls = [_as_float(t.get("pnl_usdt"), 0.0) for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0

    by_day: Dict[str, float] = {}
    for t in trades:
        ts = t.get("closed_at") or t.get("opened_at")
        if not ts:
            continue
        try:
            day = datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date().isoformat()
        except Exception:
            continue
        by_day[day] = by_day.get(day, 0.0) + _as_float(t.get("pnl_usdt"), 0.0)

    days_sorted = sorted(by_day.keys())
    equity = float(start_equity)
    peak = float(start_equity)
    max_dd_pct = 0.0
    daily_returns: List[float] = []
    equity_curve: List[Dict[str, Any]] = []
    for day in days_sorted:
        prev = equity
        equity += float(by_day[day])
        if prev > 0:
            daily_returns.append((equity - prev) / prev)
        peak = max(peak, equity)
        if peak > 0:
            dd = (equity - peak) / peak
            if dd < max_dd_pct:
                max_dd_pct = dd
        equity_curve.append({"date": day, "equity": round(equity, 2)})
    if equity_curve:
        equity_curve = [{"date": "Start", "equity": round(start_equity, 2)}] + equity_curve

    sharpe = 0.0
    volatility_pct = 0.0
    if len(daily_returns) >= 2:
        mean_r = sum(daily_returns) / len(daily_returns)
        var_r = sum((r - mean_r) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_r = math.sqrt(var_r)
        if std_r > 0:
            sharpe = (mean_r / std_r) * math.sqrt(365)
        volatility_pct = std_r * math.sqrt(30) * 100.0

    pnl_30d = sum(
        _as_float(t.get("pnl_usdt"), 0.0)
        for t in trades
        if str(t.get("closed_at") or "") >= since_30d
    )

    playbook_analysis = _fallback_empty_playbook_analysis(now_utc=now_utc)
    if _PLAYBOOK_ANALYSIS_BUILDER is not None:
        try:
            playbook_analysis = _PLAYBOOK_ANALYSIS_BUILDER(trades, now_utc=now_utc)
        except Exception as analysis_err:
            logger.warning(f"[Performance] playbook analysis failed: {analysis_err}")

    return {
        "metrics": {
            "sharpe": round(float(sharpe), 2),
            "max_drawdown_pct": round(float(max_dd_pct) * 100.0, 2),
            "win_rate_pct": round(float(win_rate), 2),
            "total_trades": int(total_trades),
            "volatility_pct": round(float(volatility_pct), 2),
        },
        "equity_curve": equity_curve,
        "pnl_30d": round(float(pnl_30d), 2),
        "start_equity": round(float(start_equity), 2),
        "playbook_analysis": playbook_analysis,
    }


@router.get("/performance")
async def get_performance(tg_id: int = Depends(get_current_user)):
    return await build_performance_payload(tg_id=tg_id)
