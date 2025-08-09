"""
Telegram Command Handlers for CryptoMentor AI Bot
Separated for better code organization
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime


class TelegramHandlers:
    """
    Collection of Telegram command handlers
    """

    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.db = bot_instance.db
        self.crypto_api = bot_instance.crypto_api
        self.ai = bot_instance.ai
        self.admin_id = bot_instance.admin_id

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user

        try:
            if not user or not user.id:
                await update.message.reply_text("❌ Terjadi kesalahan dalam mengidentifikasi user.")
                return

            # Handle referral
            referred_by = None
            if context.args and len(context.args) > 0:
                arg = context.args[0]
                if arg.startswith('ref_'):
                    try:
                        referred_by = int(arg[4:])
                    except ValueError:
                        pass

            # Create or get user
            existing_user = self.db.get_user(user.id)
            if not existing_user:
                success = self.db.create_user(
                    telegram_id=user.id,
                    username=user.username or 'no_username',
                    first_name=user.first_name or 'Unknown',
                    last_name=user.last_name,
                    language_code=user.language_code or 'id',
                    referred_by=referred_by
                )

                # Give referral bonus
                if referred_by and success:
                    try:
                        self.db.add_credits(referred_by, 10)
                        self.db.log_user_activity(referred_by, "referral_bonus", f"Got 10 credits for referring user {user.id}")
                    except Exception as e:
                        print(f"Error giving referral bonus: {e}")

            # Welcome message
            welcome_text = f"""🎉 **Selamat datang di CryptoMentor AI, {user.first_name}!**

🤖 AI assistant crypto trading dengan data real-time.

💡 **Quick Start:**
• `/price btc` - Harga Bitcoin real-time (GRATIS)
• `/analyze btc` - Analisis komprehensif (20 credit)
• `/futures btc` - Trading signals dengan SnD (20 credit)
• `/help` - Panduan lengkap

💳 **Credit System:**
- User baru: 100 credit gratis
- Premium: Unlimited access

🚀 **Data real-time dari CoinAPI & Binance!**"""

            await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

        except Exception as e:
            print(f"Error in start command: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan. Silakan coba lagi.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🤖 **CryptoMentor AI - Panduan Lengkap**

📊 **Harga & Data:**
• `/price <symbol>` - Harga real-time **[GRATIS]**
• `/market` - Overview pasar global (20 credit)

📈 **Analisis Trading:**
• `/analyze <symbol>` - Analisis mendalam (20 credit)
• `/futures <symbol>` - Analisis futures SnD (20 credit)  
• `/futures_signals` - Sinyal futures lengkap (60 credit)

💼 **Portfolio & Credit:**
• `/portfolio` - Lihat portfolio
• `/credits` - Cek sisa credit
• `/subscribe` - Upgrade premium

🎯 **Lainnya:**
• `/ask_ai <pertanyaan>` - Tanya AI crypto **[GRATIS]**
• `/referral` - Program referral

💳 **Sistem Credit:**
- User baru: 100 credit gratis
- `/analyze` = 20 credit
- `/futures` = 20 credit  
- `/futures_signals` = 60 credit
- `/market` = 20 credit

🚀 **Data Sources:**
- Real-time: CoinAPI + Binance
- SnD Analysis: Internal algorithm"""

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/price <symbol>`\nContoh: `/price btc`", parse_mode='Markdown')
            return

        symbol = context.args[0].upper()
        loading_msg = await update.message.reply_text(f"⏳ Mengambil data real-time {symbol}...")

        # Get price data
        price_data = self.crypto_api.get_crypto_price(symbol, force_refresh=True)

        if price_data and 'error' not in price_data and price_data.get('price', 0) > 0:
            current_price = price_data.get('price', 0)
            change_24h = price_data.get('change_24h', 0)

            # Format price
            if current_price < 1:
                price_format = f"${current_price:.8f}"
            elif current_price < 100:
                price_format = f"${current_price:.4f}"
            else:
                price_format = f"${current_price:,.2f}"

            change_emoji = "📈" if change_24h >= 0 else "📉"
            change_color = "+" if change_24h >= 0 else ""

            message = f"""📊 **{symbol} Real-Time Data**

💰 **Harga**: {price_format}
{change_emoji} **Change 24h**: {change_color}{change_24h:.2f}%

⏰ **Update**: {datetime.now().strftime('%H:%M:%S WIB')}
🔄 **Source**: {price_data.get('source', 'Real-time API')}"""

            # Add volume if available
            if price_data.get('volume_24h', 0) > 0:
                volume = price_data.get('volume_24h', 0)
                if volume > 1000000000:
                    volume_format = f"${volume/1000000000:.2f}B"
                elif volume > 1000000:
                    volume_format = f"${volume/1000000:.1f}M"
                else:
                    volume_format = f"${volume:,.0f}"
                message += f"\n📊 **Volume 24h**: {volume_format}"

        else:
            error_reason = price_data.get('error', 'API unavailable') if price_data else 'API unavailable'
            message = f"""❌ **Data tidak tersedia untuk {symbol}**

⚠️ **Error**: {error_reason}

🔄 **Solusi:**
• Coba beberapa saat lagi
• Pastikan symbol benar (contoh: BTC, ETH, SOL)"""

        await loading_msg.edit_text(message, parse_mode='Markdown')

    async def credits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /credits command"""
        user_id = update.message.from_user.id

        try:
            credits = self.db.get_user_credits(user_id)
            is_premium = self.db.is_user_premium(user_id)

            if is_premium:
                status_text = "⭐ **PREMIUM USER** - Unlimited Access"
                credit_text = "∞ Unlimited"
            else:
                status_text = "🆓 **FREE USER**"
                credit_text = f"{credits} credits"

            message = f"""💳 **STATUS CREDIT ANDA**

👤 **Status**: {status_text}
🪙 **Credits**: {credit_text}

📊 **Harga Commands:**
• `/analyze` = 20 credits
• `/futures` = 20 credits
• `/futures_signals` = 60 credits
• `/market` = 20 credits

🎁 **Cara Dapat Credit:**
• `/referral` - Ajak teman (10 credit/referral)
• `/subscribe` - Upgrade premium (unlimited)

💡 **Info**: `/price` dan `/ask_ai` GRATIS!"""

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text("❌ Gagal mengambil data credit. Coba lagi nanti.")
            print(f"Error in credits command: {e}")

    async def ask_ai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask_ai command"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/ask_ai <pertanyaan>`\nContoh: `/ask_ai apa itu bitcoin?`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        question = ' '.join(context.args)

        loading_msg = await update.message.reply_text("🤖 AI sedang memproses pertanyaan Anda...")

        try:
            response = self.ai.get_ai_response(question, 'id', user_id)
            await loading_msg.edit_text(response, parse_mode='Markdown')
        except Exception as e:
            await loading_msg.edit_text("❌ Terjadi kesalahan saat memproses pertanyaan. Coba lagi nanti.")
            print(f"Error in ask_ai command: {e}")

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command with enhanced CoinAPI analysis"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/analyze <symbol>`\nContoh: `/analyze btc`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        symbol = context.args[0].lower()

        # Check credits
        if not self.db.check_and_deduct_credits(user_id, 20):
            await update.message.reply_text("❌ Credit tidak cukup. Anda memerlukan 20 credit untuk analisis.\nGunakan `/credits` untuk cek saldo atau `/subscribe` untuk upgrade premium.", parse_mode='Markdown')
            return

        loading_msg = await update.message.reply_text(f"🔄 Menganalisis {symbol.upper()} dengan CoinAPI + multi-timeframe...")

        try:
            # Get enhanced comprehensive analysis
            result = await self.ai.analyze_command(symbol, user_id)
            await loading_msg.edit_text(result, parse_mode='Markdown')

            # Log activity
            self.db.log_user_activity(user_id, "analyze", f"Enhanced analysis: {symbol}")

        except Exception as e:
            await loading_msg.edit_text(f"❌ Error analisis: {str(e)}")
            print(f"Error in analyze command: {e}")

    async def futures_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /futures command with enhanced CoinAPI analysis"""
        if not context.args:
            await update.message.reply_text("❌ Gunakan format: `/futures <symbol>`\nContoh: `/futures btc`", parse_mode='Markdown')
            return

        user_id = update.message.from_user.id
        symbol = context.args[0].upper()

        # Check credits
        if not self.db.check_and_deduct_credits(user_id, 20):
            await update.message.reply_text("❌ Credit tidak cukup. Anda memerlukan 20 credit untuk futures analysis.\nGunakan `/credits` untuk cek saldo atau `/subscribe` untuk upgrade premium.", parse_mode='Markdown')
            return

        loading_msg = await update.message.reply_text(f"🔄 Menganalisis futures {symbol} dengan CoinAPI + confidence scoring...")

        try:
            # Use enhanced AI assistant futures analysis
            result = await self.ai.futures_command(symbol, user_id)
            await loading_msg.edit_text(result, parse_mode='Markdown')

            # Log activity
            self.db.log_user_activity(user_id, "futures_analysis", f"Symbol: {symbol}")

        except Exception as e:
            await loading_msg.edit_text(f"❌ Error futures analysis: {str(e)}")
            print(f"Error in futures command: {e}")

    async def futures_signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /futures_signals command with enhanced analysis"""
        user_id = update.message.from_user.id

        # Check credits
        if not self.db.check_and_deduct_credits(user_id, 60):
            await update.message.reply_text("❌ Credit tidak cukup. Anda memerlukan 60 credit untuk futures signals.\nGunakan `/credits` untuk cek saldo atau `/subscribe` untuk upgrade premium.", parse_mode='Markdown')
            return

        loading_msg = await update.message.reply_text("🔄 Scanning multiple coins dengan CoinAPI + confidence scoring...")

        try:
            # Use enhanced AI assistant futures signals
            result = await self.ai.futures_signals_command(user_id)
            await loading_msg.edit_text(result, parse_mode='Markdown')

            # Log activity
            self.db.log_user_activity(user_id, "futures_signals", "Enhanced multiple signals")

        except Exception as e:
            await loading_msg.edit_text(f"❌ Error generating signals: {str(e)}")
            print(f"Error in futures signals command: {e}")