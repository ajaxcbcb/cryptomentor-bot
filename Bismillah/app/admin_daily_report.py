"""
Admin Daily Analytics Report
Sends a comprehensive daily summary to all admins every night at 23:00 UTC+7.
Covers: active engines, trades, PnL, stopped engines with reasoning.
"""

import asyncio
import html
import logging
import os
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

TZ_WIB = timezone(timedelta(hours=7))  # UTC+7 (WIB)


def _get_admin_ids() -> list[int]:
    ids = set()
    for key in ("ADMIN_IDS", "ADMIN1", "ADMIN2", "ADMIN3", "ADMIN_USER_ID", "ADMIN2_USER_ID"):
        for part in os.getenv(key, "").split(","):
            part = part.strip()
            if part.isdigit():
                ids.add(int(part))
    return sorted(ids)


def _fmt(val, prefix="$", decimals=2) -> str:
    try:
        v = float(val or 0)
        sign = "+" if v > 0 else ""
        return f"{sign}{prefix}{v:,.{decimals}f}"
    except Exception:
        return "N/A"


def _to_float(val, default: float = 0.0) -> float:
    try:
        return float(val or 0)
    except Exception:
        return float(default)


def _escape_html(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _parse_iso_utc(raw) -> datetime | None:
    if not raw:
        return None
    try:
        txt = str(raw)
        if txt.endswith("Z"):
            txt = txt[:-1] + "+00:00"
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _freshness_label(raw, now_utc: datetime) -> str:
    dt = _parse_iso_utc(raw)
    if dt is None:
        return "n/a"
    try:
        sec = max(0, int((now_utc - dt).total_seconds()))
    except Exception:
        return "n/a"
    if sec < 60:
        return f"{sec}s"
    if sec < 3600:
        return f"{sec // 60}m"
    return f"{sec // 3600}h"


def _close_reason_key(row: dict) -> str:
    return str(row.get("close_reason") or row.get("status") or "unknown").strip().lower() or "unknown"


def _is_expected_winning_close(row: dict) -> bool:
    reason = _close_reason_key(row)
    pnl = _to_float(row.get("pnl_usdt"), 0.0)
    if reason in {"closed_tp", "closed_tp3"}:
        return True
    if reason == "closed_flip" and pnl > 0:
        return True
    return False


def _is_expected_losing_close(row: dict) -> bool:
    return _to_float(row.get("pnl_usdt"), 0.0) < 0 and not _is_expected_winning_close(row)


def _format_missing_reason_map(missing: dict[str, int], max_items: int = 6) -> str:
    if not missing:
        return "-"
    items = sorted(missing.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    shown = items[:max_items]
    txt = ", ".join(f"{k}:{int(v)}" for k, v in shown)
    if len(items) > max_items:
        txt += f", +{len(items) - max_items} more"
    return txt


def _format_playbook_clusters_brief(rows: list[dict], max_items: int = 3) -> str:
    if not rows:
        return "-"
    out: list[str] = []
    for row in list(rows)[: max(1, int(max_items or 3))]:
        label = str(row.get("label") or "-")
        support = int(row.get("support", 0) or 0)
        win_rate = float(row.get("win_rate", 0.0) or 0.0) * 100.0
        expectancy = float(row.get("expectancy_usdt", 0.0) or 0.0)
        median_r = float(row.get("median_r", 0.0) or 0.0)
        out.append(
            f"{label} (n={support}, wr={win_rate:.1f}%, exp={expectancy:+.4f}, R~{median_r:+.2f})"
        )
    return " | ".join(out) if out else "-"


def _build_user_pnl_breakdown_rows(all_sessions: list[dict], trades_today: list[dict]) -> list[dict]:
    """
    Build per-user 24h trade/PnL breakdown rows.

    Coverage policy:
    - Include all real users present in autotrade_sessions (even with zero trades).
    - Include trade-only users seen in the 24h trade window even if session row is missing.
    """
    session_by_uid: dict[int, dict] = {}
    for sess in all_sessions or []:
        uid_raw = sess.get("telegram_id")
        if not _is_real_user_id(uid_raw):
            continue
        uid = int(uid_raw)
        if uid not in session_by_uid:
            session_by_uid[uid] = sess

    rows_by_uid: dict[int, dict] = {}

    def _ensure(uid: int) -> dict:
        if uid in rows_by_uid:
            return rows_by_uid[uid]

        sess = session_by_uid.get(uid) or {}
        row = {
            "telegram_id": int(uid),
            "status": str(sess.get("status") or "no_session"),
            "trading_mode": str(sess.get("trading_mode") or "-"),
            "opened": 0,
            "closed": 0,
            "open_now": 0,
            "wins": 0,
            "losses": 0,
            "pnl_usdt": 0.0,
        }
        rows_by_uid[uid] = row
        return row

    for uid in session_by_uid.keys():
        _ensure(uid)

    for trade in trades_today or []:
        uid_raw = trade.get("telegram_id")
        if not _is_real_user_id(uid_raw):
            continue
        uid = int(uid_raw)
        row = _ensure(uid)
        row["opened"] += 1

        status = str(trade.get("status") or "").strip().lower()
        pnl = _to_float(trade.get("pnl_usdt"), 0.0)
        if status == "open":
            row["open_now"] += 1
            continue

        row["closed"] += 1
        row["pnl_usdt"] += pnl
        if pnl > 0:
            row["wins"] += 1
        elif pnl < 0:
            row["losses"] += 1

    return [rows_by_uid[uid] for uid in sorted(rows_by_uid.keys())]


def _summarize_coordinator_pending_snapshot(
    snapshot: dict | None,
    *,
    pending_ttl_seconds: float = 90.0,
    top_n: int = 5,
) -> dict:
    data = dict(snapshot or {})
    users = data.get("users") or {}
    ttl = max(1.0, float(pending_ttl_seconds or 90.0))
    pending_total = 0
    pending_with_position = 0
    pending_without_position = 0
    stale_pending_without_position = 0
    owner_mix: dict[str, int] = {}
    symbol_counts: dict[str, int] = {}

    for user_data in users.values():
        symbols = (user_data or {}).get("symbols") or {}
        for symbol, st in symbols.items():
            if not bool(st.get("pending_order", False)):
                continue
            pending_total += 1
            has_position = bool(st.get("has_position", False))
            if has_position:
                pending_with_position += 1
            else:
                pending_without_position += 1
                age = st.get("pending_age_seconds")
                try:
                    if age is not None and float(age) > ttl:
                        stale_pending_without_position += 1
                except Exception:
                    pass
            owner = str(st.get("pending_owner") or st.get("owner") or "unknown").strip().lower() or "unknown"
            owner_mix[owner] = owner_mix.get(owner, 0) + 1
            sym = str(symbol or "").upper()
            if sym:
                symbol_counts[sym] = symbol_counts.get(sym, 0) + 1

    owner_mix_sorted = sorted(owner_mix.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))
    top_symbols_sorted = sorted(symbol_counts.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))[: max(1, int(top_n))]
    owner_mix_text = ", ".join(f"{owner}:{count}" for owner, count in owner_mix_sorted) if owner_mix_sorted else "-"
    top_symbols_text = ", ".join(f"{symbol}({count})" for symbol, count in top_symbols_sorted) if top_symbols_sorted else "-"

    return {
        "pending_total": int(pending_total),
        "pending_with_position": int(pending_with_position),
        "pending_without_position": int(pending_without_position),
        "stale_pending_without_position": int(stale_pending_without_position),
        "pending_ttl_seconds": float(ttl),
        "owner_mix": owner_mix,
        "owner_mix_text": owner_mix_text,
        "top_symbols": top_symbols_sorted,
        "top_symbols_text": top_symbols_text,
        "snapshot_user_count": len(users),
    }


def _split_message_lines(text: str, max_len: int = 3800) -> list[str]:
    """
    Split long Telegram messages safely by line boundaries.
    Keeps HTML entities/tags intact per line and avoids 4096-char limit.
    """
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    current_lines: list[str] = []
    current_len = 0

    for raw_line in text.splitlines(keepends=True):
        line = raw_line

        # Fallback: a single very long line still must be split.
        while len(line) > max_len:
            head = line[:max_len]
            tail = line[max_len:]
            if current_lines:
                chunks.append("".join(current_lines).rstrip())
                current_lines = []
                current_len = 0
            chunks.append(head.rstrip())
            line = tail

        line_len = len(line)
        if current_lines and (current_len + line_len) > max_len:
            chunks.append("".join(current_lines).rstrip())
            current_lines = [line]
            current_len = line_len
        else:
            current_lines.append(line)
            current_len += line_len

    if current_lines:
        chunks.append("".join(current_lines).rstrip())

    return chunks


def _is_real_user_id(raw_id) -> bool:
    """
    Accept real Telegram user IDs without legacy hard cutoff.
    Old logic used < 999,999,990 and excluded most modern 10-digit IDs.
    """
    try:
        uid = int(raw_id)
    except Exception:
        return False
    # Exclude empty/invalid and obviously non-user sentinels.
    return uid > 0


def _engine_stop_reason(session: dict, has_api_keys: bool) -> str:
    """Determine why an engine is stopped based on session data."""
    status = session.get("status", "")

    if status == "stopped":
        return "🔴 Manually stopped by user (or auto-stopped by system)"
    if not has_api_keys:
        return "🔑 API keys not found in database — user needs to re-link keys via /autotrade"
    if status in ("pending_verification", "pending"):
        return "⏳ Awaiting UID verification"
    if status == "uid_rejected":
        return "❌ UID verification rejected"
    if not session.get("engine_active", False):
        return "⚠️ Engine crashed / unexpected stop — health check will auto-restart"
    return "❓ Unknown reason"


async def send_daily_report(bot):
    """Build and send the daily analytics report to all admins."""
    try:
        from app.supabase_repo import _client
        from app.autotrade_engine import is_running
        from app.handlers_autotrade import get_user_api_keys
        from app.exchange_registry import get_client
        from app.adaptive_confluence import classify_outcome_class, get_adaptive_overrides
        from app.confidence_adaptation import (
            get_confidence_adaptation_snapshot,
            refresh_global_confidence_adaptation_state,
        )
        from app.sideways_governor import refresh_sideways_governor_state, get_sideways_governor_snapshot
        from app.symbol_coordinator import get_coordinator
        from app.win_playbook import refresh_global_win_playbook_state, get_win_playbook_snapshot
        from app.playbook_analytics import build_playbook_analysis

        s = _client()
        now_wib = datetime.now(TZ_WIB)
        today_str = now_wib.strftime("%d %b %Y")
        since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

        # ── 1. All sessions ───────────────────────────────────────────
        all_sessions_res = s.table("autotrade_sessions").select("*").execute()
        all_sessions = all_sessions_res.data or []

        total_users = len([
            sess for sess in all_sessions
            if _is_real_user_id(sess.get("telegram_id"))
        ])

        active_engines = []
        stopped_engines = []
        pending_engines = []

        for sess in all_sessions:
            uid = sess.get("telegram_id")
            if not _is_real_user_id(uid):
                continue
            status = sess.get("status", "")
            if status in ("pending_verification", "uid_rejected", "pending"):
                pending_engines.append(sess)
            elif is_running(uid):
                active_engines.append(sess)
            else:
                stopped_engines.append(sess)

        key_cache: dict[int, dict | None] = {}

        def _cached_user_keys(uid: int):
            try:
                uid_i = int(uid)
            except Exception:
                return None
            if uid_i not in key_cache:
                try:
                    key_cache[uid_i] = get_user_api_keys(uid_i)
                except Exception:
                    key_cache[uid_i] = None
            return key_cache[uid_i]

        async def _resolve_live_equity(sess: dict) -> tuple[float, str]:
            uid = int(sess.get("telegram_id") or 0)
            fallback = _to_float(sess.get("current_balance"), 0.0)
            keys = _cached_user_keys(uid)
            if not keys:
                return fallback, "db_no_keys"

            exchange_id = str(keys.get("exchange") or sess.get("exchange") or "bitunix")
            try:
                ex_client = get_client(exchange_id, keys["api_key"], keys["api_secret"])
                acc = await asyncio.wait_for(
                    asyncio.to_thread(ex_client.get_account_info),
                    timeout=4.0,
                )
                if bool(acc.get("success")):
                    available = _to_float(acc.get("available"), 0.0)
                    frozen = _to_float(acc.get("frozen"), 0.0)
                    unrealized = _to_float(acc.get("total_unrealized_pnl"), 0.0)
                    equity = available + frozen + unrealized

                    # Keep DB snapshot fresh so admin reports and other consumers
                    # do not keep showing stale bootstrap balances.
                    if abs(equity - fallback) > 0.01:
                        try:
                            s.table("autotrade_sessions").update({
                                "current_balance": equity,
                                "updated_at": datetime.now(timezone.utc).isoformat(),
                            }).eq("telegram_id", uid).execute()
                        except Exception as e:
                            logger.warning(
                                f"[DailyReport] Failed to persist equity snapshot for {uid}: {e}"
                            )
                    return equity, "live"
            except Exception as e:
                logger.warning(f"[DailyReport] Live equity fetch failed for {uid}: {e}")

            return fallback, "db_fallback"

        # Hydrate live equity for all users shown in active/stopped sections.
        report_sessions = []
        report_sessions.extend(active_engines)
        report_sessions.extend(stopped_engines)
        if report_sessions:
            sem = asyncio.Semaphore(8)

            async def _hydrate_one(sess: dict):
                uid = int(sess.get("telegram_id") or 0)
                if uid <= 0:
                    return
                async with sem:
                    equity, source = await _resolve_live_equity(sess)
                sess["_equity_value"] = equity
                sess["_equity_source"] = source

            await asyncio.gather(*[_hydrate_one(sess) for sess in report_sessions])

        # ── 2. Today's trades ─────────────────────────────────────────
        trades_res = s.table("autotrade_trades").select(
            "telegram_id, symbol, side, pnl_usdt, status, close_reason, loss_reasoning, trade_subtype, "
            "win_reasoning, playbook_match_score, effective_risk_pct, risk_overlay_pct, opened_at, closed_at"
        ).gte("opened_at", since_24h).execute()
        trades_today = trades_res.data or []

        closed_trades = [t for t in trades_today if str(t.get("status") or "").lower() != "open"]
        open_trades = [t for t in trades_today if t.get("status") == "open"]

        total_pnl = sum(float(t.get("pnl_usdt") or 0) for t in closed_trades)
        wins = [t for t in closed_trades if float(t.get("pnl_usdt") or 0) > 0]
        losses = [t for t in closed_trades if float(t.get("pnl_usdt") or 0) < 0]
        win_pnl = sum(float(t.get("pnl_usdt") or 0) for t in wins)
        loss_pnl = sum(float(t.get("pnl_usdt") or 0) for t in losses)
        win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0

        user_pnl_rows = _build_user_pnl_breakdown_rows(all_sessions, trades_today)
        users_with_closed_trades = sum(1 for row in user_pnl_rows if int(row.get("closed", 0) or 0) > 0)

        # ── 2b. Outcome taxonomy + adaptive snapshot ───────────────────
        taxonomy_counts = {
            "strategy_loss": 0,
            "strategy_win": 0,
            "timeout_exit": 0,
            "ops_reconcile": 0,
            "unknown": 0,
        }
        for t in closed_trades:
            oc = classify_outcome_class(t)
            taxonomy_counts[oc] = taxonomy_counts.get(oc, 0) + 1

        strategy_total = taxonomy_counts["strategy_loss"] + taxonomy_counts["strategy_win"]
        strategy_loss_rate_24h = (
            taxonomy_counts["strategy_loss"] / strategy_total * 100
            if strategy_total > 0 else 0.0
        )
        ops_rate_24h = (
            taxonomy_counts["ops_reconcile"] / len(closed_trades) * 100
            if closed_trades else 0.0
        )
        timeout_exits = [t for t in closed_trades if classify_outcome_class(t) == "timeout_exit"]
        timeout_losses = [t for t in timeout_exits if float(t.get("pnl_usdt") or 0) < 0]
        timeout_loss_pnl = sum(float(t.get("pnl_usdt") or 0) for t in timeout_losses)
        timeout_loss_count = len(timeout_losses)
        timeout_loss_rate = (
            timeout_loss_count / len(timeout_exits) * 100
            if timeout_exits else 0.0
        )
        timeout_avg_loss = (
            timeout_loss_pnl / timeout_loss_count if timeout_loss_count > 0 else 0.0
        )
        timeout_protected = [
            t for t in timeout_exits
            if "timeout_protection=applied" in str(t.get("loss_reasoning") or "").lower()
        ]
        timeout_protected_near_flat = [
            t for t in timeout_protected
            if abs(float(t.get("pnl_usdt") or 0)) <= 0.02
        ]
        timeout_protection_effectiveness = (
            len(timeout_protected_near_flat) / len(timeout_protected) * 100
            if timeout_protected else 0.0
        )
        timeout_by_subtype = {
            "trend_scalp": {"count": 0, "negative_count": 0},
            "sideways_scalp": {"count": 0, "negative_count": 0},
        }
        for t in timeout_exits:
            subtype = str(t.get("trade_subtype") or "trend_scalp").strip().lower() or "trend_scalp"
            if subtype not in timeout_by_subtype:
                timeout_by_subtype[subtype] = {"count": 0, "negative_count": 0}
            timeout_by_subtype[subtype]["count"] += 1
            if float(t.get("pnl_usdt") or 0.0) < 0.0:
                timeout_by_subtype[subtype]["negative_count"] += 1

        adaptive = get_adaptive_overrides()
        try:
            refresh_sideways_governor_state()
        except Exception:
            pass
        sideways_governor_snapshot = get_sideways_governor_snapshot()
        try:
            refresh_global_win_playbook_state()
        except Exception:
            pass
        playbook_snapshot = get_win_playbook_snapshot()
        try:
            refresh_global_confidence_adaptation_state()
        except Exception:
            pass
        confidence_adapt_snapshot = get_confidence_adaptation_snapshot()
        now_utc = datetime.now(timezone.utc)
        overlay_pct = float(playbook_snapshot.get("risk_overlay_pct", 0.0) or 0.0)
        effective_risk_min = min(10.0, 0.25 + overlay_pct)
        effective_risk_max = min(10.0, 5.0 + overlay_pct)
        active_tags = playbook_snapshot.get("active_tags", []) or []
        top_tags = [str(t.get("tag")) for t in active_tags[:5]]
        top_tag_context = ", ".join(
            f"{str(t.get('tag'))}(w={float(t.get('weight', 0.0) or 0.0):.3f},n={int(t.get('support', 0) or 0)})"
            for t in active_tags[:3]
        )
        adaptive_decision = str(adaptive.get("decision_reason") or "n/a")
        adaptive_sample = int(adaptive.get("strategy_sample_size", 0) or 0)
        adaptive_freshness = _freshness_label(adaptive.get("updated_at"), now_utc)
        overlay_action = str(playbook_snapshot.get("last_overlay_action") or "hold")
        playbook_freshness = _freshness_label(playbook_snapshot.get("updated_at"), now_utc)
        analysis_rows = []
        try:
            analysis_rows_res = (
                s.table("autotrade_trades")
                .select(
                    "id,symbol,status,close_reason,pnl_usdt,entry_reasons,closed_at,trade_type,timeframe,"
                    "confidence,entry_price,sl_price,qty,quantity,original_quantity,win_reasoning,playbook_match_score"
                )
                .neq("status", "open")
                .order("closed_at", desc=True)
                .limit(2500)
                .execute()
            )
            analysis_rows = analysis_rows_res.data or []
        except Exception as analysis_fetch_err:
            logger.warning(f"[DailyReport] Playbook analysis fetch failed: {analysis_fetch_err}")
        playbook_analysis = build_playbook_analysis(analysis_rows, now_utc=now_utc)
        playbook_analysis_coverage = playbook_analysis.get("coverage") or {}
        playbook_analysis_freshness = _freshness_label(playbook_analysis.get("generated_at"), now_utc)
        playbook_analysis_promote = _format_playbook_clusters_brief(
            list(playbook_analysis.get("promote") or []),
            max_items=3,
        )
        playbook_analysis_avoid = _format_playbook_clusters_brief(
            list(playbook_analysis.get("avoid") or []),
            max_items=3,
        )
        playbook_analysis_wins_reason_pct = float(
            playbook_analysis_coverage.get("wins_with_reasoning_pct", 100.0) or 100.0
        )
        playbook_analysis_tags_pct = float(
            playbook_analysis_coverage.get("closed_with_usable_tags_pct", 0.0) or 0.0
        )
        playbook_analysis_weak_match_pct = float(
            playbook_analysis_coverage.get("weak_or_missing_playbook_match_wins_pct", 100.0) or 100.0
        )
        playbook_analysis_sample_size = int(playbook_analysis.get("sample_size", 0) or 0)
        playbook_analysis_sparse = bool(playbook_analysis.get("sparse_data", True))

        expected_winning_closes = [t for t in closed_trades if _is_expected_winning_close(t)]
        expected_losing_closes = [t for t in closed_trades if _is_expected_losing_close(t)]
        wins_with_reason = [w for w in expected_winning_closes if str(w.get("win_reasoning") or "").strip()]
        losses_with_reason = [l for l in expected_losing_closes if str(l.get("loss_reasoning") or "").strip()]
        win_reason_coverage = (
            len(wins_with_reason) / len(expected_winning_closes) * 100
            if expected_winning_closes else 100.0
        )
        loss_reason_coverage = (
            len(losses_with_reason) / len(expected_losing_closes) * 100
            if expected_losing_closes else 100.0
        )
        missing_win_reason_by_close: dict[str, int] = {}
        for row in expected_winning_closes:
            if str(row.get("win_reasoning") or "").strip():
                continue
            key = _close_reason_key(row)
            missing_win_reason_by_close[key] = missing_win_reason_by_close.get(key, 0) + 1
        missing_loss_reason_by_close: dict[str, int] = {}
        for row in expected_losing_closes:
            if str(row.get("loss_reasoning") or "").strip():
                continue
            key = _close_reason_key(row)
            missing_loss_reason_by_close[key] = missing_loss_reason_by_close.get(key, 0) + 1
        missing_win_reason_summary = _format_missing_reason_map(missing_win_reason_by_close)
        missing_loss_reason_summary = _format_missing_reason_map(missing_loss_reason_by_close)
        playbook_matched_wins = [
            w for w in expected_winning_closes if float(w.get("playbook_match_score") or 0) >= 0.55
        ]
        non_matched_wins = max(0, len(expected_winning_closes) - len(playbook_matched_wins))
        conf_modes = confidence_adapt_snapshot.get("modes") or {}
        conf_swing = conf_modes.get("swing") or {}
        conf_scalp = conf_modes.get("scalping") or {}

        def _fmt_bucket(bucket: dict | None) -> str:
            if not bucket:
                return "-"
            return (
                f"{bucket.get('bucket', '-')} "
                f"(n={int(bucket.get('n', 0) or 0)}, edge={float(bucket.get('edge_adj', 0.0) or 0.0):+.3f}, "
                f"penalty={int(bucket.get('bucket_penalty', 0) or 0)}, "
                f"scale={float(bucket.get('bucket_risk_scale', 1.0) or 1.0):.2f})"
            )

        def _fmt_active(active_rows: list, max_rows: int = 4) -> str:
            rows = list(active_rows or [])[:max_rows]
            if not rows:
                return "-"
            return ", ".join(
                f"{str(r.get('bucket', '-'))}:p{int(r.get('bucket_penalty', 0) or 0)}/s{float(r.get('bucket_risk_scale', 1.0) or 1.0):.2f}"
                for r in rows
            )

        # 7-day trend from closed trades
        since_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        closed_7d_res = s.table("autotrade_trades").select(
            "status, close_reason, pnl_usdt, loss_reasoning"
        ).gte("closed_at", since_7d).neq("status", "open").execute()
        closed_7d = closed_7d_res.data or []
        strategy_7d = [r for r in closed_7d if classify_outcome_class(r) in ("strategy_loss", "strategy_win")]
        strategy_losses_7d = [r for r in strategy_7d if classify_outcome_class(r) == "strategy_loss"]
        strategy_loss_rate_7d = (
            len(strategy_losses_7d) / len(strategy_7d) * 100 if strategy_7d else 0.0
        )
        trades_per_day_7d = (len(strategy_7d) / 7.0) if strategy_7d else 0.0

        # ── 3. New users today ────────────────────────────────────────
        new_users_res = s.table("users").select("telegram_id, first_name, created_at").gte(
            "created_at", since_24h
        ).execute()
        new_users = new_users_res.data or []

        # ── 4. Pending verifications ──────────────────────────────────
        pending_ver_res = s.table("user_verifications").select(
            "telegram_id, status, submitted_at"
        ).eq("status", "pending").execute()
        pending_verifications = pending_ver_res.data or []

        coordinator_pending = {
            "pending_total": 0,
            "pending_with_position": 0,
            "pending_without_position": 0,
            "stale_pending_without_position": 0,
            "pending_ttl_seconds": 90.0,
            "owner_mix_text": "-",
            "top_symbols_text": "-",
            "snapshot_user_count": 0,
        }
        try:
            coordinator = get_coordinator()
            coord_snapshot = await coordinator.export_debug_snapshot()
            coordinator_pending = _summarize_coordinator_pending_snapshot(
                coord_snapshot,
                pending_ttl_seconds=float(getattr(coordinator, "_pending_ttl_seconds", 90.0) or 90.0),
                top_n=5,
            )
        except Exception as coord_err:
            logger.warning(f"[DailyReport] Coordinator pending snapshot failed: {coord_err}")

        # ── 5. Build message ──────────────────────────────────────────
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        pnl_str = _fmt(total_pnl)

        msg = (
            f"📊 <b>CryptoMentor Daily Report</b>\n"
            f"📅 {today_str} | 23:00 WIB\n"
            f"{'─' * 35}\n\n"

            f"👥 <b>USER OVERVIEW</b>\n"
            f"• Total registered users: <b>{total_users}</b>\n"
            f"• New users today: <b>{len(new_users)}</b>\n"
            f"• Pending UID verification: <b>{len(pending_verifications)}</b>\n\n"

            f"⚙️ <b>ENGINE STATUS</b>\n"
            f"• 🟢 Active engines: <b>{len(active_engines)}</b>\n"
            f"• 🔴 Stopped engines: <b>{len(stopped_engines)}</b>\n"
            f"• ⏳ Pending/unverified: <b>{len(pending_engines)}</b>\n\n"

            f"🔐 <b>COORDINATOR PENDING LOCKS (Runtime)</b>\n"
            f"• Pending total: <b>{int(coordinator_pending.get('pending_total', 0) or 0)}</b>\n"
            f"• Pending with open position: <b>{int(coordinator_pending.get('pending_with_position', 0) or 0)}</b>\n"
            f"• Pending without open position: <b>{int(coordinator_pending.get('pending_without_position', 0) or 0)}</b>\n"
            f"• Stale pending without position (> {int(float(coordinator_pending.get('pending_ttl_seconds', 90.0) or 90.0))}s): "
            f"<b>{int(coordinator_pending.get('stale_pending_without_position', 0) or 0)}</b>\n"
            f"• Pending owner mix: <b>{_escape_html(str(coordinator_pending.get('owner_mix_text', '-')))}</b>\n"
            f"• Top pending symbols: <b>{_escape_html(str(coordinator_pending.get('top_symbols_text', '-')))}</b>\n\n"

            f"{pnl_emoji} <b>TRADING (Last 24h)</b>\n"
            f"• Total trades opened: <b>{len(trades_today)}</b>\n"
            f"• Closed trades: <b>{len(closed_trades)}</b>\n"
            f"• Currently open: <b>{len(open_trades)}</b>\n"
            f"• Win rate: <b>{win_rate:.1f}%</b> ({len(wins)}W / {len(losses)}L)\n"
            f"• Total PnL: <b>{pnl_str}</b>\n"
            f"• Profit: <b>+${win_pnl:,.2f}</b> | Loss: <b>-${abs(loss_pnl):,.2f}</b>\n\n"

            f"👤 <b>USER PNL BREAKDOWN (Last 24h)</b>\n"
            f"• Users covered: <b>{len(user_pnl_rows)}</b>\n"
            f"• Users with closed trades: <b>{users_with_closed_trades}</b>\n\n"

            f"🧠 <b>ADAPTIVE CONFLUENCE (24h)</b>\n"
            f"• Strategy outcomes: <b>{strategy_total}</b> "
            f"({taxonomy_counts['strategy_win']}W / {taxonomy_counts['strategy_loss']}L)\n"
            f"• Strategy loss rate: <b>{strategy_loss_rate_24h:.1f}%</b>\n"
            f"• Timeout exits: <b>{taxonomy_counts['timeout_exit']}</b>\n"
            f"• Ops/reconcile closures: <b>{taxonomy_counts['ops_reconcile']}</b> ({ops_rate_24h:.1f}%)\n"
            f"• Timeout losses: <b>{timeout_loss_count}</b> "
            f"({timeout_loss_rate:.1f}% of timeout exits)\n"
            f"• Timeout by subtype: <b>trend={timeout_by_subtype.get('trend_scalp', {}).get('count', 0)}</b> "
            f"(neg {timeout_by_subtype.get('trend_scalp', {}).get('negative_count', 0)}), "
            f"<b>sideways={timeout_by_subtype.get('sideways_scalp', {}).get('count', 0)}</b> "
            f"(neg {timeout_by_subtype.get('sideways_scalp', {}).get('negative_count', 0)})\n"
            f"• Timeout loss PnL: <b>{_fmt(timeout_loss_pnl)}</b> "
            f"(avg <b>{_fmt(timeout_avg_loss)}</b>)\n"
            f"• Timeout protection effectiveness: <b>{timeout_protection_effectiveness:.1f}%</b> "
            f"(near-flat {len(timeout_protected_near_flat)}/{len(timeout_protected)})\n"
            f"• Active thresholds: conf_delta=<b>{int(adaptive.get('conf_delta', 0)):+d}</b>, "
            f"vol_delta=<b>{float(adaptive.get('volume_min_ratio_delta', 0.0)):+.2f}</b>, "
            f"ob_mode=<b>{adaptive.get('ob_fvg_requirement_mode', 'soft')}</b>\n"
            f"• Controller intent: <b>{_escape_html(adaptive_decision)}</b> | "
            f"sample=<b>{adaptive_sample}</b> | freshness=<b>{adaptive_freshness}</b>\n"
            f"• 7-day trend: strategy_loss=<b>{strategy_loss_rate_7d:.1f}%</b>, "
            f"strategy_trades/day=<b>{trades_per_day_7d:.1f}</b>\n\n"

            f"🏆 <b>WIN PLAYBOOK (Global)</b>\n"
            f"• Active tags: <b>{len(active_tags)}</b>"
            + (f" ({', '.join(top_tags)})" if top_tags else "") + "\n"
            f"• Runtime overlay: <b>{overlay_pct:+.2f}%</b>\n"
            f"• Overlay action: <b>{_escape_html(overlay_action)}</b> | "
            f"freshness=<b>{playbook_freshness}</b>\n"
            f"• Effective risk bounds: <b>{effective_risk_min:.2f}% - {effective_risk_max:.2f}%</b>\n"
            f"• Guardrails: win_rate=<b>{float(playbook_snapshot.get('rolling_win_rate', 0.0))*100:.1f}%</b>, "
            f"expectancy=<b>{float(playbook_snapshot.get('rolling_expectancy', 0.0)):+.4f}</b>, "
            f"sample=<b>{int(playbook_snapshot.get('sample_size', 0) or 0)}</b>\n"
            f"• Top-tag context: <b>{_escape_html(top_tag_context or '-')}</b>\n"
            f"• Win-reason coverage: <b>{win_reason_coverage:.1f}%</b> "
            f"({len(wins_with_reason)}/{len(expected_winning_closes)})\n"
            f"• Loss-reason coverage: <b>{loss_reason_coverage:.1f}%</b> "
            f"({len(losses_with_reason)}/{len(expected_losing_closes)})\n"
            f"• Missing win reasons by close: <b>{_escape_html(missing_win_reason_summary)}</b>\n"
            f"• Missing loss reasons by close: <b>{_escape_html(missing_loss_reason_summary)}</b>\n"
            f"• Playbook-matched wins: <b>{len(playbook_matched_wins)}</b> | "
            f"Non-matched wins: <b>{non_matched_wins}</b>\n\n"

            f"📚 <b>PLAYBOOK ANALYZER V2</b>\n"
            f"• Sample size: <b>{playbook_analysis_sample_size}</b> | "
            f"freshness=<b>{playbook_analysis_freshness}</b> | "
            f"sparse=<b>{playbook_analysis_sparse}</b>\n"
            f"• Best working setups: <b>{_escape_html(playbook_analysis_promote)}</b>\n"
            f"• Underperforming setups: <b>{_escape_html(playbook_analysis_avoid)}</b>\n"
            f"• Coverage KPIs: wins_with_reasoning=<b>{playbook_analysis_wins_reason_pct:.1f}%</b> | "
            f"usable_tags=<b>{playbook_analysis_tags_pct:.1f}%</b> | "
            f"weak_or_missing_strong_match=<b>{playbook_analysis_weak_match_pct:.1f}%</b>\n\n"

            f"🎚️ <b>CONFIDENCE ADAPTATION (Global)</b>\n"
            f"• Enabled: <b>{bool(confidence_adapt_snapshot.get('enabled', False))}</b> | "
            f"lookback=<b>{int(confidence_adapt_snapshot.get('lookback_days', 14) or 14)}d</b> | "
            f"min_support=<b>{int(confidence_adapt_snapshot.get('min_support', 30) or 30)}</b>\n"
            f"• Swing sample: <b>{int(conf_swing.get('sample_size', 0) or 0)}</b> | "
            f"top=<b>{_escape_html(_fmt_bucket(conf_swing.get('top_bucket')))}</b> | "
            f"worst=<b>{_escape_html(_fmt_bucket(conf_swing.get('worst_bucket')))}</b>\n"
            f"• Swing active table: <b>{_escape_html(_fmt_active(conf_swing.get('active_adaptations') or []))}</b>\n"
            f"• Scalping sample: <b>{int(conf_scalp.get('sample_size', 0) or 0)}</b> | "
            f"top=<b>{_escape_html(_fmt_bucket(conf_scalp.get('top_bucket')))}</b> | "
            f"worst=<b>{_escape_html(_fmt_bucket(conf_scalp.get('worst_bucket')))}</b>\n"
            f"• Scalping active table: <b>{_escape_html(_fmt_active(conf_scalp.get('active_adaptations') or []))}</b>\n\n"

            f"🧭 <b>SIDEWAYS GOVERNOR (Runtime)</b>\n"
            f"• Mode: <b>{_escape_html(str(sideways_governor_snapshot.get('mode', 'strict')).upper())}</b> | "
            f"basis=<b>{_escape_html(str(sideways_governor_snapshot.get('sample_basis_window', 'bootstrap_strict')))}</b> | "
            f"sample=<b>{int(sideways_governor_snapshot.get('sample_size_basis', 0) or 0)}</b>\n"
            f"• Basis expectancy: <b>{float(sideways_governor_snapshot.get('sideways_expectancy_basis', 0.0) or 0.0):+.4f}</b> | "
            f"timeout-loss rate: <b>{float(sideways_governor_snapshot.get('sideways_timeout_loss_rate_basis', 0.0) or 0.0) * 100:.1f}%</b>\n"
            f"• Sideways fallback enabled: <b>{bool(sideways_governor_snapshot.get('allow_sideways_fallback', False))}</b> | "
            f"recovery windows=<b>{int(sideways_governor_snapshot.get('fallback_recovery_windows', 0) or 0)}</b>\n\n"
        )

        if user_pnl_rows:
            for row in user_pnl_rows:
                uid = int(row.get("telegram_id") or 0)
                status = _escape_html(str(row.get("status") or "n/a"))
                mode = _escape_html(str(row.get("trading_mode") or "-"))
                opened = int(row.get("opened", 0) or 0)
                closed = int(row.get("closed", 0) or 0)
                open_now = int(row.get("open_now", 0) or 0)
                wins_u = int(row.get("wins", 0) or 0)
                losses_u = int(row.get("losses", 0) or 0)
                pnl_u = float(row.get("pnl_usdt", 0.0) or 0.0)
                msg += (
                    f"• <code>{uid}</code> | PnL: <b>{_fmt(pnl_u)}</b> | "
                    f"closed: <b>{closed}</b> ({wins_u}W/{losses_u}L) | "
                    f"opened: <b>{opened}</b> | open_now: <b>{open_now}</b> | "
                    f"status: <b>{status}</b> | mode: <b>{mode}</b>\n"
                )
            msg += "\n"

        # ── 6. Stopped engines with reasoning ────────────────────────
        if stopped_engines:
            msg += f"🔴 <b>STOPPED ENGINES ({len(stopped_engines)})</b>\n"
            for sess in stopped_engines:
                uid = sess.get("telegram_id")
                username = _escape_html(sess.get("username") or f"#{uid}")
                has_keys = _cached_user_keys(uid) is not None
                reason = _engine_stop_reason(sess, has_keys)
                last_update = sess.get("updated_at", "")[:10] if sess.get("updated_at") else "N/A"
                equity = _to_float(sess.get("_equity_value", sess.get("current_balance")), 0.0)
                msg += (
                    f"  • <code>{uid}</code> @{username} — "
                    f"{_escape_html(reason)} | Equity: ${equity:,.2f} "
                    f"(last: {_escape_html(last_update)})\n"
                )
            msg += "\n"

        # ── 7. Active engines summary ─────────────────────────────────
        if active_engines:
            msg += f"🟢 <b>ACTIVE ENGINES ({len(active_engines)})</b>\n"
            for sess in active_engines:
                uid = sess.get("telegram_id")
                mode = _escape_html(sess.get("trading_mode", "scalping").title())
                risk = _to_float(sess.get("risk_per_trade"), 1.0)
                equity = _to_float(sess.get("_equity_value", sess.get("current_balance")), 0.0)
                msg += (
                    f"  • <code>{uid}</code> — {mode} | "
                    f"Risk: {risk:.2f}% | Equity: ${equity:,.2f}\n"
                )
            msg += "\n"

        # ── 8. New users list ─────────────────────────────────────────
        if new_users:
            msg += f"🆕 <b>NEW USERS TODAY</b>\n"
            for u in new_users:
                name = _escape_html(u.get("first_name", "Unknown"))
                uid = u.get("telegram_id", "?")
                msg += f"  • {name} (<code>{uid}</code>)\n"
            msg += "\n"

        # ── 9. Top trades today ───────────────────────────────────────
        if closed_trades:
            top_trades = sorted(closed_trades, key=lambda t: abs(float(t.get("pnl_usdt") or 0)), reverse=True)[:5]
            msg += f"🏆 <b>TOP TRADES TODAY</b>\n"
            for t in top_trades:
                pnl = float(t.get("pnl_usdt") or 0)
                emoji = "✅" if pnl > 0 else "❌"
                symbol = _escape_html(t.get("symbol", "?"))
                side = _escape_html(t.get("side", "?"))
                msg += f"  {emoji} {symbol} {side} — {_fmt(pnl)}\n"
            msg += "\n"

        msg += f"{'─' * 35}\n"
        msg += f"🤖 <i>Auto-generated by CryptoMentor AI</i>"

        # ── 10. Send to all admins ────────────────────────────────────
        admin_ids = _get_admin_ids()
        for admin_id in admin_ids:
            try:
                chunks = _split_message_lines(msg)
                total = len(chunks)
                for idx, chunk in enumerate(chunks, start=1):
                    chunk_text = chunk
                    if total > 1 and idx > 1:
                        chunk_text = (
                            f"📊 <b>CryptoMentor Daily Report (Cont. {idx}/{total})</b>\n\n"
                            f"{chunk}"
                        )
                    await bot.send_message(
                        chat_id=admin_id,
                        text=chunk_text,
                        parse_mode='HTML'
                    )
                logger.info(f"[DailyReport] ✅ Sent to admin {admin_id}")
            except Exception as e:
                logger.error(f"[DailyReport] ❌ Failed to send to admin {admin_id}: {e}")

    except Exception as e:
        logger.error(f"[DailyReport] Critical error: {e}")
        import traceback
        traceback.print_exc()


async def daily_report_task(application):
    """Background task — runs every day at 23:00 WIB."""
    logger.info("[DailyReport] Task started, will send report at 23:00 WIB daily")

    while True:
        try:
            now = datetime.now(TZ_WIB)
            # Calculate seconds until next 23:00 WIB
            target = now.replace(hour=23, minute=0, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)
            wait_seconds = (target - now).total_seconds()

            logger.info(f"[DailyReport] Next report in {wait_seconds / 3600:.1f} hours ({target.strftime('%d %b %Y %H:%M WIB')})")
            await asyncio.sleep(wait_seconds)

            logger.info("[DailyReport] Sending daily analytics report...")
            await send_daily_report(application.bot)

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[DailyReport] Error in task loop: {e}")
            await asyncio.sleep(3600)  # retry in 1 hour on error
