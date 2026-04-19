#!/usr/bin/env python3
"""
Hourly admin report for trading engine status and trade/no-trade summary.

Usage:
  python scripts/hourly_admin_engine_report.py --mode send-now
  python scripts/hourly_admin_engine_report.py --mode dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
BISMILLAH_DIR = ROOT / "Bismillah"
LOG_DIR = ROOT / "logs" / "hourly_admin_reports"
TZ_WIB = timezone(timedelta(hours=7))

if str(BISMILLAH_DIR) not in sys.path:
    sys.path.insert(0, str(BISMILLAH_DIR))


def _load_environment() -> None:
    env_files = [
        BISMILLAH_DIR / ".env",
        ROOT / ".env",
        ROOT / "website-backend" / ".env",
    ]
    for env_path in env_files:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)

    # Best-effort: include manager env on Linux VPS.
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
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v)
        except Exception:
            pass


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v or 0)
    except Exception:
        return float(default)


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _fmt_usdt(v: float) -> str:
    sign = "+" if v > 0 else ""
    return f"{sign}${v:,.2f}"


def _load_admin_ids() -> List[int]:
    out: List[int] = []
    seen = set()

    def add(raw: Any) -> None:
        try:
            uid = int(str(raw).strip())
        except Exception:
            return
        if uid <= 0 or uid in seen:
            return
        seen.add(uid)
        out.append(uid)

    for token in (os.getenv("ADMIN_IDS", "") or "").split(","):
        if token.strip():
            add(token)

    for key in ("ADMIN1", "ADMIN2", "ADMIN3", "ADMIN_USER_ID", "ADMIN2_USER_ID"):
        add(os.getenv(key, ""))

    return out


def _service_snapshot(service_name: str) -> Dict[str, str]:
    snap = {
        "active": "unknown",
        "main_pid": "N/A",
        "active_state": "N/A",
        "sub_state": "N/A",
    }
    if os.name == "nt":
        snap["active"] = "n/a (non-systemd host)"
        return snap
    try:
        res = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=6,
        )
        snap["active"] = (res.stdout or "").strip() or (res.stderr or "").strip() or "unknown"
    except Exception as e:
        snap["active"] = f"error:{e}"

    try:
        res = subprocess.run(
            ["systemctl", "show", service_name, "-p", "MainPID", "-p", "ActiveState", "-p", "SubState"],
            capture_output=True,
            text=True,
            timeout=6,
        )
        if res.returncode == 0:
            for line in (res.stdout or "").splitlines():
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k == "MainPID":
                    snap["main_pid"] = v
                elif k == "ActiveState":
                    snap["active_state"] = v
                elif k == "SubState":
                    snap["sub_state"] = v
    except Exception:
        pass

    return snap


def _journal_indicators(service_name: str, minutes: int) -> Dict[str, int]:
    out = {
        "no_quality_setups": 0,
        "confidence_gate_reject": 0,
        "trade_skipped": 0,
        "api_key_or_decrypt_issue": 0,
    }
    if os.name == "nt":
        return out

    try:
        cmd = [
            "journalctl",
            "-u",
            service_name,
            "--since",
            f"{minutes} minutes ago",
            "--no-pager",
            "-o",
            "cat",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if res.returncode != 0:
            return out
        text = (res.stdout or "").lower()
    except Exception:
        return out

    out["no_quality_setups"] = text.count("no quality setups found")
    out["confidence_gate_reject"] = (
        text.count("rejected by confidence gate")
        + text.count("confidence gate reject")
    )
    out["trade_skipped"] = text.count("trade skipped")
    out["api_key_or_decrypt_issue"] = (
        text.count("api keys not found")
        + text.count("decrypt failed")
        + text.count("api key decrypt")
    )
    return out


def _build_report(minutes: int, service_name: str) -> Dict[str, Any]:
    from app.supabase_repo import _client
    from app.adaptive_confluence import classify_outcome_class

    # Optional snapshots; keep report resilient if any module fails.
    playbook_snapshot: Dict[str, Any] = {}
    confidence_snapshot: Dict[str, Any] = {}
    sideways_snapshot: Dict[str, Any] = {}
    try:
        from app.win_playbook import refresh_global_win_playbook_state, get_win_playbook_snapshot
        refresh_global_win_playbook_state()
        playbook_snapshot = get_win_playbook_snapshot() or {}
    except Exception:
        pass
    try:
        from app.confidence_adaptation import (
            refresh_global_confidence_adaptation_state,
            get_confidence_adaptation_snapshot,
        )
        refresh_global_confidence_adaptation_state()
        confidence_snapshot = get_confidence_adaptation_snapshot() or {}
    except Exception:
        pass
    try:
        from app.sideways_governor import refresh_sideways_governor_state, get_sideways_governor_snapshot
        refresh_sideways_governor_state()
        sideways_snapshot = get_sideways_governor_snapshot() or {}
    except Exception:
        pass

    now_utc = datetime.now(timezone.utc)
    since_utc = now_utc - timedelta(minutes=minutes)
    now_wib = now_utc.astimezone(TZ_WIB)
    since_wib = since_utc.astimezone(TZ_WIB)

    s = _client()

    sessions_rows = (
        s.table("autotrade_sessions")
        .select("telegram_id,status,engine_active,trading_mode,risk_per_trade,current_balance,updated_at")
        .execute()
        .data
        or []
    )

    opened_rows = (
        s.table("autotrade_trades")
        .select("id,telegram_id,symbol,side,trade_type,status,pnl_usdt,confidence,opened_at")
        .gte("opened_at", since_utc.isoformat())
        .execute()
        .data
        or []
    )
    closed_rows = (
        s.table("autotrade_trades")
        .select("id,telegram_id,symbol,side,trade_type,status,pnl_usdt,close_reason,loss_reasoning,closed_at")
        .gte("closed_at", since_utc.isoformat())
        .neq("status", "open")
        .execute()
        .data
        or []
    )
    open_now_res = (
        s.table("autotrade_trades")
        .select("id", count="exact")
        .eq("status", "open")
        .execute()
    )
    open_now_count = int(open_now_res.count or len(open_now_res.data or []))

    mode_counts = Counter(
        str(r.get("trading_mode") or "scalping").strip().lower() for r in sessions_rows
    )
    pending_statuses = {"pending", "pending_verification", "uid_rejected", "awaiting_approval"}
    pending_sessions = sum(
        1 for r in sessions_rows if str(r.get("status") or "").strip().lower() in pending_statuses
    )
    engine_active_control_plane = sum(1 for r in sessions_rows if bool(r.get("engine_active")))

    opened_type_counts = Counter(str(r.get("trade_type") or "unknown").strip().lower() for r in opened_rows)
    closed_type_counts = Counter(str(r.get("trade_type") or "unknown").strip().lower() for r in closed_rows)
    closed_outcome_counts = Counter(classify_outcome_class(r) for r in closed_rows)

    closed_pnl = sum(_safe_float(r.get("pnl_usdt"), 0.0) for r in closed_rows)
    closed_wins = sum(1 for r in closed_rows if _safe_float(r.get("pnl_usdt"), 0.0) > 0)
    closed_losses = sum(1 for r in closed_rows if _safe_float(r.get("pnl_usdt"), 0.0) < 0)
    avg_conf_opened = 0.0
    conf_values = [_safe_float(r.get("confidence"), 0.0) for r in opened_rows if r.get("confidence") is not None]
    if conf_values:
        avg_conf_opened = sum(conf_values) / len(conf_values)

    indicators = _journal_indicators(service_name=service_name, minutes=minutes)
    service = _service_snapshot(service_name=service_name)

    no_trade_reasons: List[str] = []
    if len(opened_rows) == 0:
        if indicators["no_quality_setups"] > 0:
            no_trade_reasons.append(
                f"Quality filter blocked candidates (`No quality setups found`: {indicators['no_quality_setups']} logs)."
            )
        if indicators["confidence_gate_reject"] > 0:
            no_trade_reasons.append(
                f"Confidence gate rejected setups ({indicators['confidence_gate_reject']} logs)."
            )
        if indicators["trade_skipped"] > 0:
            no_trade_reasons.append(
                f"Execution path skipped candidates ({indicators['trade_skipped']} logs)."
            )
        if indicators["api_key_or_decrypt_issue"] > 0:
            no_trade_reasons.append(
                f"API/decrypt issues reduced tradable sessions ({indicators['api_key_or_decrypt_issue']} logs)."
            )

        governor_mode = str(sideways_snapshot.get("mode") or "").strip().lower()
        if governor_mode in {"strict", "defensive"}:
            no_trade_reasons.append(
                f"Sideways governor is in `{governor_mode}` mode (tighter entry policy)."
            )
        if engine_active_control_plane <= 0:
            no_trade_reasons.append("No sessions are currently marked engine-active in control plane.")
        if not no_trade_reasons:
            no_trade_reasons.append("No dominant blocker found in logs; market conditions likely did not pass entry thresholds.")

    return {
        "window_minutes": minutes,
        "generated_at_utc": now_utc.isoformat(),
        "window_start_wib": since_wib.strftime("%d %b %Y %H:%M"),
        "window_end_wib": now_wib.strftime("%d %b %Y %H:%M"),
        "service": service,
        "sessions": {
            "total": len(sessions_rows),
            "engine_active_control_plane": engine_active_control_plane,
            "pending": pending_sessions,
            "mode_counts": dict(mode_counts),
        },
        "trades": {
            "opened": len(opened_rows),
            "opened_type_counts": dict(opened_type_counts),
            "avg_open_confidence": avg_conf_opened,
            "closed": len(closed_rows),
            "closed_type_counts": dict(closed_type_counts),
            "closed_outcome_counts": dict(closed_outcome_counts),
            "closed_pnl": closed_pnl,
            "closed_wins": closed_wins,
            "closed_losses": closed_losses,
            "open_now": open_now_count,
        },
        "adaptation": {
            "sideways_mode": str(sideways_snapshot.get("mode") or "unknown"),
            "playbook_overlay_pct": _safe_float(playbook_snapshot.get("risk_overlay_pct"), 0.0),
            "confidence_adapt_enabled": bool(confidence_snapshot.get("enabled", False)),
            "confidence_samples": {
                "swing": _safe_int((confidence_snapshot.get("modes") or {}).get("swing", {}).get("sample_size"), 0),
                "scalping": _safe_int((confidence_snapshot.get("modes") or {}).get("scalping", {}).get("sample_size"), 0),
            },
        },
        "log_indicators": indicators,
        "no_trade_reasons": no_trade_reasons,
    }


def _render_html_message(report: Dict[str, Any]) -> str:
    service = report["service"]
    sessions = report["sessions"]
    trades = report["trades"]
    adapt = report["adaptation"]
    indicators = report["log_indicators"]

    mode_counts = sessions.get("mode_counts", {})
    mode_text = ", ".join(
        f"{k}:{v}" for k, v in sorted(mode_counts.items(), key=lambda kv: kv[0])
    ) or "-"

    opened_by_type = trades.get("opened_type_counts", {})
    opened_type_text = ", ".join(
        f"{k}:{v}" for k, v in sorted(opened_by_type.items(), key=lambda kv: kv[0])
    ) or "-"
    outcomes = trades.get("closed_outcome_counts", {})
    outcome_text = ", ".join(
        f"{k}:{v}" for k, v in sorted(outcomes.items(), key=lambda kv: kv[0])
    ) or "-"

    msg = (
        "🕐 <b>Hourly Engine Summary</b>\n"
        f"🗓 <b>WIB:</b> {report['window_start_wib']} - {report['window_end_wib']}\n\n"
        "⚙️ <b>ENGINE STATUS</b>\n"
        f"• Service: <b>{service.get('active')}</b> "
        f"(state={service.get('active_state')}/{service.get('sub_state')}, pid={service.get('main_pid')})\n"
        f"• Sessions: total=<b>{sessions.get('total', 0)}</b>, "
        f"engine_active=<b>{sessions.get('engine_active_control_plane', 0)}</b>, "
        f"pending=<b>{sessions.get('pending', 0)}</b>\n"
        f"• Modes: <b>{mode_text}</b>\n\n"
        "📈 <b>TRADES (Last 1h)</b>\n"
        f"• Opened: <b>{trades.get('opened', 0)}</b> ({opened_type_text})\n"
        f"• Closed: <b>{trades.get('closed', 0)}</b> | Open now: <b>{trades.get('open_now', 0)}</b>\n"
        f"• Closed PnL: <b>{_fmt_usdt(_safe_float(trades.get('closed_pnl'), 0.0))}</b>\n"
        f"• W/L: <b>{trades.get('closed_wins', 0)}W / {trades.get('closed_losses', 0)}L</b>\n"
        f"• Outcome mix: <b>{outcome_text}</b>\n"
        f"• Avg confidence (opened): <b>{_safe_float(trades.get('avg_open_confidence'), 0.0):.1f}</b>\n\n"
        "🎚️ <b>RUNTIME ADAPTATION</b>\n"
        f"• Sideways governor mode: <b>{adapt.get('sideways_mode')}</b>\n"
        f"• Playbook risk overlay: <b>{_safe_float(adapt.get('playbook_overlay_pct'), 0.0):+.2f}%</b>\n"
        f"• Confidence adaptation: <b>{adapt.get('confidence_adapt_enabled')}</b> "
        f"(samples swing={adapt.get('confidence_samples', {}).get('swing', 0)}, "
        f"scalping={adapt.get('confidence_samples', {}).get('scalping', 0)})\n\n"
    )

    if _safe_int(trades.get("opened"), 0) == 0:
        msg += "🔎 <b>WHY NO NEW TRADES (Last 1h)</b>\n"
        for reason in report.get("no_trade_reasons", []):
            msg += f"• {reason}\n"
        msg += (
            f"• Log counters: quality={indicators.get('no_quality_setups', 0)}, "
            f"conf_reject={indicators.get('confidence_gate_reject', 0)}, "
            f"skipped={indicators.get('trade_skipped', 0)}, "
            f"api/decrypt={indicators.get('api_key_or_decrypt_issue', 0)}\n"
        )
    else:
        msg += "✅ <b>No-trade condition:</b> not active in this hour (new trades were opened).\n"

    msg += "\n🤖 <i>Auto-generated by CryptoMentor hourly monitor</i>"
    return msg


def _send_telegram_html(token: str, chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    data = urlparse.urlencode(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, method="POST")
    try:
        with urlrequest.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"http_error:{e.code} {detail[:200]}") from e
    except Exception as e:
        raise RuntimeError(f"transport_error:{e}") from e

    try:
        body = json.loads(raw)
    except Exception:
        raise RuntimeError(f"invalid_telegram_response:{raw[:200]}")

    if not bool(body.get("ok")):
        raise RuntimeError(str(body.get("description") or "telegram_send_failed"))


def _persist_run_artifact(report: Dict[str, Any], send_result: Dict[str, Any]) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = LOG_DIR / f"hourly_admin_report_{stamp}.json"
    payload = {
        "report": report,
        "send_result": send_result,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Send hourly engine/trade summary to Telegram admins.")
    parser.add_argument("--mode", choices=["send-now", "dry-run"], default="send-now")
    parser.add_argument("--window-minutes", type=int, default=60)
    parser.add_argument("--service-name", default="cryptomentor")
    args = parser.parse_args()

    _load_environment()

    report = _build_report(minutes=max(1, int(args.window_minutes)), service_name=str(args.service_name))
    message = _render_html_message(report)

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    admin_ids = _load_admin_ids()

    if args.mode == "dry-run":
        sys.stdout.buffer.write(b"=== DRY RUN MESSAGE ===\n")
        sys.stdout.buffer.write((message + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n=== SNAPSHOT ===\n")
        sys.stdout.buffer.write((json.dumps(report, indent=2) + "\n").encode("utf-8", errors="replace"))
        return 0

    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not configured.")
        return 2
    if not admin_ids:
        print("ERROR: No admin IDs found from ADMIN_IDS/ADMIN1/ADMIN2/...")
        return 3

    sent = 0
    failed = 0
    failed_items: List[Dict[str, Any]] = []
    for admin_id in admin_ids:
        try:
            _send_telegram_html(token=token, chat_id=admin_id, text=message)
            sent += 1
        except Exception as e:
            failed += 1
            failed_items.append({"telegram_id": admin_id, "error": str(e)})

    result = {
        "ok": failed == 0,
        "admin_target": len(admin_ids),
        "sent": sent,
        "failed": failed,
        "failed_items": failed_items,
    }
    artifact = _persist_run_artifact(report=report, send_result=result)

    print(json.dumps({
        **result,
        "artifact": str(artifact),
        "snapshot": {
            "opened_1h": report.get("trades", {}).get("opened", 0),
            "closed_1h": report.get("trades", {}).get("closed", 0),
            "sideways_mode": report.get("adaptation", {}).get("sideways_mode"),
            "no_quality_setups": report.get("log_indicators", {}).get("no_quality_setups", 0),
        },
    }, indent=2))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
