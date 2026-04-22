#!/usr/bin/env python3
"""
Read-only gatekeeper fleet audit.

Reports cross-table verification drift between:
- user_verifications (canonical)
- autotrade_sessions (legacy/session compatibility)
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from app.db.supabase import _client
from app.services.verification_status import (
    VER_APPROVED,
    load_verification_snapshot,
    normalize_session_verification_status,
    normalize_verification_status,
)


def _as_tid(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_report(sample_limit: int = 20) -> dict[str, Any]:
    s = _client()
    uv_rows = (
        s.table("user_verifications")
        .select("telegram_id,status,bitunix_uid")
        .execute()
        .data
        or []
    )
    sess_rows = (
        s.table("autotrade_sessions")
        .select("telegram_id,status,bitunix_uid")
        .execute()
        .data
        or []
    )

    uv_by_tid = {}
    for row in uv_rows:
        tid = _as_tid(row.get("telegram_id"))
        if tid is not None:
            uv_by_tid[tid] = row

    sess_by_tid = {}
    for row in sess_rows:
        tid = _as_tid(row.get("telegram_id"))
        if tid is not None:
            sess_by_tid[tid] = row

    all_tids = sorted(set(uv_by_tid.keys()) | set(sess_by_tid.keys()))
    stats = {
        "total_tracked_users": len(all_tids),
        "uv_approved": 0,
        "session_approved_compat": 0,
        "resolver_approved": 0,
        "drift_disagreements": 0,
        "uid_mismatch_on_dual_present": 0,
    }
    drift_examples = []
    mismatch_examples = []

    for tid in all_tids:
        uv = uv_by_tid.get(tid) or {}
        sess = sess_by_tid.get(tid) or {}

        uv_status = normalize_verification_status(uv.get("status"))
        sess_status = normalize_session_verification_status(sess.get("status"), sess.get("bitunix_uid"))
        resolver = load_verification_snapshot(tid)
        resolver_status = str(resolver.get("status") or "none")

        uv_uid = str(uv.get("bitunix_uid") or "").strip()
        sess_uid = str(sess.get("bitunix_uid") or "").strip()
        uid_mismatch = bool(uv_uid and sess_uid and uv_uid != sess_uid)

        if uv_status == VER_APPROVED:
            stats["uv_approved"] += 1
        if sess_status == VER_APPROVED:
            stats["session_approved_compat"] += 1
        if resolver_status == VER_APPROVED:
            stats["resolver_approved"] += 1
        if uid_mismatch:
            stats["uid_mismatch_on_dual_present"] += 1
            if len(mismatch_examples) < sample_limit:
                mismatch_examples.append(
                    {
                        "telegram_id": tid,
                        "uv_uid_suffix": uv_uid[-4:],
                        "session_uid_suffix": sess_uid[-4:],
                    }
                )

        if uv_status != "none" and sess_status != "none" and uv_status != sess_status:
            stats["drift_disagreements"] += 1
            if len(drift_examples) < sample_limit:
                drift_examples.append(
                    {
                        "telegram_id": tid,
                        "uv_status": uv_status,
                        "session_status": sess_status,
                        "resolver_status": resolver_status,
                        "decision_reason": resolver.get("decision_reason"),
                        "uid_compatible": not uid_mismatch,
                    }
                )

    return {
        "stats": stats,
        "drift_examples": drift_examples,
        "uid_mismatch_examples": mismatch_examples,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only verification fleet audit")
    parser.add_argument("--sample-limit", type=int, default=20, help="Max example rows per section")
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit non-zero if drift_disagreements > 0 or uid mismatch > 0",
    )
    args = parser.parse_args()

    report = build_report(sample_limit=max(1, int(args.sample_limit)))
    print(json.dumps(report, indent=2, sort_keys=True))

    drift = int(report["stats"].get("drift_disagreements") or 0)
    uid_mismatch = int(report["stats"].get("uid_mismatch_on_dual_present") or 0)
    if args.fail_on_drift and (drift > 0 or uid_mismatch > 0):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
