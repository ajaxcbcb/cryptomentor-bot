"""
Bulk-enable AutoTrade and set global risk percentage.

Behavior:
1) Finds verified users from `user_verifications` (supports legacy approved aliases).
2) Sets `risk_per_trade` for all approved users in `autotrade_sessions`.
3) Enables autotrade (`status=active`, `engine_active=true`) for approved users
   that already have API keys in `user_api_keys`.

Usage:
    python enable_autotrade_all.py
    python enable_autotrade_all.py --risk 1.0 --dry-run
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from typing import Dict, Set

from dotenv import load_dotenv
from supabase import create_client


APPROVED_ALIASES = {"approved", "uid_verified", "active", "verified"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_status(raw: str) -> str:
    status = str(raw or "").strip().lower()
    if status in APPROVED_ALIASES:
        return "approved"
    return status or "none"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enable autotrade for all approved users.")
    parser.add_argument("--risk", type=float, default=1.0, help="Risk percentage per trade. Default: 1.0")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing to DB.")
    parser.add_argument(
        "--activate-without-keys",
        action="store_true",
        help="Also activate users even if API keys are missing.",
    )
    return parser.parse_args()


def _require_env() -> tuple[str, str]:
    load_dotenv()
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL and/or SUPABASE_SERVICE_KEY. "
            "Create website-backend/.env or export env vars first."
        )
    return url, key


def main() -> None:
    args = _parse_args()
    if args.risk <= 0 or args.risk > 100:
        raise RuntimeError(f"Invalid risk: {args.risk}. Must be > 0 and <= 100.")

    url, key = _require_env()
    s = create_client(url, key)

    ver_rows = (
        s.table("user_verifications")
        .select("telegram_id,status")
        .execute()
        .data
        or []
    )
    approved_ids: Set[int] = set()
    status_count: Dict[str, int] = {}
    for row in ver_rows:
        uid = row.get("telegram_id")
        status = _normalize_status(row.get("status"))
        status_count[status] = status_count.get(status, 0) + 1
        if status == "approved" and uid is not None:
            approved_ids.add(int(uid))

    key_rows = (
        s.table("user_api_keys")
        .select("telegram_id")
        .execute()
        .data
        or []
    )
    ids_with_keys = {int(r["telegram_id"]) for r in key_rows if r.get("telegram_id") is not None}

    now = _iso_now()
    to_activate = approved_ids if args.activate_without_keys else (approved_ids & ids_with_keys)
    missing_keys = sorted(list(approved_ids - ids_with_keys))

    print("=== Bulk AutoTrade Rollout ===")
    print(f"Verified rows: {len(ver_rows)}")
    print(f"Status distribution: {status_count}")
    print(f"Approved users: {len(approved_ids)}")
    print(f"Approved users with API keys: {len(approved_ids & ids_with_keys)}")
    print(f"Target risk_per_trade: {args.risk}%")
    print(f"Will activate engines: {len(to_activate)} users")
    if missing_keys:
        print(f"Approved but missing API keys: {len(missing_keys)}")

    if args.dry_run:
        print("\nDry run only. No DB changes written.")
        return

    # 1) Set risk for all approved users (create/update session row).
    risk_updates = 0
    for uid in sorted(approved_ids):
        payload = {
            "telegram_id": uid,
            "risk_per_trade": float(args.risk),
            "updated_at": now,
        }
        s.table("autotrade_sessions").upsert(payload, on_conflict="telegram_id").execute()
        risk_updates += 1

    # 2) Activate users that can actually trade (have API keys by default).
    activations = 0
    for uid in sorted(to_activate):
        payload = {
            "telegram_id": uid,
            "status": "active",
            "engine_active": True,
            "risk_per_trade": float(args.risk),
            "updated_at": now,
        }
        s.table("autotrade_sessions").upsert(payload, on_conflict="telegram_id").execute()
        activations += 1

    print("\n=== Completed ===")
    print(f"Risk updated for approved users: {risk_updates}")
    print(f"AutoTrade activated: {activations}")
    if missing_keys and not args.activate_without_keys:
        print("Note: users without API keys were left non-activated for safety.")


if __name__ == "__main__":
    main()

