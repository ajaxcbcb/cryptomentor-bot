#!/usr/bin/env python3
"""
API-Issue Recovery Broadcast

Target: verified users missing/invalid Bitunix API key.

Modes:
- dry-run: resolve audience + reasons, no Telegram sends
- test-admin: send one preview to first configured admin
- full-send: send to full resolved target audience
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
BISMILLAH_DIR = ROOT / "Bismillah"
if str(BISMILLAH_DIR) not in sys.path:
    sys.path.insert(0, str(BISMILLAH_DIR))


APPROVED_ALIASES = {"approved", "uid_verified", "active", "verified"}
EXCLUDED_UIDS = {999999999, 999999998, 999999997, 500000025, 500000026}
BITUNIX_EXCHANGE_ALIASES = {"", "bitunix"}


MESSAGE_TEMPLATE = (
    "⚠️ <b>API Key Issue Requires Attention</b>\n\n"
    "Kami mendeteksi masalah pada API Bitunix Anda, sehingga engine AutoTrade belum bisa berjalan.\n"
    "We detected an issue with your Bitunix API, so your AutoTrade engine cannot run yet.\n\n"
    "<b>📘 Tutorial / How To Fix</b>\n"
    "1) Buka <b>Bitunix → API Management</b>.\n"
    "   Open <b>Bitunix → API Management</b>.\n"
    "2) Buat/perbarui API key dengan izin <b>Trade</b>.\n"
    "   Create/refresh API key with <b>Trade</b> permission.\n"
    "3) Pastikan API key aktif dan dapat digunakan.\n"
    "   Ensure the API key is active and usable.\n"
    "4) Klik tombol dashboard di bawah lalu update API key Anda.\n"
    "   Click the dashboard button below and update your API key.\n\n"
    "Kami berharap Anda segera kembali trading bersama CryptoMentor.\n"
    "We hope to have you back trading soon."
)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_environment() -> None:
    # Keep order consistent with runtime defaults (Bismillah -> repo root -> website-backend).
    candidate_envs = [
        BISMILLAH_DIR / ".env",
        ROOT / ".env",
        ROOT / "website-backend" / ".env",
    ]
    for env_file in candidate_envs:
        if env_file.exists():
            load_dotenv(dotenv_path=env_file, override=False)

    # Best-effort: load systemd manager env when running on Linux VPS.
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
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value)
        except Exception:
            pass


def normalize_status(raw_status: Any) -> str:
    status = str(raw_status or "").strip().lower()
    if status in APPROVED_ALIASES:
        return "approved"
    if status in {"pending", "pending_verification", "awaiting_approval"}:
        return "pending"
    if status in {"rejected", "uid_rejected", "denied"}:
        return "rejected"
    return "none"


def _safe_uid(value: Any) -> Optional[int]:
    try:
        uid = int(value)
    except Exception:
        return None
    if uid <= 0:
        return None
    if uid in EXCLUDED_UIDS:
        return None
    return uid


def _load_admin_ids_ordered() -> List[int]:
    ordered: List[int] = []
    seen: Set[int] = set()

    def add(uid: Optional[int]) -> None:
        if uid is None or uid in seen:
            return
        ordered.append(uid)
        seen.add(uid)

    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        for token in admin_ids_str.split(","):
            add(_safe_uid(token.strip()))

    for key in ("ADMIN1", "ADMIN2", "ADMIN3", "ADMIN_USER_ID", "ADMIN2_USER_ID"):
        add(_safe_uid(os.getenv(key)))

    return ordered


@dataclass
class UserProfile:
    telegram_id: int
    username: str
    first_name: str


@dataclass
class TargetRecord:
    telegram_id: int
    verification_source: str
    verification_status_raw: str
    reason_tags: List[str]
    username: str
    first_name: str


@dataclass
class SendResult:
    telegram_id: int
    outcome: str
    error: str = ""


def _dedup_keep_order(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for v in values:
        if v in seen:
            continue
        out.append(v)
        seen.add(v)
    return out


def _is_blocked_or_forbidden(err_text: str) -> bool:
    s = (err_text or "").strip().lower()
    patterns = [
        "blocked",
        "forbidden",
        "deactivated",
        "chat not found",
        "user is deactivated",
        "bot was blocked by the user",
    ]
    return any(p in s for p in patterns)


async def _validate_bitunix_key(
    api_key: str,
    api_secret_plain: str,
    conn_timeout: float,
) -> Tuple[bool, str]:
    from app.bitunix_autotrade_client import BitunixAutoTradeClient

    client = BitunixAutoTradeClient(api_key=api_key, api_secret=api_secret_plain)
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(client.check_connection),
            timeout=conn_timeout,
        )
    except asyncio.TimeoutError:
        return False, "connection_timeout"
    except Exception as exc:
        return False, f"connection_error:{str(exc)[:120]}"

    if bool(result.get("online")):
        return True, "ok"

    error_text = str(result.get("error", "")).strip()
    upper = error_text.upper()
    if "TOKEN_INVALID" in upper:
        return False, "token_invalid"
    if "IP_BLOCKED" in upper:
        return False, "ip_blocked"
    if error_text:
        return False, f"connection_failed:{error_text[:120]}"
    return False, "connection_failed"


async def _resolve_api_state_for_uid(
    uid: int,
    key_rows: Sequence[Dict[str, Any]],
    conn_timeout: float,
) -> Tuple[str, List[str]]:
    from app.lib.crypto import decrypt

    if not key_rows:
        return "missing_api", ["missing_api:no_bitunix_row"]

    material_rows: List[Dict[str, Any]] = []
    has_any_api_key = False
    has_any_api_secret = False

    for row in key_rows:
        api_key = str(row.get("api_key") or "").strip()
        api_secret_enc = str(row.get("api_secret_enc") or "").strip()
        has_any_api_key = has_any_api_key or bool(api_key)
        has_any_api_secret = has_any_api_secret or bool(api_secret_enc)
        if api_key and api_secret_enc:
            material_rows.append(row)

    if not material_rows:
        tags: List[str] = ["missing_api:incomplete_bitunix_key_row"]
        if not has_any_api_key:
            tags.append("missing_api:missing_api_key")
        if not has_any_api_secret:
            tags.append("missing_api:missing_api_secret")
        return "missing_api", _dedup_keep_order(tags)

    invalid_tags: List[str] = []
    for row in material_rows:
        api_key = str(row.get("api_key") or "").strip()
        api_secret_enc = str(row.get("api_secret_enc") or "").strip()

        try:
            api_secret_plain = decrypt(api_secret_enc)
        except Exception as exc:
            invalid_tags.append(f"invalid_api:decrypt_failed:{str(exc)[:80]}")
            continue

        valid, reason = await _validate_bitunix_key(
            api_key=api_key,
            api_secret_plain=api_secret_plain,
            conn_timeout=conn_timeout,
        )
        if valid:
            return "valid_api", ["valid_api"]
        invalid_tags.append(f"invalid_api:{reason}")

    return "invalid_api", _dedup_keep_order(invalid_tags or ["invalid_api:unknown"])


async def resolve_targets(conn_timeout: float) -> Tuple[List[TargetRecord], Dict[str, int], Dict[str, Any]]:
    from app.supabase_repo import _client

    s = _client()

    users_rows = (
        s.table("users")
        .select("telegram_id,username,first_name")
        .execute()
        .data
        or []
    )
    uv_rows = (
        s.table("user_verifications")
        .select("telegram_id,status")
        .execute()
        .data
        or []
    )
    sess_rows = (
        s.table("autotrade_sessions")
        .select("telegram_id,status")
        .execute()
        .data
        or []
    )
    key_rows = (
        s.table("user_api_keys")
        .select("telegram_id,exchange,api_key,api_secret_enc,key_hint")
        .execute()
        .data
        or []
    )

    users: Dict[int, UserProfile] = {}
    for row in users_rows:
        uid = _safe_uid(row.get("telegram_id"))
        if uid is None:
            continue
        users[uid] = UserProfile(
            telegram_id=uid,
            username=str(row.get("username") or ""),
            first_name=str(row.get("first_name") or ""),
        )

    uv_by_uid: Dict[int, str] = {}
    verified_uids: Set[int] = set()

    for row in uv_rows:
        uid = _safe_uid(row.get("telegram_id"))
        if uid is None:
            continue
        raw = str(row.get("status") or "")
        uv_by_uid[uid] = raw
        if normalize_status(raw) == "approved":
            verified_uids.add(uid)

    sess_by_uid: Dict[int, str] = {}
    for row in sess_rows:
        uid = _safe_uid(row.get("telegram_id"))
        if uid is None:
            continue
        raw = str(row.get("status") or "")
        sess_by_uid[uid] = raw
        if uid not in uv_by_uid and normalize_status(raw) == "approved":
            verified_uids.add(uid)

    verified_uids = {uid for uid in verified_uids if uid in users}

    keys_by_uid: Dict[int, List[Dict[str, Any]]] = {}
    for row in key_rows:
        uid = _safe_uid(row.get("telegram_id"))
        if uid is None:
            continue
        exchange = str(row.get("exchange") or "").strip().lower()
        if exchange not in BITUNIX_EXCHANGE_ALIASES:
            continue
        keys_by_uid.setdefault(uid, []).append(row)

    targets: List[TargetRecord] = []
    for uid in sorted(verified_uids):
        api_state, reason_tags = await _resolve_api_state_for_uid(
            uid=uid,
            key_rows=keys_by_uid.get(uid, []),
            conn_timeout=conn_timeout,
        )
        if api_state not in {"missing_api", "invalid_api"}:
            continue

        profile = users[uid]
        if uid in uv_by_uid:
            source = "user_verifications"
            raw_status = uv_by_uid.get(uid, "")
        else:
            source = "autotrade_sessions"
            raw_status = sess_by_uid.get(uid, "")

        targets.append(
            TargetRecord(
                telegram_id=uid,
                verification_source=source,
                verification_status_raw=str(raw_status),
                reason_tags=_dedup_keep_order(reason_tags),
                username=profile.username,
                first_name=profile.first_name,
            )
        )

    stats = {
        "USERS_TOTAL": len(users),
        "VERIFIED_TOTAL": len(verified_uids),
        "TARGETS_TOTAL": len(targets),
    }
    meta = {
        "verified_uids": sorted(verified_uids),
    }
    return targets, stats, meta


def _target_reason_counter(targets: Sequence[TargetRecord]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for target in targets:
        for tag in target.reason_tags:
            out[tag] = out.get(tag, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: kv[0]))


def _build_dashboard_url(target: TargetRecord) -> str:
    from app.lib.auth import generate_dashboard_url

    return generate_dashboard_url(
        telegram_id=target.telegram_id,
        username=target.username,
        first_name=target.first_name,
    )


def _build_admin_preview_url(admin_uid: int, users_by_uid: Dict[int, TargetRecord]) -> str:
    from app.lib.auth import generate_dashboard_url

    candidate = users_by_uid.get(admin_uid)
    username = candidate.username if candidate else ""
    first_name = candidate.first_name if candidate else ""
    return generate_dashboard_url(
        telegram_id=admin_uid,
        username=username,
        first_name=first_name,
    )


async def _send_single_message(
    bot: Any,
    chat_id: int,
    url: str,
) -> SendResult:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔑 Setup API on Dashboard", url=url)]]
    )
    try:
        await bot.send_message(
            chat_id=int(chat_id),
            text=MESSAGE_TEMPLATE,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return SendResult(telegram_id=int(chat_id), outcome="SENT", error="")
    except Exception as exc:
        err_text = str(exc)
        if _is_blocked_or_forbidden(err_text):
            return SendResult(
                telegram_id=int(chat_id),
                outcome="BLOCKED_OR_FORBIDDEN",
                error=err_text[:240],
            )
        return SendResult(
            telegram_id=int(chat_id),
            outcome="FAILED",
            error=err_text[:240],
        )


def _init_run_paths(mode: str) -> Tuple[str, Path, Path]:
    run_id = f"api_issue_broadcast_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{mode}"
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    json_path = log_dir / f"{run_id}.json"
    csv_path = log_dir / f"{run_id}.csv"
    return run_id, json_path, csv_path


def _write_csv(csv_path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp_utc",
                    "run_id",
                    "mode",
                    "telegram_id",
                    "outcome",
                    "reason_tags",
                    "error",
                ]
            )
        return

    fieldnames = [
        "timestamp_utc",
        "run_id",
        "mode",
        "telegram_id",
        "outcome",
        "reason_tags",
        "error",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _print_campaign_summary(
    audience_label: str,
    total_target: int,
    sent: int,
    failed: int,
    blocked_or_forbidden: int,
    notes: str,
) -> None:
    print("Campaign Summary:")
    print(f"- Audience: {audience_label}")
    print(f"- TOTAL_TARGET: {total_target}")
    print(f"- SENT: {sent}")
    print(f"- FAILED: {failed}")
    print(f"- BLOCKED_OR_FORBIDDEN: {blocked_or_forbidden}")
    print(f"- Notes: {notes}")


async def run(mode: str, rate_delay: float, conn_timeout: float) -> int:
    load_environment()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    admin_ids = _load_admin_ids_ordered()

    print(f"[{now_utc_iso()}] Resolving verified audience and API state...")
    targets, stats, _meta = await resolve_targets(conn_timeout=conn_timeout)

    print(f"USERS_TOTAL={stats['USERS_TOTAL']}")
    print(f"VERIFIED_TOTAL={stats['VERIFIED_TOTAL']}")
    print(f"TOTAL_TARGET={stats['TARGETS_TOTAL']}")
    print(f"TARGET_REASON_COUNTS={json.dumps(_target_reason_counter(targets), ensure_ascii=False)}")

    for t in targets:
        print(
            f"TARGET uid={t.telegram_id} source={t.verification_source} "
            f"status={t.verification_status_raw} reasons={','.join(t.reason_tags)}"
        )

    run_id, json_path, csv_path = _init_run_paths(mode=mode)

    sent = 0
    failed = 0
    blocked = 0
    send_rows: List[Dict[str, Any]] = []
    send_results: List[Dict[str, Any]] = []
    preview: Dict[str, Any] = {"attempted": False}

    if mode == "dry-run":
        for t in targets:
            send_rows.append(
                {
                    "timestamp_utc": now_utc_iso(),
                    "run_id": run_id,
                    "mode": mode,
                    "telegram_id": t.telegram_id,
                    "outcome": "TARGET_DRY_RUN",
                    "reason_tags": "|".join(t.reason_tags),
                    "error": "",
                }
            )
        notes = "dry-run only; no Telegram send"
        _print_campaign_summary(
            audience_label="verified_missing_or_invalid_api",
            total_target=len(targets),
            sent=sent,
            failed=failed,
            blocked_or_forbidden=blocked,
            notes=notes,
        )

    else:
        if not bot_token:
            raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or BOT_TOKEN in environment.")

        from telegram import Bot

        bot = Bot(token=bot_token)

        if mode == "test-admin":
            preview["attempted"] = True
            if not admin_ids:
                raise RuntimeError("No admin IDs configured for --mode test-admin.")

            admin_uid = int(admin_ids[0])
            preview_url = _build_admin_preview_url(admin_uid, {})
            result = await _send_single_message(bot=bot, chat_id=admin_uid, url=preview_url)

            preview.update(
                {
                    "admin_uid": admin_uid,
                    "outcome": result.outcome,
                    "error": result.error,
                }
            )

            if result.outcome == "SENT":
                sent += 1
            elif result.outcome == "BLOCKED_OR_FORBIDDEN":
                blocked += 1
            else:
                failed += 1

            send_results.append(asdict(result))
            send_rows.append(
                {
                    "timestamp_utc": now_utc_iso(),
                    "run_id": run_id,
                    "mode": mode,
                    "telegram_id": admin_uid,
                    "outcome": result.outcome,
                    "reason_tags": "admin_preview",
                    "error": result.error,
                }
            )

            notes = "admin preview only; full audience not sent in this mode"
            _print_campaign_summary(
                audience_label="verified_missing_or_invalid_api",
                total_target=len(targets),
                sent=sent,
                failed=failed,
                blocked_or_forbidden=blocked,
                notes=notes,
            )

        elif mode == "full-send":
            for idx, t in enumerate(targets, start=1):
                url = _build_dashboard_url(t)
                result = await _send_single_message(
                    bot=bot,
                    chat_id=t.telegram_id,
                    url=url,
                )

                send_results.append(asdict(result))
                send_rows.append(
                    {
                        "timestamp_utc": now_utc_iso(),
                        "run_id": run_id,
                        "mode": mode,
                        "telegram_id": t.telegram_id,
                        "outcome": result.outcome,
                        "reason_tags": "|".join(t.reason_tags),
                        "error": result.error,
                    }
                )

                if result.outcome == "SENT":
                    sent += 1
                elif result.outcome == "BLOCKED_OR_FORBIDDEN":
                    blocked += 1
                else:
                    failed += 1

                print(
                    f"[{idx}/{len(targets)}] uid={t.telegram_id} outcome={result.outcome}"
                    + (f" error={result.error}" if result.error else "")
                )
                if rate_delay > 0:
                    await asyncio.sleep(rate_delay)

            notes = (
                "full-send completed; "
                "consistency_check="
                f"{len(targets)}=={sent + failed + blocked}"
            )
            _print_campaign_summary(
                audience_label="verified_missing_or_invalid_api",
                total_target=len(targets),
                sent=sent,
                failed=failed,
                blocked_or_forbidden=blocked,
                notes=notes,
            )
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    payload = {
        "run_id": run_id,
        "mode": mode,
        "created_at_utc": now_utc_iso(),
        "audience": "verified_missing_or_invalid_api",
        "config": {
            "rate_delay": rate_delay,
            "conn_timeout": conn_timeout,
        },
        "stats": stats,
        "targets": [asdict(t) for t in targets],
        "metrics": {
            "TOTAL_TARGET": len(targets),
            "SENT": sent,
            "FAILED": failed,
            "BLOCKED_OR_FORBIDDEN": blocked,
        },
        "preview": preview,
        "send_results": send_results,
    }

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _write_csv(csv_path=csv_path, rows=send_rows)

    print(f"Saved JSON log: {json_path}")
    print(f"Saved CSV log: {csv_path}")
    return 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Broadcast API issue recovery campaign.")
    parser.add_argument(
        "--mode",
        choices=["dry-run", "test-admin", "full-send"],
        required=True,
        help="Execution mode.",
    )
    parser.add_argument(
        "--rate-delay",
        type=float,
        default=0.25,
        help="Delay between sends in full-send mode (seconds). Default: 0.25",
    )
    parser.add_argument(
        "--conn-timeout",
        type=float,
        default=15.0,
        help="Bitunix connection check timeout in seconds. Default: 15",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        return asyncio.run(
            run(
                mode=args.mode,
                rate_delay=float(args.rate_delay),
                conn_timeout=float(args.conn_timeout),
            )
        )
    except KeyboardInterrupt:
        print("Interrupted by user.")
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

