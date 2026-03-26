"""
Auto Trade Handlers for Telegram Bot
API Key user disimpan di Supabase, terenkripsi AES-256-GCM.
"""

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from typing import Optional, Dict
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.crypto import encrypt, decrypt
from app.supabase_repo import _client

# Conversation states
WAITING_API_KEY        = 1
WAITING_API_SECRET     = 2
WAITING_TRADE_AMOUNT   = 3
WAITING_LEVERAGE       = 4
WAITING_NEW_LEVERAGE   = 5
WAITING_BITUNIX_UID    = 6
WAITING_NEW_AMOUNT     = 7

BITUNIX_REFERRAL_URL  = "https://www.bitunix.com/register?vipCode=sq45"
BITUNIX_REFERRAL_CODE = "sq45"


# ------------------------------------------------------------------ #
#  Supabase helpers — user_api_keys                                   #
# ------------------------------------------------------------------ #

def save_user_api_keys(telegram_id: int, api_key: str, api_secret: str):
    """Simpan API key + secret terenkripsi ke Supabase."""
    s = _client()
    row = {
        "telegram_id": int(telegram_id),
        "exchange": "bitunix",
        "api_key": api_key,
        "api_secret_enc": encrypt(api_secret),
        "key_hint": api_key[-4:],
        "updated_at": datetime.utcnow().isoformat(),
    }
    s.table("user_api_keys").upsert(row, on_conflict="telegram_id").execute()


def get_user_api_keys(telegram_id: int) -> Optional[Dict]:
    """Ambil dan dekripsi API keys dari Supabase."""
    s = _client()
    res = s.table("user_api_keys").select("*").eq("telegram_id", int(telegram_id)).limit(1).execute()
    if not res.data:
        return None
    row = res.data[0]
    try:
        secret = decrypt(row["api_secret_enc"])
    except Exception:
        return None
    return {
        "api_key": row["api_key"],
        "api_secret": secret,
        "exchange": row.get("exchange", "bitunix"),
        "created_at": row.get("created_at"),
        "key_hint": row.get("key_hint", row["api_key"][-4:]),
    }


def delete_user_api_keys(telegram_id: int):
    """Hapus API keys dari Supabase."""
    _client().table("user_api_keys").delete().eq("telegram_id", int(telegram_id)).execute()


# ------------------------------------------------------------------ #
#  Supabase helpers — autotrade_sessions                              #
# ------------------------------------------------------------------ #

def _ensure_autotrade_table():
    """Pastikan tabel autotrade_sessions ada (idempotent via upsert)."""
    pass  # dibuat via SQL migration


def get_autotrade_session(telegram_id: int) -> Optional[Dict]:
    s = _client()
    res = s.table("autotrade_sessions").select("*").eq("telegram_id", int(telegram_id)).limit(1).execute()
    return res.data[0] if res.data else None


def save_autotrade_session(telegram_id: int, amount: float, leverage: int = 10):
    s = _client()
    row = {
        "telegram_id": int(telegram_id),
        "initial_deposit": amount,
        "current_balance": amount,
        "total_profit": 0,
        "status": "active",
        "leverage": leverage,
        "started_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    s.table("autotrade_sessions").upsert(row, on_conflict="telegram_id").execute()


def update_autotrade_status(telegram_id: int, status: str):
    s = _client()
    s.table("autotrade_sessions").upsert(
        {"telegram_id": int(telegram_id), "status": status,
         "updated_at": datetime.utcnow().isoformat()},
        on_conflict="telegram_id"
    ).execute()


# ------------------------------------------------------------------ #
#  Conversation: /autotrade entry                                     #
# ------------------------------------------------------------------ #

async def cmd_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keys = get_user_api_keys(user_id)
    session = get_autotrade_session(user_id)
    is_active = session and session.get("status") == "active"

    if keys and is_active:
        from app.autotrade_engine import is_running as engine_running
        engine_on = engine_running(user_id)
        engine_status = "🟢 Engine running" if engine_on else "🟡 Engine inactive"

        # Fetch real balance dari Bitunix
        balance_line = ""
        try:
            import asyncio
            from app.bitunix_autotrade_client import BitunixAutoTradeClient
            acc = await asyncio.wait_for(
                asyncio.to_thread(BitunixAutoTradeClient(
                    api_key=keys['api_key'], api_secret=keys['api_secret']
                ).get_account_info),
                timeout=8.0
            )
            if acc.get('success'):
                balance_line = (
                    f"💳 Bitunix Balance: <b>{acc['available']:.2f} USDT</b>\n"
                    f"📈 Unrealized PnL: <b>{acc['total_unrealized_pnl']:+.2f} USDT</b>\n"
                )
        except Exception:
            balance_line = ""

        engine_btn = (
            [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")]
            if engine_on else
            [InlineKeyboardButton("🔄 Restart Engine", callback_data="at_restart_engine")]
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Status Portfolio",  callback_data="at_status")],
            [InlineKeyboardButton("📈 Trade History",     callback_data="at_history")],
            engine_btn,
            [InlineKeyboardButton("🧠 Bot Skills",        callback_data="skills_menu")],
            [InlineKeyboardButton("⚙️ Settings",          callback_data="at_settings")],
            [InlineKeyboardButton("🔑 Change API Key",    callback_data="at_change_key")],
        ])
        current_leverage = int(session.get("leverage", 10))
        current_margin   = session.get("margin_mode", "cross")
        margin_label     = "Cross ♾️" if current_margin == "cross" else "Isolated 🔒"

        await update.message.reply_text(
            "🤖 <b>Auto Trade Dashboard</b>\n\n"
            "✅ Status: <b>ACTIVE</b>\n\n"
            f"💵 <b>Trading Capital:</b> {session['initial_deposit']} USDT\n"
            f"   <i>(USDT amount used by the bot for trading)</i>\n"
            f"{balance_line}"
            f"📈 Profit: {session['total_profit']:.2f} USDT\n\n"
            f"⚙️ Leverage: <b>{current_leverage}x</b> | Margin: <b>{margin_label}</b>\n"
            f"🔑 API Key: <code>...{keys['key_hint']}</code>\n"
            f"🏦 Exchange: {keys['exchange'].upper()}\n"
            f"⚙️ {engine_status}",
            parse_mode='HTML', reply_markup=keyboard
        )
        return ConversationHandler.END

    elif keys:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Start Trading",   callback_data="at_start_trade")],
            [InlineKeyboardButton("🔑 Change API Key",  callback_data="at_change_key")],
            [InlineKeyboardButton("❌ Delete API Key",  callback_data="at_delete_key")],
        ])
        await update.message.reply_text(
            "🤖 <b>Auto Trade - Bitunix</b>\n\n"
            f"✅ API Key saved: <code>...{keys['key_hint']}</code>\n"
            "⏸ Status: Not active\n\nChoose an action:",
            parse_mode='HTML', reply_markup=keyboard
        )
        return ConversationHandler.END

    else:
        GROUP_URL = "https://t.me/+pKKCinyKUQlhMjk1"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Join CryptoMentor x Bitunix Group", url=GROUP_URL)],
            [InlineKeyboardButton("🔗 Register Bitunix via Referral", url=BITUNIX_REFERRAL_URL)],
            [InlineKeyboardButton("✅ Already Joined & Registered, Continue Setup", callback_data="at_confirm_referral")],
            [InlineKeyboardButton("❓ Why Referral Required?", callback_data="at_why_referral")],
        ])
        await update.message.reply_text(
            "🤖 <b>Auto Trade - Bitunix</b>\n\n"
            "Before starting, there are 2 important steps:\n\n"
            "👥 <b>Step 1 — Join Exclusive Group:</b>\n"
            f"<a href=\"{GROUP_URL}\">CryptoMentor AI x Bitunix</a>\n"
            "There will be many <b>exclusive Bitunix events</b> for CryptoMentor AI users "
            "who have activated AutoTrade. Don't miss out! 🎁\n\n"
            "🔗 <b>Step 2 — Register Bitunix via Referral:</b>\n"
            f"<code>{BITUNIX_REFERRAL_URL}</code>\n"
            f"🎟 Referral Code: <code>{BITUNIX_REFERRAL_CODE}</code>\n\n"
            "Click the button below, then come back here when done.",
            parse_mode='HTML',
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Referral gate & UID verification                                   #
# ------------------------------------------------------------------ #

async def callback_why_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ <b>Why is Referral Required?</b>\n\n"
        "Referral allows us to keep developing this bot for free for you.\n\n"
        "✅ You retain full control over your own Bitunix account\n"
        "✅ Your funds are safe — API Key only has Trade permission, cannot withdraw\n"
        "✅ No additional fees from us\n\n"
        f"🔗 Register now: {BITUNIX_REFERRAL_URL}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Register Now", url=BITUNIX_REFERRAL_URL)],
            [InlineKeyboardButton("✅ Already Registered", callback_data="at_confirm_referral")],
            [InlineKeyboardButton("🔙 Back",               callback_data="at_cancel")],
        ]),
        disable_web_page_preview=True
    )
    return ConversationHandler.END


async def callback_confirm_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User konfirmasi sudah daftar via referral — minta UID Bitunix."""
    query = update.callback_query
    await query.answer()

    # Kalau sudah punya UID tersimpan, skip langsung ke setup key
    user_id = query.from_user.id
    existing_keys = get_user_api_keys(user_id)
    if existing_keys:
        # Sudah pernah setup sebelumnya
        await query.edit_message_text(
            f"✅ <b>Account already registered</b>\n\n"
            f"🔑 API Key: <code>...{existing_keys['key_hint']}</code>\n\n"
            "Continue to trading setup:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start Trading", callback_data="at_start_trade")],
                [InlineKeyboardButton("🔑 Change API Key", callback_data="at_change_key")],
            ])
        )
        return ConversationHandler.END

    # Cek apakah UID sudah tersimpan di session
    uid_saved = _get_saved_uid(user_id)
    if uid_saved:
        session = get_autotrade_session(user_id)
        uid_status = session.get("status", "") if session else ""

        if uid_status == "uid_verified":
            # UID already verified, go straight to API key setup
            await query.edit_message_text(
                f"✅ <b>Bitunix UID verified:</b> <code>{uid_saved}</code>\n\n"
                "Now enter your API Key:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Setup API Key", callback_data="at_setup_key")],
                ])
            )
            return ConversationHandler.END
        elif uid_status == "pending_verification":
            await query.edit_message_text(
                f"⏳ <b>Your UID is being verified by admin</b>\n\n"
                f"🔢 UID: <code>{uid_saved}</code>\n\n"
                "Please wait — you'll receive a notification once verified.",
                parse_mode='HTML'
            )
            return ConversationHandler.END
        elif uid_status == "uid_rejected":
            await query.edit_message_text(
                f"❌ <b>Previous UID was rejected</b>\n\n"
                f"UID <code>{uid_saved}</code> could not be verified.\n\n"
                "Enter a new UID if you've re-registered via referral:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔗 Register via Referral", url=BITUNIX_REFERRAL_URL)],
                    [InlineKeyboardButton("🔄 Enter New UID",         callback_data="at_confirm_referral")],
                ])
            )
            # Reset UID so user can re-enter
            _save_uid(user_id, "", status="pending")
            return ConversationHandler.END

    await query.edit_message_text(
        "✅ <b>Step 1/3 — UID Verification</b>\n\n"
        "Enter your <b>Bitunix UID</b>.\n\n"
        "📍 How to find your UID:\n"
        "Login to Bitunix → tap your profile photo → UID is shown below your name\n\n"
        "Example: <code>123456789</code>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]
        ])
    )
    return WAITING_BITUNIX_UID


async def receive_bitunix_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive Bitunix UID from user, send to admin for verification."""
    uid = update.message.text.strip()
    user_id = update.effective_user.id
    user = update.effective_user

    try:
        await update.message.delete()
    except Exception:
        pass

    # Validate: Bitunix UID is typically a numeric string 5–12 digits
    if not uid.isdigit() or len(uid) < 5:
        await update.message.reply_text(
            "❌ Invalid UID. Bitunix UID is a number (example: <code>123456789</code>).\n\nTry again:",
            parse_mode='HTML'
        )
        return WAITING_BITUNIX_UID

    # Demo users: auto-approve without admin verification
    from app.demo_users import is_demo_user
    if is_demo_user(user_id):
        _save_uid(user_id, uid, status="uid_verified")
        await update.message.reply_text(
            f"✅ <b>UID Verified!</b>\n\n"
            f"🔢 UID: <code>{uid}</code>\n\n"
            "Proceed to setup your API Key:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Setup API Key", callback_data="at_setup_key")],
            ])
        )
        return ConversationHandler.END

    # Save UID to Supabase with pending_verification status
    _save_uid(user_id, uid, status="pending_verification")

    # Notify all admins
    admin_ids = _get_admin_ids()
    username_display = f"@{user.username}" if user.username else f"#{user_id}"
    full_name = user.full_name or "Unknown"

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ APPROVE", callback_data=f"uid_acc_{user_id}"),
            InlineKeyboardButton("❌ REJECT",  callback_data=f"uid_reject_{user_id}"),
        ]
    ])

    admin_text = (
        f"🔔 <b>AutoTrade UID Verification</b>\n\n"
        f"👤 User: <b>{full_name}</b> ({username_display})\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"🔢 Bitunix UID: <code>{uid}</code>\n\n"
        f"Verify that this UID is registered under referral <b>sq45</b> on Bitunix.\n\n"
        f"Approve or reject this user's registration:"
    )

    notified = 0
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode='HTML',
                reply_markup=admin_keyboard
            )
            notified += 1
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to notify admin {admin_id}: {e}")

    # Confirm to user that UID is being verified
    await update.message.reply_text(
        f"⏳ <b>Your UID is being verified</b>\n\n"
        f"🔢 UID: <code>{uid}</code>\n\n"
        "Our admin will verify that your Bitunix account is registered under our referral.\n\n"
        "You'll receive a notification once verification is complete (usually within a few minutes).",
        parse_mode='HTML'
    )
    return ConversationHandler.END


def _save_uid(telegram_id: int, uid: str, status: str = "pending_verification"):
    """Simpan Bitunix UID ke Supabase autotrade_sessions."""
    try:
        _client().table("autotrade_sessions").upsert({
            "telegram_id": int(telegram_id),
            "bitunix_uid": uid,
            "status": status,
            "initial_deposit": 0,
            "current_balance": 0,
            "total_profit": 0,
            "updated_at": datetime.utcnow().isoformat(),
        }, on_conflict="telegram_id").execute()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"_save_uid error: {e}")


def _get_admin_ids() -> list:
    """Ambil semua admin ID dari env vars."""
    import os
    admin_ids = []
    for key in ['ADMIN1', 'ADMIN2', 'ADMIN3', 'ADMIN_IDS']:
        val = os.getenv(key, '')
        if not val:
            continue
        for part in val.split(','):
            part = part.strip()
            if part.isdigit():
                admin_ids.append(int(part))
    return list(set(admin_ids))


def _get_saved_uid(telegram_id: int) -> Optional[str]:
    """Ambil UID yang sudah tersimpan."""
    try:
        res = _client().table("autotrade_sessions").select("bitunix_uid").eq(
            "telegram_id", int(telegram_id)
        ).limit(1).execute()
        if res.data:
            return res.data[0].get("bitunix_uid")
    except Exception:
        pass
    return None


# ------------------------------------------------------------------ #
#  Conversation: input API Key                                        #
# ------------------------------------------------------------------ #

async def callback_setup_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # If key already exists, don't ask for input again — go straight to dashboard
    existing = get_user_api_keys(user_id)
    if existing:
        await query.edit_message_text(
            f"✅ <b>API Key already saved</b>\n\n"
            f"🔑 Key: <code>...{existing['key_hint']}</code>\n"
            f"🏦 Exchange: {existing['exchange'].upper()}\n\n"
            "Use <b>Change API Key</b> if you want to replace it.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start Trading",  callback_data="at_start_trade")],
                [InlineKeyboardButton("🔑 Change API Key", callback_data="at_change_key")],
                [InlineKeyboardButton("❌ Delete API Key", callback_data="at_delete_key")],
            ])
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "🔑 <b>Setup API Key — Step 1/2</b>\n\n"
        "Enter your Bitunix <b>API Key</b> below.\n\n"
        "📖 <b>How to create your API Key:</b>\n"
        "1️⃣ Go to <a href=\"https://www.bitunix.com/account/api-management\">Bitunix API Management</a>\n"
        "2️⃣ Click <b>Create API Key</b>\n"
        "3️⃣ Set a label (e.g. <code>CryptoMentor Bot</code>)\n"
        "4️⃣ Enable permissions: ✅ <b>Trade</b>, ✅ <b>Read</b>\n"
        "5️⃣ <b>Leave IP Address field empty</b> (do not restrict by IP)\n"
        "6️⃣ Copy the <b>API Key</b> and paste it here\n\n"
        "⚠️ Never share your API Key with anyone else.",
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]])
    )
    return WAITING_API_KEY


async def callback_change_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔑 <b>Change API Key — Step 1/2</b>\n\n"
        "Enter your new Bitunix <b>API Key</b> below.\n\n"
        "📖 <b>How to create your API Key:</b>\n"
        "1️⃣ Go to <a href=\"https://www.bitunix.com/account/api-management\">Bitunix API Management</a>\n"
        "2️⃣ Click <b>Create API Key</b>\n"
        "3️⃣ Set a label (e.g. <code>CryptoMentor Bot</code>)\n"
        "4️⃣ Enable permissions: ✅ <b>Trade</b>, ✅ <b>Read</b>\n"
        "5️⃣ <b>Leave IP Address field empty</b> (do not restrict by IP)\n"
        "6️⃣ Copy the <b>API Key</b> and paste it here\n\n"
        "⚠️ Never share your API Key with anyone else.",
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]])
    )
    return WAITING_API_KEY


async def receive_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_key = update.message.text.strip()
    try:
        await update.message.delete()
    except Exception:
        pass

    if len(api_key) < 10:
        await update.message.reply_text("❌ Invalid API Key (min 10 characters). Try again:")
        return WAITING_API_KEY

    context.user_data['temp_api_key'] = api_key
    await update.message.reply_text(
        "✅ API Key received.\n\n"
        "🔐 <b>Step 2/2</b> — Enter your <b>API Secret</b>:\n\n"
        "⚠️ This message will be deleted after processing.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]])
    )
    return WAITING_API_SECRET


async def receive_api_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    api_secret = update.message.text.strip()
    user_id = update.effective_user.id
    try:
        await update.message.delete()
    except Exception:
        pass

    if len(api_secret) < 10:
        await update.message.reply_text("❌ Invalid API Secret. Try again:")
        return WAITING_API_SECRET

    api_key = context.user_data.pop('temp_api_key', None)
    if not api_key:
        await update.message.reply_text("❌ Session expired. Restart with /autotrade")
        return ConversationHandler.END

    # Save encrypted to Supabase
    try:
        save_user_api_keys(user_id, api_key, api_secret)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save API Key: {e}")
        return ConversationHandler.END

    loading = await update.message.reply_text("⏳ <b>Verifying connection...</b>", parse_mode='HTML')

    try:
        import asyncio
        from app.bitunix_autotrade_client import BitunixAutoTradeClient
        client = BitunixAutoTradeClient(api_key=api_key, api_secret=api_secret)
        result = await asyncio.wait_for(
            asyncio.to_thread(client.check_connection),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        result = {'online': False, 'error': 'Timeout: server did not respond within 15 seconds'}
    except Exception as e:
        result = {'online': False, 'error': str(e)}

    if result.get('online'):
        await loading.edit_text(
            "✅ <b>API Key saved and verified!</b>\n\n"
            f"🔑 Key: <code>...{api_key[-4:]}</code>\n"
            "🏦 Exchange: BITUNIX\n"
            "🔒 Secret: encrypted AES-256-GCM\n\n"
            "Ready to start trading:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start Trading", callback_data="at_start_trade")],
            ])
        )
    else:
        err = result.get('error', '')
        if '403' in str(err) or 'TOKEN_INVALID' in str(err):
            msg = (
                "⚠️ <b>API Key saved, but access was denied</b>\n\n"
                "Your API Key has an <b>IP Restriction</b> that is blocking the bot server.\n\n"
                "<b>How to fix (required):</b>\n"
                "1. Login to Bitunix → API Management\n"
                "2. Delete the existing API Key\n"
                "3. Create a new API Key\n"
                "4. In <b>Bind IP Address</b> → <b>LEAVE BLANK</b> (do not enter anything)\n"
                "5. Check permission: ✅ Trade\n"
                "6. Re-setup in this bot\n\n"
                "⚠️ <b>Why must it be blank?</b>\n"
                "The bot server uses dynamic IPs. If a specific IP is set, Bitunix will block all requests from other IPs."
            )
        else:
            msg = (
                f"⚠️ <b>Saved, but verification failed:</b>\n{err}\n\n"
                "Make sure your API Key and Secret are correct, then try again."
            )
        await loading.edit_text(
            msg,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❓ Tutorial",        callback_data="at_howto")],
                [InlineKeyboardButton("🔄 Try Again",       callback_data="at_setup_key")],
                [InlineKeyboardButton("✅ Save Anyway",     callback_data="at_dashboard")],
            ])
        )
    return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Conversation: mulai trading                                        #
# ------------------------------------------------------------------ #

async def callback_start_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not get_user_api_keys(user_id):
        await query.edit_message_text("❌ API Key not found. Use /autotrade to set it up.")
        return ConversationHandler.END

    # Check real balance from Bitunix
    keys = get_user_api_keys(user_id)
    try:
        import asyncio
        from app.bitunix_autotrade_client import BitunixAutoTradeClient
        acc = await asyncio.wait_for(
            asyncio.to_thread(BitunixAutoTradeClient(
                api_key=keys['api_key'], api_secret=keys['api_secret']
            ).get_account_info),
            timeout=10.0
        )
        balance_line = f"\n💳 Available balance: <b>{acc.get('available', 0):.2f} USDT</b>" if acc.get('success') else ""
    except Exception:
        balance_line = ""

    await query.edit_message_text(
        f"💰 <b>Start Auto Trade</b>{balance_line}\n\n"
        "Enter the amount of USDT to trade with:\n\n"
        "📌 Min: 10 USDT | Max: 1000 USDT\n"
        "Example: type <code>50</code>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]])
    )
    context.user_data['at_flow'] = 'start_trade'
    return WAITING_TRADE_AMOUNT


async def receive_trade_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a number. Example: <code>50</code>", parse_mode='HTML')
        return WAITING_TRADE_AMOUNT

    if amount < 10:
        await update.message.reply_text("❌ Minimum 10 USDT.")
        return WAITING_TRADE_AMOUNT
    if amount > 1000:
        await update.message.reply_text("❌ Maximum 1000 USDT.")
        return WAITING_TRADE_AMOUNT

    keys = get_user_api_keys(user_id)
    if not keys:
        await update.message.reply_text("❌ API Key not found. Use /autotrade.")
        return ConversationHandler.END

    context.user_data['trade_amount'] = amount

    # Ask for leverage
    await update.message.reply_text(
        f"⚙️ <b>Select Leverage</b>\n\n"
        f"Capital: <b>{amount} USDT</b>\n\n"
        "Choose a leverage or type a number (1-125):",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("5x",  callback_data="at_lev_5"),
                InlineKeyboardButton("10x", callback_data="at_lev_10"),
                InlineKeyboardButton("20x", callback_data="at_lev_20"),
            ],
            [
                InlineKeyboardButton("50x",  callback_data="at_lev_50"),
                InlineKeyboardButton("75x",  callback_data="at_lev_75"),
                InlineKeyboardButton("100x", callback_data="at_lev_100"),
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")],
        ])
    )
    return WAITING_LEVERAGE


# ------------------------------------------------------------------ #
#  Misc callbacks                                                     #
# ------------------------------------------------------------------ #

async def _show_leverage_preview(update_or_query, context, leverage: int, from_callback: bool):
    """Tampilkan risk/reward preview berdasarkan amount + leverage, minta konfirmasi."""
    amount = context.user_data.get('trade_amount', 0)

    # Contoh kalkulasi dengan asumsi trade 2% move
    notional = amount * leverage
    potential_profit_2pct = notional * 0.02   # TP ~2%
    potential_loss_2pct   = notional * 0.02   # SL ~2%
    liquidation_pct       = round(100 / leverage, 1)

    # Risk level label
    if leverage <= 10:
        risk_label = "🟢 LOW"
        risk_note  = "Suitable for beginners. Low liquidation risk."
    elif leverage <= 25:
        risk_label = "🟡 MEDIUM"
        risk_note  = "Requires good risk management."
    elif leverage <= 50:
        risk_label = "🟠 HIGH"
        risk_note  = "For experienced traders only."
    else:
        risk_label = "🔴 VERY HIGH"
        risk_note  = "Extremely high liquidation risk. Be careful!"

    text = (
        f"📊 <b>Risk/Reward Preview — {leverage}x Leverage</b>\n\n"
        f"💵 Capital: <b>{amount} USDT</b>\n"
        f"📈 Notional value: <b>{notional:.0f} USDT</b>\n\n"
        f"✅ Potential profit (TP ~2%): <b>+{potential_profit_2pct:.2f} USDT</b>\n"
        f"❌ Potential loss (SL ~2%): <b>-{potential_loss_2pct:.2f} USDT</b>\n"
        f"💥 Liquidation if price moves: <b>{liquidation_pct}%</b>\n\n"
        f"⚠️ Risk Level: {risk_label}\n"
        f"📝 {risk_note}\n\n"
        f"Bot will automatically:\n"
        f"• Scan SMC + Order Block signals every minute\n"
        f"• Execute orders with automatic TP & SL\n"
        f"• Notify you on every trade entry\n\n"
        f"Continue with <b>{leverage}x</b>?"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Start with {leverage}x", callback_data=f"at_confirm_trade")],
        [InlineKeyboardButton("🔄 Change Leverage",         callback_data="at_start_trade")],
        [InlineKeyboardButton("❌ Cancel",                  callback_data="at_cancel")],
    ])

    context.user_data['trade_leverage'] = leverage

    if from_callback:
        await update_or_query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    else:
        await update_or_query.reply_text(text, parse_mode='HTML', reply_markup=keyboard)


async def callback_leverage_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tombol leverage 5x/10x/20x/50x/75x/100x."""
    query = update.callback_query
    await query.answer()
    leverage = int(query.data.split("_")[-1])
    await _show_leverage_preview(query, context, leverage, from_callback=True)
    return ConversationHandler.END


async def receive_leverage_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual leverage input (number)."""
    try:
        leverage = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a leverage number. Example: <code>20</code>", parse_mode='HTML')
        return WAITING_LEVERAGE

    if leverage < 1 or leverage > 125:
        await update.message.reply_text("❌ Leverage must be between 1–125.")
        return WAITING_LEVERAGE

    await _show_leverage_preview(update.message, context, leverage, from_callback=False)
    return ConversationHandler.END


async def callback_confirm_trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User konfirmasi — start engine."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    amount   = context.user_data.get('trade_amount')
    leverage = context.user_data.get('trade_leverage', 10)

    if not amount:
        await query.edit_message_text("❌ Session expired. Restart with /autotrade.")
        return ConversationHandler.END

    keys = get_user_api_keys(user_id)
    if not keys:
        await query.edit_message_text("❌ API Key not found.")
        return ConversationHandler.END

    # Check balance before starting
    loading = await query.edit_message_text("⏳ <b>Verifying balance...</b>", parse_mode='HTML')

    try:
        import asyncio
        from app.bitunix_autotrade_client import BitunixAutoTradeClient
        _client = BitunixAutoTradeClient(
            api_key=keys['api_key'], api_secret=keys['api_secret']
        )
        acc = await asyncio.wait_for(
            asyncio.to_thread(_client.get_account_info),
            timeout=15.0
        )
    except asyncio.TimeoutError:
        await loading.edit_text("❌ Timeout while checking balance. Try again.")
        return ConversationHandler.END
    except Exception as e:
        await loading.edit_text(f"❌ Error: {e}")
        return ConversationHandler.END

    if not acc.get('success'):
        err = acc.get('error', '')
        if '403' in str(err) or 'TOKEN_INVALID' in str(err):
            await loading.edit_text(
                "❌ <b>Access denied by Bitunix</b>\n\n"
                "Your API Key has an <b>IP Restriction</b> that is blocking the bot server.\n\n"
                "<b>How to fix:</b>\n"
                "1. Login to Bitunix → API Management\n"
                "2. Delete the existing API Key\n"
                "3. Create a new API Key\n"
                "4. In <b>Bind IP Address</b> → <b>LEAVE BLANK</b>\n"
                "5. Check permission: ✅ Trade\n"
                "6. Re-setup in bot: /autotrade → Change API Key",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❓ Full Tutorial",       callback_data="at_howto")],
                    [InlineKeyboardButton("🔑 Re-setup API Key",    callback_data="at_change_key")],
                ])
            )
        else:
            await loading.edit_text(f"❌ Failed to check balance: {err}", parse_mode='HTML')
        return ConversationHandler.END

    available = acc.get('available', 0)
    if available < amount:
        await loading.edit_text(
            f"❌ <b>Insufficient balance</b>\n\n"
            f"Available: {available:.2f} USDT\n"
            f"Required: {amount} USDT",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    # Save session and start engine
    save_autotrade_session(user_id, amount, leverage)

    # Cek skill dual_tp_rr3 — has_skill sudah otomatis grant ke admin & premium
    from app.skills_repo import has_skill
    _is_premium = has_skill(user_id, "dual_tp_rr3")

    from app.autotrade_engine import start_engine
    start_engine(
        bot=query.get_bot(),
        user_id=user_id,
        api_key=keys['api_key'],
        api_secret=keys['api_secret'],
        amount=amount,
        leverage=leverage,
        notify_chat_id=user_id,
        is_premium=_is_premium,
    )

    await loading.edit_text(
        f"✅ <b>AutoTrade Active!</b>\n\n"
        f"💵 Capital: {amount} USDT\n"
        f"⚙️ Leverage: {leverage}x\n"
        f"🏦 Exchange: BITUNIX\n\n"
        f"Bot is now monitoring the market. You'll receive a notification every time a trade is placed.\n\n"
        f"Use /autotrade to check status or stop.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")],
            [InlineKeyboardButton("📊 Dashboard",      callback_data="at_dashboard")],
        ])
    )
    return ConversationHandler.END


async def callback_status_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan posisi terbuka saat ini dari Bitunix."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keys = get_user_api_keys(user_id)
    if not keys:
        await query.edit_message_text(
            "❌ API Key not set up.\n\nUse /autotrade to set it up.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="at_dashboard")]])
        )
        return

    await query.edit_message_text("⏳ Fetching position data from Bitunix...")

    try:
        import asyncio
        from app.bitunix_autotrade_client import BitunixAutoTradeClient

        client = BitunixAutoTradeClient(api_key=keys['api_key'], api_secret=keys['api_secret'])

        pos_result  = await asyncio.to_thread(client.get_positions)
        acc_result  = await asyncio.to_thread(client.get_account_info)

        back_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="at_status"),
             InlineKeyboardButton("🔙 Back", callback_data="at_dashboard")]
        ])

        if not pos_result.get('success'):
            await query.edit_message_text(
                f"❌ Failed to fetch positions: {pos_result.get('error', 'Unknown error')}",
                reply_markup=back_kb
            )
            return

        positions = pos_result.get('positions', [])
        balance   = acc_result.get('balance', 0) if acc_result.get('success') else 0
        upnl      = acc_result.get('total_unrealized_pnl', 0) if acc_result.get('success') else 0

        from app.autotrade_engine import is_running
        engine_status = "🟢 Active" if is_running(user_id) else "🔴 Inactive"

        lines = [
            f"📊 <b>Portfolio Status</b>",
            f"",
            f"⚙️ Engine: {engine_status}",
            f"💰 Balance: <b>{balance:.2f} USDT</b>",
            f"📈 Unrealized PnL: <b>{upnl:+.2f} USDT</b>",
            f"🔄 Open positions: <b>{len(positions)}</b>",
            f"",
        ]

        if positions:
            lines.append("📋 <b>Active Positions:</b>")
            for p in positions:
                pnl      = p.get('pnl', 0)
                pnl_emoji = "📈" if pnl >= 0 else "📉"
                side_emoji = "🟢" if p.get('side') == 'BUY' else "🔴"
                entry    = p.get('entry_price', 0)
                mark     = p.get('mark_price', 0)
                lev      = p.get('leverage', '-')
                sym      = p.get('symbol', '?').replace('USDT', '')
                pnl_pct  = ((mark - entry) / entry * 100) if entry > 0 else 0
                if p.get('side') == 'SELL':
                    pnl_pct = -pnl_pct

                lines.append(
                    f"\n{side_emoji} <b>{sym}</b> {p.get('side')} {lev}x\n"
                    f"  📍 Entry: <code>{entry:.4f}</code>\n"
                    f"  💹 Mark:  <code>{mark:.4f}</code>\n"
                    f"  📦 Size:  {p.get('size')}\n"
                    f"  {pnl_emoji} PnL: <b>{pnl:+.4f} USDT</b> ({pnl_pct:+.2f}%)"
                )
        else:
            lines.append("💤 <i>No open positions at the moment.</i>")

        from datetime import datetime
        lines.append(f"\n⏱ Updated: {datetime.now().strftime('%H:%M:%S')}")

        await query.edit_message_text(
            "\n".join(lines),
            parse_mode='HTML',
            reply_markup=back_kb
        )

    except Exception as e:
        await query.edit_message_text(
            f"❌ Error: {str(e)[:150]}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="at_dashboard")]])
        )


async def callback_trade_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show trade history from Supabase autotrade_trades table."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="at_history"),
         InlineKeyboardButton("🔙 Back",    callback_data="at_dashboard")]
    ])

    try:
        from app.trade_history import get_trade_history

        trades = get_trade_history(user_id, limit=15)

        if not trades:
            await query.edit_message_text(
                "📈 <b>Trade History</b>\n\n💤 No trade history yet.\n\n"
                "<i>Trades will appear here once the engine executes orders.</i>",
                parse_mode='HTML',
                reply_markup=back_kb
            )
            return

        total_pnl  = 0.0
        wins       = 0
        losses     = 0
        lines      = ["📈 <b>Trade History (last 15)</b>\n"]

        for t in trades:
            side        = t.get("side", "?")
            symbol      = t.get("symbol", "?").replace("USDT", "")
            entry       = t.get("entry_price", 0)
            exit_px     = t.get("exit_price")
            pnl         = t.get("pnl_usdt")
            status      = t.get("status", "open")
            leverage    = t.get("leverage", "-")
            confidence  = t.get("confidence", 0)
            opened_at   = (t.get("opened_at") or "")[:16].replace("T", " ")
            is_flip     = t.get("is_flip", False)
            loss_reason = t.get("loss_reasoning", "")

            side_emoji   = "🟢" if side == "LONG" else "🔴"
            flip_tag     = " 🔄" if is_flip else ""

            if status == "open":
                status_emoji = "⏳"
                pnl_line     = "   ⏳ Position still open"
            elif status in ("closed_tp",):
                status_emoji = "✅"
                pnl_line     = f"   📈 PnL: <b>+{pnl:.4f} USDT</b>"
                wins += 1
                total_pnl += pnl or 0
            elif status in ("closed_sl", "closed_flip"):
                status_emoji = "❌"
                pnl_line     = f"   📉 PnL: <b>{pnl:.4f} USDT</b>"
                if loss_reason:
                    # Show first reason only to keep it compact
                    short_reason = loss_reason.split(" | ")[0] if " | " in loss_reason else loss_reason
                    pnl_line    += f"\n   💡 <i>{short_reason[:80]}</i>"
                losses += 1
                total_pnl += pnl or 0
            else:
                status_emoji = "🔵"
                pnl_line     = f"   PnL: {pnl:.4f} USDT" if pnl is not None else ""

            line = (
                f"{status_emoji} {side_emoji} <b>{symbol}</b> {side}{flip_tag} | {leverage}x\n"
                f"   📍 Entry: <code>{entry:.4f}</code>"
            )
            if exit_px:
                line += f" → Exit: <code>{exit_px:.4f}</code>"
            line += f"\n   🧠 Conf: {confidence}% | {opened_at}"
            line += f"\n{pnl_line}"
            lines.append(line)

        # Summary footer
        total_trades = wins + losses
        win_rate     = round(wins / total_trades * 100) if total_trades > 0 else 0
        pnl_emoji    = "📈" if total_pnl >= 0 else "📉"
        lines.append(
            f"\n━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Closed: {total_trades} | ✅ {wins}W / ❌ {losses}L | WR: {win_rate}%\n"
            f"{pnl_emoji} Total PnL: <b>{total_pnl:+.4f} USDT</b>"
        )

        from datetime import datetime
        lines.append(f"⏱ Updated: {datetime.now().strftime('%H:%M:%S')}")

        await query.edit_message_text(
            "\n\n".join(lines),
            parse_mode='HTML',
            reply_markup=back_kb
        )

    except Exception as e:
        await query.edit_message_text(
            f"❌ Error: {str(e)[:150]}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="at_dashboard")]])
        )


async def callback_stop_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop autotrade engine for this user."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    from app.autotrade_engine import stop_engine, is_running
    if is_running(user_id):
        stop_engine(user_id)
        # Update status in Supabase
        try:
            _client().table("autotrade_sessions").update({
                "status": "stopped",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("telegram_id", user_id).execute()
        except Exception:
            pass
        await query.edit_message_text(
            "🛑 <b>AutoTrade stopped.</b>\n\nUse /autotrade to start again.",
            parse_mode='HTML'
        )
    else:
        await query.edit_message_text(
            "ℹ️ AutoTrade is not currently running.\n\nUse /autotrade to start.",
            parse_mode='HTML'
        )
    return ConversationHandler.END


def _get_server_ip() -> str:
    """Get this server's public IP (Railway/VPS)."""
    try:
        import requests as _req
        r = _req.get("https://api.ipify.org?format=json", timeout=5)
        return r.json().get("ip", "unknown")
    except Exception:
        return "unknown"


async def callback_howto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📖 <b>How to Setup Bitunix API Key</b>\n\n"
        "<b>Steps:</b>\n"
        "1. Login to <a href='https://www.bitunix.com'>bitunix.com</a>\n"
        "2. Click your profile photo → <b>API Management</b>\n"
        "3. Click <b>Create API Key</b>\n"
        "4. Fill in <b>Note</b>: anything (e.g. AutoTrade)\n"
        "5. <b>Purpose</b>: select <b>Trading API</b>\n"
        "6. <b>Bind IP address</b>: ⚠️ <b>MUST BE BLANK</b> — do not enter anything\n"
        "7. <b>Permission</b>: check ✅ <b>Trade</b>\n"
        "8. Click <b>Confirm</b> → verify via email\n"
        "9. Copy your <b>API Key</b> and <b>Secret Key</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🚫 <b>DO NOT fill in Bind IP Address</b>\n\n"
        "The bot server uses dynamic IPs that can change at any time. "
        "If an IP is set, Bitunix will block all requests from other IPs and autotrade won't work.\n\n"
        "✅ <b>Is it safe without IP restriction?</b>\n"
        "Yes — this API key only has <b>Trade</b> permission, "
        "it cannot withdraw funds. Your funds remain safe.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ Secret Key is only shown <b>once</b> — save it before clicking Got it!",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔑 Setup API Key", callback_data="at_setup_key")],
            [InlineKeyboardButton("🌐 Open Bitunix API Management",
                                  url="https://www.bitunix.com/user/api-management")],
        ]),
        disable_web_page_preview=True
    )
    return ConversationHandler.END



async def callback_delete_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⚠️ <b>Delete API Key?</b>\n\nThis will stop auto trading and remove your API Key.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete", callback_data="at_confirm_delete")],
            [InlineKeyboardButton("❌ Cancel",      callback_data="at_cancel")],
        ])
    )
    return ConversationHandler.END


async def callback_confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    delete_user_api_keys(user_id)
    update_autotrade_status(user_id, 'inactive')
    await query.edit_message_text("✅ API Key deleted. Use /autotrade to set up again.")
    return ConversationHandler.END


async def callback_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.pop('temp_api_key', None)
    context.user_data.pop('at_flow', None)
    await query.edit_message_text("❌ Cancelled. Use /autotrade to start again.")
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('temp_api_key', None)
    context.user_data.pop('at_flow', None)
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


async def callback_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    keys = get_user_api_keys(user_id)
    session = get_autotrade_session(user_id)
    is_active = session and session.get("status") == "active"

    if is_active and keys:
        await query.edit_message_text(
            "🤖 <b>Auto Trade Dashboard</b>\n\n"
            "✅ Status: <b>ACTIVE</b>\n"
            f"💰 Deposit: {session['initial_deposit']} USDT\n"
            f"🔑 Key: <code>...{keys['key_hint']}</code>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 Status",    callback_data="at_status")],
                [InlineKeyboardButton("💸 Withdraw",  callback_data="at_withdraw")],
            ])
        )
    else:
        await query.edit_message_text(
            "🤖 <b>Auto Trade</b>\n\n"
            f"✅ API Key: <code>...{keys['key_hint'] if keys else '????'}</code>\n"
            "⏸ Status: Not active",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start Trading", callback_data="at_start_trade")]
            ])
        )
    return ConversationHandler.END


async def callback_restart_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart autotrade engine for this user without restarting the bot."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    keys = get_user_api_keys(user_id)
    session = get_autotrade_session(user_id)

    if not keys or not session or session.get("status") != "active":
        await query.edit_message_text(
            "❌ No active session. Use /autotrade to start.",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    from app.autotrade_engine import start_engine, is_running
    if is_running(user_id):
        await query.answer("✅ Engine is already running!", show_alert=True)
        return ConversationHandler.END

    amount = float(session.get("initial_deposit", 10))
    leverage = int(session.get("leverage", 10))

    from app.skills_repo import has_skill
    _is_premium = has_skill(user_id, "dual_tp_rr3")

    start_engine(
        bot=query.get_bot(),
        user_id=user_id,
        api_key=keys["api_key"],
        api_secret=keys["api_secret"],
        amount=amount,
        leverage=leverage,
        notify_chat_id=user_id,
        is_premium=_is_premium,
    )

    await query.edit_message_text(
        "✅ <b>Engine restarted successfully!</b>\n\n"
        f"💵 Capital: {amount} USDT | ⚙️ Leverage: {leverage}x\n\n"
        "Bot is monitoring the market. Use /autotrade to check status.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Dashboard",      callback_data="at_dashboard")],
            [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")],
        ])
    )
    return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Admin: verifikasi UID user                                         #
# ------------------------------------------------------------------ #

async def callback_uid_acc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin acc UID user — update status dan notifikasi user."""
    query = update.callback_query
    await query.answer("✅ User di-ACC")
    admin_id = query.from_user.id

    # Parse target user_id dari callback data: uid_acc_{user_id}
    target_user_id = int(query.data.split("_")[-1])

    # Update status di Supabase
    try:
        _client().table("autotrade_sessions").update({
            "status": "uid_verified",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("telegram_id", target_user_id).execute()
    except Exception:
        pass

    # Edit pesan admin
    await query.edit_message_text(
        query.message.text + f"\n\n✅ <b>Di-ACC oleh admin</b>",
        parse_mode='HTML'
    )

    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                "✅ <b>Your UID Has Been Verified!</b>\n\n"
                "Your Bitunix account is confirmed under our referral.\n\n"
                "Now set up your API Key to start Auto Trade:"
            ),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Setup API Key", callback_data="at_setup_key")]
            ])
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to notify user {target_user_id}: {e}")


async def callback_uid_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin tolak UID user — update status dan notifikasi user."""
    query = update.callback_query
    await query.answer("❌ User ditolak")

    target_user_id = int(query.data.split("_")[-1])

    # Update status di Supabase
    try:
        _client().table("autotrade_sessions").update({
            "status": "uid_rejected",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("telegram_id", target_user_id).execute()
    except Exception:
        pass

    # Edit pesan admin
    await query.edit_message_text(
        query.message.text + f"\n\n❌ <b>Ditolak oleh admin</b>",
        parse_mode='HTML'
    )

    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                "❌ <b>UID Verification Rejected</b>\n\n"
                "Your Bitunix UID was not detected as registered under our referral.\n\n"
                "Make sure you registered on Bitunix using the following link:\n"
                f"🔗 <code>{BITUNIX_REFERRAL_URL}</code>\n\n"
                "After re-registering with the correct referral, send your new UID with /autotrade."
            ),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Re-register via Referral", url=BITUNIX_REFERRAL_URL)],
                [InlineKeyboardButton("🔄 Try Again", callback_data="at_confirm_referral")],
            ]),
            disable_web_page_preview=True
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to notify user {target_user_id}: {e}")


# ------------------------------------------------------------------ #
#  Settings: leverage & margin mode                                   #
# ------------------------------------------------------------------ #

async def callback_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan menu settings leverage & margin mode."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    session = get_autotrade_session(user_id)
    current_leverage = int(session.get("leverage", 10)) if session else 10
    current_amount   = float(session.get("initial_deposit", 0)) if session else 0
    current_margin   = session.get("margin_mode", "cross") if session else "cross"
    margin_label     = "Cross ♾️" if current_margin == "cross" else "Isolated 🔒"

    # Kalkulasi notional & liquidation untuk preview
    notional       = current_amount * current_leverage
    liquidation_pct = round(100 / current_leverage, 1) if current_leverage > 0 else 100
    if current_leverage <= 10:
        risk_label = "🟢 Low"
    elif current_leverage <= 25:
        risk_label = "🟡 Medium"
    elif current_leverage <= 50:
        risk_label = "🟠 High"
    else:
        risk_label = "🔴 Very High"

    await query.edit_message_text(
        f"⚙️ <b>AutoTrade Settings</b>\n\n"
        f"💵 Trading capital: <b>{current_amount:.0f} USDT</b>\n"
        f"   <i>(from your total Bitunix balance)</i>\n"
        f"📊 Leverage: <b>{current_leverage}x</b>\n"
        f"📈 Notional value: <b>{notional:.0f} USDT</b>\n"
        f"💥 Liquidation if price moves: <b>{liquidation_pct}%</b>\n"
        f"⚠️ Risk level: {risk_label}\n"
        f"💼 Margin mode: <b>{margin_label}</b>\n\n"
        "Select what to change:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Change Trading Capital", callback_data="at_set_amount")],
            [InlineKeyboardButton("📊 Change Leverage",        callback_data="at_set_leverage")],
            [InlineKeyboardButton("💼 Change Margin Mode",     callback_data="at_set_margin")],
            [InlineKeyboardButton("🔙 Back",                   callback_data="at_dashboard")],
        ])
    )
    return ConversationHandler.END


async def callback_set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan form ubah modal trading."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    session = get_autotrade_session(user_id)
    current_amount   = float(session.get("initial_deposit", 0)) if session else 0
    current_leverage = int(session.get("leverage", 10)) if session else 10

    # Cek balance real dari Bitunix
    keys = get_user_api_keys(user_id)
    balance_line = ""
    try:
        import asyncio
        from app.bitunix_autotrade_client import BitunixAutoTradeClient
        acc = await asyncio.wait_for(
            asyncio.to_thread(BitunixAutoTradeClient(
                api_key=keys['api_key'], api_secret=keys['api_secret']
            ).get_account_info),
            timeout=8.0
        )
        if acc.get('success'):
            avail = acc.get('available', 0)
            balance_line = f"💳 Available Bitunix balance: <b>{avail:.2f} USDT</b>\n\n"
    except Exception:
        pass

    await query.edit_message_text(
        f"💰 <b>Change Trading Capital</b>\n\n"
        f"{balance_line}"
        f"Current capital: <b>{current_amount:.0f} USDT</b>\n"
        f"Leverage: <b>{current_leverage}x</b>\n\n"
        f"ℹ️ <b>Trading capital</b> = the amount of USDT from your Bitunix balance the bot uses to open positions.\n"
        f"The larger the capital, the larger the potential profit <i>and</i> loss.\n\n"
        f"Enter new capital amount (USDT):\n"
        f"📌 Min: 10 USDT | Max: 10,000 USDT",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("10",  callback_data="at_newamt_10"),
                InlineKeyboardButton("25",  callback_data="at_newamt_25"),
                InlineKeyboardButton("50",  callback_data="at_newamt_50"),
            ],
            [
                InlineKeyboardButton("100", callback_data="at_newamt_100"),
                InlineKeyboardButton("250", callback_data="at_newamt_250"),
                InlineKeyboardButton("500", callback_data="at_newamt_500"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="at_settings")],
        ])
    )
    return WAITING_NEW_AMOUNT


async def receive_new_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new capital input from text."""
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a number. Example: <code>100</code>", parse_mode='HTML')
        return WAITING_NEW_AMOUNT

    if amount < 10:
        await update.message.reply_text("❌ Minimum 10 USDT.")
        return WAITING_NEW_AMOUNT
    if amount > 10000:
        await update.message.reply_text("❌ Maximum 10,000 USDT.")
        return WAITING_NEW_AMOUNT

    await _apply_new_amount(update.message, update.effective_user.id, amount, context, from_callback=False)
    return ConversationHandler.END


async def callback_new_amount_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tombol preset modal (at_newamt_XX)."""
    query = update.callback_query
    await query.answer()
    amount = float(query.data.split("_")[-1])
    await _apply_new_amount(query, query.from_user.id, amount, context, from_callback=True)
    return ConversationHandler.END


async def _apply_new_amount(msg_or_query, user_id: int, amount: float,
                             context, from_callback: bool):
    """Simpan modal baru ke Supabase + restart engine jika aktif."""
    keys    = get_user_api_keys(user_id)
    session = get_autotrade_session(user_id)
    leverage = int(session.get("leverage", 10)) if session else 10

    # Check if balance is sufficient
    balance_ok = True
    if keys:
        try:
            import asyncio
            from app.bitunix_autotrade_client import BitunixAutoTradeClient
            acc = await asyncio.wait_for(
                asyncio.to_thread(BitunixAutoTradeClient(
                    api_key=keys['api_key'], api_secret=keys['api_secret']
                ).get_account_info),
                timeout=8.0
            )
            if acc.get('success') and acc.get('available', 0) < amount:
                avail = acc.get('available', 0)
                text = (
                    f"❌ <b>Insufficient balance</b>\n\n"
                    f"Available balance: <b>{avail:.2f} USDT</b>\n"
                    f"Requested capital: <b>{amount:.0f} USDT</b>\n\n"
                    "Reduce the capital amount or top up your Bitunix balance."
                )
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="at_set_amount")]])
                if from_callback:
                    await msg_or_query.edit_message_text(text, parse_mode='HTML', reply_markup=kb)
                else:
                    await msg_or_query.reply_text(text, parse_mode='HTML', reply_markup=kb)
                return
        except Exception:
            pass

    # Simpan ke Supabase
    try:
        _client().table("autotrade_sessions").update({
            "initial_deposit": amount,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("telegram_id", user_id).execute()
    except Exception:
        pass

    # Restart engine jika sedang berjalan
    from app.autotrade_engine import is_running, start_engine, stop_engine
    engine_restarted = ""
    if is_running(user_id) and keys and session:
        stop_engine(user_id)
        import asyncio
        await asyncio.sleep(0.5)
        bot = msg_or_query.get_bot() if from_callback else context.bot
        start_engine(
            bot=bot,
            user_id=user_id,
            api_key=keys['api_key'],
            api_secret=keys['api_secret'],
            amount=amount,
            leverage=leverage,
            notify_chat_id=user_id,
        )
        engine_restarted = "\n🔄 Engine restarted with new capital."

    notional = amount * leverage
    liquidation_pct = round(100 / leverage, 1)

    text = (
        f"✅ <b>Trading capital updated to {amount:.0f} USDT</b>\n\n"
        f"📊 Leverage: {leverage}x\n"
        f"📈 Notional value: <b>{notional:.0f} USDT</b>\n"
        f"💥 Liquidation if price moves: <b>{liquidation_pct}%</b>"
        f"{engine_restarted}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings",  callback_data="at_settings")],
        [InlineKeyboardButton("🏠 Dashboard", callback_data="at_dashboard")],
    ])

    if from_callback:
        await msg_or_query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    else:
        await msg_or_query.reply_text(text, parse_mode='HTML', reply_markup=keyboard)


async def callback_set_leverage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show new leverage options."""
    query = update.callback_query
    await query.answer()

    session = get_autotrade_session(query.from_user.id)
    current = int(session.get("leverage", 10)) if session else 10

    await query.edit_message_text(
        f"📊 <b>Change Leverage</b>\n\n"
        f"Current leverage: <b>{current}x</b>\n\n"
        "Choose a new leverage or type a number (1–125):",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("5x",  callback_data="at_newlev_5"),
                InlineKeyboardButton("10x", callback_data="at_newlev_10"),
                InlineKeyboardButton("20x", callback_data="at_newlev_20"),
            ],
            [
                InlineKeyboardButton("50x",  callback_data="at_newlev_50"),
                InlineKeyboardButton("75x",  callback_data="at_newlev_75"),
                InlineKeyboardButton("100x", callback_data="at_newlev_100"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="at_settings")],
        ])
    )
    return WAITING_NEW_LEVERAGE


async def receive_new_leverage_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual leverage input from text."""
    try:
        leverage = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Enter a number. Example: <code>25</code>", parse_mode='HTML')
        return WAITING_NEW_LEVERAGE

    if leverage < 1 or leverage > 125:
        await update.message.reply_text("❌ Leverage must be between 1–125.")
        return WAITING_NEW_LEVERAGE

    await _apply_new_leverage(update.message, update.effective_user.id, leverage, context, from_callback=False)
    return ConversationHandler.END


async def callback_new_leverage_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tombol leverage baru (at_newlev_XX)."""
    query = update.callback_query
    await query.answer()
    leverage = int(query.data.split("_")[-1])
    await _apply_new_leverage(query, query.from_user.id, leverage, context, from_callback=True)
    return ConversationHandler.END


async def _apply_new_leverage(msg_or_query, user_id: int, leverage: int,
                               context, from_callback: bool):
    """Simpan leverage baru ke Supabase + apply ke Bitunix jika engine aktif."""
    from app.bitunix_autotrade_client import BitunixAutoTradeClient
    import asyncio

    keys    = get_user_api_keys(user_id)
    session = get_autotrade_session(user_id)

    # Update di Supabase
    try:
        _client().table("autotrade_sessions").update({
            "leverage": leverage,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("telegram_id", user_id).execute()
    except Exception as e:
        pass

    # Apply to Bitunix for all active symbols
    apply_status = ""
    if keys:
        try:
            client = BitunixAutoTradeClient(api_key=keys['api_key'], api_secret=keys['api_secret'])
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
            margin_mode = session.get("margin_mode", "cross") if session else "cross"
            results = []
            for sym in symbols:
                r = await asyncio.to_thread(client.set_leverage, sym, leverage, margin_mode)
                results.append("✅" if r.get("success") else "⚠️")
            apply_status = f"\n\nApplied to Bitunix: {' '.join(results)}"
        except Exception as e:
            apply_status = f"\n\n⚠️ Failed to apply to Bitunix: {e}"

    # Restart engine with new leverage if running
    from app.autotrade_engine import is_running, start_engine, stop_engine
    engine_restarted = ""
    if is_running(user_id) and keys and session:
        stop_engine(user_id)
        import asyncio
        await asyncio.sleep(0.5)
        bot = msg_or_query.get_bot() if from_callback else context.bot
        start_engine(
            bot=bot,
            user_id=user_id,
            api_key=keys['api_key'],
            api_secret=keys['api_secret'],
            amount=float(session.get("initial_deposit", 10)),
            leverage=leverage,
            notify_chat_id=user_id,
        )
        engine_restarted = "\n🔄 Engine restarted with new leverage."

    text = (
        f"✅ <b>Leverage updated to {leverage}x</b>"
        f"{apply_status}"
        f"{engine_restarted}"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Settings",  callback_data="at_settings")],
        [InlineKeyboardButton("🏠 Dashboard", callback_data="at_dashboard")],
    ])

    if from_callback:
        await msg_or_query.edit_message_text(text, parse_mode='HTML', reply_markup=keyboard)
    else:
        await msg_or_query.reply_text(text, parse_mode='HTML', reply_markup=keyboard)


async def callback_set_margin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan pilihan margin mode."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    session = get_autotrade_session(user_id)
    current = session.get("margin_mode", "cross") if session else "cross"

    cross_check    = "✅ " if current == "cross"    else ""
    isolated_check = "✅ " if current == "isolated" else ""

    await query.edit_message_text(
        f"💼 <b>Change Margin Mode</b>\n\n"
        f"Current mode: <b>{'Cross ♾️' if current == 'cross' else 'Isolated 🔒'}</b>\n\n"
        "<b>Cross Margin</b> — entire balance used as margin, lower liquidation risk.\n"
        "<b>Isolated Margin</b> — margin limited per position, max loss = allocated margin.\n\n"
        "Select mode:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{cross_check}♾️ Cross Margin",       callback_data="at_margin_cross")],
            [InlineKeyboardButton(f"{isolated_check}🔒 Isolated Margin", callback_data="at_margin_isolated")],
            [InlineKeyboardButton("🔙 Back", callback_data="at_settings")],
        ])
    )
    return ConversationHandler.END


async def callback_margin_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Apply margin mode yang dipilih."""
    query = update.callback_query
    await query.answer()
    user_id  = query.from_user.id
    mode     = query.data.split("_")[-1]   # "cross" or "isolated"
    mode_label = "Cross ♾️" if mode == "cross" else "Isolated 🔒"

    keys    = get_user_api_keys(user_id)
    session = get_autotrade_session(user_id)
    leverage = int(session.get("leverage", 10)) if session else 10

    # Simpan ke Supabase
    try:
        _client().table("autotrade_sessions").update({
            "margin_mode": mode,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("telegram_id", user_id).execute()
    except Exception:
        pass

    # Apply to Bitunix
    apply_status = ""
    if keys:
        try:
            import asyncio
            from app.bitunix_autotrade_client import BitunixAutoTradeClient
            client  = BitunixAutoTradeClient(api_key=keys['api_key'], api_secret=keys['api_secret'])
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
            results = []
            for sym in symbols:
                r = await asyncio.to_thread(client.set_leverage, sym, leverage, mode)
                results.append("✅" if r.get("success") else "⚠️")
            apply_status = f"\n\nApplied to Bitunix: {' '.join(results)}"
        except Exception as e:
            apply_status = f"\n\n⚠️ Failed to apply: {e}"

    await query.edit_message_text(
        f"✅ <b>Margin mode updated to {mode_label}</b>"
        f"{apply_status}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Settings",  callback_data="at_settings")],
            [InlineKeyboardButton("🏠 Dashboard", callback_data="at_dashboard")],
        ])
    )
    return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Register handlers                                                  #
# ------------------------------------------------------------------ #

def register_autotrade_handlers(application):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("autotrade", cmd_autotrade),
            CallbackQueryHandler(callback_setup_key,        pattern="^at_setup_key$"),
            CallbackQueryHandler(callback_change_key,       pattern="^at_change_key$"),
            CallbackQueryHandler(callback_start_trade,      pattern="^at_start_trade$"),
            CallbackQueryHandler(callback_set_leverage,     pattern="^at_set_leverage$"),
            CallbackQueryHandler(callback_set_amount,       pattern="^at_set_amount$"),
            CallbackQueryHandler(callback_confirm_referral, pattern="^at_confirm_referral$"),
        ],
        states={
            WAITING_BITUNIX_UID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_bitunix_uid),
                CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
            ],
            WAITING_API_KEY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_key),
                CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
            ],
            WAITING_API_SECRET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_api_secret),
                CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
            ],
            WAITING_TRADE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trade_amount),
                CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
            ],
            WAITING_LEVERAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_leverage_text),
                CallbackQueryHandler(callback_leverage_select, pattern="^at_lev_\\d+$"),
                CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
            ],
            WAITING_NEW_LEVERAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_leverage_text),
                CallbackQueryHandler(callback_new_leverage_select, pattern="^at_newlev_\\d+$"),
                CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
            ],
            WAITING_NEW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_amount),
                CallbackQueryHandler(callback_new_amount_select, pattern="^at_newamt_\\d+$"),
                CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    application.add_handler(conv)
    application.add_handler(CallbackQueryHandler(callback_howto,              pattern="^at_howto$"))
    application.add_handler(CallbackQueryHandler(callback_delete_key,         pattern="^at_delete_key$"))
    application.add_handler(CallbackQueryHandler(callback_confirm_delete,     pattern="^at_confirm_delete$"))
    application.add_handler(CallbackQueryHandler(callback_dashboard,          pattern="^at_dashboard$"))
    application.add_handler(CallbackQueryHandler(callback_confirm_trade,      pattern="^at_confirm_trade$"))
    application.add_handler(CallbackQueryHandler(callback_stop_engine,        pattern="^at_stop_engine$"))
    application.add_handler(CallbackQueryHandler(callback_restart_engine,     pattern="^at_restart_engine$"))
    application.add_handler(CallbackQueryHandler(callback_settings,           pattern="^at_settings$"))
    application.add_handler(CallbackQueryHandler(callback_set_margin,         pattern="^at_set_margin$"))
    application.add_handler(CallbackQueryHandler(callback_margin_select,      pattern="^at_margin_(cross|isolated)$"))
    application.add_handler(CallbackQueryHandler(callback_new_leverage_select,pattern="^at_newlev_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_new_amount_select,  pattern="^at_newamt_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_why_referral,       pattern="^at_why_referral$"))
    application.add_handler(CallbackQueryHandler(callback_uid_acc,            pattern="^uid_acc_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_uid_reject,         pattern="^uid_reject_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_status_portfolio,   pattern="^at_status$"))
    application.add_handler(CallbackQueryHandler(callback_trade_history,      pattern="^at_history$"))

    # Skills handlers
    from app.handlers_skills import register_skills_handlers
    register_skills_handlers(application)

    # at_back_dashboard → redirect ke cmd_autotrade flow
    async def _back_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await callback_dashboard(update, context)

    application.add_handler(CallbackQueryHandler(_back_dashboard, pattern="^at_back_dashboard$"))

    print("✅ AutoTrade handlers registered (Supabase + AES-256-GCM + Engine)")
