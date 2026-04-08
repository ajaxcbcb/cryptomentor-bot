"""
Performance analytics endpoint — real PnL data from autotrade_trades.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, Depends
from app.routes.dashboard import get_current_user
from app.db.supabase import _client

router = APIRouter(prefix="/dashboard", tags=["performance"])


@router.get("/performance")
async def get_performance(tg_id: int = Depends(get_current_user)):
    s = _client()
    since_90d = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    # Fetch closed trades last 90 days
    res = s.table("autotrade_trades").select(
        "pnl_usdt, closed_at, tp1_hit, tp2_hit, tp3_hit, status"
    ).eq("telegram_id", tg_id).eq("status", "closed").gte(
        "closed_at", since_90d
    ).order("closed_at").execute()

    trades = res.data or []

    if not trades:
        return {
            "metrics": {
                "sharpe": 0,
                "max_drawdown_pct": 0,
                "win_rate_pct": 0,
                "total_trades": 0,
                "volatility_pct": 0,
            },
            "equity_curve": [],
            "pnl_30d": 0.0,
        }

    pnls = [float(t.get("pnl_usdt") or 0) for t in trades]
    wins = sum(1 for p in pnls if p > 0)
    total = len(pnls)
    win_rate = (wins / total * 100) if total > 0 else 0

    # Cumulative equity curve — field name "equity" matches frontend AreaChart dataKey
    cumulative = 0.0
    equity_curve = []
    for t in trades:
        cumulative += float(t.get("pnl_usdt") or 0)
        equity_curve.append({
            "date": (t.get("closed_at") or "")[:10],
            "equity": round(cumulative, 4),
        })

    # Max drawdown
    peak = 0.0
    max_dd = 0.0
    running = 0.0
    for p in pnls:
        running += p
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_dd:
            max_dd = dd
    max_dd_pct = (max_dd / peak * 100) if peak > 0 else 0

    # Monthly volatility (std of monthly PnL)
    import statistics
    monthly: Dict[str, float] = {}
    for t in trades:
        month = (t.get("closed_at") or "")[:7]
        if month:
            monthly[month] = monthly.get(month, 0) + float(t.get("pnl_usdt") or 0)
    monthly_vals = list(monthly.values())
    vol = statistics.stdev(monthly_vals) if len(monthly_vals) >= 2 else 0

    # Sharpe (simplified: mean/std of trade PnLs)
    mean_pnl = statistics.mean(pnls) if pnls else 0
    std_pnl = statistics.stdev(pnls) if len(pnls) >= 2 else 1
    sharpe = round(mean_pnl / std_pnl, 2) if std_pnl > 0 else 0

    # PnL last 30 days
    since_30d = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    pnl_30d = sum(
        float(t.get("pnl_usdt") or 0)
        for t in trades
        if (t.get("closed_at") or "") >= since_30d
    )

    return {
        "metrics": {
            "sharpe": sharpe,
            "max_drawdown_pct": round(max_dd_pct, 1),
            "win_rate_pct": round(win_rate, 1),
            "total_trades": total,
            "volatility_pct": round(vol, 1),
        },
        "equity_curve": equity_curve,
        "pnl_30d": round(pnl_30d, 2),
    }
