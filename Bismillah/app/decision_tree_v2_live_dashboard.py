from __future__ import annotations

import html
import json
import logging
import re
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.supabase_repo import _client
from app.volume_pair_selector import get_ranked_top_volume_pairs, get_selector_health

logger = logging.getLogger(__name__)
_ROOT = Path(__file__).resolve().parents[2]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return float(default)


def _score_distribution(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    buckets: Counter[str] = Counter()
    for row in rows:
        value = _safe_float(row.get(field), 0.0)
        if value < 0.20:
            buckets["lt_0_20"] += 1
        elif value < 0.40:
            buckets["0_20_to_0_39"] += 1
        elif value < 0.60:
            buckets["0_40_to_0_59"] += 1
        elif value < 0.80:
            buckets["0_60_to_0_79"] += 1
        else:
            buckets["gte_0_80"] += 1
    return dict(buckets)


def _load_live_candidates(minutes: int) -> list[dict[str, Any]]:
    cutoff = (_utc_now() - timedelta(minutes=int(minutes))).isoformat()
    client = _client()
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        batch = (
            client.table("trade_candidates_log")
            .select("*")
            .gte("created_at", cutoff)
            .order("created_at", desc=False)
            .range(offset, offset + 999)
            .execute()
            .data
            or []
        )
        rows.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000

    live_rows: list[dict[str, Any]] = []
    for row in rows:
        metadata = row.get("metadata") or {}
        if isinstance(metadata, dict) and str(metadata.get("execution_mode") or "").lower() == "live":
            live_rows.append(row)
    return live_rows


def _normalize_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def _run_journal_query(minutes: int, tail: int) -> dict[str, Any]:
    if shutil.which("journalctl") is None:
        return {"available": False, "reason": "journalctl_not_found"}

    since = f"{int(minutes)} minutes ago"
    cmd = ["journalctl", "-u", "cryptomentor", "--since", since, "--no-pager", "--output=cat"]
    try:
        raw_log = subprocess.check_output(cmd, text=True, errors="replace")
    except Exception as exc:
        return {"available": False, "reason": f"journalctl_failed: {exc}"}

    symbol_stats: dict[str, Counter[str]] = {}

    def _bump(symbol: str, metric: str) -> None:
        sym = _normalize_symbol(symbol)
        if not sym:
            return
        bucket = symbol_stats.setdefault(sym, Counter())
        bucket[metric] += 1

    scan_re = re.compile(r"Scanning 10 top-volume pairs:\s*(.+)$")
    paused_re = re.compile(r"\b([A-Z0-9]+USDT)\b sideways entry paused by governor")
    signal_re = re.compile(r"Signal generated:\s*([A-Z0-9]+USDT)\s+(LONG|SHORT)")
    candidate_re = re.compile(r"Candidate funnel .*symbols=([A-Z0-9,.-]+)")
    selected_re = re.compile(r"Decision Tree V2 mode=live apply=True candidates=\d+ selected_symbols=([A-Z0-9,.-]+)")
    rejected_re = re.compile(r"V2 rejected signal symbol=([A-Z0-9]+USDT)")
    cooldown_re = re.compile(r"V2 rejection cooldown active symbol=([A-Z0-9]+USDT)")

    interesting_lines = [
        line.strip()
        for line in raw_log.splitlines()
        if (
            "Scanning 10 top-volume pairs:" in line
            or "Candidate funnel " in line
            or "Decision Tree V2 mode=live apply=" in line
            or "V2 rejected signal" in line
            or "V2 rejection cooldown active" in line
            or "sideways entry paused by governor" in line
        )
    ]
    for line in raw_log.splitlines():
        match = scan_re.search(line)
        if match:
            for symbol in [part.strip() for part in match.group(1).split(",") if part.strip()]:
                _bump(symbol, "scanned")
        match = paused_re.search(line)
        if match:
            _bump(match.group(1), "sideways_paused")
        match = signal_re.search(line)
        if match:
            _bump(match.group(1), "signal_generated")
        match = candidate_re.search(line)
        if match:
            symbols = [part.strip() for part in match.group(1).split(",") if part.strip() and part.strip() != "-"]
            for symbol in symbols:
                _bump(symbol, "candidate_funnel")
        match = selected_re.search(line)
        if match:
            symbols = [part.strip() for part in match.group(1).split(",") if part.strip() and part.strip() != "-"]
            for symbol in symbols:
                _bump(symbol, "v2_selected")
        match = rejected_re.search(line)
        if match:
            _bump(match.group(1), "v2_rejected")
        match = cooldown_re.search(line)
        if match:
            _bump(match.group(1), "cooldown_active")
    return {
        "available": True,
        "window": since,
        "metrics": {
            "signal_generated": raw_log.count("Signal generated:"),
            "candidate_funnel": raw_log.count("Candidate funnel "),
            "candidate_funnel_after_cooldown": raw_log.count("Candidate funnel after V2 cooldown "),
            "decision_tree_live_apply": raw_log.count("Decision Tree V2 mode=live apply="),
            "v2_rejected": raw_log.count("V2 rejected signal"),
            "v2_rejection_cooldown_active": raw_log.count("V2 rejection cooldown active"),
            "scan_zero": raw_log.count("0 signals found, 0 validated"),
            "sideways_paused": raw_log.count("sideways entry paused by governor"),
        },
        "symbol_stats": {
            symbol: dict(counter)
            for symbol, counter in sorted(
                symbol_stats.items(),
                key=lambda item: (
                    -int(item[1].get("v2_selected", 0)),
                    -int(item[1].get("candidate_funnel", 0)),
                    -int(item[1].get("signal_generated", 0)),
                    item[0],
                ),
            )
        },
        "recent_lines": interesting_lines[-tail:],
    }


def _top_pairs_snapshot(limit: int = 10) -> dict[str, Any]:
    try:
        return {
            "pairs": list(get_ranked_top_volume_pairs(limit)),
            "health": get_selector_health(),
        }
    except Exception as exc:
        logger.warning("[DecisionTreeV2Dashboard] top pairs snapshot failed: %s", exc)
        return {"pairs": [], "health": {"error": str(exc)}}


def _candidate_summary(rows: list[dict[str, Any]], tail: int) -> dict[str, Any]:
    approved = [row for row in rows if row.get("approved") is True]
    rejected = [row for row in rows if row.get("approved") is False]
    return {
        "live_candidate_count": len(rows),
        "approved_count": len(approved),
        "rejected_count": len(rejected),
        "symbol_histogram": dict(Counter((row.get("symbol") or "unknown") for row in rows).most_common(8)),
        "reject_histogram": dict(Counter((row.get("reject_reason") or "approved") for row in rows).most_common(8)),
        "tier_histogram": dict(Counter((row.get("user_equity_tier") or "unknown") for row in rows).most_common(8)),
        "quality_histogram": dict(Counter((row.get("quality_bucket") or "unknown") for row in rows).most_common(8)),
        "tradeability_distribution": _score_distribution(rows, "tradeability_score"),
        "final_score_distribution": _score_distribution(rows, "final_score"),
        "recent_samples": [
            {
                "created_at": row.get("created_at"),
                "symbol": row.get("symbol"),
                "tier": row.get("user_equity_tier"),
                "approved": row.get("approved"),
                "reject_reason": row.get("reject_reason"),
                "final_score": row.get("final_score"),
            }
            for row in rows[-tail:]
        ],
    }


def get_live_dashboard_snapshot(minutes: int = 30, tail: int = 6) -> dict[str, Any]:
    rows = _load_live_candidates(minutes)
    return {
        "generated_at": _utc_now().isoformat(),
        "window_minutes": int(minutes),
        "top_pairs": _top_pairs_snapshot(limit=10),
        "db": _candidate_summary(rows, tail),
        "journal": _run_journal_query(minutes, tail),
    }


def write_live_dashboard_snapshot(snapshot: dict[str, Any]) -> str:
    out_dir = _ROOT / "logs" / "decision_tree_v2"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"telegram_live_dashboard_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return str(out_path)


def _format_histogram(hist: dict[str, int], empty: str = "-") -> str:
    if not hist:
        return empty
    return ", ".join(f"{html.escape(str(k))}:{int(v)}" for k, v in hist.items())


def _fmt_recent_samples(samples: list[dict[str, Any]]) -> str:
    if not samples:
        return "-"
    lines: list[str] = []
    for sample in samples[-4:]:
        symbol = html.escape(str(sample.get("symbol") or "-"))
        tier = html.escape(str(sample.get("tier") or "-"))
        status = "ok" if sample.get("approved") else "rej"
        reason = html.escape(str(sample.get("reject_reason") or "-"))
        score = _safe_float(sample.get("final_score"), 0.0)
        lines.append(f"{symbol} {status} {tier} {reason} {score:.3f}")
    return "\n".join(lines)


def _fmt_recent_lines(lines: list[str]) -> str:
    if not lines:
        return "-"
    trimmed = [html.escape(line[-120:]) for line in lines[-3:]]
    return "\n".join(trimmed)


def _fmt_symbol_breakdown(symbol_stats: dict[str, dict[str, int]], limit: int = 8) -> str:
    if not symbol_stats:
        return "-"
    lines: list[str] = []
    for symbol, stats in list(symbol_stats.items())[:limit]:
        lines.append(
            f"{html.escape(symbol)} sc={int(stats.get('scanned', 0))} "
            f"sig={int(stats.get('signal_generated', 0))} "
            f"cand={int(stats.get('candidate_funnel', 0))} "
            f"sel={int(stats.get('v2_selected', 0))} "
            f"rej={int(stats.get('v2_rejected', 0))} "
            f"cd={int(stats.get('cooldown_active', 0))} "
            f"pause={int(stats.get('sideways_paused', 0))}"
        )
    return "\n".join(lines)


def format_live_dashboard_message(snapshot: dict[str, Any]) -> str:
    top_pairs = snapshot.get("top_pairs") or {}
    top_pairs_list = top_pairs.get("pairs") or []
    health = top_pairs.get("health") or {}
    db = snapshot.get("db") or {}
    journal = snapshot.get("journal") or {}
    metrics = journal.get("metrics") or {}

    lines = [
        "<b>Decision Tree V2 Live Dashboard</b>",
        f"Window: <code>{int(snapshot.get('window_minutes') or 30)}m</code>",
        f"Generated: <code>{html.escape(str(snapshot.get('generated_at') or '-'))}</code>",
        "",
        "<b>Universe</b>",
        f"Top-volume: <code>{html.escape(', '.join(top_pairs_list[:10]) or '-')}</code>",
        f"Selector: <code>source={html.escape(str(health.get('source') or '-'))} count={int(health.get('pair_count') or len(top_pairs_list))}</code>",
        "",
        "<b>Candidates</b>",
        f"Live rows: <code>{int(db.get('live_candidate_count') or 0)}</code> | Approved: <code>{int(db.get('approved_count') or 0)}</code> | Rejected: <code>{int(db.get('rejected_count') or 0)}</code>",
        f"Top symbols: <code>{_format_histogram(db.get('symbol_histogram') or {})}</code>",
        f"Rejects: <code>{_format_histogram(db.get('reject_histogram') or {})}</code>",
        f"Tiers: <code>{_format_histogram(db.get('tier_histogram') or {})}</code>",
        "",
        "<b>Funnel</b>",
        f"Signals: <code>{int(metrics.get('signal_generated') or 0)}</code> | V2 apply: <code>{int(metrics.get('decision_tree_live_apply') or 0)}</code> | V2 rejected: <code>{int(metrics.get('v2_rejected') or 0)}</code>",
        f"Cooldown active: <code>{int(metrics.get('v2_rejection_cooldown_active') or 0)}</code> | Sideways paused: <code>{int(metrics.get('sideways_paused') or 0)}</code>",
        "",
        "<b>Recent Samples</b>",
        f"<code>{_fmt_recent_samples(db.get('recent_samples') or [])}</code>",
    ]

    if journal.get("available"):
        lines.extend([
            "",
            "<b>Recent Runtime</b>",
            f"<code>{_fmt_recent_lines(journal.get('recent_lines') or [])}</code>",
        ])
    else:
        lines.extend([
            "",
            "<b>Recent Runtime</b>",
            f"<code>{html.escape(str(journal.get('reason') or 'unavailable'))}</code>",
        ])

    message = "\n".join(lines)
    if len(message) <= 3900:
        return message
    return message[:3890] + "\n…"


def format_live_symbol_breakdown_message(snapshot: dict[str, Any]) -> str:
    journal = snapshot.get("journal") or {}
    metrics = journal.get("metrics") or {}
    symbol_stats = journal.get("symbol_stats") or {}
    lines = [
        "<b>Decision Tree V2 Symbol Breakdown</b>",
        f"Window: <code>{int(snapshot.get('window_minutes') or 30)}m</code>",
        f"Generated: <code>{html.escape(str(snapshot.get('generated_at') or '-'))}</code>",
        "",
        "<b>Legend</b>",
        "<code>sc=scanned sig=signals cand=funnel sel=v2-selected rej=v2-rejected cd=cooldown pause=sideways</code>",
        "",
        "<b>Per Symbol</b>",
        f"<code>{_fmt_symbol_breakdown(symbol_stats, limit=10)}</code>",
        "",
        "<b>Totals</b>",
        f"<code>signals={int(metrics.get('signal_generated') or 0)} apply={int(metrics.get('decision_tree_live_apply') or 0)} rejected={int(metrics.get('v2_rejected') or 0)} cooldown={int(metrics.get('v2_rejection_cooldown_active') or 0)} paused={int(metrics.get('sideways_paused') or 0)}</code>",
    ]
    message = "\n".join(lines)
    if len(message) <= 3900:
        return message
    return message[:3890] + "\n…"
