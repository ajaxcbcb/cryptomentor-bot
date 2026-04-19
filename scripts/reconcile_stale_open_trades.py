#!/usr/bin/env python3
"""
Operational stale-open reconcile backfill.

Usage:
  python scripts/reconcile_stale_open_trades.py --mode dry-run
  python scripts/reconcile_stale_open_trades.py --mode apply --trade-type scalping
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
BISMILLAH_DIR = ROOT / "Bismillah"
LOG_DIR = ROOT / "logs"
EXCLUDED_UIDS = {999999999, 999999998, 999999997, 500000025, 500000026}
ACTIVE_ALIASES = {"active", "uid_verified", "approved", "verified"}
PENDING_STATUSES = {"pending", "pending_verification", "uid_rejected", "awaiting_approval"}

if str(BISMILLAH_DIR) not in sys.path:
    sys.path.insert(0, str(BISMILLAH_DIR))


def _load_environment() -> None:
    for env_path in (
        BISMILLAH_DIR / ".env",
        ROOT / ".env",
        ROOT / "website-backend" / ".env",
    ):
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)

    if os.name != "nt":
        try:
            res = subprocess.run(
                ["systemctl", "show-environment"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                for line in (res.stdout or "").splitlines():
                    if "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val)
        except Exception:
            pass


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_status(raw: Any) -> str:
    return str(raw or "").strip().lower()


def _scope_match(status: str, session_scope: str) -> bool:
    st = _normalize_status(status)
    if session_scope == "active":
        return st in ACTIVE_ALIASES
    # nonpending
    return st not in PENDING_STATUSES


def _resolve_user_scope(session_scope: str, limit_users: Optional[int]) -> List[Dict[str, Any]]:
    from app.supabase_repo import _client

    s = _client()
    rows = (
        s.table("autotrade_sessions")
        .select("telegram_id,status,engine_active,trading_mode,updated_at")
        .execute()
        .data
        or []
    )
    scoped: List[Dict[str, Any]] = []
    for r in rows:
        uid = r.get("telegram_id")
        try:
            uid_int = int(uid)
        except Exception:
            continue
        if uid_int <= 0 or uid_int in EXCLUDED_UIDS:
            continue
        if not _scope_match(r.get("status"), session_scope):
            continue
        scoped.append(
            {
                "telegram_id": uid_int,
                "session_status": _normalize_status(r.get("status")),
                "engine_active": bool(r.get("engine_active")),
                "trading_mode": str(r.get("trading_mode") or ""),
                "updated_at": r.get("updated_at"),
            }
        )
    scoped.sort(key=lambda x: x["telegram_id"])
    if limit_users is not None and limit_users > 0:
        scoped = scoped[: int(limit_users)]
    return scoped


def _get_exchange_client(uid: int):
    from app.supabase_repo import get_user_api_key
    from app.exchange_registry import get_client

    keys = get_user_api_key(uid)
    if not keys:
        return None, "missing_api_key"

    exchange_id = str(keys.get("exchange") or "bitunix").strip().lower() or "bitunix"
    api_key = str(keys.get("api_key") or "").strip()
    api_secret = str(keys.get("api_secret") or "").strip()
    if not api_key or not api_secret:
        return None, "missing_api_material"
    try:
        return get_client(exchange_id, api_key, api_secret), ""
    except Exception as e:
        return None, f"client_init_failed:{e}"


def _write_artifacts(payload: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, str]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = LOG_DIR / f"reconcile_stale_open_trades_{stamp}.json"
    csv_path = LOG_DIR / f"reconcile_stale_open_trades_{stamp}.csv"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    fieldnames = [
        "telegram_id",
        "session_status",
        "engine_active",
        "trading_mode",
        "exchange_fetch_ok",
        "exchange_error",
        "db_open_count",
        "exchange_open_count",
        "stale_count",
        "stale_symbols",
        "healed_count",
        "healed_trade_ids",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fieldnames})
    return {"json": str(json_path), "csv": str(csv_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile stale open DB trades against live exchange positions.")
    parser.add_argument("--mode", choices=["dry-run", "apply"], default="dry-run")
    parser.add_argument("--trade-type", choices=["all", "scalping", "swing"], default="all")
    parser.add_argument("--session-scope", choices=["active", "nonpending"], default="active")
    parser.add_argument("--rate-delay", type=float, default=0.2)
    parser.add_argument("--limit-users", type=int, default=0)
    args = parser.parse_args()

    _load_environment()
    trade_type: Optional[str] = None if args.trade_type == "all" else str(args.trade_type)
    limit_users = int(args.limit_users) if int(args.limit_users or 0) > 0 else None

    from app.trade_history import inspect_open_trade_drift, apply_open_trade_reconcile

    scoped_users = _resolve_user_scope(session_scope=str(args.session_scope), limit_users=limit_users)
    rows: List[Dict[str, Any]] = []

    checked_with_keys = 0
    candidate_users = 0
    stale_open_total = 0
    healed_total = 0

    for u in scoped_users:
        uid = int(u["telegram_id"])
        client, client_err = _get_exchange_client(uid)
        if client is None:
            rows.append(
                {
                    **u,
                    "exchange_fetch_ok": False,
                    "exchange_error": client_err,
                    "db_open_count": 0,
                    "exchange_open_count": 0,
                    "stale_count": 0,
                    "stale_symbols": [],
                    "healed_count": 0,
                    "healed_trade_ids": [],
                }
            )
            continue

        checked_with_keys += 1
        drift = inspect_open_trade_drift(uid, client, trade_type=trade_type)
        stale_count = len(drift.get("stale_trade_ids") or [])
        stale_open_total += stale_count
        if stale_count > 0:
            candidate_users += 1

        healed_count = 0
        healed_trade_ids: List[int] = []
        if args.mode == "apply" and stale_count > 0:
            applied = apply_open_trade_reconcile(uid, client, trade_type=trade_type, drift=drift)
            healed_count = int(applied.get("healed_count", 0) or 0)
            healed_trade_ids = [int(x) for x in (applied.get("healed_trade_ids") or [])]
            healed_total += healed_count
            if float(args.rate_delay) > 0:
                time.sleep(float(args.rate_delay))

        rows.append(
            {
                **u,
                "exchange_fetch_ok": bool(drift.get("exchange_fetch_ok", False)),
                "exchange_error": str(drift.get("exchange_error") or ""),
                "db_open_count": int(drift.get("db_open_count", 0) or 0),
                "exchange_open_count": int(drift.get("exchange_open_count", 0) or 0),
                "stale_count": stale_count,
                "stale_symbols": list(drift.get("stale_symbols") or []),
                "healed_count": healed_count,
                "healed_trade_ids": healed_trade_ids,
            }
        )

    summary = {
        "generated_at_utc": _now_utc_iso(),
        "mode": str(args.mode),
        "trade_type": str(args.trade_type),
        "session_scope": str(args.session_scope),
        "rate_delay": float(args.rate_delay),
        "limit_users": limit_users,
        "total_users_scoped": len(scoped_users),
        "checked_with_keys": checked_with_keys,
        "candidate_users": candidate_users,
        "stale_open_total": stale_open_total,
        "healed_total": healed_total,
    }
    payload = {"summary": summary, "rows": rows}
    artifacts = _write_artifacts(payload=payload, rows=rows)
    print(json.dumps({**summary, "artifacts": artifacts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
