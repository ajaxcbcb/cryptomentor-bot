"""
Admin handlers for UID verification callbacks.
"""

import logging
import os
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    admin_ids = set()
    for key in ("ADMIN_IDS", "ADMIN1", "ADMIN2", "ADMIN3", "ADMIN_USER_ID", "ADMIN2_USER_ID"):
        raw = os.getenv(key, "")
        for token in str(raw).split(","):
            token = token.strip()
            if token.isdigit():
                admin_ids.add(int(token))
    return user_id in admin_ids


async def callback_uid_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        admin_id = query.from_user.id
        if not _is_admin(admin_id):
            await query.edit_message_text("❌ Unauthorized: admin only.")
            return

        user_id = int(query.data.split("_")[-1])
        now_iso = datetime.now(timezone.utc).isoformat()

        from app.supabase_repo import _client

        s = _client()

        # Fetch existing uid; fallback to legacy table if needed.
        existing = s.table("user_verifications").select("bitunix_uid").eq("telegram_id", user_id).limit(1).execute()
        existing_uid = (existing.data or [{}])[0].get("bitunix_uid")
        if not existing_uid:
            legacy = s.table("autotrade_sessions").select("bitunix_uid").eq("telegram_id", user_id).limit(1).execute()
            existing_uid = (legacy.data or [{}])[0].get("bitunix_uid") or "unknown"

        # Central verification state used by website gatekeeper.
        s.table("user_verifications").upsert(
            {
                "telegram_id": user_id,
                "bitunix_uid": existing_uid,
                "status": "approved",
                "reviewed_at": now_iso,
                "reviewed_by_admin_id": admin_id,
                "updated_at": now_iso,
            },
            on_conflict="telegram_id",
        ).execute()

        # Legacy mirror for existing bot logic that still checks autotrade_sessions.
        s.table("autotrade_sessions").upsert(
            {
                "telegram_id": user_id,
                "status": "uid_verified",
                "updated_at": now_iso,
            },
            on_conflict="telegram_id",
        ).execute()

        from app.lib.auth import generate_dashboard_url

        dash_url = generate_dashboard_url(user_id)
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🌐 Dashboard", url=dash_url)]]
        )
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ <b>UID Verified!</b>\n\nReady to trade.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        await query.edit_message_text(f"✅ Approved User {user_id}")
    except Exception as e:
        logger.error("Error in callback_uid_acc: %s", e)
        await query.edit_message_text(f"❌ Error: {e}")


async def callback_uid_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        admin_id = query.from_user.id
        if not _is_admin(admin_id):
            await query.edit_message_text("❌ Unauthorized: admin only.")
            return

        user_id = int(query.data.split("_")[-1])
        now_iso = datetime.now(timezone.utc).isoformat()

        from app.supabase_repo import _client

        s = _client()

        # Fetch existing uid; fallback to legacy table if needed.
        existing = s.table("user_verifications").select("bitunix_uid").eq("telegram_id", user_id).limit(1).execute()
        existing_uid = (existing.data or [{}])[0].get("bitunix_uid")
        if not existing_uid:
            legacy = s.table("autotrade_sessions").select("bitunix_uid").eq("telegram_id", user_id).limit(1).execute()
            existing_uid = (legacy.data or [{}])[0].get("bitunix_uid") or "unknown"

        # Central verification state used by website gatekeeper.
        s.table("user_verifications").upsert(
            {
                "telegram_id": user_id,
                "bitunix_uid": existing_uid,
                "status": "rejected",
                "reviewed_at": now_iso,
                "reviewed_by_admin_id": admin_id,
                "updated_at": now_iso,
            },
            on_conflict="telegram_id",
        ).execute()

        # Legacy mirror for existing bot logic that still checks autotrade_sessions.
        s.table("autotrade_sessions").upsert(
            {
                "telegram_id": user_id,
                "status": "uid_rejected",
                "updated_at": now_iso,
            },
            on_conflict="telegram_id",
        ).execute()

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ <b>UID Rejected</b>\n\nPlease retry with a valid UID.",
            parse_mode="HTML",
        )
        await query.edit_message_text(f"❌ Rejected User {user_id}")
    except Exception as e:
        logger.error("Error in callback_uid_reject: %s", e)
        await query.edit_message_text(f"❌ Error: {e}")
