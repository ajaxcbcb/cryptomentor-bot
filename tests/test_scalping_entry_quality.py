import os
import sys
from types import SimpleNamespace

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BISMILLAH = os.path.join(_ROOT, "Bismillah")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if _BISMILLAH not in sys.path:
    sys.path.insert(0, _BISMILLAH)

import app.scalping_engine as scalping_engine  # type: ignore
from app.scalping_engine import ScalpingEngine  # type: ignore
from app.trading_mode import MicroScalpSignal  # type: ignore


def _make_engine():
    engine = ScalpingEngine.__new__(ScalpingEngine)
    engine.user_id = 9001
    engine.config = SimpleNamespace(
        min_confidence=0.72,
        min_rr=1.5,
        sideways_min_rr=1.1,
        max_concurrent_positions=4,
        min_atr_pct=0.2,
        max_atr_pct=10.0,
        pairs=["BTCUSDT"],
        signal_confirmation_max_gap_seconds=45,
    )
    engine.positions = {}
    engine._active_scan_pairs = ["BTCUSDT"]
    engine._mixed_mode = False
    engine._adaptive_overlay = {"conf_delta": 0, "volume_min_ratio_delta": 0.0}
    engine._confidence_adapt_snapshot = {}
    engine._scalp_risk_parity_snapshot = {}
    engine._sideways_governor_snapshot = {
        "mode": "strict",
        "allow_sideways_entries": True,
        "allow_sideways_fallback": False,
        "sideways_min_rr_override": 1.25,
        "sideways_min_volume_floor": 1.1,
        "sideways_confidence_bonus": 3,
        "sideways_confirmations_required": 2,
        "sample_size_24h": 0,
        "sample_basis_window": "14d_fallback",
        "sample_size_basis": 28,
        "sideways_expectancy_basis": -0.02,
        "sideways_timeout_loss_rate_basis": 0.75,
        "fallback_recovery_windows": 0,
        "decision_reason": "strict_sideways_quality",
    }
    engine._win_playbook_snapshot = {"guardrails_healthy": False}
    return engine


def _patch_validation_dependencies(monkeypatch, *, match_meta):
    monkeypatch.setattr(scalping_engine, "_client", lambda: object())
    monkeypatch.setattr(
        scalping_engine,
        "get_confidence_adaptation",
        lambda *args, **kwargs: {
            "bucket": "70-74",
            "bucket_penalty": 0,
            "bucket_risk_scale": 1.0,
            "edge_adj": 0.0,
            "bucket_sample_size": 100,
            "reason": "ok",
        },
    )
    monkeypatch.setattr(
        scalping_engine,
        "apply_scalping_confidence_relief",
        lambda conf_adapt, parity_controls: {**conf_adapt, "parity_conf_relief_applied": False},
    )
    monkeypatch.setattr(
        scalping_engine,
        "get_scalping_risk_parity_controls",
        lambda *_args, **_kwargs: {"regime": "disabled", "ratio": 1.0},
    )
    monkeypatch.setattr(
        scalping_engine,
        "compute_playbook_match_from_reasons",
        lambda *args, **kwargs: dict(match_meta),
    )
    monkeypatch.setattr(
        scalping_engine,
        "evaluate_adaptive_daily_circuit_breaker",
        lambda **kwargs: {
            "blocked": False,
            "override_applied": False,
            "decision_reason": "within_adaptive_limit",
            "threshold_source": "adaptive_win_playbook",
            "loss_pct_today": 0.0,
            "adaptive_limit_pct": 0.05,
            "base_limit_pct": 0.05,
            "adaptive_step": 0,
            "adaptive_step_reason": "neutral",
            "sample_size": 0,
            "rolling_win_rate": 0.0,
            "rolling_expectancy": 0.0,
            "strong_opportunity": False,
        },
    )


def test_validate_scalping_entry_rejects_low_confidence_trend_without_volume_and_playbook(monkeypatch):
    engine = _make_engine()
    _patch_validation_dependencies(
        monkeypatch,
        match_meta={
            "playbook_match_score": 0.19,
            "matched_tags": [],
            "matched_pair_tags": [],
            "reason_tags": ["ema_alignment"],
            "strong_match": False,
        },
    )

    signal = SimpleNamespace(
        symbol="BTCUSDT",
        side="LONG",
        confidence=74.0,
        rr_ratio=1.6,
        volume_ratio=1.2,
        atr_pct=1.0,
        reasons=["EMA aligned"],
        is_emergency=False,
    )

    assert engine.validate_scalping_entry(signal) is False


def test_validate_scalping_entry_allows_low_confidence_trend_with_volume_and_playbook(monkeypatch):
    engine = _make_engine()
    _patch_validation_dependencies(
        monkeypatch,
        match_meta={
            "playbook_match_score": 0.25,
            "matched_tags": ["volume_confirmation"],
            "matched_pair_tags": [],
            "reason_tags": ["volume_confirmation", "ema_alignment"],
            "strong_match": False,
        },
    )

    signal = SimpleNamespace(
        symbol="BTCUSDT",
        side="LONG",
        confidence=74.0,
        rr_ratio=1.6,
        volume_ratio=1.2,
        atr_pct=1.0,
        reasons=["Volume confirmation 1.6x", "EMA aligned"],
        is_emergency=False,
    )

    assert engine.validate_scalping_entry(signal) is True


def test_validate_scalping_entry_rejects_sideways_without_bounce_confirmation(monkeypatch):
    engine = _make_engine()
    _patch_validation_dependencies(
        monkeypatch,
        match_meta={
            "playbook_match_score": 0.0,
            "matched_tags": [],
            "matched_pair_tags": [],
            "reason_tags": ["range_context"],
            "strong_match": False,
        },
    )

    signal = MicroScalpSignal(
        symbol="BTCUSDT",
        side="LONG",
        entry_price=100.0,
        tp_price=101.6,
        sl_price=98.5,
        rr_ratio=1.3,
        range_support=99.0,
        range_resistance=102.0,
        range_width_pct=1.8,
        confidence=85,
        bounce_confirmed=False,
        rsi_divergence_detected=False,
        volume_ratio=1.2,
        reasons=["Sideways market: range"],
    )

    assert engine.validate_scalping_entry(signal) is False
