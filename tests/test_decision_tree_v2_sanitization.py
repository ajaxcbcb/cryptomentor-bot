import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

from app.trade_candidate import TradeCandidate
from app.tradeability import score_tradeability


def test_tradeability_rejects_invalid_candidate():
    candidate = TradeCandidate(
        user_id=1,
        symbol="BTCUSDT",
        engine="swing",
        side="LONG",
        regime="trend_continuation",
        setup_name="x",
        entry_price=0.0,
        stop_loss=0.0,
        take_profit_hint=0.0,
        rr_estimate=0.0,
        signal_confidence=0.0,
    )
    result = score_tradeability(candidate, market_context=type("Ctx", (), {"session_quality": 0.5})(), symbol_memory={})
    assert result["hard_reject_reason"] == "invalid_candidate"
    assert result["tradeability_score"] == 0.0

