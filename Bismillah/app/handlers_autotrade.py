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
from app.supabase_repo import _client, get_risk_mode, set_risk_mode, get_risk_per_trade, set_risk_per_trade
from app.ui_components import (
    progress_indicator,
    onboarding_welcome,
    error_message_actionable,
    loading_message,
    success_message,
    settings_group,
    section_header,
    status_badge,
)

# Conversation states
WAITING_API_KEY        = 1
WAITING_API_SECRET     = 2
WAITING_TRADE_AMOUNT   = 3
WAITING_LEVERAGE       = 4
WAITING_NEW_LEVERAGE   = 5
WAITING_BITUNIX_UID    = 6
WAITING_NEW_AMOUNT     = 7
WAITING_MANUAL_MARGIN  = 8

# Legacy constants (tetap untuk backward compat)
BITUNIX_REFERRAL_URL  = "https://www.bitunix.com/register?vipCode=sq45"
BITUNIX_REFERRAL_CODE = "sq45"

# ── Exchange selection helpers ──────────────────────────────────────
def _get_user_exchange(context) -> str:
    """Ambil exchange yang dipilih user dari context.user_data, default bitunix."""
    return context.user_data.get("selected_exchange", "bitunix")

def _set_user_exchange(context, exchange_id: str):
    context.user_data["selected_exchange"] = exchange_id


# ------------------------------------------------------------------ #
#  Supabase helpers — user_api_keys                                   #
# ------------------------------------------------------------------ #

def save_user_api_keys(telegram_id: int, api_key: str, api_secret: str, exchange: str = "bitunix"):
    """Simpan API key + secret terenkripsi ke Supabase."""
    from app.supabase_repo import ensure_user_exists_no_credit
    ensure_user_exists_no_credit(int(telegram_id))
    s = _client()
    row = {
        "telegram_id": int(telegram_id),
        "exchange": exchange,
        "api_key": api_key,
        "api_secret_enc": encrypt(api_secret),
        "key_hint": api_key[-4:],
        "updated_at": datetime.utcnow().isoformat(),
    }
    # upsert by (telegram_id, exchange) — support multi-exchange
    s.table("user_api_keys").upsert(row, on_conflict="telegram_id,exchange").execute()


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
    user = update.effective_user
    user_id = user.id
    
    # Registration logic (for both /start and /autotrade)
    try:
        from app.chat_store import remember_chat
        remember_chat(user_id, update.effective_chat.id)
    except Exception:
        pass

    # Simpan user ke Supabase di background (non-blocking)
    import asyncio

    async def _register_user():
        try:
            from app.supabase_repo import upsert_user_with_welcome
            result = await asyncio.to_thread(
                upsert_user_with_welcome,
                user_id, user.username, user.first_name, user.last_name, 100
            )
            if result.get("is_new"):
                print(f"✅ New user registered: {user_id} ({user.first_name})")
        except Exception as e:
            print(f"⚠️ Supabase registration error: {e}")

        try:
            from services import get_database
            db = get_database()
            referrer_id = None
            if context.args:
                ref_code = context.args[0]
                if ref_code.startswith('ref_'):
                    code = ref_code[4:]
                    referrer_id = db.get_user_by_referral_code(code) if code.startswith('F') else (int(code) if code.isdigit() else None)
                elif ref_code.startswith('prem_'):
                    referrer_id = db.get_user_by_premium_referral_code(ref_code[5:])
            await asyncio.to_thread(
                db.create_user, user_id, user.username, user.first_name, user.last_name, 'id', referrer_id
            )
            if referrer_id:
                await asyncio.to_thread(db.process_referral_reward, referrer_id, user_id)
        except Exception as e:
            print(f"⚠️ SQLite registration error: {e}")

    asyncio.create_task(_register_user())

    # Cek apakah user masuk via link komunitas
    if context.args:
        ref_code = context.args[0]
        if ref_code.startswith('community_'):
            community_code = ref_code.replace('community_', '')
            context.user_data['community_code'] = community_code
            # Simpan ke autotrade_sessions jika sudah ada
            try:
                from app.supabase_repo import _client
                _client().table("autotrade_sessions").upsert({
                    "telegram_id": user_id,
                    "community_code": community_code,
                    "status": "pending_verification",
                    "initial_deposit": 0,
                    "current_balance": 0,
                    "total_profit": 0,
                    "updated_at": __import__('datetime').datetime.utcnow().isoformat(),
                }, on_conflict="telegram_id").execute()
            except Exception:
                pass

    # Main autotrade logic
    keys = get_user_api_keys(user_id)
    session = get_autotrade_session(user_id)
    is_active = session and session.get("status") in ("active", "uid_verified")

    if keys and is_active:
        from app.autotrade_engine import is_running as engine_running
        from app.exchange_registry import get_exchange, get_client
        from app.trading_mode_manager import TradingModeManager, TradingMode
        
        # Check if engine is running
        # Priority 1: Check actual running task
        engine_on = engine_running(user_id)
        
        # Priority 2: If task not found but session is active, engine might be starting (auto-restore)
        # Show as "active" to avoid confusion during bot restart
        if not engine_on and session and session.get("status") in ("active", "uid_verified"):
            # Engine should be running based on DB, might be starting up
            engine_on = True  # Assume active to avoid user confusion
        
        engine_status = "🟢 Engine running" if engine_on else "🟡 Engine inactive"
        exchange_id = keys.get("exchange", "bitunix")
        ex_cfg = get_exchange(exchange_id)
        
        # Load trading mode
        trading_mode = TradingModeManager.get_mode(user_id)
        mode_emoji = "⚡" if trading_mode == TradingMode.SCALPING else "📊"
        mode_label = "Scalping (5M)" if trading_mode == TradingMode.SCALPING else "Swing (15M)"
        
        # Get market sentiment
        from app.market_sentiment_detector import detect_market_condition
        try:
            sentiment = detect_market_condition("BTC")
            condition = sentiment['condition']
            confidence = sentiment['confidence']
            
            # Emoji based on condition
            if condition == "SIDEWAYS":
                sentiment_emoji = "📊"
                sentiment_color = "🟡"
            elif condition == "TRENDING":
                sentiment_emoji = "📈"
                sentiment_color = "🟢"
            else:
                sentiment_emoji = "⚡"
                sentiment_color = "🟠"
            
            sentiment_text = (
                f"\n{sentiment_emoji} <b>Market Sentiment</b>\n"
                f"{sentiment_color} {condition} ({confidence}%)\n"
                f"💡 Optimal: {sentiment['recommended_mode'].upper()}\n"
            )
        except Exception as e:
            sentiment_text = ""

        engine_btn = (
            [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")]
            if engine_on else
            [InlineKeyboardButton("🔄 Restart Engine", callback_data="at_restart_engine")]
        )

        # Show Community Partners for all users who have a session (any verified status)
        uid_status = session.get("status", "")
        show_community = uid_status not in ["pending_verification", "uid_rejected", "pending", ""]
        
        # Build keyboard based on verification status (REMOVED Trading Mode button)
        keyboard_buttons = [
            [InlineKeyboardButton("📊 Status Portfolio",  callback_data="at_status")],
            [InlineKeyboardButton("📈 Trade History",     callback_data="at_history")],
            engine_btn,
            [InlineKeyboardButton("🧠 Bot Skills",        callback_data="skills_menu")],
        ]
        
        # Only add Community Partners button if user is verified
        if show_community:
            keyboard_buttons.append([InlineKeyboardButton("👥 Community Partners", callback_data="community_partners")])
        
        keyboard_buttons.extend([
            [InlineKeyboardButton("⚙️ Settings",          callback_data="at_settings")],
            [InlineKeyboardButton("🔑 Change API Key",    callback_data="at_change_key")],
        ])
        
        keyboard = InlineKeyboardMarkup(keyboard_buttons)
        current_leverage = int(session.get("leverage", 10))
        current_margin   = session.get("margin_mode", "cross")
        margin_label     = "Cross ♾️" if current_margin == "cross" else "Isolated 🔒"

        # Kirim dashboard dulu (instant), lalu fetch balance di background
        sent_msg = await update.message.reply_text(
            "🤖 <b>Auto Trade Dashboard</b>\n\n"
            "✅ Status: <b>ACTIVE</b>\n"
            f"{mode_emoji} Mode: <b>{mode_label}</b> (Auto)\n"
            f"{sentiment_text}\n"
            f"💵 <b>Trading Capital:</b> {session['initial_deposit']} USDT\n"
            f"💳 Balance: <i>loading...</i>\n"
            f"📈 Profit: {session['total_profit']:.2f} USDT\n\n"
            f"⚙️ Leverage: <b>{current_leverage}x</b> | Margin: <b>{margin_label}</b>\n"
            f"🔑 API Key: <code>...{keys['key_hint']}</code>\n"
            f"🏦 Exchange: {ex_cfg['emoji']} <b>{ex_cfg['name']}</b>\n"
            f"⚙️ {engine_status}",
            parse_mode='HTML', reply_markup=keyboard
        )

        # Fetch balance di background lalu update pesan
        import asyncio
        import logging as _logging
        _bg_logger = _logging.getLogger(__name__)

        async def _update_balance():
            try:
                client = get_client(exchange_id, keys["api_key"], keys["api_secret"])
                acc = await asyncio.wait_for(
                    asyncio.to_thread(client.get_account_info),
                    timeout=6.0
                )
                if acc.get("success"):
                    balance_line = (
                        f"💳 {ex_cfg['name']} Balance: <b>{acc['available']:.2f} USDT</b>\n"
                        f"📊 Unrealized PnL: <b>{acc['total_unrealized_pnl']:+.2f} USDT</b>\n"
                    )
                else:
                    balance_line = f"💳 Balance: <i>{acc.get('error', 'error')[:50]}</i>\n"
                    _bg_logger.warning(f"[Balance] get_account_info failed: {acc.get('error')}")
            except Exception as e:
                balance_line = "💳 Balance: <i>tidak tersedia</i>\n"
                _bg_logger.warning(f"[Balance] Exception: {e}")

            try:
                await sent_msg.edit_text(
                    "🤖 <b>Auto Trade Dashboard</b>\n\n"
                    "✅ Status: <b>ACTIVE</b>\n"
                    f"{mode_emoji} Mode: <b>{mode_label}</b> (Auto)\n"
                    f"{sentiment_text}\n"
                    f"💵 <b>Trading Capital:</b> {session['initial_deposit']} USDT\n"
                    f"{balance_line}"
                    f"📈 Profit: {session['total_profit']:.2f} USDT\n\n"
                    f"⚙️ Leverage: <b>{current_leverage}x</b> | Margin: <b>{margin_label}</b>\n"
                    f"🔑 API Key: <code>...{keys['key_hint']}</code>\n"
                    f"🏦 Exchange: {ex_cfg['emoji']} <b>{ex_cfg['name']}</b>\n"
                    f"⚙️ {engine_status}",
                    parse_mode='HTML', reply_markup=keyboard
                )
            except Exception as e:
                _bg_logger.warning(f"[Balance] edit_text failed: {e}")

        asyncio.create_task(_update_balance())
        return ConversationHandler.END

    elif keys:
        # User has API key - check if they completed risk mode selection
        risk_mode = get_risk_mode(user_id)
        
        # If user already selected risk mode, they should see dashboard
        # But session might not be "active" yet - redirect to dashboard anyway
        if risk_mode:
            # User completed setup, show dashboard
            from app.autotrade_engine import is_running as engine_running
            from app.exchange_registry import get_exchange
            from app.trading_mode_manager import TradingModeManager, TradingMode
            
            # Load session to check verification status
            session = get_autotrade_session(user_id)
            
            # Check if engine is running
            # Priority 1: Check actual running task
            engine_on = engine_running(user_id)
            
            # Priority 2: If task not found but session is active, engine might be starting (auto-restore)
            # Show as "active" to avoid confusion during bot restart
            if not engine_on and session and session.get("status") in ("active", "uid_verified"):
                # Engine should be running based on DB, might be starting up
                engine_on = True  # Assume active to avoid user confusion
            
            engine_status = "🟢 Engine running" if engine_on else "🟡 Engine inactive"
            exchange_id = keys.get("exchange", "bitunix")
            ex_cfg = get_exchange(exchange_id)
            
            # Load trading mode
            trading_mode = TradingModeManager.get_mode(user_id)
            mode_emoji = "⚡" if trading_mode == TradingMode.SCALPING else "📊"
            mode_label = "Scalping (5M)" if trading_mode == TradingMode.SCALPING else "Swing (15M)"
            
            # Get market sentiment
            from app.market_sentiment_detector import detect_market_condition
            try:
                sentiment = detect_market_condition("BTC")
                condition = sentiment['condition']
                confidence = sentiment['confidence']
                
                # Emoji based on condition
                if condition == "SIDEWAYS":
                    sentiment_emoji = "📊"
                    sentiment_color = "🟡"
                elif condition == "TRENDING":
                    sentiment_emoji = "📈"
                    sentiment_color = "🟢"
                else:
                    sentiment_emoji = "⚡"
                    sentiment_color = "🟠"
                
                sentiment_text = (
                    f"\n{sentiment_emoji} <b>Market Sentiment</b>\n"
                    f"{sentiment_color} {condition} ({confidence}%)\n"
                    f"💡 Optimal: {sentiment['recommended_mode'].upper()}\n"
                )
            except Exception as e:
                sentiment_text = ""

            engine_btn = (
                [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")]
                if engine_on else
                [InlineKeyboardButton("🚀 Start AutoTrade", callback_data="at_start_engine_now")]
            )

            # Show Community Partners for all users who have a session (any verified status)
            uid_status = session.get("status", "") if session else ""
            show_community = uid_status not in ["pending_verification", "uid_rejected", "pending", ""]
            
            # Build keyboard based on verification status (REMOVED Trading Mode button)
            keyboard_buttons = [
                [InlineKeyboardButton("📊 Status Portfolio",  callback_data="at_status")],
                [InlineKeyboardButton("📈 Trade History",     callback_data="at_history")],
                engine_btn,
                [InlineKeyboardButton("🧠 Bot Skills",        callback_data="skills_menu")],
            ]
            
            # Only add Community Partners button if user is verified
            if show_community:
                keyboard_buttons.append([InlineKeyboardButton("👥 Community Partners", callback_data="community_partners")])
            
            keyboard_buttons.extend([
                [InlineKeyboardButton("⚙️ Settings",          callback_data="at_settings")],
                [InlineKeyboardButton("🔑 Change API Key",    callback_data="at_change_key")],
            ])

            await update.message.reply_text(
                f"🤖 <b>AutoTrade Dashboard</b>\n\n"
                f"{engine_status}\n"
                f"{mode_emoji} Mode: <b>{mode_label}</b> (Auto)\n"
                f"🏦 Exchange: {ex_cfg['name']}\n"
                f"{sentiment_text}\n"
                f"Use the buttons below to manage your AutoTrade:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard_buttons)
            )
            return ConversationHandler.END
        
        # User has API key but hasn't selected risk mode yet - show risk mode selection
        from app.exchange_registry import get_exchange
        exchange_id = keys.get("exchange", "bitunix")
        ex_cfg = get_exchange(exchange_id)
        
        # Get current balance if available
        try:
            session = get_autotrade_session(user_id)
            balance = session.get("initial_deposit", 0) if session else 0
            balance_text = f"\n💰 Balance Anda: ${balance:.2f}\n" if balance > 0 else ""
        except:
            balance_text = ""
        
        # Add progress indicator
        progress = progress_indicator(3, 4, "Risk Management")
        
        # Build comparison cards
        from app.ui_components import comparison_card
        
        recommended_card = comparison_card(
            title="REKOMENDASI",
            emoji="🌟",
            pros=[
                "Otomatis hitung margin",
                "Safe compounding",
                "Account protection",
                "Cocok pemula & pro"
            ],
            badge="✨ 95% user pilih ini"
        )
        
        manual_card = comparison_card(
            title="MANUAL",
            emoji="⚙️",
            pros=[
                "Full control",
                "Fixed position size"
            ],
            cons=[
                "Butuh pengalaman",
                "Risk lebih tinggi"
            ]
        )
        
        text = f"{progress}\n\n"
        text += f"✅ <b>API Key Connected - {ex_cfg['name']}</b>\n"
        text += f"{balance_text}\n"
        text += "🎯 <b>Choose Trading Mode</b>\n\n"
        text += recommended_card + "\n"
        text += manual_card + "\n"
        text += "💡 <b>Our recommendation:</b> Choose Recommended for the best results!\n"

        keyboard = [
            [InlineKeyboardButton("🌟 Choose Recommended", callback_data="at_mode_risk_based")],
            [InlineKeyboardButton("⚙️ Choose Manual", callback_data="at_mode_manual")],
            [InlineKeyboardButton("🔑 Change API Key", callback_data="at_change_key")],
        ]
        
        await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return ConversationHandler.END

    else:
        # No API key yet — show exchange selector first
        from app.exchange_registry import exchange_list_keyboard
        
        # Add welcoming onboarding message with progress
        welcome_text = onboarding_welcome(total_steps=4)
        welcome_text += "\n" + progress_indicator(1, 4, "Pilih Exchange")
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=exchange_list_keyboard()
        )
        return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Exchange selection callback                                        #
# ------------------------------------------------------------------ #

async def callback_select_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User memilih exchange dari daftar."""
    query = update.callback_query
    await query.answer()

    exchange_id = query.data.replace("at_exchange_", "")
    from app.exchange_registry import get_exchange, EXCHANGES
    if exchange_id not in EXCHANGES:
        await query.edit_message_text("❌ Unknown exchange.")
        return ConversationHandler.END

    _set_user_exchange(context, exchange_id)
    ex = get_exchange(exchange_id)

    # Cek apakah exchange ini perlu verifikasi UID referral
    requires_uid = ex.get('requires_uid_verification', False)

    # Jika tidak perlu UID verification (BingX, Binance, Bybit), langsung ke setup API Key
    if not requires_uid:
        # Add progress indicator
        progress = progress_indicator(2, 4, "Setup API Key")
        
        await query.edit_message_text(
            f"{progress}\n\n"
            f"<b>Auto Trade — {ex['name']}</b>\n\n"
            f"🔑 <b>Setup API Key</b>\n\n"
            f"To start auto trading, you need to connect your {ex['name']} account via API Key.\n\n"
            f"📖 <b>How to create your API Key:</b>\n{ex['api_key_help']}\n\n"
            f"🔒 <b>Security note:</b> The API Key only needs <b>Trade</b> permission.\n"
            f"Never enable Withdraw — your funds stay safe.\n\n"
            "Click the button below to open API Management, then return here to enter your API Key.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔗 Open {ex['name']} API Management", url=ex.get("api_key_url", ex.get("referral_url", "")))],
                [InlineKeyboardButton("✅ I have my API Key, Continue", callback_data="at_confirm_referral")],
                [InlineKeyboardButton("🔙 Change Exchange", callback_data="at_change_exchange")],
            ]),
            disable_web_page_preview=True
        )
        return ConversationHandler.END

    # Untuk exchange yang perlu UID verification (Bitunix)
    # Cek apakah user masuk via link komunitas — gunakan referral komunitas
    community_code = context.user_data.get("community_code")
    community_ref_url = ex["referral_url"]
    community_ref_code = ex["referral_code"]
    community_name = None

    if community_code:
        try:
            from app.handlers_community import get_community_by_code
            community = get_community_by_code(community_code)
            if community and community.get("status") == "active":
                c_ref_code = community.get("bitunix_referral_code", "")
                c_ref_url = community.get("bitunix_referral_url", "")
                if c_ref_code and c_ref_url:
                    community_ref_url = c_ref_url
                    community_ref_code = c_ref_code
                    community_name = community.get("community_name", "")
        except Exception:
            pass

    buttons = []
    if ex.get("group_url"):
        buttons.append([InlineKeyboardButton(
            f"👥 Join CryptoMentor x {ex['name']} Group", url=ex["group_url"]
        )])
    buttons += [
        [InlineKeyboardButton(
            f"🔗 Register {ex['name']} via Referral", url=community_ref_url
        )],
        [InlineKeyboardButton(
            "✅ Already Registered via Referral, Continue Setup", callback_data="at_confirm_referral"
        )],
        [InlineKeyboardButton("❓ Why is Referral Required?", callback_data="at_why_referral")],
        [InlineKeyboardButton("🔙 Change Exchange", callback_data="at_change_exchange")],
    ]

    text = (
        f"<b>Auto Trade — {ex['name']}</b>\n\n"
    )
    if community_name:
        text += f"👥 Kamu bergabung via komunitas: <b>{community_name}</b>\n\n"

    # Add progress indicator
    progress = progress_indicator(2, 4, "Registrasi & API Key")
    text = progress + "\n\n" + text
    
    text += "Sebelum mulai, ada 2 langkah penting:\n\n"

    if ex.get("group_url"):
        text += (
            f"👥 <b>Step 1 — Join Exclusive Group:</b>\n"
            f"Join to get exclusive events & updates 🎁\n\n"
            f"🔗 <b>Step 2 — Register {ex['name']} via Referral:</b>\n"
        )
    else:
        text += f"🔗 <b>Step 1 — Register {ex['name']} via Referral:</b>\n"

    text += (
        f"<code>{community_ref_url}</code>\n"
        f"🎟 Referral Code: <code>{community_ref_code}</code>\n\n"
        "Klik tombol di bawah, lalu kembali ke sini setelah selesai."
    )

    await query.edit_message_text(
        text, parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )
    return ConversationHandler.END


async def callback_change_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kembali ke pilih exchange."""
    query = update.callback_query
    await query.answer()
    from app.exchange_registry import exchange_list_keyboard
    await query.edit_message_text(
        "🤖 <b>Auto Trade — Select Exchange</b>\n\n"
        "Choose the exchange you want to use for AutoTrade:",
        parse_mode='HTML',
        reply_markup=exchange_list_keyboard()
    )
    return ConversationHandler.END


# ------------------------------------------------------------------ #
#  Referral gate & UID verification                                   #
# ------------------------------------------------------------------ #

async def callback_why_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.exchange_registry import get_exchange
    exchange_id = _get_user_exchange(context)
    ex = get_exchange(exchange_id)
    await query.edit_message_text(
        "❓ <b>Why is Referral Required?</b>\n\n"
        "Referral allows us to keep developing this bot for free for you.\n\n"
        f"✅ You retain full control over your {ex['name']} account\n"
        "✅ Your funds are safe — API Key only has Trade permission, cannot withdraw\n"
        "✅ No additional fees from us\n\n"
        f"🔗 Register now: {ex['referral_url']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Register Now", url=ex["referral_url"])],
            [InlineKeyboardButton("✅ Already Registered", callback_data="at_confirm_referral")],
            [InlineKeyboardButton("🔙 Back",               callback_data="at_cancel")],
        ]),
        disable_web_page_preview=True
    )
    return ConversationHandler.END


async def callback_confirm_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User konfirmasi sudah daftar via referral — langsung minta API Key dulu."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    from app.exchange_registry import get_exchange
    exchange_id = _get_user_exchange(context)
    ex = get_exchange(exchange_id)

    # Kalau sudah punya API key untuk exchange ini, skip ke dashboard
    existing_keys = get_user_api_keys(user_id)
    if existing_keys and existing_keys.get("exchange") == exchange_id:
        await query.edit_message_text(
            f"✅ <b>Account already registered</b>\n\n"
            f"🔑 API Key: <code>...{existing_keys['key_hint']}</code>\n"
            f"🏦 Exchange: {ex['name']}\n\n"
            "Continue to trading setup:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start Trading",  callback_data="at_start_trade")],
                [InlineKeyboardButton("🔑 Change API Key", callback_data="at_change_key")],
            ])
        )
        return ConversationHandler.END

    # Ask for API Key first — UID is collected AFTER API key is verified
    await query.edit_message_text(
        f"🔑 <b>Setup API Key — Step 1/2</b>\n\n"
        f"Enter your {ex['name']} <b>API Key</b> below.\n\n"
        f"📖 <b>How to create your API Key:</b>\n{ex['api_key_help']}\n\n"
        f"🔒 <b>Security note:</b> The API Key only needs <b>Trade</b> permission.\n"
        f"Never enable Withdraw — your funds stay safe.\n\n"
        "⚠️ Never share your API Key with anyone.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔗 Open {ex['name']} API Management", url=ex.get("api_key_url", ex["referral_url"]))],
            [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]
        ])
    )
    return WAITING_API_KEY


async def receive_bitunix_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive UID dari user, kirim ke admin untuk verifikasi."""
    uid = update.message.text.strip()
    user_id = update.effective_user.id
    user = update.effective_user

    from app.exchange_registry import get_exchange
    exchange_id = _get_user_exchange(context)
    ex = get_exchange(exchange_id)

    try:
        await update.message.delete()
    except Exception:
        pass

    if not uid.isdigit() or len(uid) < ex["uid_min_len"]:
        await update.message.reply_text(
            f"❌ Invalid UID. {ex['uid_label']} must be a number "
            f"(example: <code>{ex['uid_example']}</code>).\n\nTry again:",
            parse_mode='HTML'
        )
        return WAITING_BITUNIX_UID

    from app.demo_users import is_demo_user
    if is_demo_user(user_id):
        _save_uid(user_id, uid, status="uid_verified", exchange=exchange_id)
        await update.message.reply_text(
            f"✅ <b>UID Verified!</b>\n\n"
            f"🔢 UID: <code>{uid}</code>\n"
            f"🏦 Exchange: {ex['name']}\n\n"
            "Setup complete! Ready to start trading:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Start Trading", callback_data="at_start_trade")],
            ])
        )
        return ConversationHandler.END

    _save_uid(user_id, uid, status="pending_verification", exchange=exchange_id)

    admin_ids = _get_admin_ids()
    username_display = f"@{user.username}" if user.username else f"#{user_id}"
    full_name = user.full_name or "Unknown"

    # Cek apakah user masuk via link komunitas
    community_code = context.user_data.get("community_code")
    if not community_code:
        # Cek di autotrade_sessions
        session = get_autotrade_session(user_id)
        community_code = session.get("community_code") if session else None

    if community_code:
        # Kirim notifikasi ke ketua komunitas, bukan admin
        from app.handlers_community import get_community_by_code
        community = get_community_by_code(community_code)
        if community and community.get("status") == "active":
            leader_id = community.get("telegram_id")
            community_name = community.get("community_name", "")
            leader_keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ APPROVE", callback_data=f"cmember_acc_{user_id}"),
                    InlineKeyboardButton("❌ REJECT",  callback_data=f"cmember_reject_{user_id}"),
                ]
            ])
            leader_text = (
                f"🔔 <b>Verifikasi UID Anggota Komunitas</b>\n\n"
                f"👤 User: <b>{full_name}</b> ({username_display})\n"
                f"🆔 Telegram ID: <code>{user_id}</code>\n"
                f"🏦 Exchange: <b>{ex['name']}</b>\n"
                f"🔢 {ex['uid_label']}: <code>{uid}</code>\n"
                f"👥 Komunitas: <b>{community_name}</b>\n\n"
                f"Verifikasi bahwa UID ini terdaftar di bawah referral komunitas kamu.\n"
                f"Approve atau reject:"
            )
            try:
                await context.bot.send_message(
                    chat_id=leader_id, text=leader_text,
                    parse_mode='HTML', reply_markup=leader_keyboard
                )
            except Exception as e:
                import logging as _log
                _log.getLogger(__name__).warning(f"Failed to notify community leader {leader_id}: {e}")
                # Fallback ke admin jika gagal kirim ke leader
                for admin_id in admin_ids:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id, text=leader_text,
                            parse_mode='HTML', reply_markup=leader_keyboard
                        )
                    except Exception:
                        pass

            await update.message.reply_text(
                f"⏳ <b>UID sedang diverifikasi</b>\n\n"
                f"🔢 UID: <code>{uid}</code>\n"
                f"🏦 Exchange: {ex['name']}\n"
                f"👥 Komunitas: {community_name}\n\n"
                f"Ketua komunitas akan memverifikasi UID kamu.\n"
                f"Kamu akan mendapat notifikasi setelah disetujui.",
                parse_mode='HTML'
            )
            return ConversationHandler.END

    # Default: kirim ke admin
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
        f"🏦 Exchange: <b>{ex['name']}</b>\n"
        f"🔢 {ex['uid_label']}: <code>{uid}</code>\n\n"
        f"Verify that this UID is registered under referral "
        f"<b>{ex['referral_code']}</b> on {ex['name']}.\n\n"
        f"Approve or reject this user's registration:"
    )

    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id, text=admin_text,
                parse_mode='HTML', reply_markup=admin_keyboard
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to notify admin {admin_id}: {e}")

    await update.message.reply_text(
        f"⏳ <b>Your UID is being verified</b>\n\n"
        f"🔢 UID: <code>{uid}</code>\n"
        f"🏦 Exchange: {ex['name']}\n\n"
        "Our admin will verify that your account is registered under our referral.\n\n"
        "✅ Your API Key has been saved.\n"
        "You will receive a notification once your UID is approved and trading is unlocked.",
        parse_mode='HTML'
    )
    return ConversationHandler.END


def _save_uid(telegram_id: int, uid: str, status: str = "pending_verification", exchange: str = "bitunix"):
    """Simpan exchange UID ke Supabase autotrade_sessions."""
    try:
        _client().table("autotrade_sessions").upsert({
            "telegram_id": int(telegram_id),
            "bitunix_uid": uid,      # kolom lama, tetap diisi untuk backward compat
            "exchange_uid": uid,     # kolom baru multi-exchange
            "exchange": exchange,
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
    from app.exchange_registry import get_exchange
    exchange_id = _get_user_exchange(context)
    ex = get_exchange(exchange_id)

    existing = get_user_api_keys(user_id)
    if existing and existing.get("exchange") == exchange_id:
        await query.edit_message_text(
            f"✅ <b>API Key already saved</b>\n\n"
            f"🔑 Key: <code>...{existing['key_hint']}</code>\n"
            f"🏦 Exchange: {ex['name']}\n\n"
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
        f"🔑 <b>Setup API Key — Step 1/2</b>\n\n"
        f"Enter your {ex['name']} <b>API Key</b> below.\n\n"
        f"📖 <b>How to create your API Key:</b>\n{ex['api_key_help']}\n\n"
        f"🔒 <b>Security note:</b> The API Key only needs <b>Trade</b> permission.\n"
        f"Never enable Withdraw — your funds stay safe.\n\n"
        "⚠️ Never share your API Key with anyone.",
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔗 Open {ex['name']} API Management", url=ex.get("api_key_url", ex["referral_url"]))],
            [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]
        ])
    )
    return WAITING_API_KEY


async def callback_change_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    from app.exchange_registry import get_exchange
    exchange_id = _get_user_exchange(context)
    ex = get_exchange(exchange_id)
    await query.edit_message_text(
        f"🔑 <b>Change API Key — Step 1/2</b>\n\n"
        f"Enter your new {ex['name']} <b>API Key</b> below.\n\n"
        f"📖 <b>How to create your API Key:</b>\n{ex['api_key_help']}\n\n"
        f"🔒 <b>Security note:</b> The API Key only needs <b>Trade</b> permission.\n"
        f"Never enable Withdraw — your funds stay safe.\n\n"
        "⚠️ Never share your API Key with anyone.",
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"🔗 Open {ex['name']} API Management", url=ex.get("api_key_url", ex["referral_url"]))],
            [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]
        ])
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
        exchange_id = _get_user_exchange(context)
        save_user_api_keys(user_id, api_key, api_secret, exchange=exchange_id)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to save API Key: {e}")
        return ConversationHandler.END

    loading = await update.message.reply_text("⏳ <b>Verifying connection...</b>", parse_mode='HTML')

    try:
        import asyncio
        from app.exchange_registry import get_client, get_exchange
        ex_cfg = get_exchange(exchange_id)
        client = get_client(exchange_id, api_key, api_secret)
        result = await asyncio.wait_for(
            asyncio.to_thread(client.check_connection),
            timeout=8.0
        )
    except asyncio.TimeoutError:
        result = {'online': False, 'error': 'Timeout: server did not respond within 8 seconds'}
    except Exception as e:
        result = {'online': False, 'error': str(e)}

    if result.get('online') or result.get('success'):
        # API Key OK — cek apakah exchange perlu verifikasi UID referral
        requires_uid = ex_cfg.get('requires_uid_verification', False)
        uid_saved = _get_saved_uid(user_id)
        session = get_autotrade_session(user_id)
        uid_status = session.get("status", "") if session else ""

        # Jika exchange tidak perlu verifikasi UID (BingX, Binance, Bybit)
        if not requires_uid:
            await loading.edit_text(
                "✅ <b>API Key saved & verified!</b>\n\n"
                f"🔑 Key: <code>...{api_key[-4:]}</code>\n"
                f"🏦 Exchange: {ex_cfg['name']}\n\n"
                "Next step: Choose your risk management mode:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 Choose Risk Mode", callback_data="at_choose_risk_mode")],
                ])
            )
        # Jika exchange perlu verifikasi UID (Bitunix)
        elif uid_status == "uid_verified" and uid_saved:
            await loading.edit_text(
                "✅ <b>API Key saved & verified!</b>\n\n"
                f"🔑 Key: <code>...{api_key[-4:]}</code>\n"
                f"🏦 Exchange: {ex_cfg['name']}\n"
                f"🔢 UID: <code>{uid_saved}</code> ✅\n\n"
                "Next step: Choose your risk management mode:",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 Choose Risk Mode", callback_data="at_choose_risk_mode")],
                ])
            )
        elif uid_status == "pending_verification" and uid_saved:
            await loading.edit_text(
                "✅ <b>API Key saved!</b>\n\n"
                f"🔑 Key: <code>...{api_key[-4:]}</code>\n"
                f"🏦 Exchange: {ex_cfg['name']}\n\n"
                f"⏳ UID <code>{uid_saved}</code> is still pending admin verification.\n"
                "You will receive a notification once approved.",
                parse_mode='HTML'
            )
        else:
            # Bitunix perlu UID verification
            await loading.edit_text(
                f"✅ <b>API Key saved & verified!</b>\n\n"
                f"🔑 Key: <code>...{api_key[-4:]}</code>\n"
                f"🏦 Exchange: {ex_cfg['name']}\n\n"
                f"<b>Last step — UID Verification</b>\n\n"
                f"Enter your <b>{ex_cfg['uid_label']}</b>.\n\n"
                f"📍 How to find your UID:\n{ex_cfg['uid_help']}\n\n"
                f"Example: <code>{ex_cfg['uid_example']}</code>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancel", callback_data="at_cancel")]
                ])
            )
            return WAITING_BITUNIX_UID
    else:
        err = result.get('error', '')
        if '403' in str(err) or 'TOKEN_INVALID' in str(err) or 'IP' in str(err).upper():
            msg = (
                f"❌ <b>API Key Ditolak oleh {ex_cfg['name']}</b>\n\n"
                "⚠️ <b>Masalah:</b> API Key Anda memiliki <b>IP Restriction</b> yang memblokir server bot.\n\n"
                "🔧 <b>Cara Memperbaiki (WAJIB):</b>\n"
                f"1. Login ke {ex_cfg['name']} → API Management\n"
                "2. Hapus API Key yang lama\n"
                "3. Buat API Key baru:\n"
                "   • Di <b>Bind IP Address</b> → <b>KOSONGKAN</b> (jangan isi apapun)\n"
                "   • Centang permission: ✅ Trade / Futures Trading\n"
                "   • Copy API Key & Secret Key dengan benar\n"
                "4. Re-setup di bot: /autotrade → Change API Key\n\n"
                "❓ <b>Kenapa harus dikosongkan?</b>\n"
                "Server bot menggunakan IP dinamis. Jika IP tertentu di-set, exchange akan memblokir semua request dari IP lain.\n\n"
                "💬 <b>Butuh Bantuan?</b>\n"
                "Hubungi Admin: @BillFarr\n"
                "Admin akan membantu Anda setup API Key dengan benar."
            )
        else:
            msg = (
                f"⚠️ <b>Tersimpan, tapi verifikasi gagal:</b>\n{err}\n\n"
                "Pastikan API Key dan Secret Key Anda benar, lalu coba lagi.\n\n"
                "💬 <b>Butuh Bantuan?</b>\n"
                "Hubungi Admin: @BillFarr untuk panduan lengkap."
            )
        await loading.edit_text(
            msg,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❓ Tutorial Lengkap",   callback_data="at_howto")],
                [InlineKeyboardButton("🔄 Re-setup API Key", callback_data="at_setup_key")],
                [InlineKeyboardButton("✅ Simpan Saja",     callback_data="at_dashboard")],
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

    # Check real balance from exchange
    keys = get_user_api_keys(user_id)
    try:
        import asyncio
        from app.exchange_registry import get_client as _get_client
        exchange_id = keys.get("exchange", "bitunix") if keys else "bitunix"
        _ex_client = _get_client(exchange_id, keys['api_key'], keys['api_secret'])
        acc = await asyncio.wait_for(
            asyncio.to_thread(_ex_client.get_account_info),
            timeout=3.0
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
        from app.exchange_registry import get_client as _get_client, get_exchange as _get_exchange
        exchange_id = keys.get("exchange", "bitunix")
        ex_cfg = _get_exchange(exchange_id)
        _client = _get_client(exchange_id, keys['api_key'], keys['api_secret'])
        acc = await asyncio.wait_for(
            asyncio.to_thread(_client.get_account_info),
            timeout=8.0
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
            ex_name = ex_cfg.get('name', 'Exchange')
            api_url = ex_cfg.get('api_key_url', '')
            await loading.edit_text(
                f"❌ <b>API Key Ditolak oleh {ex_name}</b>\n\n"
                "⚠️ <b>Masalah:</b> API Key Anda memiliki <b>IP Restriction</b> yang memblokir server bot.\n\n"
                "🔧 <b>Cara Memperbaiki:</b>\n"
                f"1. Login ke {ex_name} → API Management\n"
                "2. Hapus API Key yang lama\n"
                "3. Buat API Key baru:\n"
                "   • Di <b>Bind IP Address</b> → <b>KOSONGKAN</b>\n"
                "   • Centang permission: ✅ Trade / Futures Trading\n"
                "4. Re-setup di bot: /autotrade → Change API Key\n\n"
                "💬 <b>Butuh Bantuan?</b>\n"
                "Hubungi Admin: @BillFarr untuk panduan lengkap.",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❓ Tutorial Lengkap",       callback_data="at_howto")],
                    [InlineKeyboardButton("🔑 Re-setup API Key",    callback_data="at_change_key")],
                ])
            )
        else:
            await loading.edit_text(
                f"❌ <b>Gagal cek balance:</b> {acc.get('error', '')}\n\n"
                "💬 <b>Butuh Bantuan?</b>\n"
                "Hubungi Admin: @BillFarr",
                parse_mode='HTML'
            )
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
        exchange_id=exchange_id,  # Pass exchange_id to engine
    )

    await loading.edit_text(
        f"✅ <b>AutoTrade Active!</b>\n\n"
        f"💵 Capital: {amount} USDT\n"
        f"⚙️ Leverage: {leverage}x\n"
        f"🏦 Exchange: {ex_cfg['name']}\n\n"
        f"Bot is now monitoring the market. You'll receive a notification every time a trade is placed.\n\n"
        f"Use /autotrade to check status or stop.",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")],
            [InlineKeyboardButton("📊 Dashboard",      callback_data="at_dashboard")],
        ])
    )
    return ConversationHandler.END


async def callback_start_engine_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start engine immediately for risk-based mode.
    All settings already saved to database by callback_select_risk_pct.
    """
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Get settings from database
    session = get_autotrade_session(user_id)
    if not session:
        await query.edit_message_text("❌ Session not found. Please restart with /autotrade.")
        return ConversationHandler.END

    amount = float(session.get("initial_deposit", 0))
    leverage = int(session.get("leverage", 10))
    risk_mode = session.get("risk_mode", "manual")

    if amount <= 0:
        await query.edit_message_text("❌ Invalid balance. Please restart with /autotrade.")
        return ConversationHandler.END

    keys = get_user_api_keys(user_id)
    if not keys:
        await query.edit_message_text("❌ API Key not found.")
        return ConversationHandler.END

    # Add progress indicator and loading message
    progress = progress_indicator(4, 4, "Start Trading")
    loading_text = loading_message(
        action="Starting AutoTrade",
        tip="Bot akan otomatis execute trades berdasarkan signal yang masuk"
    )
    loading = await query.edit_message_text(f"{progress}\n\n{loading_text}", parse_mode='HTML')

    try:
        from app.exchange_registry import get_exchange as _get_exchange
        exchange_id = keys.get("exchange", "bitunix")
        ex_cfg = _get_exchange(exchange_id)

        # Cek skill dual_tp_rr3 — has_skill sudah otomatis grant ke admin & premium
        from app.skills_repo import has_skill
        _is_premium = has_skill(user_id, "dual_tp_rr3")

        from app.autotrade_engine import start_engine

        # CRITICAL: Update status to active BEFORE starting engine
        # Otherwise engine will read "stopped" status and immediately stop
        from app.supabase_repo import _client as _sc
        try:
            _sc().table("autotrade_sessions").update({
                "status": "active",
                "engine_active": False  # will be set True by start_engine
            }).eq("telegram_id", user_id).execute()
        except Exception as _e:
            logger.warning(f"[StartEngine:{user_id}] Failed to update status: {_e}")

        start_engine(
            bot=query.get_bot(),
            user_id=user_id,
            api_key=keys['api_key'],
            api_secret=keys['api_secret'],
            amount=amount,
            leverage=leverage,
            notify_chat_id=user_id,
            is_premium=_is_premium,
            exchange_id=exchange_id,
        )

        # Get risk info for display
        risk_pct = session.get("risk_per_trade", 2.0)
        risk_amount = amount * (risk_pct / 100)

        mode_text = "🎯 Recommended" if risk_mode == "risk_based" else "⚙️ Manual"

        # Use success message component
        success_text = success_message(
            "AutoTrade Active!",
            {
                "Mode": mode_text,
                "Balance": f"${amount:.2f} USDT",
                "Risk per trade": f"{risk_pct}% (${risk_amount:.2f})" if risk_mode == "risk_based" else "Fixed margin",
                "Leverage": f"{leverage}x",
                "Exchange": ex_cfg['name']
            }
        )
        
        success_text += (
            "\n🤖 Bot is now monitoring the market. You'll receive a notification every time a trade is placed.\n\n"
            "💡 The system will automatically calculate margin and position size per trade.\n\n"
            "Use /autotrade to check status or stop."
        )

        await loading.edit_text(
            success_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")],
                [InlineKeyboardButton("📊 Dashboard",      callback_data="at_dashboard")],
            ])
        )
    except Exception as e:
        await loading.edit_text(
            f"❌ <b>Failed to start engine:</b> {str(e)[:150]}\n\n"
            "Please try again or contact admin.",
            parse_mode='HTML'
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

    await query.edit_message_text("⏳ Fetching position data...")

    try:
        import asyncio
        from app.exchange_registry import get_client as _get_client

        exchange_id = keys.get("exchange", "bitunix")
        client = _get_client(exchange_id, keys['api_key'], keys['api_secret'])

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
        
        # Check if engine is running
        # Priority 1: Check actual running task
        engine_on = is_running(user_id)
        
        # Priority 2: If task not found but session is active, engine might be starting (auto-restore)
        # Show as "active" to avoid confusion during bot restart
        if not engine_on:
            session = get_autotrade_session(user_id)
            if session and session.get("status") in ("active", "uid_verified"):
                # Engine should be running based on DB, might be starting up
                engine_on = True  # Assume active to avoid user confusion
        
        engine_status = "🟢 Active" if engine_on else "🔴 Inactive"

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

            # Get open trades from DB to get TP/SL prices
            from app.trade_history import get_open_trades
            db_trades = {t.get('symbol'): t for t in get_open_trades(user_id)}

            for p in positions:
                pnl       = p.get('pnl', 0)
                rpnl      = p.get('realized_pnl', 0)
                pnl_emoji = "📈" if pnl >= 0 else "📉"
                side_emoji = "🟢" if p.get('side') == 'BUY' else "🔴"
                entry     = p.get('entry_price', 0)
                mark      = p.get('mark_price', 0)
                liq       = p.get('liq_price', 0)
                lev       = p.get('leverage', '-')
                sym       = p.get('symbol', '?').replace('USDT', '')
                pnl_pct   = ((mark - entry) / entry * 100) if entry > 0 else 0
                if p.get('side') == 'SELL':
                    pnl_pct = -pnl_pct

                # Get TP/SL from DB trade record
                db_trade  = db_trades.get(p.get('symbol'), {})
                tp_price  = float(db_trade.get('tp_price') or p.get('tp_price') or 0)
                sl_price  = float(db_trade.get('sl_price') or p.get('sl_price') or 0)

                pos_line = (
                    f"\n{side_emoji} <b>{sym}</b> {p.get('side')} {lev}x\n"
                    f"  📍 Entry: <code>{entry:.4f}</code>\n"
                    f"  💹 Mark:  <code>{mark:.4f}</code>\n"
                )
                if tp_price > 0:
                    pos_line += f"  🎯 TP:    <code>{tp_price:.4f}</code>\n"
                if sl_price > 0:
                    pos_line += f"  🛡 SL:    <code>{sl_price:.4f}</code>\n"
                if liq and liq > 0:
                    pos_line += f"  ⚠️ Liq:   <code>{liq:.4f}</code>\n"
                pos_line += (
                    f"  📦 Size:  {p.get('size')}\n"
                    f"  {pnl_emoji} uPnL: <b>{pnl:+.4f} USDT</b> ({pnl_pct:+.2f}%)"
                )
                if rpnl != 0:
                    pos_line += f"\n  💰 rPnL: <b>{rpnl:+.4f} USDT</b>"
                lines.append(pos_line)
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
        from app.trade_history import get_trade_history, reconcile_open_trades_with_exchange

        # Self-heal stale "open" rows before rendering. Pulls live positions
        # from the user's exchange and closes any DB row that no longer has
        # a matching position (orphans from restarts, manual closes, missed
        # SL/TP fills, scalping closes the engine never persisted).
        try:
            keys = get_user_api_keys(user_id)
            if keys and keys.get('api_key') and keys.get('api_secret'):
                from app.bitunix_autotrade_client import BitunixAutoTradeClient
                client = BitunixAutoTradeClient(
                    api_key=keys['api_key'],
                    api_secret=keys['api_secret'],
                )
                healed = reconcile_open_trades_with_exchange(user_id, client)
                if healed:
                    import logging as _log
                    _log.getLogger(__name__).info(
                        f"[/history:{user_id}] reconciled {healed} stale open trades"
                    )
        except Exception as _rec_err:
            import logging as _log
            _log.getLogger(__name__).warning(
                f"[/history:{user_id}] reconcile skipped: {_rec_err}"
            )

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
        open_count = 0
        lines      = ["📈 <b>Trade History (last 15)</b>\n"]

        for t in trades:
            side        = t.get("side", "?")
            symbol      = t.get("symbol", "?").replace("USDT", "")
            entry       = float(t.get("entry_price") or 0)
            exit_px     = t.get("exit_price")
            pnl         = t.get("pnl_usdt")
            sl_price    = float(t.get("sl_price") or 0)
            tp_price    = float(t.get("tp_price") or 0)
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
                open_count  += 1
            elif status in ("closed_tp", "closed_tp1", "closed_tp2", "closed_tp3"):
                status_emoji = "✅"
                pnl_val      = float(pnl) if pnl is not None else 0.0
                pnl_line     = f"   📈 PnL: <b>+{pnl_val:.4f} USDT</b>"
                wins += 1
                total_pnl += pnl_val
            elif status in ("closed_sl", "closed_flip"):
                status_emoji = "❌"
                pnl_val      = float(pnl) if pnl is not None else 0.0
                pnl_line     = f"   📉 PnL: <b>{pnl_val:.4f} USDT</b>"
                if loss_reason:
                    short_reason = loss_reason.split(" | ")[0] if " | " in loss_reason else loss_reason
                    pnl_line    += f"\n   💡 <i>{short_reason[:80]}</i>"
                losses += 1
                total_pnl += pnl_val
            else:
                status_emoji = "🔵"
                pnl_val      = float(pnl) if pnl is not None else 0.0
                pnl_line     = f"   PnL: {pnl_val:.4f} USDT" if pnl is not None else ""

            line = (
                f"{status_emoji} {side_emoji} <b>{symbol}</b> {side}{flip_tag} | {leverage}x\n"
                f"   📍 Entry: <code>{entry:.4f}</code>"
            )
            if exit_px:
                line += f" → Exit: <code>{float(exit_px):.4f}</code>"
            # Show SL/TP for open trades
            if status == "open":
                if sl_price > 0:
                    line += f"\n   🛡 SL: <code>{sl_price:.4f}</code>"
                if tp_price > 0:
                    line += f"  🎯 TP: <code>{tp_price:.4f}</code>"
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
            f"⏳ Open: {open_count} positions\n"
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
        # Update status in Supabase — set BOTH status AND engine_active atomically
        try:
            _client().table("autotrade_sessions").update({
                "status": "stopped",
                "engine_active": False,
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
    is_active = session and session.get("status") in ("active", "uid_verified")

    if keys:
        from app.autotrade_engine import is_running as engine_running
        from app.exchange_registry import get_exchange
        from app.trading_mode_manager import TradingModeManager, TradingMode
        from app.market_sentiment_detector import detect_market_condition
        
        # Check if engine is running
        # Priority 1: Check actual running task
        engine_on = engine_running(user_id)
        
        # Priority 2: If task not found but session is active, engine might be starting (auto-restore)
        # Show as "active" to avoid confusion during bot restart
        if not engine_on and session and session.get("status") in ("active", "uid_verified"):
            # Engine should be running based on DB, might be starting up
            engine_on = True  # Assume active to avoid user confusion
        
        engine_status = "🟢 Engine running" if engine_on else "🟡 Engine inactive"
        exchange_id = keys.get("exchange", "bitunix")
        ex_cfg = get_exchange(exchange_id)
        
        # Load trading mode
        trading_mode = TradingModeManager.get_mode(user_id)
        mode_emoji = "⚡" if trading_mode == TradingMode.SCALPING else "📊"
        mode_label = "Scalping (5M)" if trading_mode == TradingMode.SCALPING else "Swing (15M)"
        
        # Get market sentiment
        try:
            sentiment = detect_market_condition("BTC")
            condition = sentiment['condition']
            confidence = sentiment['confidence']
            
            # Emoji based on condition
            if condition == "SIDEWAYS":
                sentiment_emoji = "📊"
                sentiment_color = "🟡"
            elif condition == "TRENDING":
                sentiment_emoji = "📈"
                sentiment_color = "🟢"
            else:
                sentiment_emoji = "⚡"
                sentiment_color = "🟠"
            
            sentiment_text = (
                f"\n{sentiment_emoji} <b>Market Sentiment</b>\n"
                f"{sentiment_color} {condition} ({confidence}%)\n"
                f"💡 Optimal: {sentiment['recommended_mode'].upper()}\n"
            )
        except Exception as e:
            sentiment_text = ""

        engine_btn = (
            [InlineKeyboardButton("🛑 Stop AutoTrade", callback_data="at_stop_engine")]
            if engine_on else
            [InlineKeyboardButton("🚀 Start AutoTrade", callback_data="at_start_engine_now")]
        )

        # Check if user is verified (UID approved) - only show Community Partners if verified
        uid_status = session.get("status", "") if session else ""
        show_community = uid_status in ["uid_verified", "active", "stopped"]
        
        # Build keyboard based on verification status (REMOVED Trading Mode button)
        keyboard_buttons = [
            [InlineKeyboardButton("📊 Status Portfolio",  callback_data="at_status")],
            [InlineKeyboardButton("📈 Trade History",     callback_data="at_history")],
            engine_btn,
            [InlineKeyboardButton("🧠 Bot Skills",        callback_data="skills_menu")],
        ]
        
        # Only add Community Partners button if user is verified
        if show_community:
            keyboard_buttons.append([InlineKeyboardButton("👥 Community Partners", callback_data="community_partners")])
        
        keyboard_buttons.extend([
            [InlineKeyboardButton("⚙️ Settings",          callback_data="at_settings")],
            [InlineKeyboardButton("🔑 Change API Key",    callback_data="at_change_key")],
        ])

        await query.edit_message_text(
            f"🤖 <b>AutoTrade Dashboard</b>\n\n"
            f"{engine_status}\n"
            f"{mode_emoji} Mode: <b>{mode_label}</b> (Auto)\n"
            f"🏦 Exchange: {ex_cfg['name']}\n"
            f"{sentiment_text}\n"
            f"Use the buttons below to manage your AutoTrade:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard_buttons)
        )
    else:
        await query.edit_message_text(
            "🤖 <b>Auto Trade</b>\n\n"
            "⏸ No API Key configured\n\n"
            "Use /autotrade to set up your account.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Setup API Key", callback_data="at_setup_key")]
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

    if not keys or not session or session.get("status") not in ("active", "uid_verified"):
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

    exchange_id = keys.get("exchange", "bitunix")
    start_engine(
        bot=query.get_bot(),
        user_id=user_id,
        api_key=keys["api_key"],
        api_secret=keys["api_secret"],
        amount=amount,
        leverage=leverage,
        notify_chat_id=user_id,
        is_premium=_is_premium,
        exchange_id=exchange_id,
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
        query.message.text + f"\n\n✅ <b>Approved by admin</b>",
        parse_mode='HTML'
    )

    # Notify user
    try:
        # Cek apakah user sudah punya API key
        existing_keys = get_user_api_keys(target_user_id)

        if existing_keys:
            # API key sudah ada — langsung arahkan ke risk mode selection
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "✅ <b>UID Kamu Sudah Diverifikasi!</b>\n\n"
                    "Akun Bitunix kamu sudah terkonfirmasi di bawah referral kami.\n\n"
                    "API Key kamu sudah tersimpan sebelumnya.\n"
                    "Ketik /autotrade untuk melanjutkan setup risk management."
                ),
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 Choose Risk Mode", callback_data="at_choose_risk_mode")]
                ])
            )
        else:
            # Belum ada API key — minta setup
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "✅ <b>UID Kamu Sudah Diverifikasi!</b>\n\n"
                    "Akun Bitunix kamu sudah terkonfirmasi di bawah referral kami.\n\n"
                    "Sekarang setup API Key untuk mulai Auto Trade:"
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
    # Register standalone /start handler FIRST (highest priority)
    # This ensures /start always responds, even outside conversation
    application.add_handler(CommandHandler("start", cmd_autotrade), group=0)
    
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
            WAITING_MANUAL_MARGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_manual_margin),
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
    application.add_handler(CallbackQueryHandler(callback_start_engine_now,   pattern="^at_start_engine_now$"))
    application.add_handler(CallbackQueryHandler(callback_stop_engine,        pattern="^at_stop_engine$"))
    application.add_handler(CallbackQueryHandler(callback_restart_engine,     pattern="^at_restart_engine$"))
    application.add_handler(CallbackQueryHandler(callback_settings,           pattern="^at_settings$"))
    application.add_handler(CallbackQueryHandler(callback_toggle_auto_mode,   pattern="^at_toggle_auto_mode$"))
    application.add_handler(CallbackQueryHandler(callback_set_margin,         pattern="^at_set_margin$"))
    application.add_handler(CallbackQueryHandler(callback_margin_select,      pattern="^at_margin_(cross|isolated)$"))
    application.add_handler(CallbackQueryHandler(callback_new_leverage_select,pattern="^at_newlev_\\d+$"))
    
    # Risk Management handlers
    application.add_handler(CallbackQueryHandler(callback_risk_settings,      pattern="^at_risk_settings$"))
    application.add_handler(CallbackQueryHandler(callback_set_risk,           pattern="^at_set_risk_[1235]$"))
    application.add_handler(CallbackQueryHandler(callback_risk_education,     pattern="^at_risk_edu$"))
    application.add_handler(CallbackQueryHandler(callback_risk_simulator,     pattern="^at_risk_sim$"))
    
    # Risk Mode Selection handlers (new dual mode system)
    from app.handlers_risk_mode import (
        callback_choose_risk_mode,
        callback_mode_risk_based,
        callback_select_risk_pct,
        callback_mode_manual,
        callback_switch_risk_mode
    )
    application.add_handler(CallbackQueryHandler(callback_choose_risk_mode,   pattern="^at_choose_risk_mode$"))
    application.add_handler(CallbackQueryHandler(callback_mode_risk_based,    pattern="^at_mode_risk_based$"))
    application.add_handler(CallbackQueryHandler(callback_select_risk_pct,    pattern="^at_risk_[1235]$"))
    application.add_handler(CallbackQueryHandler(callback_mode_manual,        pattern="^at_mode_manual$"))
    application.add_handler(CallbackQueryHandler(callback_switch_risk_mode,   pattern="^at_switch_risk_mode$"))
    
    # Multi-exchange callbacks
    application.add_handler(CallbackQueryHandler(callback_select_exchange,    pattern="^at_exchange_\\w+$"))
    application.add_handler(CallbackQueryHandler(callback_change_exchange,    pattern="^at_change_exchange$"))
    # No-op untuk tombol coming soon
    application.add_handler(CallbackQueryHandler(
        lambda u, c: u.callback_query.answer("🔜 Coming Soon!", show_alert=False),
        pattern="^at_noop$"
    ))
    application.add_handler(CallbackQueryHandler(callback_new_amount_select,  pattern="^at_newamt_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_why_referral,       pattern="^at_why_referral$"))
    application.add_handler(CallbackQueryHandler(callback_uid_acc,            pattern="^uid_acc_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_uid_reject,         pattern="^uid_reject_\\d+$"))
    application.add_handler(CallbackQueryHandler(callback_status_portfolio,   pattern="^at_status$"))
    application.add_handler(CallbackQueryHandler(callback_trade_history,      pattern="^at_history$"))
    
    # Trading Mode handlers
    application.add_handler(CallbackQueryHandler(callback_trading_mode_menu,  pattern="^trading_mode_menu$"))
    application.add_handler(CallbackQueryHandler(callback_select_scalping,    pattern="^mode_select_scalping$"))
    application.add_handler(CallbackQueryHandler(callback_select_swing,       pattern="^mode_select_swing$"))

    # Skills handlers
    from app.handlers_skills import register_skills_handlers
    register_skills_handlers(application)

    # at_back_dashboard → redirect ke cmd_autotrade flow
    async def _back_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await callback_dashboard(update, context)

    application.add_handler(CallbackQueryHandler(_back_dashboard, pattern="^at_back_dashboard$"))

    # Reminder callbacks: tombol dari pesan reminder harian
    async def _reminder_start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User klik 'Daftar AutoTrade' dari pesan reminder — arahkan ke exchange selector."""
        query = update.callback_query
        await query.answer()
        from app.exchange_registry import exchange_list_keyboard
        await query.edit_message_text(
            "🤖 <b>Auto Trade — Pilih Exchange</b>\n\n"
            "Kami support beberapa exchange terpercaya.\n"
            "Pilih exchange yang ingin kamu gunakan:",
            parse_mode='HTML',
            reply_markup=exchange_list_keyboard()
        )

    async def _reminder_learn_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User klik 'Pelajari Lebih Lanjut' dari pesan reminder."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📚 <b>AutoTrade — Cara Kerja Lengkap</b>\n\n"
            "<b>Apa itu AutoTrade?</b>\n"
            "Bot trading otomatis yang terhubung ke akun exchange kamu via API Key.\n\n"
            "<b>Teknologi yang digunakan:</b>\n"
            "• Smart Money Concept (SMC) — analisa institusional\n"
            "• Supply & Demand Zone detection\n"
            "• Change of Character (CHoCH) untuk konfirmasi entry\n"
            "• Multi-timeframe analysis (15m, 1H, 4H)\n\n"
            "<b>Exchange yang didukung:</b>\n"
            "• Binance Futures\n"
            "• Bybit Futures\n"
            "• Bitunix Futures\n\n"
            "<b>Keamanan:</b>\n"
            "• API Key hanya izin Trade (tidak bisa withdraw)\n"
            "• Dana tetap di exchange kamu\n"
            "• Enkripsi AES-256-GCM\n\n"
            "Siap mulai? Klik tombol di bawah 👇",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Mulai Setup AutoTrade", callback_data="at_start_onboarding")],
            ])
        )

    application.add_handler(CallbackQueryHandler(_reminder_start_onboarding, pattern="^at_start_onboarding$"))
    application.add_handler(CallbackQueryHandler(_reminder_learn_more,        pattern="^at_learn_more$"))

    print("✅ AutoTrade handlers registered (Supabase + AES-256-GCM + Engine)")
