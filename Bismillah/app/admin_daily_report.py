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

        s = _client()
        now_wib = datetime.now(TZ_WIB)
        today_str = now_wib.strftime("%d %b %Y")
        since_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

        # ── 1. All sessions ───────────────────────────────────────────
        all_sessions_res = s.table("autotrade_sessions").select("*").execute()
        all_sessions = all_sessions_res.data or []

        total_users = len([
            sess for sess in all_sessions
            if sess.get("telegram_id") and int(sess.get("telegram_id", 0)) < 999999990
        ])

        active_engines = []
        stopped_engines = []
        pending_engines = []

        for sess in all_sessions:
            uid = sess.get("telegram_id")
            if not uid or int(uid) >= 999999990:
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
            "telegram_id, symbol, side, pnl_usdt, status, opened_at, closed_at"
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
