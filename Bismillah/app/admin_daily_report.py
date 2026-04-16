"""
Admin Daily Analytics Report
Sends a comprehensive daily summary to all admins every night at 23:00 UTC+7.
Covers: active engines, trades, PnL, stopped engines with reasoning.
"""

import asyncio
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
        from app.adaptive_confluence import classify_outcome_class, get_adaptive_overrides
        from app.win_playbook import refresh_global_win_playbook_state, get_win_playbook_snapshot

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

        # ── 2. Today's trades ─────────────────────────────────────────
        trades_res = s.table("autotrade_trades").select(
            "telegram_id, symbol, side, pnl_usdt, status, close_reason, loss_reasoning, "
            "win_reasoning, playbook_match_score, effective_risk_pct, risk_overlay_pct, opened_at, closed_at"
        ).gte("opened_at", since_24h).execute()
        trades_today = trades_res.data or []

        closed_trades = [t for t in trades_today if t.get("status", "").startswith("closed")]
        open_trades = [t for t in trades_today if t.get("status") == "open"]

        total_pnl = sum(float(t.get("pnl_usdt") or 0) for t in closed_trades)
        wins = [t for t in closed_trades if float(t.get("pnl_usdt") or 0) > 0]
        losses = [t for t in closed_trades if float(t.get("pnl_usdt") or 0) < 0]
        win_pnl = sum(float(t.get("pnl_usdt") or 0) for t in wins)
        loss_pnl = sum(float(t.get("pnl_usdt") or 0) for t in losses)
        win_rate = (len(wins) / len(closed_trades) * 100) if closed_trades else 0

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

        adaptive = get_adaptive_overrides()
        try:
            refresh_global_win_playbook_state()
        except Exception:
            pass
        playbook_snapshot = get_win_playbook_snapshot()
        overlay_pct = float(playbook_snapshot.get("risk_overlay_pct", 0.0) or 0.0)
        effective_risk_min = min(10.0, 0.25 + overlay_pct)
        effective_risk_max = min(10.0, 5.0 + overlay_pct)
        active_tags = playbook_snapshot.get("active_tags", []) or []
        top_tags = [str(t.get("tag")) for t in active_tags[:5]]
        wins_with_reason = [w for w in wins if str(w.get("win_reasoning") or "").strip()]
        win_reason_coverage = (len(wins_with_reason) / len(wins) * 100) if wins else 0.0
        playbook_matched_wins = [
            w for w in wins if float(w.get("playbook_match_score") or 0) >= 0.55
        ]
        non_matched_wins = max(0, len(wins) - len(playbook_matched_wins))

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

            f"{pnl_emoji} <b>TRADING (Last 24h)</b>\n"
            f"• Total trades opened: <b>{len(trades_today)}</b>\n"
            f"• Closed trades: <b>{len(closed_trades)}</b>\n"
            f"• Currently open: <b>{len(open_trades)}</b>\n"
            f"• Win rate: <b>{win_rate:.1f}%</b> ({len(wins)}W / {len(losses)}L)\n"
            f"• Total PnL: <b>{pnl_str}</b>\n"
            f"• Profit: <b>+${win_pnl:,.2f}</b> | Loss: <b>-${abs(loss_pnl):,.2f}</b>\n\n"

            f"🧠 <b>ADAPTIVE CONFLUENCE (24h)</b>\n"
            f"• Strategy outcomes: <b>{strategy_total}</b> "
            f"({taxonomy_counts['strategy_win']}W / {taxonomy_counts['strategy_loss']}L)\n"
            f"• Strategy loss rate: <b>{strategy_loss_rate_24h:.1f}%</b>\n"
            f"• Timeout exits: <b>{taxonomy_counts['timeout_exit']}</b>\n"
            f"• Ops/reconcile closures: <b>{taxonomy_counts['ops_reconcile']}</b> ({ops_rate_24h:.1f}%)\n"
            f"• Active thresholds: conf_delta=<b>{int(adaptive.get('conf_delta', 0)):+d}</b>, "
            f"vol_delta=<b>{float(adaptive.get('volume_min_ratio_delta', 0.0)):+.2f}</b>, "
            f"ob_mode=<b>{adaptive.get('ob_fvg_requirement_mode', 'soft')}</b>\n"
            f"• 7-day trend: strategy_loss=<b>{strategy_loss_rate_7d:.1f}%</b>, "
            f"strategy_trades/day=<b>{trades_per_day_7d:.1f}</b>\n\n"

            f"🏆 <b>WIN PLAYBOOK (Global)</b>\n"
            f"• Active tags: <b>{len(active_tags)}</b>"
            + (f" ({', '.join(top_tags)})" if top_tags else "") + "\n"
            f"• Runtime overlay: <b>{overlay_pct:+.2f}%</b>\n"
            f"• Effective risk bounds: <b>{effective_risk_min:.2f}% - {effective_risk_max:.2f}%</b>\n"
            f"• Guardrails: win_rate=<b>{float(playbook_snapshot.get('rolling_win_rate', 0.0))*100:.1f}%</b>, "
            f"expectancy=<b>{float(playbook_snapshot.get('rolling_expectancy', 0.0)):+.4f}</b>, "
            f"sample=<b>{int(playbook_snapshot.get('sample_size', 0) or 0)}</b>\n"
            f"• Win-reason coverage: <b>{win_reason_coverage:.1f}%</b> "
            f"({len(wins_with_reason)}/{len(wins) if wins else 0})\n"
            f"• Playbook-matched wins: <b>{len(playbook_matched_wins)}</b> | "
            f"Non-matched wins: <b>{non_matched_wins}</b>\n\n"
        )

        # ── 6. Stopped engines with reasoning ────────────────────────
        if stopped_engines:
            msg += f"🔴 <b>STOPPED ENGINES ({len(stopped_engines)})</b>\n"
            for sess in stopped_engines[:10]:  # max 10 to avoid message too long
                uid = sess.get("telegram_id")
                username = sess.get("username") or f"#{uid}"
                has_keys = get_user_api_keys(uid) is not None
                reason = _engine_stop_reason(sess, has_keys)
                last_update = sess.get("updated_at", "")[:10] if sess.get("updated_at") else "N/A"
                msg += f"  • <code>{uid}</code> @{username} — {reason} (last: {last_update})\n"
            if len(stopped_engines) > 10:
                msg += f"  ... and {len(stopped_engines) - 10} more\n"
            msg += "\n"

        # ── 7. Active engines summary ─────────────────────────────────
        if active_engines:
            msg += f"🟢 <b>ACTIVE ENGINES ({len(active_engines)})</b>\n"
            for sess in active_engines[:8]:
                uid = sess.get("telegram_id")
                mode = sess.get("trading_mode", "scalping").title()
                risk = sess.get("risk_per_trade", 1.0)
                balance = sess.get("current_balance", 0)
                msg += f"  • <code>{uid}</code> — {mode} | Risk: {risk}% | Bal: ${float(balance or 0):,.0f}\n"
            if len(active_engines) > 8:
                msg += f"  ... and {len(active_engines) - 8} more\n"
            msg += "\n"

        # ── 8. New users list ─────────────────────────────────────────
        if new_users:
            msg += f"🆕 <b>NEW USERS TODAY</b>\n"
            for u in new_users[:5]:
                name = u.get("first_name", "Unknown")
                uid = u.get("telegram_id", "?")
                msg += f"  • {name} (<code>{uid}</code>)\n"
            if len(new_users) > 5:
                msg += f"  ... and {len(new_users) - 5} more\n"
            msg += "\n"

        # ── 9. Top trades today ───────────────────────────────────────
        if closed_trades:
            top_trades = sorted(closed_trades, key=lambda t: abs(float(t.get("pnl_usdt") or 0)), reverse=True)[:5]
            msg += f"🏆 <b>TOP TRADES TODAY</b>\n"
            for t in top_trades:
                pnl = float(t.get("pnl_usdt") or 0)
                emoji = "✅" if pnl > 0 else "❌"
                msg += f"  {emoji} {t.get('symbol', '?')} {t.get('side', '?')} — {_fmt(pnl)}\n"
            msg += "\n"

        msg += f"{'─' * 35}\n"
        msg += f"🤖 <i>Auto-generated by CryptoMentor AI</i>"

        # ── 10. Send to all admins ────────────────────────────────────
        admin_ids = _get_admin_ids()
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=msg,
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
