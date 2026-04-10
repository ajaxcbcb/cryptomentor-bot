\"\"\"
AutoTrade Handlers - Gatekeeper Mode (Phase 1 Migration)
Redirection flow from Telegram Bot to Web Dashboard.
\"\"\"

import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from typing import Optional, Dict

from app.supabase_repo import get_autotrade_session, save_autotrade_session
from app.lib.auth import generate_dashboard_url

# Conversation states
WAITING_BITUNIX_UID = 6

# Constants
BITUNIX_REFERRAL_URL = "https://www.bitunix.com/register?vipCode=sq45"
PORTFOLIO_STATUS = "portfolio_status"

async def cmd_autotrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Registration logic
    try:
        from app.chat_store import remember_chat
        remember_chat(user_id, update.effective_chat.id)
    except Exception:
        pass

    # Background registration
    import asyncio
    async def _register_user():
        try:
            from app.supabase_repo import upsert_user_with_welcome
            await asyncio.to_thread(upsert_user_with_welcome, user_id, user.username, user.first_name, user.last_name, 100)
        except Exception: pass
    asyncio.create_task(_register_user())

    # 1. Check Verification Status from Supabase
    try:
        session = get_autotrade_session(user_id)
        status = session.get("status", "none") if session else "none"
        uid = session.get("bitunix_uid") if session else None
    except Exception:
        status = "none"
        uid = None

    dash_url = generate_dashboard_url(user_id, user.username, user.first_name)

    # 2. Gatekeeper Logic
    if status == "active" or status == "uid_verified":
        text = (
            f"✅ <b>Identity Verified</b>\n\n"
            f"UID: <code>{uid}</code>\n"
            f"Status: <b>{status.upper()}</b>\n\n"
            f"Your account is verified. You can now manage all trading operations, "
            f"API keys, and risk settings directly from the web dashboard."
        )
        keyboard = [
            [InlineKeyboardButton("🌐 Go to Web Dashboard", url=dash_url)],
            [InlineKeyboardButton("📊 Portfolio Status", callback_data=PORTFOLIO_STATUS)]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        return

    if status == "pending_verification":
        text = (
            f"⏳ <b>Verification Pending</b>\n\n"
            f"UID: <code>{uid}</code>\n\n"
            f"Your UID is currently being verified by our team. "
            f"Once approved, you will be notified here and can start trading on the dashboard."
        )
        keyboard = [[InlineKeyboardButton("🌐 Open Web Dashboard", url=dash_url)]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        return

    # User not yet verified or session missing
    text = (
        f"🚀 <b>Welcome to CryptoMentor AI</b>\n\n"
        f"To start automated trading, you need to verify your account by connecting it to your Bitunix UID.\n\n"
        f"1️⃣ <b>Register on Bitunix</b> (if you haven't)\n"
        f"2️⃣ <b>Submit your UID</b> for verification\n"
        f"3️⃣ <b>Configure API</b> on the Web Dashboard\n\n"
        f"Choose an option below:"
    )
    keyboard = [
        [InlineKeyboardButton("🌐 Register / Open Dashboard", url=dash_url)],
        [InlineKeyboardButton("🆔 Submit UID here", callback_data="submit_uid_bot")],
        [InlineKeyboardButton("🔗 Register on Bitunix", url=BITUNIX_REFERRAL_URL)]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')


# ------------------------------------------------------------------ #
#  UID Submission Flow (Manual via Bot)                               #
# ------------------------------------------------------------------ #

async def handle_submit_uid_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "📝 <b>Submit Bitunix UID</b>\n\n"
        "Please enter your Bitunix UID (numbers only).\n\n"
        "<i>Note: If you don't have one, please register using the link in the previous menu first.</i>",
        parse_mode='HTML'
    )
    return WAITING_BITUNIX_UID


async def process_uid_input_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.text.strip()
    user_id = update.effective_user.id
    
    if not uid.isdigit():
        await update.message.reply_text("❌ UID must be numbers only. Please try again:")
        return WAITING_BITUNIX_UID
        
    try:
        from app.supabase_repo import _client
        s = _client()
        s.table("autotrade_sessions").upsert({
            "telegram_id": user_id,
            "bitunix_uid": uid,
            "status": "pending_verification",
            "updated_at": datetime.utcnow().isoformat()
        }, on_conflict="telegram_id").execute()
        
        await notify_admins_of_uid(context.bot, user_id, uid)
        
        dash_url = generate_dashboard_url(user_id, update.effective_user.username, update.effective_user.first_name)
        
        await update.message.reply_text(
            f"✅ <b>UID Submitted!</b>\n\n"
            f"UID: <code>{uid}</code>\n"
            f"Status: <b>PENDING VERIFICATION</b>\n\n"
            f"We will verify your UID and notify you shortly. In the meantime, "
            f"you can explore the Web Dashboard.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Open Dashboard", url=dash_url)]]),
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error saving UID: {e}")
        
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


async def callback_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Operation cancelled.")
    return ConversationHandler.END


async def notify_admins_of_uid(bot, user_id: int, uid: str):
    admin_ids = []
    for key in ['ADMIN_IDS', 'ADMIN1', 'ADMIN2', 'ADMIN_USER_ID', 'ADMIN2_USER_ID']:
        val = os.getenv(key)
        if val:
            for part in val.split(','):
                part = part.strip()
                if part.isdigit(): admin_ids.append(int(part))
    
    msg = (
        f"🔔 <b>New UID Verification Request</b>\n\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Bitunix UID: <code>{uid}</code>\n\n"
        f"Approving this will allow the user to start trading on the dashboard."
    )
    for aid in set(admin_ids):
        try: await bot.send_message(chat_id=aid, text=msg, parse_mode='HTML')
        except Exception: pass





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
        query.message.text + f"\n\n✅ <b>Approved by admin</b>",
        parse_mode='HTML'
    )

    # Notify user — send dashboard link after approval
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=(
                "✅ <b>Your UID Has Been Verified!</b>\n\n"
                "Now complete your setup on the dashboard:\n"
                "• Connect your Bitunix API Key\n"
                "• Configure risk settings\n"
                "• Start trading\n"
            ),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌐 Open Dashboard", url=WEB_DASHBOARD_URL)]
            ])
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to notify user {target_user_id}: {e}")


async def callback_uid_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin tolak UID user — update status dan notifikasi user."""
    query = update.callback_query
    await query.answer("❌ User rejected")

    target_user_id = int(query.data.split("_")[-1])

    try:
        _client().table("autotrade_sessions").update({
            "status": "uid_rejected",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("telegram_id", target_user_id).execute()
    except Exception:
        pass

    await query.edit_message_text(
        query.message.text + f"\n\n❌ <b>Rejected by admin</b>",
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
    
    # Get risk mode and risk per trade
    risk_mode = get_risk_mode(user_id)
    current_risk = get_risk_per_trade(user_id)

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

    # Build header with section_header
    header = section_header("AUTOTRADE SETTINGS", "⚙️")
    
    # Build mode-specific display
    if risk_mode == "risk_based":
        # Get auto mode status
        auto_mode_enabled = session.get("auto_mode_enabled", True) if session else True
        auto_mode_status = "✅ ON" if auto_mode_enabled else "❌ OFF"
        
        # Status section - simplified for risk-based mode
        status_section = settings_group(
            title="CURRENT STATUS",
            emoji="📊",
            items=[
                f"Mode: 🎯 Rekomendasi (Risk Per Trade)",
                f"Balance: <b>${current_amount:.0f} USDT</b>",
                f"Risk per trade: <b>{current_risk}%</b>",
                f"Risk level: {risk_label}",
                f"Auto Mode Switch: {auto_mode_status}",
                f"",
                f"<i>✨ Leverage & Margin dihitung otomatis oleh sistem</i>",
            ],
            show_divider=False
        )
        
        mode_text = (
            f"{header}\n"
            f"{status_section}\n"
            "💡 <b>Sistem otomatis menghitung:</b>\n"
            f"   • Leverage: <code>{current_leverage}x</code> (rekomendasi)\n"
            f"   • Margin mode: <code>{margin_label}</code>\n"
            f"   • Position size berdasarkan risk % & SL distance\n\n"
            "Select what to change:"
        )
        keyboard = [
            [InlineKeyboardButton("🎯 Change Risk %", callback_data="at_risk_settings")],
            [InlineKeyboardButton(f"🤖 Auto Mode: {auto_mode_status}", callback_data="at_toggle_auto_mode")],
            [InlineKeyboardButton("🔄 Switch to Manual Mode", callback_data="at_switch_risk_mode")],
            [InlineKeyboardButton("🔙 Back", callback_data="at_dashboard")],
        ]
    else:
        # Get auto mode status
        auto_mode_enabled = session.get("auto_mode_enabled", True) if session else True
        auto_mode_status = "✅ ON" if auto_mode_enabled else "❌ OFF"
        
        # Status section for manual mode
        status_section = settings_group(
            title="CURRENT STATUS",
            emoji="📊",
            items=[
                f"Mode: ⚙️ Manual (Fixed Margin)",
                f"Margin per trade: <b>${current_amount:.0f} USDT</b>",
                f"Leverage: <b>{current_leverage}x</b>",
                f"Notional: <b>${notional:.0f} USDT</b>",
                f"Liquidation: <b>{liquidation_pct}%</b> move",
                f"Risk level: {risk_label}",
                f"Margin mode: <b>{margin_label}</b>",
                f"Auto Mode Switch: {auto_mode_status}",
            ],
            show_divider=False
        )
        
        mode_text = (
            f"{header}\n"
            f"{status_section}\n"
            "💡 Position size tetap fixed per trade\n\n"
            "Select what to change:"
        )
        keyboard = [
            [InlineKeyboardButton("💰 Change Margin", callback_data="at_set_amount")],
            [InlineKeyboardButton("📊 Change Leverage", callback_data="at_set_leverage")],
            [InlineKeyboardButton("💼 Change Margin Mode", callback_data="at_set_margin")],
            [InlineKeyboardButton(f"🤖 Auto Mode: {auto_mode_status}", callback_data="at_toggle_auto_mode")],
            [InlineKeyboardButton("🔄 Switch to Rekomendasi Mode", callback_data="at_switch_risk_mode")],
            [InlineKeyboardButton("🔙 Back", callback_data="at_dashboard")],
        ]

    await query.edit_message_text(
        mode_text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END


async def callback_set_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan form ubah modal trading."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Check risk mode - block for risk-based mode
    risk_mode = get_risk_mode(user_id)
    
    if risk_mode == "risk_based":
        await query.edit_message_text(
            "❌ <b>Tidak Tersedia untuk Mode Rekomendasi</b>\n\n"
            "Dalam mode Rekomendasi, sistem otomatis menghitung margin dari balance Anda.\n\n"
            "💡 <b>Yang bisa Anda ubah:</b>\n"
            "• Risk per trade (1%, 2%, 3%)\n\n"
            "Jika ingin kontrol margin manual, switch ke Manual Mode.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="at_settings")]
            ])
        )
        return ConversationHandler.END

    session = get_autotrade_session(user_id)
    current_amount   = float(session.get("initial_deposit", 0)) if session else 0
    current_leverage = int(session.get("leverage", 10)) if session else 10

    # Cek balance real dari exchange (timeout pendek, non-blocking)
    keys = get_user_api_keys(user_id)
    balance_line = ""
    try:
        import asyncio
        from app.exchange_registry import get_client as _get_client
        exchange_id = keys.get("exchange", "bitunix") if keys else "bitunix"
        _ex_c = _get_client(exchange_id, keys['api_key'], keys['api_secret'])
        acc = await asyncio.wait_for(
            asyncio.to_thread(_ex_c.get_account_info),
            timeout=3.0
        )
        if acc.get('success'):
            avail = acc.get('available', 0)
            balance_line = f"💳 Available balance: <b>{avail:.2f} USDT</b>\n\n"
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


async def receive_manual_margin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual margin input for manual mode during registration."""
    if not context.user_data.get('awaiting_manual_margin'):
        return ConversationHandler.END
    
    try:
        margin = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka yang valid (contoh: 10)", parse_mode='HTML')
        return WAITING_MANUAL_MARGIN
    
    if margin <= 0:
        await update.message.reply_text("❌ Margin harus lebih dari 0")
        return WAITING_MANUAL_MARGIN
    
    if margin > 10000:
        await update.message.reply_text("❌ Maximum 10,000 USDT")
        return WAITING_MANUAL_MARGIN
    
    user_id = update.effective_user.id
    
    # Save margin to context
    context.user_data['trade_amount'] = margin
    context.user_data['awaiting_manual_margin'] = False
    
    # Show leverage selection
    await update.message.reply_text(
        f"⚙️ <b>Select Leverage</b>\n\n"
        f"Margin: <b>{margin} USDT</b>\n\n"
        "Choose a leverage:",
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
            [InlineKeyboardButton("« Kembali", callback_data="at_choose_risk_mode")],
        ])
    )
    return WAITING_LEVERAGE


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
            from app.exchange_registry import get_client as _get_client, get_exchange as _get_exchange
            exchange_id = keys.get("exchange", "bitunix")
            ex_cfg2 = _get_exchange(exchange_id)
            acc = await asyncio.wait_for(
                asyncio.to_thread(_get_client(exchange_id, keys['api_key'], keys['api_secret']).get_account_info),
                timeout=3.0
            )
            if acc.get('success') and acc.get('available', 0) < amount:
                avail = acc.get('available', 0)
                text = (
                    f"❌ <b>Insufficient balance</b>\n\n"
                    f"Available balance: <b>{avail:.2f} USDT</b>\n"
                    f"Requested capital: <b>{amount:.0f} USDT</b>\n\n"
                    f"Reduce the capital amount or top up your {ex_cfg2.get('name', 'exchange')} balance."
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
        exchange_id = keys.get("exchange", "bitunix")
        start_engine(
            bot=bot,
            user_id=user_id,
            api_key=keys['api_key'],
            api_secret=keys['api_secret'],
            amount=amount,
            leverage=leverage,
            notify_chat_id=user_id,
            exchange_id=exchange_id,
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
    user_id = query.from_user.id
    
    # Check risk mode - block for risk-based mode
    risk_mode = get_risk_mode(user_id)
    
    if risk_mode == "risk_based":
        await query.edit_message_text(
            "❌ <b>Tidak Tersedia untuk Mode Rekomendasi</b>\n\n"
            "Dalam mode Rekomendasi, leverage fixed <b>10x</b> (optimal untuk risk management).\n\n"
            "💡 <b>Yang bisa Anda ubah:</b>\n"
            "• Risk per trade (1%, 2%, 3%)\n\n"
            "Jika ingin kontrol leverage manual, switch ke Manual Mode.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="at_settings")]
            ])
        )
        return ConversationHandler.END

    session = get_autotrade_session(user_id)
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
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT", "ATOMUSDT", "XAUUSDT", "CLUSDT", "QQQUSDT"]
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
        exchange_id = keys.get("exchange", "bitunix")
        start_engine(
            bot=bot,
            user_id=user_id,
            api_key=keys['api_key'],
            api_secret=keys['api_secret'],
            amount=float(session.get("initial_deposit", 10)),
            leverage=leverage,
            notify_chat_id=user_id,
            exchange_id=exchange_id,
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
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT", "ATOMUSDT", "XAUUSDT", "CLUSDT", "QQQUSDT"]
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
#  Auto Mode Switcher Toggle                                          #
# ------------------------------------------------------------------ #

async def callback_toggle_auto_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto mode switching on/off"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    try:
        from app.supabase_repo import _client
        s = _client()
        
        # Get current status
        result = s.table("autotrade_sessions").select("auto_mode_enabled").eq(
            "telegram_id", int(user_id)
        ).limit(1).execute()
        
        current_status = True  # Default ON
        if result.data:
            current_status = result.data[0].get("auto_mode_enabled", True)
        
        # Toggle status
        new_status = not current_status
        
        # Update database
        s.table("autotrade_sessions").upsert({
            "telegram_id": int(user_id),
            "auto_mode_enabled": new_status
        }, on_conflict="telegram_id").execute()
        
        status_text = "✅ ENABLED" if new_status else "❌ DISABLED"
        emoji = "🤖" if new_status else "⚠️"
        
        message = (
            f"{emoji} <b>Auto Mode Switcher {status_text}</b>\n\n"
        )
        
        if new_status:
            message += (
                "✅ <b>Auto Mode is now ON</b>\n\n"
                "📊 System will automatically:\n"
                "• Detect market sentiment every 15 minutes\n"
                "• Switch to SCALPING when market is sideways\n"
                "• Switch to SWING when market is trending\n"
                "• Notify you when mode changes\n\n"
                "💡 This ensures you always use the optimal strategy "
                "for current market conditions.\n\n"
                "🎯 <b>Benefits:</b>\n"
                "• More trading opportunities\n"
                "• Better risk-adjusted returns\n"
                "• No manual mode switching needed"
            )
        else:
            message += (
                "⚠️ <b>Auto Mode is now OFF</b>\n\n"
                "You will stay in your current trading mode until you manually change it.\n\n"
                "💡 Enable auto mode to let the system automatically "
                "switch between scalping and swing based on market conditions."
            )
        
        await query.edit_message_text(
            message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="at_settings")],
                [InlineKeyboardButton("🏠 Dashboard", callback_data="at_dashboard")],
            ])
        )
        
        logger.info(f"[AutoMode:{user_id}] Toggled: {current_status} → {new_status}")
        
    except Exception as e:
        logger.error(f"[AutoMode:{user_id}] Toggle failed: {e}")
        await query.edit_message_text(
            "❌ Failed to toggle auto mode. Please try again.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="at_settings")]
            ])
        )
    
    return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Risk Management Settings (Professional Money Management)           #
# ------------------------------------------------------------------ #

async def callback_risk_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show risk management settings menu"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    from app.supabase_repo import get_risk_per_trade
    from app.position_sizing import format_risk_info, get_recommended_risk
    
    # Get current settings
    session = get_autotrade_session(user_id)
    current_risk = get_risk_per_trade(user_id)
    current_amount = float(session.get("initial_deposit", 0)) if session else 0
    
    # Get balance from exchange
    keys = get_user_api_keys(user_id)
    balance = current_amount  # fallback
    if keys:
        try:
            import asyncio
            from app.exchange_registry import get_client as _get_client
            exchange_id = keys.get("exchange", "bitunix")
            _ex_c = _get_client(exchange_id, keys['api_key'], keys['api_secret'])
            acc = await asyncio.wait_for(
                asyncio.to_thread(_ex_c.get_account_info),
                timeout=3.0
            )
            if acc.get('success'):
                balance = acc.get('available', current_amount)
        except Exception:
            pass
    
    # Format risk info
    risk_info = format_risk_info(balance, current_risk)
    recommended = get_recommended_risk(balance)
    
    # Check marks for current selection
    check_1 = "✅ " if current_risk == 1.0 else ""
    check_2 = "✅ " if current_risk == 2.0 else ""
    check_3 = "✅ " if current_risk == 3.0 else ""
    check_5 = "✅ " if current_risk == 5.0 else ""
    
    await query.edit_message_text(
        f"🎯 <b>Risk Management Settings</b>\n\n"
        f"💰 Current Balance: <b>${balance:.2f}</b>\n"
        f"{risk_info}\n"
        f"💡 Recommended for your balance: <b>{recommended}%</b>\n\n"
        f"<b>What is Risk Per Trade?</b>\n"
        f"Instead of fixed margin, you choose how much % of your balance to risk per trade. "
        f"This enables safe compounding and protects your account.\n\n"
        f"<b>Example:</b> Balance $100, Risk 2%\n"
        f"• Max loss per trade: $2\n"
        f"• Position size auto-calculated based on stop loss\n"
        f"• As balance grows, position size grows too\n\n"
        f"Select your risk level:",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(f"{check_1}🛡️ 1%", callback_data="at_set_risk_1"),
                InlineKeyboardButton(f"{check_2}⚖️ 2%", callback_data="at_set_risk_2"),
            ],
            [
                InlineKeyboardButton(f"{check_3}⚡ 3%", callback_data="at_set_risk_3"),
                InlineKeyboardButton(f"{check_5}🔥 5%", callback_data="at_set_risk_5"),
            ],
            [InlineKeyboardButton("📚 Learn More", callback_data="at_risk_edu")],
            [InlineKeyboardButton("🧮 Simulator", callback_data="at_risk_sim")],
            [InlineKeyboardButton("🔙 Back", callback_data="at_settings")],
        ])
    )
    return ConversationHandler.END


async def callback_set_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Apply selected risk percentage"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Extract risk percentage from callback data
    risk_map = {
        "at_set_risk_1": 1.0,
        "at_set_risk_2": 2.0,
        "at_set_risk_3": 3.0,
        "at_set_risk_5": 5.0,
    }
    
    risk_pct = risk_map.get(query.data, 2.0)
    
    # Save to database
    from app.supabase_repo import set_risk_per_trade
    result = set_risk_per_trade(user_id, risk_pct)
    
    if not result['success']:
        await query.edit_message_text(
            f"❌ <b>Failed to update risk setting</b>\n\n"
            f"Error: {result['error']}\n\n"
            f"Please try again or contact support.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="at_risk_settings")],
            ])
        )
        return ConversationHandler.END
    
    # Get balance for display
    session = get_autotrade_session(user_id)
    current_amount = float(session.get("initial_deposit", 0)) if session else 0
    risk_amount = current_amount * (risk_pct / 100)
    
    # Determine risk level label
    if risk_pct <= 1.0:
        level = "Conservative 🛡️"
    elif risk_pct <= 2.0:
        level = "Moderate ⚖️"
    elif risk_pct <= 3.0:
        level = "Aggressive ⚡"
    else:
        level = "Very Aggressive 🔥"
    
    # Check if engine is running - if yes, notify user to restart
    from app.autotrade_engine import is_running as engine_running
    engine_on = engine_running(user_id)
    restart_note = ""
    if engine_on:
        restart_note = (
            "\n\n⚠️ <b>Important:</b> Your AutoTrade engine is currently running. "
            "The new risk setting will apply to <b>new trades only</b>. "
            "Existing positions are not affected."
        )
    
    await query.edit_message_text(
        f"✅ <b>Risk Setting Updated!</b>\n\n"
        f"Risk per trade: <b>{risk_pct}%</b>\n"
        f"Risk level: <b>{level}</b>\n"
        f"Max loss per trade: <b>${risk_amount:.2f}</b>\n\n"
        f"Your position sizes will now be calculated automatically based on:\n"
        f"• Your current balance\n"
        f"• Risk percentage ({risk_pct}%)\n"
        f"• Stop loss distance\n\n"
        f"This enables safe compounding as your balance grows! 📈"
        f"{restart_note}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Settings", callback_data="at_settings")],
            [InlineKeyboardButton("🏠 Dashboard", callback_data="at_dashboard")],
        ])
    )
    return ConversationHandler.END


async def callback_risk_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show risk management education"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📚 <b>Risk Per Trade Education</b>\n\n"
        "<b>Why Risk % Instead of Fixed Margin?</b>\n\n"
        "❌ <b>Fixed Margin Problem:</b>\n"
        "• Balance $100, trade $10 = 10% risk\n"
        "• Balance grows to $200, still trade $10 = 5% risk\n"
        "• Balance drops to $50, still trade $10 = 20% risk!\n"
        "• Can't compound gains, high risk when losing\n\n"
        "✅ <b>Risk % Solution:</b>\n"
        "• Always risk same % regardless of balance\n"
        "• Position size grows with balance (compound)\n"
        "• Position size shrinks when losing (protection)\n"
        "• Professional money management\n\n"
        "<b>Example: 2% Risk</b>\n\n"
        "Balance $100:\n"
        "• Risk: $2 per trade\n"
        "• 50 consecutive losses to blow account\n\n"
        "Balance grows to $150:\n"
        "• Risk: $3 per trade (auto-adjusted)\n"
        "• Still 50 consecutive losses to blow\n\n"
        "Balance drops to $80:\n"
        "• Risk: $1.60 per trade (protected)\n"
        "• Still 50 consecutive losses to blow\n\n"
        "<b>Key Benefits:</b>\n"
        "✅ Safe compounding\n"
        "✅ Account protection\n"
        "✅ Consistent risk\n"
        "✅ Professional approach",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="at_risk_settings")],
        ])
    )
    return ConversationHandler.END


async def callback_risk_simulator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show risk simulation"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    from app.supabase_repo import get_risk_per_trade
    
    # Get current settings
    session = get_autotrade_session(user_id)
    current_risk = get_risk_per_trade(user_id)
    current_amount = float(session.get("initial_deposit", 0)) if session else 100
    
    # Simulate scenarios
    scenarios = []
    
    # Scenario 1: 10 wins
    balance_10w = current_amount
    for _ in range(10):
        risk_amt = balance_10w * (current_risk / 100)
        profit = risk_amt * 2  # Assume 1:2 R:R
        balance_10w += profit
    
    # Scenario 2: 5 wins, 5 losses
    balance_5w5l = current_amount
    for _ in range(5):
        risk_amt = balance_5w5l * (current_risk / 100)
        profit = risk_amt * 2
        balance_5w5l += profit
    for _ in range(5):
        risk_amt = balance_5w5l * (current_risk / 100)
        balance_5w5l -= risk_amt
    
    # Scenario 3: 10 losses
    balance_10l = current_amount
    for _ in range(10):
        risk_amt = balance_10l * (current_risk / 100)
        balance_10l -= risk_amt
    
    # Calculate survivability
    survivability = int(100 / current_risk)
    
    await query.edit_message_text(
        f"🧮 <b>Risk Simulator</b>\n\n"
        f"Starting Balance: <b>${current_amount:.2f}</b>\n"
        f"Risk per trade: <b>{current_risk}%</b>\n"
        f"Assumed R:R: <b>1:2</b>\n\n"
        f"<b>Scenario 1: 10 Wins</b>\n"
        f"Final balance: <b>${balance_10w:.2f}</b>\n"
        f"Profit: <b>+${balance_10w - current_amount:.2f}</b> "
        f"({((balance_10w / current_amount - 1) * 100):.1f}%)\n\n"
        f"<b>Scenario 2: 5 Wins, 5 Losses</b>\n"
        f"Final balance: <b>${balance_5w5l:.2f}</b>\n"
        f"Profit: <b>+${balance_5w5l - current_amount:.2f}</b> "
        f"({((balance_5w5l / current_amount - 1) * 100):.1f}%)\n\n"
        f"<b>Scenario 3: 10 Losses</b>\n"
        f"Final balance: <b>${balance_10l:.2f}</b>\n"
        f"Loss: <b>-${current_amount - balance_10l:.2f}</b> "
        f"({((1 - balance_10l / current_amount) * 100):.1f}%)\n\n"
        f"<b>Survivability:</b>\n"
        f"Can survive <b>{survivability}+</b> consecutive losses\n"
        f"before account blown.\n\n"
        f"💡 Notice how losses don't blow your account!\n"
        f"This is the power of risk management.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="at_risk_settings")],
        ])
    )
    return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Trading Mode Selection Handlers                                    #
# ------------------------------------------------------------------ #

async def callback_trading_mode_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display trading mode selection menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    from app.trading_mode_manager import TradingModeManager, TradingMode
    current_mode = TradingModeManager.get_mode(user_id)
    
    scalping_check = "✅ " if current_mode == TradingMode.SCALPING else ""
    swing_check = "✅ " if current_mode == TradingMode.SWING else ""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{scalping_check}⚡ Scalping Mode (5M)",
            callback_data="mode_select_scalping"
        )],
        [InlineKeyboardButton(
            f"{swing_check}📊 Swing Mode (15M)",
            callback_data="mode_select_swing"
        )],
        [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="at_dashboard")],
    ])
    
    await query.edit_message_text(
        "⚙️ <b>Select Trading Mode</b>\n\n"
        "⚡ <b>Scalping Mode (5M):</b>\n"
        "• Fast trades on 5-minute chart\n"
        "• 10-20 trades per day\n"
        "• Single TP at 1.5R\n"
        "• 30-minute max hold time\n"
        "• Pairs: BTC, ETH\n\n"
        "📊 <b>Swing Mode (15M):</b>\n"
        "• Swing trades on 15-minute chart\n"
        "• 2-3 trades per day\n"
        "• 3-tier TP (StackMentor)\n"
        "• No max hold time\n"
        "• Pairs: BTC, ETH, SOL, BNB\n\n"
        f"Current mode: <b>{current_mode.value.upper()}</b>",
        parse_mode='HTML',
        reply_markup=keyboard
    )


async def callback_select_scalping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scalping mode selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    from app.trading_mode_manager import TradingModeManager, TradingMode
    current_mode = TradingModeManager.get_mode(user_id)
    
    if current_mode == TradingMode.SCALPING:
        await query.edit_message_text(
            "⚡ You're already in Scalping Mode!",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="trading_mode_menu")]
            ])
        )
        return
    
    # Switch mode
    result = await TradingModeManager.switch_mode(
        user_id, TradingMode.SCALPING, context.application.bot, context
    )
    
    if result["success"]:
        await query.edit_message_text(
            "✅ <b>Trading Mode Changed</b>\n\n"
            "⚡ <b>Scalping Mode Activated</b>\n\n"
            "📊 Configuration:\n"
            "• Timeframe: 5 minutes\n"
            "• Scan interval: 15 seconds\n"
            "• Profit target: 1.5R (single TP)\n"
            "• Max hold time: 30 minutes\n"
            "• Trading pairs: Top 10 (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, DOT, MATIC)\n"
            "• Max concurrent: 4 positions\n"
            "• Min confidence: 80%\n\n"
            "🚀 Engine restarted with scalping parameters.\n"
            "You'll receive signals when high-probability setups appear.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Dashboard", callback_data="at_dashboard")]
            ])
        )
    else:
        await query.edit_message_text(
            f"❌ Failed to switch mode: {result['message']}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="trading_mode_menu")]
            ])
        )


async def callback_select_swing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle swing mode selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    from app.trading_mode_manager import TradingModeManager, TradingMode
    current_mode = TradingModeManager.get_mode(user_id)
    
    if current_mode == TradingMode.SWING:
        await query.edit_message_text(
            "📊 You're already in Swing Mode!",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="trading_mode_menu")]
            ])
        )
        return
    
    # Switch mode
    result = await TradingModeManager.switch_mode(
        user_id, TradingMode.SWING, context.application.bot, context
    )
    
    if result["success"]:
        await query.edit_message_text(
            "✅ <b>Trading Mode Changed</b>\n\n"
            "📊 <b>Swing Mode Activated</b>\n\n"
            "📊 Configuration:\n"
            "• Timeframe: 15 minutes\n"
            "• Scan interval: 45 seconds\n"
            "• Profit targets: 3-tier (StackMentor)\n"
            "• No max hold time\n"
            "• Trading pairs: Top 10 (BTC, ETH, SOL, BNB, XRP, DOGE, ADA, AVAX, DOT, MATIC)\n"
            "• Max concurrent: 4 positions\n"
            "• Min confidence: 68%\n\n"
            "🚀 Engine restarted with swing parameters.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Dashboard", callback_data="at_dashboard")]
            ])
        )
    else:
        await query.edit_message_text(
            f"❌ Failed to switch mode: {result['message']}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="trading_mode_menu")]
            ])
        )


# ------------------------------------------------------------------ #
#  Register handlers                                                  #
# ------------------------------------------------------------------ #


def register_autotrade_handlers(application):
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("autotrade", cmd_autotrade),
            CommandHandler("start", cmd_autotrade),
            CallbackQueryHandler(handle_submit_uid_bot, pattern="^submit_uid_bot$"),
        ],
        states={
            WAITING_BITUNIX_UID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_uid_input_bot),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CallbackQueryHandler(callback_cancel, pattern="^at_cancel$"),
        ],
        per_user=True, per_chat=True, allow_reentry=True,
    )
    application.add_handler(conv)
    

    # Ad-hoc UID approval callbacks for admins
    from app.handlers_autotrade_admin import callback_uid_acc, callback_uid_reject
    application.add_handler(CallbackQueryHandler(callback_uid_acc, pattern="^uid_acc_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_uid_reject, pattern="^uid_reject_\\d+$"))

    print("✅ AutoTrade Gatekeeper handlers registered")
