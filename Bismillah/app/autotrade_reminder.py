"""
AutoTrade Daily Reminder
Send daily messages to users who haven't registered for autotrade.
"""

import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Reminder messages in English
REMINDER_MESSAGES = [
    # Day 1 - Introduction
    (
        "🤖 <b>Did you know? This bot can do automatic trading for you!</b>\n\n"
        "So far you might have just used manual signals — but there's a more powerful feature:\n\n"
        "⚡ <b>AutoTrade</b> — a bot that manages your exchange account in real-time.\n\n"
        "How it works:\n"
        "• You connect your exchange API key (Binance/Bybit/Bitunix)\n"
        "• Bot analyzes the market 24/7 using AI + SMC indicators\n"
        "• If there's a good setup, bot immediately opens positions automatically\n"
        "• SL/TP managed automatically, you just monitor profits\n\n"
        "💰 Minimum capital can start from <b>10 USDT</b>\n"
        "🔒 Your funds stay on your exchange, bot only has Trade permission\n\n"
        "Want to try? Type /autotrade"
    ),
    # Day 2 - Proof & how it works
    (
        "📊 <b>How does AutoTrade work?</b>\n\n"
        "Your bot connects directly to the exchange via API Key.\n\n"
        "Every second, the bot:\n"
        "1️⃣ Scans 20+ crypto pairs in real-time\n"
        "2️⃣ Analyzes market structure (CHoCH, BOS, S&D Zone)\n"
        "3️⃣ If confidence ≥75%, opens positions automatically\n"
        "4️⃣ Manages SL/TP and trailing stop\n"
        "5️⃣ Sends you notifications for every trade\n\n"
        "You don't need to sit in front of the chart all day.\n"
        "The bot does the work, you get the results. 🎯\n\n"
        "Sign up now: /autotrade"
    ),
    # Day 3 - Security
    (
        "🔒 <b>Is AutoTrade safe?</b>\n\n"
        "A fair question. Here's the answer:\n\n"
        "✅ Your funds <b>stay on the exchange</b> (Binance/Bybit/Bitunix)\n"
        "✅ API Key only has <b>Trade</b> permission — cannot withdraw\n"
        "✅ You can <b>stop anytime</b> with one click\n"
        "✅ API Key encrypted with AES-256 on our server\n"
        "✅ You maintain full control of your exchange account\n\n"
        "Already <b>15+ active users</b> using AutoTrade now.\n\n"
        "Want to join? /autotrade"
    ),
    # Day 4 - Strong CTA
    (
        "🚀 <b>1,200+ users, but only 15 using AutoTrade</b>\n\n"
        "You're one of the majority who hasn't tried it yet.\n\n"
        "But setup is just 3 steps:\n"
        "1. Register an exchange via our referral\n"
        "2. Create API Key (Trade only)\n"
        "3. Enter into bot → choose capital → start!\n\n"
        "⏱ Total setup time: <b>~5 minutes</b>\n\n"
        "After that, the bot works 24/7 for you.\n\n"
        "Start now: /autotrade"
    ),
]


def _get_reminder_index(telegram_id: int, sent_count: int) -> int:
    """Select message based on how many times it has been sent (cycling)."""
    return sent_count % len(REMINDER_MESSAGES)


async def send_autotrade_reminders(bot):
    """
    Send reminders to all users who haven't registered for autotrade.
    Called once daily from the scheduler.
    """
    try:
        from app.supabase_repo import _client
        s = _client()

        # Get all users who DON'T have an active autotrade session
        # Use pagination to bypass Supabase 1000-row limit
        all_users = []
        page_size = 1000
        offset = 0
        while True:
            res = s.table("users").select("telegram_id, first_name").range(offset, offset + page_size - 1).execute()
            batch = res.data or []
            all_users.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size

        if not all_users:
            logger.info("[Reminder] No users found")
            return

        # Get users who already have an autotrade session (exclude them)
        at_res = s.table("autotrade_sessions").select("telegram_id").execute()
        at_user_ids = {row["telegram_id"] for row in (at_res.data or [])}

        # Filter: only users who don't have a session at all
        target_users = [u for u in all_users if u["telegram_id"] not in at_user_ids]

        logger.info(f"[Reminder] Total users: {len(all_users)}, AT users: {len(at_user_ids)}, Targets: {len(target_users)}")
        print(f"[Reminder] Total users: {len(all_users)}, AT users: {len(at_user_ids)}, Targets: {len(target_users)}")

        # Get reminder logs for today to avoid duplicates (with pagination)
        today = datetime.utcnow().date().isoformat()
        sent_today_ids = set()
        offset2 = 0
        while True:
            res2 = s.table("autotrade_reminder_log").select("telegram_id").eq("sent_date", today).range(offset2, offset2 + 999).execute()
            batch2 = res2.data or []
            sent_today_ids.update(row["telegram_id"] for row in batch2)
            if len(batch2) < 1000:
                break
            offset2 += 1000

        # Get total count per user to select the right message (with pagination)
        count_map = {}
        offset3 = 0
        while True:
            res3 = s.table("autotrade_reminder_log").select("telegram_id, count").range(offset3, offset3 + 999).execute()
            batch3 = res3.data or []
            for row in batch3:
                count_map[row["telegram_id"]] = row.get("count", 0)
            if len(batch3) < 1000:
                break
            offset3 += 1000

        sent = 0
        failed = 0
        skipped = 0

        for user in target_users:
            uid = user["telegram_id"]

            # Skip if already sent reminder today
            if uid in sent_today_ids:
                skipped += 1
                continue

            sent_count = count_map.get(uid, 0)
            msg_index = _get_reminder_index(uid, sent_count)
            message = REMINDER_MESSAGES[msg_index]

            try:
                await bot.send_message(
                    chat_id=uid,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=_autotrade_keyboard()
                )

                # Log the send
                _log_reminder_sent(s, uid, today)
                sent += 1

                # Rate limit: don't spam Telegram API
                await asyncio.sleep(0.05)

            except Exception as e:
                err_str = str(e)
                # User blocked bot or invalid — skip
                if any(x in err_str for x in ["blocked", "deactivated", "not found", "chat not found", "Forbidden"]):
                    failed += 1
                else:
                    logger.warning(f"[Reminder] Failed to send to {uid}: {e}")
                    print(f"[Reminder] ❌ Failed uid={uid}: {e}")
                    failed += 1

        logger.info(f"[Reminder] Done: {sent} sent, {skipped} skipped (already sent today), {failed} failed")
        print(f"[Reminder] Done: {sent} sent, {skipped} skipped (already sent today), {failed} failed")

    except Exception as e:
        logger.error(f"[Reminder] Task failed: {e}")
        print(f"[Reminder] ❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


def _autotrade_keyboard():
    """Inline keyboard for reminders."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Register AutoTrade Now", callback_data="at_start_onboarding")],
        [InlineKeyboardButton("ℹ️ Learn More", callback_data="at_learn_more")],
    ])


def _log_reminder_sent(s, telegram_id: int, today: str):
    """Log that a reminder was sent to the user today."""
    try:
        # Check if there's already a record for this user
        existing = s.table("autotrade_reminder_log").select("id, count").eq("telegram_id", telegram_id).limit(1).execute()
        if existing.data:
            row = existing.data[0]
            s.table("autotrade_reminder_log").update({
                "sent_date": today,
                "count": row.get("count", 0) + 1,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", row["id"]).execute()
        else:
            s.table("autotrade_reminder_log").insert({
                "telegram_id": telegram_id,
                "sent_date": today,
                "count": 1,
                "updated_at": datetime.utcnow().isoformat(),
            }).execute()
    except Exception as e:
        logger.warning(f"[Reminder] Failed to log for {telegram_id}: {e}")
