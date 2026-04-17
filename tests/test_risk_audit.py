import logging
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

try:
    from Bismillah.app.risk_audit import format_risk_audit_line, emit_order_open_risk_audit
except ImportError:
    from app.risk_audit import format_risk_audit_line, emit_order_open_risk_audit  # type: ignore


def test_format_risk_audit_line_expected_format():
    line = format_risk_audit_line(
        base_risk_pct=5.0,
        overlay_pct=-0.50,
        effective_risk_pct=4.5,
        implied_risk_usdt=0.0595,
    )
    assert line == "Risk Audit: base 5.00% | overlay -0.50% | effective 4.50% | implied $0.0595"


def test_format_risk_audit_line_invalid_values_fallback_to_zero():
    line = format_risk_audit_line(
        base_risk_pct="bad",
        overlay_pct=None,
        effective_risk_pct={},
        implied_risk_usdt="NaN-nope",
    )
    assert line == "Risk Audit: base 0.00% | overlay +0.00% | effective 0.00% | implied $0.0000"


def test_emit_order_open_risk_audit_logs_single_structured_line(caplog):
    test_logger = logging.getLogger("tests.risk_audit")

    with caplog.at_level(logging.INFO, logger="tests.risk_audit"):
        emit_order_open_risk_audit(
            test_logger,
            user_id=123,
            symbol="ORDIUSDT",
            side="SHORT",
            order_id="1435085367318471237",
            base_risk_pct=5.0,
            overlay_pct=0.25,
            effective_risk_pct=5.25,
            implied_risk_usdt=0.0595,
        )

    messages = [record.getMessage() for record in caplog.records if record.name == "tests.risk_audit"]
    assert len(messages) == 1
    msg = messages[0]
    assert "order_open_risk_audit" in msg
    assert "user_id=123" in msg
    assert "symbol=ORDIUSDT" in msg
    assert "side=SHORT" in msg
    assert "order_id=1435085367318471237" in msg
    assert "base_risk=5.00" in msg
    assert "overlay=+0.25" in msg
    assert "effective_risk=5.25" in msg
    assert "implied_risk_usdt=0.0595" in msg
