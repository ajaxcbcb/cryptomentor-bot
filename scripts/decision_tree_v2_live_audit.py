"""
Read-only Decision Tree V2 live audit helper.

Usage examples:
  python scripts/decision_tree_v2_live_audit.py
  python scripts/decision_tree_v2_live_audit.py --minutes 30 --tail 20 --write
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
_BISMILLAH = _ROOT / "Bismillah"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_BISMILLAH) not in sys.path:
    sys.path.insert(0, str(_BISMILLAH))

load_dotenv(_BISMILLAH / ".env")
load_dotenv(_ROOT / ".env", override=True)
load_dotenv(_ROOT / "website-backend" / ".env", override=False)

from app.supabase_repo import _client


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect live Decision Tree V2 runtime and database telemetry.")
    parser.add_argument("--minutes", type=int, default=30, help="Lookback window in minutes. Default: 30")
    parser.add_argument("--tail", type=int, default=20, help="How many recent DB samples and log lines to include. Default: 20")
    parser.add_argument("--write", action="store_true", help="Write the JSON audit to logs/decision_tree_v2/")
    return parser.parse_args()


def _run_journal_query(minutes: int, tail: int) -> Dict[str, Any]:
    if shutil.which("journalctl") is None:
        return {"available": False, "reason": "journalctl_not_found"}

    since = f"{int(minutes)} minutes ago"
    cmd = ["journalctl", "-u", "cryptomentor", "--since", since, "--no-pager", "--output=cat"]
    try:
        raw_log = subprocess.check_output(cmd, text=True, errors="replace")
    except Exception as exc:
        return {"available": False, "reason": f"journalctl_failed: {exc}"}

    interesting_lines = [
        line
        for line in raw_log.splitlines()
        if (
            "Candidate funnel" in line
            or "Decision Tree V2 mode=live apply=" in line
            or "V2 rejected signal" in line
            or "V2 rejection cooldown active" in line
        )
    ]
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
        "recent_lines": interesting_lines[-tail:],
    }


def _load_live_candidates(minutes: int) -> List[Dict[str, Any]]:
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=int(minutes))).isoformat()
    client = _client()
    rows: List[Dict[str, Any]] = []
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
    live_rows = []
    for row in rows:
        metadata = row.get("metadata") or {}
        if isinstance(metadata, dict) and str(metadata.get("execution_mode") or "").lower() == "live":
            live_rows.append(row)
    return live_rows


def _score_distribution(rows: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    buckets = Counter()
    for row in rows:
        try:
            value = float(row.get(field) or 0.0)
        except Exception:
            value = 0.0
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


def _candidate_summary(rows: List[Dict[str, Any]], tail: int) -> Dict[str, Any]:
    approved = [row for row in rows if row.get("approved") is True]
    rejected = [row for row in rows if row.get("approved") is False]
    return {
        "live_candidate_count": len(rows),
        "approved_count": len(approved),
        "rejected_count": len(rejected),
        "symbol_histogram": dict(Counter((row.get("symbol") or "unknown") for row in rows).most_common(15)),
        "reject_histogram": dict(Counter((row.get("reject_reason") or "approved") for row in rows).most_common(15)),
        "tier_histogram": dict(Counter((row.get("user_equity_tier") or "unknown") for row in rows).most_common(15)),
        "participation_histogram": dict(Counter((row.get("participation_bucket") or "unknown") for row in rows).most_common(15)),
        "quality_histogram": dict(Counter((row.get("quality_bucket") or "unknown") for row in rows).most_common(15)),
        "tradeability_distribution": _score_distribution(rows, "tradeability_score"),
        "final_score_distribution": _score_distribution(rows, "final_score"),
        "recent_samples": [
            {
                "created_at": row.get("created_at"),
                "symbol": row.get("symbol"),
                "tier": row.get("user_equity_tier"),
                "approved": row.get("approved"),
                "reject_reason": row.get("reject_reason"),
                "tradeability_score": row.get("tradeability_score"),
                "final_score": row.get("final_score"),
                "display_reason": row.get("display_reason"),
            }
            for row in rows[-tail:]
        ],
    }


def run_audit(minutes: int, tail: int) -> Dict[str, Any]:
    rows = _load_live_candidates(minutes)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_minutes": int(minutes),
        "db": _candidate_summary(rows, tail),
        "journal": _run_journal_query(minutes, tail),
    }
    return payload


def main() -> int:
    args = _parse_args()
    payload = run_audit(minutes=args.minutes, tail=args.tail)
    if args.write:
        out_dir = _ROOT / "logs" / "decision_tree_v2"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"live_audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["output_path"] = str(out_path)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
