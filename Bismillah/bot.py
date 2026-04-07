#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Clean Main Bot Class
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

logger = logging.getLogger(__name__)

_menu_handlers_loaded = False


def _lazy_load_menu():
    global _menu_handlers_loaded
    if not _menu_handlers_loaded:
        from menu_handlers import register_menu_handlers
        _menu_handlers_loaded = True
    from menu_handlers import register_menu_handlers
    return register_menu_handlers


class TelegramBot:
    def __init__(self):
        import time
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found")
        self.application = None
        self.admin_ids = self._load_admin_ids()
        self.start_time = time.time()
        self._ai_assistant = None
        self._crypto_api = None
        print(f"✅ Bot initialized with {len(self.admin_ids)} admin(s)")

    @property
    def ai_assistant(self):
        if self._ai_assistant is None:
            from services import get_ai_assistant
            self._ai_assistant = get_ai_assistant()
        return self._ai_assistant

    @property
    def crypto_api(self):
        if self._crypto_api is None:
            from services import get_crypto_api
            self._crypto_api = get_crypto_api()
        return self._crypto_api

    def _load_admin_ids(self):
        admin_ids = set()
        for key in ['ADMIN_IDS', 'ADMIN1', 'ADMIN2', 'ADMIN_USER_ID', 'ADMIN2_USER_ID']:
            value = os.getenv(key)
            if value:
                try:
                    if ',' in value:
                        admin_ids.update(int(a.strip()) for a in value.split(',') if a.strip())
                    else:
                        admin_ids.add(int(value))
                except ValueError:
                    continue
        return admin_ids

    async def setup_application(self):
        from telegram.request import HTTPXRequest
        # Optimasi koneksi: pool besar + timeout lebih tinggi untuk latency VPS
        request = HTTPXRequest(
            connection_pool_size=16,   # lebih banyak koneksi paralel
            read_timeout=30,           # beri waktu lebih untuk Telegram reply
            write_timeout=30,
            connect_timeout=15,
            pool_timeout=10,
        )
        self.application = Application.builder().token(self.token).request(request).build()

        # Core commands
        # NOTE: /start is handled by AutoTrade ConversationHandler (registered later)
        self.application.add_handler(CommandHandler("menu", self.menu_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("market", self.market_command))
        self.application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        self.application.add_handler(CommandHandler("credits", self.credits_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("referral", self.referral_command))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("id", self.id_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))

        # Signal handlers
        try:
            from app.handlers_manual_signals import cmd_analyze, cmd_futures, cmd_futures_signals, cmd_signal, cmd_signals
            self.application.add_handler(CommandHandler("analyze", cmd_analyze))
            self.application.add_handler(CommandHandler("futures", cmd_futures))
            self.application.add_handler(CommandHandler("futures_signals", cmd_futures_signals))
            self.application.add_handler(CommandHandler("signal", cmd_signal))
            self.application.add_handler(CommandHandler("signals", cmd_signals))
            print("✅ Signal handlers registered")
        except Exception as e:
            print(f"⚠️ Signal handlers failed: {e}")
            self.application.add_handler(CommandHandler("analyze", self.analyze_command))
            self.application.add_handler(CommandHandler("futures", self.futures_command))
            self.application.add_handler(CommandHandler("futures_signals", self.futures_signals_command))
            self.application.add_handler(CommandHandler("signal", self.signal_command))
            self.application.add_handler(CommandHandler("signals", self.signals_command))

        # Admin premium handlers
        try:
            from app.handlers_admin_premium import cmd_set_premium, cmd_revoke_premium, cmd_remove_premium, cmd_grant_credits
            self.application.add_handler(CommandHandler("set_premium", cmd_set_premium))
            self.application.add_handler(CommandHandler("setpremium", cmd_set_premium))
            self.application.add_handler(CommandHandler("remove_premium", cmd_remove_premium))
            self.application.add_handler(CommandHandler("revoke_premium", cmd_revoke_premium))
            self.application.add_handler(CommandHandler("grant_credits", cmd_grant_credits))
            print("✅ Admin premium handlers registered")
        except Exception as e:
            print(f"⚠️ Admin premium handlers failed: {e}")

        # Admin callback handler (before menu handlers)
        self.application.add_handler(CallbackQueryHandler(self.admin_button_handler, pattern=r'^admin_'))
        self.application.add_handler(CallbackQueryHandler(self.signal_callback_handler, pattern=r'^signal_tf_'))

        # AutoTrade — harus didaftarkan SEBELUM menu handlers agar ConversationHandler tidak tertimpa
        try:
            from app.handlers_autotrade import register_autotrade_handlers
            register_autotrade_handlers(self.application)
            print("✅ AutoTrade handlers registered")
        except Exception as e:
            print(f"⚠️ AutoTrade handlers failed: {e}")

        # Community Partners
        try:
            from app.handlers_community import register_community_handlers
            register_community_handlers(self.application)
        except Exception as e:
            print(f"⚠️ Community handlers failed: {e}")

        # Menu system
        register_menu_handlers = _lazy_load_menu()
        register_menu_handlers(self.application, self)

        # Auto signal admin
        try:
            from app.handlers_autosignal_admin import cmd_signal_on, cmd_signal_off, cmd_signal_status, cmd_signal_tick
            self.application.add_handler(CommandHandler("signal_on", cmd_signal_on))
            self.application.add_handler(CommandHandler("signal_off", cmd_signal_off))
            self.application.add_handler(CommandHandler("signal_status", cmd_signal_status))
            self.application.add_handler(CommandHandler("signal_tick", cmd_signal_tick))
            print("✅ Auto signal admin registered")
        except Exception as e:
            print(f"⚠️ Auto signal admin failed: {e}")

        # AI handlers
        try:
            from app.handlers_deepseek import handle_ai_analyze, handle_ai_chat, handle_ai_market_summary
            self.application.add_handler(CommandHandler("ai", handle_ai_analyze))
            self.application.add_handler(CommandHandler("chat", handle_ai_chat))
            self.application.add_handler(CommandHandler("aimarket", handle_ai_market_summary))
            print("✅ AI handlers registered")
        except Exception as e:
            print(f"⚠️ AI handlers failed: {e}")

        # Free signal
        try:
            from app.handlers_free_signal import register_free_signal_handlers
            register_free_signal_handlers(self.application)
            print("✅ Free signal handlers registered")
        except Exception as e:
            print(f"⚠️ Free signal handlers failed: {e}")

        # Server IP command (admin only)
        self.application.add_handler(CommandHandler("serverip", self.serverip_command))

        # Message handler
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        print("✅ All handlers registered")


    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            from app.chat_store import remember_chat
            remember_chat(update.effective_user.id, update.effective_chat.id)
        except Exception:
            pass
        from menu_system import MenuBuilder, get_menu_text, MAIN_MENU
        await update.message.reply_text(
            get_menu_text(MAIN_MENU),
            reply_markup=MenuBuilder.build_main_menu(),
            parse_mode='MARKDOWN'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📚 *CryptoMentor AI - Commands*\n\n"
            "📊 *Signals:*\n"
            "/analyze <symbol> - Spot analysis\n"
            "/futures <symbol> - Futures analysis\n"
            "/signal <symbol> - Quick signal\n"
            "/free_signal <symbol> - Free signal (Premium)\n\n"
            "💰 *Trading:*\n"
            "/autotrade - AutoTrade menu (Bitunix)\n\n"
            "🤖 *AI:*\n"
            "/ai <symbol> - AI analysis\n"
            "/chat <question> - AI chat\n\n"
            "📈 *Market:*\n"
            "/price <symbol> - Check price\n"
            "/market - Market overview\n\n"
            "👤 *Account:*\n"
            "/credits - Check credits\n"
            "/subscribe - Upgrade premium\n"
            "/referral - Referral program\n"
            "/menu - Show menu",
            parse_mode='MARKDOWN'
        )

    async def id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        await update.message.reply_text(
            f"🆔 Your Telegram ID: `{user.id}`\n"
            f"👤 Username: @{user.username or 'N/A'}\n"
            f"📛 Name: {user.first_name}",
            parse_mode='MARKDOWN'
        )

    async def serverip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command: tampilkan IP server Railway untuk whitelist Bitunix."""
        user_id = update.effective_user.id
        if user_id not in self.admin_ids:
            await update.message.reply_text("❌ Admin only.")
            return
        msg = await update.message.reply_text("⏳ Mengambil IP server...")
        try:
            import asyncio, requests as _req
            ip = await asyncio.to_thread(
                lambda: _req.get("https://api.ipify.org?format=json", timeout=5).json()["ip"]
            )
            await msg.edit_text(
                f"🌐 <b>IP Server Railway:</b>\n\n"
                f"<code>{ip}</code>\n\n"
                f"Masukkan IP ini ke kolom <b>Bind IP address</b> saat buat/edit API Key di Bitunix.",
                parse_mode='HTML'
            )
        except Exception as e:
            await msg.edit_text(f"❌ Gagal ambil IP: {e}")

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol = context.args[0].upper() if context.args else 'BTC'
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        await update.message.reply_text(f"⏳ Fetching price for {symbol}...")
        try:
            import requests
            r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}", timeout=10)
            data = r.json()
            if 'price' in data or 'lastPrice' in data:
                price = float(data.get('lastPrice', data.get('price', 0)))
                change = float(data.get('priceChangePercent', 0))
                emoji = "🟢" if change >= 0 else "🔴"
                await update.message.reply_text(
                    f"💰 *{symbol}*\n\n"
                    f"Price: `${price:,.4f}`\n"
                    f"{emoji} 24h Change: `{change:+.2f}%`\n"
                    f"High: `${float(data.get('highPrice',0)):,.4f}`\n"
                    f"Low: `${float(data.get('lowPrice',0)):,.4f}`",
                    parse_mode='MARKDOWN'
                )
            else:
                await update.message.reply_text(f"❌ Symbol {symbol} not found.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Loading market overview...")
        try:
            import requests
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
            lines = ["📊 *Market Overview*\n"]
            for sym in symbols:
                r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}", timeout=5)
                d = r.json()
                price = float(d.get('lastPrice', 0))
                change = float(d.get('priceChangePercent', 0))
                emoji = "🟢" if change >= 0 else "🔴"
                name = sym.replace('USDT', '')
                lines.append(f"{emoji} *{name}*: ${price:,.2f} ({change:+.2f}%)")
            await update.message.reply_text('\n'.join(lines), parse_mode='MARKDOWN')
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📊 *Portfolio*\n\nGunakan /menu → Portfolio & Credits untuk melihat portfolio Anda.",
            parse_mode='MARKDOWN'
        )

    async def credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        try:
            from app.credits_guard import check_credits_balance
            is_premium, credits = check_credits_balance(user_id)
            if is_premium:
                status = "👑 Premium/Lifetime - Unlimited access"
                credits_text = "∞ Unlimited"
            else:
                status = "👤 Free User"
                credits_text = f"{credits} credits"
            await update.message.reply_text(
                f"💳 *Credits Balance*\n\n"
                f"Status: {status}\n"
                f"Credits: {credits_text}\n\n"
                f"Gunakan /subscribe untuk upgrade Premium.",
                parse_mode='MARKDOWN'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error checking credits: {e}")

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👑 *Upgrade Premium*\n\n"
            "Hubungi admin untuk upgrade:\n"
            "• Premium 30 hari\n"
            "• Lifetime Premium\n\n"
            "Contact: @BillFarr",
            parse_mode='MARKDOWN'
        )

    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        await update.message.reply_text(
            f"🔗 *Referral Program*\n\n"
            f"Share link referral Anda dan dapatkan reward!\n\n"
            f"Link: `https://t.me/CryptoMentorAIBot?start=ref_{user_id}`",
            parse_mode='MARKDOWN'
        )

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="set_lang_id")],
            [InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")]
        ])
        await update.message.reply_text("🌐 Select language:", reply_markup=keyboard)

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol = context.args[0].upper() if context.args else 'BTC'
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        await update.message.reply_text(
            f"⏳ Analyzing {symbol}...\n\nGunakan /menu → Trading Analysis untuk analisis lengkap."
        )

    async def futures_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol = context.args[0].upper() if context.args else 'BTC'
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
        await update.message.reply_text(
            f"⏳ Futures analysis {symbol}...\n\nGunakan /menu → Trading Analysis untuk analisis lengkap."
        )

    async def futures_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Generating futures signals...\n\nGunakan /menu → Futures Signals.")

    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        symbol = context.args[0].upper() if context.args else 'BTC'
        await update.message.reply_text(f"⏳ Generating signal for {symbol}...")

    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Generating signals...\n\nGunakan /menu → Futures Signals.")

    async def signal_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        data = query.data  # signal_tf_SYMBOL_TIMEFRAME
        parts = data.split('_')
        if len(parts) >= 4:
            symbol = parts[2]
            timeframe = parts[3]
            await query.edit_message_text(f"⏳ Analyzing {symbol} {timeframe}...")


    def _admin_main_keyboard(self):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 Add Premium",     callback_data="admin_add_premium"),
             InlineKeyboardButton("❌ Remove Premium",  callback_data="admin_remove_premium")],
            [InlineKeyboardButton("♾️ Set Lifetime",    callback_data="admin_set_lifetime"),
             InlineKeyboardButton("💰 Add Credits",     callback_data="admin_add_credits")],
            [InlineKeyboardButton("📊 User Stats",      callback_data="admin_user_stats"),
             InlineKeyboardButton("📡 Signal On/Off",   callback_data="admin_signal_control")],
            [InlineKeyboardButton("📢 Broadcast",       callback_data="admin_broadcast")],
        ])

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in self.admin_ids:
            await update.message.reply_text("❌ Access denied.")
            return
        await update.message.reply_text(
            f"🔧 *Admin Panel*\n\nWelcome, Admin `{user_id}`",
            reply_markup=self._admin_main_keyboard(),
            parse_mode='MARKDOWN'
        )

    async def admin_button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        if user_id not in self.admin_ids:
            await query.answer("❌ Access denied", show_alert=True)
            return
        await query.answer()
        data = query.data

        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])

        # ── Navigation ──────────────────────────────────────────────
        if data == "admin_back":
            context.user_data.clear()
            await query.edit_message_text(
                f"🔧 *Admin Panel*\n\nWelcome, Admin `{user_id}`",
                reply_markup=self._admin_main_keyboard(),
                parse_mode='MARKDOWN'
            )

        elif data == "admin_cancel":
            context.user_data.clear()
            await query.edit_message_text(
                "✅ Dibatalkan.",
                reply_markup=self._admin_main_keyboard()
            )

        # ── Add Premium ──────────────────────────────────────────────
        elif data == "admin_add_premium":
            context.user_data['awaiting_input'] = 'admin_add_premium'
            await query.edit_message_text(
                "👑 *Add Premium*\n\nFormat: `user_id days`\nContoh: `123456789 30`",
                parse_mode='MARKDOWN', reply_markup=back_kb
            )

        # ── Remove Premium ───────────────────────────────────────────
        elif data == "admin_remove_premium":
            context.user_data['awaiting_input'] = 'admin_remove_premium'
            await query.edit_message_text(
                "❌ *Remove Premium*\n\nMasukkan `user_id`:",
                parse_mode='MARKDOWN', reply_markup=back_kb
            )

        # ── Set Lifetime ─────────────────────────────────────────────
        elif data == "admin_set_lifetime":
            context.user_data['awaiting_input'] = 'admin_set_lifetime'
            await query.edit_message_text(
                "♾️ *Set Lifetime*\n\nMasukkan `user_id`:",
                parse_mode='MARKDOWN', reply_markup=back_kb
            )

        # ── Add Credits ──────────────────────────────────────────────
        elif data == "admin_add_credits":
            context.user_data['awaiting_input'] = 'admin_add_credits_manual'
            await query.edit_message_text(
                "💰 *Add Credits*\n\nFormat: `user_id amount`\nContoh: `123456789 500`",
                parse_mode='MARKDOWN', reply_markup=back_kb
            )

        # ── User Stats ───────────────────────────────────────────────
        elif data == "admin_user_stats":
            try:
                from app.supabase_repo import _client
                s = _client()
                # Total users
                total_res = s.table("users").select("telegram_id", count="exact").execute()
                total = total_res.count or len(total_res.data or [])
                # Premium users
                prem_res = s.table("users").select("telegram_id", count="exact").eq("is_premium", True).execute()
                premium = prem_res.count or len(prem_res.data or [])
                # Lifetime users
                life_res = s.table("users").select("telegram_id", count="exact").eq("is_lifetime", True).execute()
                lifetime = life_res.count or len(life_res.data or [])
                # New today
                from datetime import datetime, timedelta
                today = (datetime.utcnow() - timedelta(hours=0)).strftime('%Y-%m-%d')
                new_res = s.table("users").select("telegram_id", count="exact").gte("created_at", today).execute()
                new_today = new_res.count or len(new_res.data or [])

                await query.edit_message_text(
                    f"📊 *User Statistics*\n\n"
                    f"👥 Total Users: `{total}`\n"
                    f"⭐ Premium: `{premium}`\n"
                    f"♾️ Lifetime: `{lifetime}`\n"
                    f"🆕 New Today: `{new_today}`\n"
                    f"🆓 Free Users: `{total - premium}`",
                    parse_mode='MARKDOWN',
                    reply_markup=back_kb
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Error stats: {e}", reply_markup=back_kb)

        # ── Signal On/Off ────────────────────────────────────────────
        elif data == "admin_signal_control":
            try:
                from app.scheduler import get_signal_status, toggle_signal
                status = get_signal_status()
                status_text = "🟢 ON" if status else "🔴 OFF"
                await query.edit_message_text(
                    f"📡 *Auto Signal Control*\n\nStatus saat ini: {status_text}",
                    parse_mode='MARKDOWN',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🟢 Turn ON",  callback_data="admin_signal_on"),
                         InlineKeyboardButton("🔴 Turn OFF", callback_data="admin_signal_off")],
                        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
                    ])
                )
            except Exception as e:
                await query.edit_message_text(f"❌ Error signal control: {e}", reply_markup=back_kb)

        elif data == "admin_signal_on":
            try:
                from app.scheduler import toggle_signal
                toggle_signal(True)
                await query.edit_message_text("✅ Auto Signal *ON*", parse_mode='MARKDOWN', reply_markup=back_kb)
            except Exception as e:
                await query.edit_message_text(f"❌ Error: {e}", reply_markup=back_kb)

        elif data == "admin_signal_off":
            try:
                from app.scheduler import toggle_signal
                toggle_signal(False)
                await query.edit_message_text("🔴 Auto Signal *OFF*", parse_mode='MARKDOWN', reply_markup=back_kb)
            except Exception as e:
                await query.edit_message_text(f"❌ Error: {e}", reply_markup=back_kb)

        # ── Broadcast ────────────────────────────────────────────────
        elif data == "admin_broadcast":
            context.user_data['awaiting_input'] = 'admin_broadcast'
            await query.edit_message_text(
                "📢 *Broadcast ke Semua User*\n\n"
                "Ketik pesan yang ingin dikirim ke semua user di Supabase.\n\n"
                "⚠️ Pesan akan dikirim ke semua user yang pernah pakai bot.\n"
                "Supports HTML formatting.",
                parse_mode='MARKDOWN',
                reply_markup=back_kb
            )


    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        try:
            from app.chat_store import remember_chat
            remember_chat(update.effective_user.id, update.effective_chat.id)
        except Exception:
            pass

        user_data = context.user_data
        text = update.message.text.strip()

        # Handle admin awaiting inputs
        awaiting = user_data.get('awaiting_input')
        if awaiting:
            parts = text.split()
            try:
                from services import get_database
                db = get_database()

                if awaiting == 'admin_add_premium':
                    if len(parts) < 2:
                        await update.message.reply_text("Format: `user_id days`", parse_mode='MARKDOWN')
                        return
                    uid, days = int(parts[0]), int(parts[1])
                    premium_until = datetime.utcnow() + timedelta(days=days)
                    db.set_user_premium(uid, premium_until)
                    try:
                        from app.supabase_repo import set_premium_normalized
                        set_premium_normalized(uid, f'{days}d')
                    except Exception:
                        pass
                    await update.message.reply_text(f"✅ Premium added!\nUser: `{uid}`\nDays: {days}", parse_mode='MARKDOWN')
                    try:
                        await context.bot.send_message(uid,
                            f"🎉 Anda mendapat Premium {days} hari!\nBerlaku hingga: {premium_until.strftime('%Y-%m-%d')}")
                    except Exception:
                        pass

                elif awaiting == 'admin_remove_premium':
                    uid = int(parts[0])
                    db.remove_user_premium(uid)
                    try:
                        from app.supabase_repo import revoke_premium
                        revoke_premium(uid)
                    except Exception:
                        pass
                    await update.message.reply_text(f"✅ Premium removed for user `{uid}`", parse_mode='MARKDOWN')
                    try:
                        await context.bot.send_message(uid, "ℹ️ Status premium Anda telah dicabut.")
                    except Exception:
                        pass

                elif awaiting == 'admin_set_lifetime':
                    uid = int(parts[0])
                    db.set_user_lifetime(uid, True)
                    try:
                        from app.supabase_repo import set_premium_normalized
                        set_premium_normalized(uid, 'lifetime')
                    except Exception:
                        pass
                    await update.message.reply_text(f"✅ Lifetime set for user `{uid}`", parse_mode='MARKDOWN')
                    try:
                        await context.bot.send_message(uid, "🎉 Anda mendapat Lifetime Premium!")
                    except Exception:
                        pass

                elif awaiting == 'admin_add_credits_manual':
                    if len(parts) < 2:
                        await update.message.reply_text("Format: `user_id amount`", parse_mode='MARKDOWN')
                        return
                    uid, credits_amt = int(parts[0]), int(parts[1])
                    db.add_user_credits(uid, credits_amt)
                    # Also update Supabase
                    try:
                        from app.supabase_repo import _client
                        s = _client()
                        # Get current credits first
                        res = s.table("users").select("credits").eq("telegram_id", uid).execute()
                        current = int(res.data[0].get('credits', 0)) if res.data else 0
                        s.table("users").update({"credits": current + credits_amt}).eq("telegram_id", uid).execute()
                    except Exception as sup_e:
                        print(f"Supabase credits update error: {sup_e}")
                    await update.message.reply_text(f"✅ Added `{credits_amt}` credits to user `{uid}`", parse_mode='MARKDOWN')
                    try:
                        await context.bot.send_message(uid, f"💰 {credits_amt} credits telah ditambahkan ke akun Anda!")
                    except Exception:
                        pass

                elif awaiting == 'admin_broadcast':
                    # Broadcast to all users in Supabase
                    broadcast_text = text  # raw text, supports HTML
                    await update.message.reply_text("⏳ Memulai broadcast...")
                    try:
                        from app.supabase_repo import _client
                        s = _client()
                        # Fetch all telegram_ids in batches
                        all_ids = []
                        page = 0
                        page_size = 1000
                        while True:
                            res = s.table("users").select("telegram_id").range(page * page_size, (page + 1) * page_size - 1).execute()
                            if not res.data:
                                break
                            all_ids.extend([r['telegram_id'] for r in res.data])
                            if len(res.data) < page_size:
                                break
                            page += 1

                        sent = 0
                        failed = 0
                        for tid in all_ids:
                            try:
                                await context.bot.send_message(
                                    chat_id=tid,
                                    text=broadcast_text,
                                    parse_mode='HTML'
                                )
                                sent += 1
                            except Exception as send_err:
                                err_str = str(send_err)
                                # Skip common expected errors silently
                                if not any(x in err_str for x in ('blocked', 'deactivated', 'not found', 'chat not found')):
                                    print(f"Broadcast error tid={tid}: {err_str[:80]}")
                                failed += 1
                            # Small delay to avoid flood
                            if sent % 30 == 0:
                                import asyncio
                                await asyncio.sleep(1)

                        await update.message.reply_text(
                            f"📢 *Broadcast selesai!*\n\n"
                            f"✅ Terkirim: `{sent}`\n"
                            f"❌ Gagal: `{failed}`\n"
                            f"👥 Total: `{len(all_ids)}`",
                            parse_mode='MARKDOWN'
                        )
                    except Exception as bc_e:
                        await update.message.reply_text(f"❌ Broadcast error: {bc_e}")

            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")
            finally:
                user_data.pop('awaiting_input', None)
                user_data.pop('state_timestamp', None)
            return

        # Handle symbol input
        if user_data.get('awaiting_manual_symbol'):
            symbol = text.upper().strip()
            # Strip USDT suffix if user typed it, then re-add cleanly
            base = symbol.replace('USDT', '').replace('/', '').strip()
            if not base:
                await update.message.reply_text("❌ Symbol tidak valid. Contoh: BTC, ETH, SOL")
                return
            symbol = base + 'USDT'
            user_data['awaiting_manual_symbol'] = False
            user_data['symbol'] = symbol
            action = user_data.get('current_action', '')

            if action == 'price':
                context.args = [symbol]
                await self.price_command(update, context)

            elif action == 'analyze':
                # Spot analysis - run directly via menu handler
                from menu_system import MenuBuilder
                msg = await update.message.reply_text(
                    f"⏳ <b>Analyzing {base}...</b>\n\nFetching Binance data...",
                    parse_mode='HTML'
                )
                # Reuse the execute_analyze_command logic via a fake query-like object
                import asyncio
                from smc_analyzer import SMCAnalyzer
                from app.credits_guard import require_credits

                user_id = update.effective_user.id
                chat_id = update.effective_chat.id
                message_id = msg.message_id

                ok, remain, credit_msg = require_credits(user_id, 20)
                if not ok:
                    await context.bot.edit_message_text(
                        chat_id=chat_id, message_id=message_id,
                        text=f"❌ {credit_msg}\n\nUpgrade ke Premium untuk akses unlimited!"
                    )
                    return

                async def run_spot():
                    try:
                        analyzer = SMCAnalyzer()
                        result = await asyncio.to_thread(analyzer.analyze, symbol, '1h', 200)
                        if 'error' in result:
                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=f"❌ Error: {result['error']}", parse_mode='HTML')
                            return
                        current_price = result.get('current_price', 0)
                        order_blocks = result.get('order_blocks', [])
                        structure = result.get('structure')
                        ema_21 = result.get('ema_21', 0)

                        def fmt_price(p):
                            if p >= 1000: return f"${p:,.2f}"
                            elif p >= 1: return f"${p:,.4f}"
                            elif p >= 0.0001: return f"${p:.6f}"
                            else: return f"${p:.8f}"

                        trend = structure.trend if structure else 'ranging'
                        bullish_obs = [ob for ob in order_blocks if ob.type == 'bullish']
                        bearish_obs = [ob for ob in order_blocks if ob.type == 'bearish']

                        if trend == 'uptrend' or (bullish_obs and not bearish_obs):
                            sentiment, sentiment_emoji = "BULLISH", "🟢"
                        elif trend == 'downtrend' or (bearish_obs and not bullish_obs):
                            sentiment, sentiment_emoji = "BEARISH", "🔴"
                        elif bullish_obs and bearish_obs:
                            best_bull = max(bullish_obs, key=lambda x: x.strength)
                            best_bear = max(bearish_obs, key=lambda x: x.strength)
                            sentiment, sentiment_emoji = ("BULLISH", "🟢") if best_bull.strength > best_bear.strength else ("BEARISH", "🔴")
                        else:
                            sentiment, sentiment_emoji = "SIDEWAYS", "🟡"

                        best_ob = order_blocks[0] if order_blocks else None
                        confidence = int(best_ob.strength) if best_ob else 55

                        response = (
                            f"📊 <b>SPOT ANALYSIS: {base} (1H)</b>\n\n"
                            f"💰 Current Price: {fmt_price(current_price)}\n"
                            f"{sentiment_emoji} Market Sentiment: <b>{sentiment}</b>\n"
                            f"✅ Confidence: {confidence}%\n\n"
                        )
                        if sentiment == "BULLISH" and bullish_obs:
                            response += "🟢 <b>BUY ZONES (SMC Order Blocks):</b>\n"
                            for i, ob in enumerate(bullish_obs[:3], 1):
                                zw = ob.high - ob.low
                                response += (f"\n<b>Zone {i}</b>\n📍 Entry: {fmt_price(ob.low)} – {fmt_price(ob.high)}\n"
                                             f"🎯 TP1: {fmt_price(ob.high + zw*1.5)}\n🎯 TP2: {fmt_price(ob.high + zw*3)}\n"
                                             f"🛑 SL: {fmt_price(ob.low - zw*0.5)}\n💪 Strength: {int(ob.strength)}%\n")
                        elif sentiment == "BEARISH" and bearish_obs:
                            response += "🔴 <b>SHORT ZONES (SMC Order Blocks):</b>\n"
                            for i, ob in enumerate(bearish_obs[:3], 1):
                                zw = ob.high - ob.low
                                response += (f"\n<b>Zone {i}</b>\n📍 Entry: {fmt_price(ob.low)} – {fmt_price(ob.high)}\n"
                                             f"🎯 TP1: {fmt_price(ob.low - zw*1.5)}\n🎯 TP2: {fmt_price(ob.low - zw*3)}\n"
                                             f"🛑 SL: {fmt_price(ob.high + zw*0.5)}\n💪 Strength: {int(ob.strength)}%\n")
                        else:
                            response += "⏳ No clear Order Block — wait for breakout\n"

                        if ema_21:
                            ema_signal = "above EMA 21 (bullish bias)" if current_price > ema_21 else "below EMA 21 (bearish bias)"
                            response += f"\n📋 <b>Context:</b>\n• Price {ema_signal}\n• EMA 21: {fmt_price(ema_21)}\n"

                        response += ("\n⚠️ <b>RISK MANAGEMENT:</b>\n• Use LIMIT orders at zone levels\n"
                                     "• Risk max 1-2% per trade\n• Always set Stop Loss\n"
                                     "<i>📌 Spot only — entry range, not market buy</i>")

                        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                            text=response, parse_mode='HTML')
                    except Exception as e:
                        print(f"❌ Spot analysis error (manual): {e}")
                        try:
                            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text=f"❌ Error: {str(e)[:100]}\n\nPlease try again", parse_mode=None)
                        except:
                            pass

                asyncio.create_task(run_spot())

            elif action == 'futures':
                # Show timeframe selection keyboard
                from menu_system import MenuBuilder
                await update.message.reply_text(
                    f"📊 <b>Futures Analysis: {base}</b>\n\nSelect timeframe:",
                    reply_markup=MenuBuilder.build_timeframe_selection(base),
                    parse_mode='HTML'
                )
            return

        # Handle amount input
        if user_data.get('awaiting_amount'):
            try:
                amount = float(text)
                symbol = user_data.get('symbol', 'Unknown')
                user_data.clear()
                await update.message.reply_text(f"✅ Added {amount} {symbol} to portfolio.")
            except ValueError:
                await update.message.reply_text("❌ Invalid amount.")
            return

        # Default
        await update.message.reply_text(
            "💡 Gunakan /menu untuk navigasi atau /help untuk daftar command.",
            parse_mode='MARKDOWN'
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def run_bot(self):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        print("🚀 Starting CryptoMentor AI Bot...")
        await self.setup_application()

        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
            logger.error(f"Error: {context.error}")

        self.application.add_error_handler(error_handler)

        # Start scheduler
        try:
            from app.scheduler import start_scheduler
            start_scheduler(self.application)
            print("✅ Scheduler started")
        except Exception as e:
            print(f"⚠️ Scheduler failed: {e}")
        
        # Start auto mode switcher
        try:
            from app.auto_mode_switcher import start_auto_mode_switcher
            start_auto_mode_switcher(self.application.bot)
            print("✅ Auto Mode Switcher started (checks every 15 min)")
        except Exception as e:
            print(f"⚠️ Auto Mode Switcher failed: {e}")

        print("✅ Bot is running!")
        await self.application.initialize()
        await self.application.start()
        
        # Note: Engine restore is handled by scheduler.start_scheduler() above
        # No need for redundant restore call here
        
        # timeout=1 = Telegram tunggu 1 detik sebelum return kosong (hemat bandwidth)
        # poll_interval=0 = langsung poll lagi setelah dapat response
        await self.application.updater.start_polling(
            drop_pending_updates=True,
            poll_interval=0.0,
            timeout=1,
            allowed_updates=["message", "callback_query", "inline_query"],
        )
        await asyncio.Event().wait()
