import os
import sys
from datetime import datetime, timedelta, timezone

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    from Bismillah.app.playbook_analytics import build_playbook_analysis  # type: ignore
except ImportError:
    from app.playbook_analytics import build_playbook_analysis  # type: ignore


def _mk_trade(
    *,
    idx: int,
    status: str,
    close_reason: str,
    pnl: float,
    reasons=None,
    win_reasoning: str = "",
    playbook_match_score: float = 0.0,
    trade_type: str = "swing",
    confidence: int = 75,
):
    base = datetime(2026, 4, 20, tzinfo=timezone.utc)
    return {
        "id": idx,
        "symbol": "BTCUSDT",
        "status": status,
        "close_reason": close_reason,
        "pnl_usdt": float(pnl),
        "entry_reasons": reasons or [],
        "closed_at": (base - timedelta(minutes=idx)).isoformat(),
        "trade_type": trade_type,
        "timeframe": "5m" if trade_type == "scalping" else "15m",
        "confidence": confidence,
        "entry_price": 100.0,
        "sl_price": 99.0,
        "qty": 1.0,
        "win_reasoning": win_reasoning,
        "playbook_match_score": playbook_match_score,
    }


def test_build_playbook_analysis_filters_non_strategy_outcomes():
    rows = []
    for i in range(10):
        rows.append(
            _mk_trade(
                idx=i,
                status="closed_tp",
                close_reason="closed_tp",
                pnl=1.0,
                reasons=["Volume confirmation"],
            )
        )
    for i in range(10, 16):
        rows.append(
            _mk_trade(
                idx=i,
                status="max_hold_time_exceeded",
                close_reason="max_hold_time_exceeded",
                pnl=-0.2,
                reasons=["Range context"],
            )
        )

    out = build_playbook_analysis(rows, now_utc=datetime(2026, 4, 20, tzinfo=timezone.utc))
    assert out["sample_size"] == 10
    assert out["window"]["strategy_rows_available"] == 10


def test_build_playbook_analysis_bucket_scoring():
    rows = []
    idx = 1
    for _ in range(30):
        rows.append(
            _mk_trade(
                idx=idx,
                status="closed_tp",
                close_reason="closed_tp",
                pnl=1.2,
                reasons=["Volume confirmation", "BTC aligned"],
                playbook_match_score=0.75,
            )
        )
        idx += 1
    for _ in range(10):
        rows.append(
            _mk_trade(
                idx=idx,
                status="closed_sl",
                close_reason="closed_sl",
                pnl=-0.3,
                reasons=["Volume confirmation"],
            )
        )
        idx += 1
    for _ in range(30):
        rows.append(
            _mk_trade(
                idx=idx,
                status="closed_sl",
                close_reason="closed_sl",
                pnl=-1.0,
                reasons=["RSI overbought"],
            )
        )
        idx += 1
    for _ in range(10):
        rows.append(
            _mk_trade(
                idx=idx,
                status="closed_tp",
                close_reason="closed_tp",
                pnl=0.1,
                reasons=["RSI overbought"],
            )
        )
        idx += 1
    rows.extend(
        [
            _mk_trade(
                idx=idx + 1,
                status="closed_tp",
                close_reason="closed_tp",
                pnl=0.3,
                reasons=["EMA cross"],
            ),
            _mk_trade(
                idx=idx + 2,
                status="closed_sl",
                close_reason="closed_sl",
                pnl=-0.3,
                reasons=["EMA cross"],
            ),
        ]
    )

    out = build_playbook_analysis(rows, now_utc=datetime(2026, 4, 20, tzinfo=timezone.utc))
    promote_labels = " ".join([str(r.get("label")) for r in out.get("promote", [])]).lower()
    avoid_labels = " ".join([str(r.get("label")) for r in out.get("avoid", [])]).lower()
    watch_labels = " ".join([str(r.get("label")) for r in out.get("watch", [])]).lower()

    assert "volume_confirmation" in promote_labels
    assert "rsi_context" in avoid_labels
    assert "ema_alignment" in watch_labels or "reason:ema_cross" in watch_labels


def test_build_playbook_analysis_coverage_kpis():
    rows = [
        _mk_trade(
            idx=1,
            status="closed_tp",
            close_reason="closed_tp",
            pnl=1.0,
            reasons=["Volume confirmation"],
            win_reasoning="good entry",
            playbook_match_score=0.80,
        ),
        _mk_trade(
            idx=2,
            status="closed_tp",
            close_reason="closed_tp",
            pnl=0.8,
            reasons=["Volume confirmation"],
            win_reasoning="",
            playbook_match_score=0.20,
        ),
        _mk_trade(
            idx=3,
            status="closed_tp",
            close_reason="closed_tp",
            pnl=0.6,
            reasons=["RSI context"],
            win_reasoning="structured win",
            playbook_match_score=0.40,
        ),
        _mk_trade(
            idx=4,
            status="closed_sl",
            close_reason="closed_sl",
            pnl=-0.7,
            reasons=[],
        ),
    ]

    out = build_playbook_analysis(rows, now_utc=datetime(2026, 4, 20, tzinfo=timezone.utc))
    cov = out["coverage"]
    assert cov["wins_count"] == 3
    assert cov["wins_with_reasoning_count"] == 2
    assert cov["wins_with_reasoning_pct"] == 66.67
    assert cov["closed_with_usable_tags_count"] == 3
    assert cov["closed_with_usable_tags_pct"] == 75.0
    assert cov["weak_or_missing_playbook_match_wins_count"] == 2
    assert cov["weak_or_missing_playbook_match_wins_pct"] == 66.67
