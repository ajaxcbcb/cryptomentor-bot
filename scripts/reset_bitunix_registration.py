#!/usr/bin/env python3
"""
One-time Bitunix registration reset tool.

Resets a user's UID registration state to pending verification and optionally
notifies user/admins via Telegram.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
BISMILLAH_DIR = ROOT / "Bismillah"
if str(BISMILLAH_DIR) not in sys.path:
    sys.path.insert(0, str(BISMILLAH_DIR))

LOG_DIR = ROOT / "logs"
ALLOWED_SUBMITTED_VIA = {"web", "telegram"}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_environment() -> None:
    # Keep order aligned with runtime scripts.
    for env_path in (
        BISMILLAH_DIR / ".env",
        ROOT / ".env",
        ROOT / "website-backend" / ".env",
    ):
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)

    # Best effort: include systemd manager env on Linux VPS.
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


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(val)
    except Exception:
        return int(default)


def _load_admin_ids() -> List[int]:
    admin_ids: List[int] = []
    seen = set()

    def _add(raw: Any) -> None:
        uid = _safe_int(str(raw).strip(), 0)
        if uid <= 0 or uid in seen:
            return
        seen.add(uid)
        admin_ids.append(uid)

    for token in (os.getenv("ADMIN_IDS", "") or "").split(","):
        if token.strip():
            _add(token)
    for key in ("ADMIN1", "ADMIN2", "ADMIN3", "ADMIN_USER_ID", "ADMIN2_USER_ID"):
        _add(os.getenv(key, ""))
    return admin_ids


def _parse_bool(raw: str) -> bool:
    value = str(raw or "").strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _send_telegram_message(
    *,
    token: str,
    chat_id: int,
    text: str,
    parse_mode: str = "HTML",
    reply_markup: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": "true",
    }
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)

    data = urlparse.urlencode(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, method="POST")
    try:
        with urlrequest.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        return False, f"http_error:{e.code}:{detail[:180]}"
    except Exception as e:
        return False, f"transport_error:{e}"

    try:
        body = json.loads(raw)
    except Exception:
        return False, f"invalid_json:{raw[:180]}"

    if not bool(body.get("ok")):
        return False, str(body.get("description") or "telegram_send_failed")
    return True, ""


@dataclass
class SendMetrics:
    user_sent: int = 0
    user_failed: int = 0
    admin_sent: int = 0
    admin_failed: int = 0


def _write_log(payload: Dict[str, Any]) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = LOG_DIR / f"bitunix_registration_reset_{ts}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _validate_new_uid(uid: str) -> str:
    uid = str(uid or "").strip()
    if not uid.isdigit() or len(uid) < 5:
        raise ValueError("new-bitunix-uid must be numeric and at least 5 digits.")
    return uid


def _project_after_rows(
    *,
    telegram_id: int,
    new_uid: str,
    uv_before: Optional[Dict[str, Any]],
    session_before: Optional[Dict[str, Any]],
    now_iso: str,
) -> Dict[str, Any]:
    uv_after = dict(uv_before or {})
    submitted_via = str((uv_before or {}).get("submitted_via") or "").strip().lower()
    if submitted_via not in ALLOWED_SUBMITTED_VIA:
        submitted_via = "web"
    uv_after.update(
        {
            "telegram_id": telegram_id,
            "bitunix_uid": new_uid,
            "status": "pending",
            "submitted_via": submitted_via,
            "submitted_at": now_iso,
            "reviewed_at": None,
            "reviewed_by_admin_id": None,
            "rejection_reason": None,
            "updated_at": now_iso,
        }
    )

    session_after = dict(session_before or {})
    session_after.update(
        {
            "telegram_id": telegram_id,
            "bitunix_uid": new_uid,
            "status": "pending_verification",
            "engine_active": False,
            "updated_at": now_iso,
        }
    )
    return {"user_verifications": uv_after, "autotrade_sessions": session_after}


def run(
    *,
    telegram_id: int,
    new_uid: str,
    mode: str,
    notify_user: bool,
    notify_admin: bool,
    actor_admin_id: Optional[int],
) -> int:
    _load_environment()

    from app.supabase_repo import _client
    from app.lib.auth import generate_dashboard_url

    now_iso = now_utc_iso()
    s = _client()

    users_res = (
        s.table("users")
        .select("telegram_id,username,first_name")
        .eq("telegram_id", int(telegram_id))
        .limit(1)
        .execute()
    )
    user_row = (users_res.data or [None])[0]
    if not user_row:
        raise RuntimeError(f"User {telegram_id} not found in users table.")

    uv_res = (
        s.table("user_verifications")
        .select("*")
        .eq("telegram_id", int(telegram_id))
        .limit(1)
        .execute()
    )
    uv_before = (uv_res.data or [None])[0]

    session_res = (
        s.table("autotrade_sessions")
        .select("*")
        .eq("telegram_id", int(telegram_id))
        .limit(1)
        .execute()
    )
    session_before = (session_res.data or [None])[0]

    keys_res = (
        s.table("user_api_keys")
        .select("telegram_id,exchange,api_key,key_hint,created_at,updated_at")
        .eq("telegram_id", int(telegram_id))
        .execute()
    )
    keys_before = keys_res.data or []
    bitunix_keys_before = [
        row for row in keys_before if str(row.get("exchange") or "").strip().lower() in {"", "bitunix"}
    ]

    open_res = (
        s.table("autotrade_trades")
        .select("id,symbol,status,opened_at,trade_type", count="exact")
        .eq("telegram_id", int(telegram_id))
        .eq("status", "open")
        .execute()
    )
    open_rows = open_res.data or []
    open_count = int(open_res.count or len(open_rows))
    if open_count > 0:
        raise RuntimeError(
            f"Abort: user {telegram_id} has {open_count} open trade(s). Reset is blocked."
        )

    effective_actor = (
        int(actor_admin_id)
        if actor_admin_id is not None
        else _safe_int((uv_before or {}).get("reviewed_by_admin_id"), 0)
    )
    submitted_via_reset = str((uv_before or {}).get("submitted_via") or "").strip().lower()
    if submitted_via_reset not in ALLOWED_SUBMITTED_VIA:
        submitted_via_reset = "web"

    projected_after = _project_after_rows(
        telegram_id=telegram_id,
        new_uid=new_uid,
        uv_before=uv_before,
        session_before=session_before,
        now_iso=now_iso,
    )

    notification_results: Dict[str, Any] = {
        "notify_user_enabled": notify_user,
        "notify_admin_enabled": notify_admin,
        "results": [],
    }
    send_metrics = SendMetrics()

    if mode == "apply":
        if uv_before:
            (
                s.table("user_verifications")
                .update(
                    {
                        "bitunix_uid": new_uid,
                        "status": "pending",
                        "submitted_via": submitted_via_reset,
                        "submitted_at": now_iso,
                        "reviewed_at": None,
                        "reviewed_by_admin_id": None,
                        "rejection_reason": None,
                        "updated_at": now_iso,
                    }
                )
                .eq("telegram_id", int(telegram_id))
                .execute()
            )
        else:
            (
                s.table("user_verifications")
                .upsert(
                    {
                        "telegram_id": int(telegram_id),
                        "bitunix_uid": new_uid,
                        "status": "pending",
                        "submitted_via": submitted_via_reset,
                        "submitted_at": now_iso,
                        "reviewed_at": None,
                        "reviewed_by_admin_id": None,
                        "rejection_reason": None,
                        "updated_at": now_iso,
                    },
                    on_conflict="telegram_id",
                )
                .execute()
            )

        if session_before:
            (
                s.table("autotrade_sessions")
                .update(
                    {
                        "bitunix_uid": new_uid,
                        "status": "pending_verification",
                        "engine_active": False,
                        "updated_at": now_iso,
                    }
                )
                .eq("telegram_id", int(telegram_id))
                .execute()
            )
        else:
            (
                s.table("autotrade_sessions")
                .upsert(
                    {
                        "telegram_id": int(telegram_id),
                        "bitunix_uid": new_uid,
                        "status": "pending_verification",
                        "engine_active": False,
                        "updated_at": now_iso,
                    },
                    on_conflict="telegram_id",
                )
                .execute()
            )

        if bitunix_keys_before:
            (
                s.table("user_api_keys")
                .delete()
                .eq("telegram_id", int(telegram_id))
                .in_("exchange", ["bitunix", ""])
                .execute()
            )

        uv_after = (
            s.table("user_verifications")
            .select("*")
            .eq("telegram_id", int(telegram_id))
            .limit(1)
            .execute()
            .data
            or [None]
        )[0]
        session_after = (
            s.table("autotrade_sessions")
            .select("*")
            .eq("telegram_id", int(telegram_id))
            .limit(1)
            .execute()
            .data
            or [None]
        )[0]
        keys_after = (
            s.table("user_api_keys")
            .select("telegram_id,exchange,api_key,key_hint,created_at,updated_at")
            .eq("telegram_id", int(telegram_id))
            .execute()
            .data
            or []
        )
    else:
        uv_after = projected_after["user_verifications"]
        session_after = projected_after["autotrade_sessions"]
        keys_after = keys_before

    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    admin_ids = _load_admin_ids()

    old_uid = str((uv_before or {}).get("bitunix_uid") or (session_before or {}).get("bitunix_uid") or "-")
    username = str(user_row.get("username") or "")
    first_name = str(user_row.get("first_name") or "User")
    dash_url = generate_dashboard_url(int(telegram_id), username, first_name)

    if mode == "apply" and token:
        if notify_user:
            user_text = (
                "<b>Bitunix Registration Reset Completed</b>\n\n"
                f"Old UID: <code>{old_uid}</code>\n"
                f"New UID: <code>{new_uid}</code>\n"
                "Status: <b>PENDING VERIFICATION</b>\n\n"
                "Your UID was reset and has been submitted for re-verification.\n"
                "Please wait for approval before trading."
            )
            ok, err = _send_telegram_message(
                token=token,
                chat_id=int(telegram_id),
                text=user_text,
                reply_markup={
                    "inline_keyboard": [[{"text": "Open Dashboard", "url": dash_url}]]
                },
            )
            if ok:
                send_metrics.user_sent += 1
            else:
                send_metrics.user_failed += 1
            notification_results["results"].append(
                {"target": "user", "telegram_id": int(telegram_id), "ok": ok, "error": err}
            )

        if notify_admin and admin_ids:
            admin_text = (
                "<b>Bitunix Registration Reset (One-Time)</b>\n\n"
                f"Telegram ID: <code>{telegram_id}</code>\n"
                f"Old UID: <code>{old_uid}</code>\n"
                f"New UID: <code>{new_uid}</code>\n"
                f"Actor Admin ID: <code>{effective_actor}</code>\n"
                "Result: <b>APPLIED</b>\n"
                "Status set to pending re-verification."
            )
            for admin_id in admin_ids:
                ok, err = _send_telegram_message(
                    token=token,
                    chat_id=int(admin_id),
                    text=admin_text,
                )
                if ok:
                    send_metrics.admin_sent += 1
                else:
                    send_metrics.admin_failed += 1
                notification_results["results"].append(
                    {"target": "admin", "telegram_id": int(admin_id), "ok": ok, "error": err}
                )
    else:
        notification_results["results"].append(
            {
                "target": "system",
                "ok": False,
                "error": "telegram_notifications_skipped (mode is dry-run or TELEGRAM_BOT_TOKEN missing)",
            }
        )

    payload = {
        "run_at_utc": now_iso,
        "mode": mode,
        "inputs": {
            "telegram_id": int(telegram_id),
            "new_bitunix_uid": new_uid,
            "notify_user": bool(notify_user),
            "notify_admin": bool(notify_admin),
            "actor_admin_id": int(effective_actor),
        },
        "preflight": {
            "open_trades_count": open_count,
            "open_trades_rows": open_rows,
        },
        "before": {
            "users": user_row,
            "user_verifications": uv_before,
            "autotrade_sessions": session_before,
            "user_api_keys_all": keys_before,
            "user_api_keys_bitunix_or_empty": bitunix_keys_before,
        },
        "after": {
            "user_verifications": uv_after,
            "autotrade_sessions": session_after,
            "user_api_keys_all": keys_after,
        },
        "notifications": notification_results,
        "metrics": {
            "USER_SENT": send_metrics.user_sent,
            "USER_FAILED": send_metrics.user_failed,
            "ADMIN_SENT": send_metrics.admin_sent,
            "ADMIN_FAILED": send_metrics.admin_failed,
        },
    }

    log_path = _write_log(payload)
    payload["log_path"] = str(log_path)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset one user's Bitunix registration to pending verification.")
    parser.add_argument("--telegram-id", type=int, required=True, help="Target Telegram ID.")
    parser.add_argument("--new-bitunix-uid", type=str, required=True, help="New Bitunix UID (numeric, >=5 digits).")
    parser.add_argument(
        "--mode",
        choices=["dry-run", "apply"],
        default="dry-run",
        help="dry-run: no DB writes, apply: persist changes.",
    )
    parser.add_argument(
        "--notify-user",
        type=_parse_bool,
        default=True,
        help="true/false. Default true.",
    )
    parser.add_argument(
        "--notify-admin",
        type=_parse_bool,
        default=True,
        help="true/false. Default true.",
    )
    parser.add_argument(
        "--actor-admin-id",
        type=int,
        default=None,
        help="Optional actor admin ID. Falls back to previous reviewer or 0.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        new_uid = _validate_new_uid(args.new_bitunix_uid)
        return run(
            telegram_id=int(args.telegram_id),
            new_uid=new_uid,
            mode=str(args.mode),
            notify_user=bool(args.notify_user),
            notify_admin=bool(args.notify_admin),
            actor_admin_id=args.actor_admin_id,
        )
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
