"""
Telegram handlers untuk Cerebras AI integration (was DeepSeek)
Ultra-fast LLM with Llama 3.1 8B
"""
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from cerebras_ai import CerebrasAI
from database import Database

# Initialize Cerebras AI (ultra-fast)
cerebras = CerebrasAI()

# Track active AI requests for cancellation
active_ai_requests = {}

async def handle_ai_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk command /ai <symbol>
    Analisis market dengan DeepSeek AI reasoning
    
    Usage: /ai btc
    """
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        db = Database()
        
        # Get user language
        user_lang = db.get_user_language(user_id)
        
        # Check if symbol provided
        if not context.args:
            if user_lang == 'id':
                await update.message.reply_text(
                    "❌ **Format salah!**\n\n"
                    "Gunakan: `/ai <symbol>`\n\n"
                    "Contoh:\n"
                    "• `/ai btc` - Analisis Bitcoin dengan AI\n"
                    "• `/ai eth` - Analisis Ethereum dengan AI\n"
                    "• `/ai sol` - Analisis Solana dengan AI",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Wrong format!**\n\n"
                    "Use: `/ai <symbol>`\n\n"
                    "Examples:\n"
                    "• `/ai btc` - Analyze Bitcoin with AI\n"
                    "• `/ai eth` - Analyze Ethereum with AI\n"
                    "• `/ai sol` - Analyze Solana with AI",
                    parse_mode='Markdown'
                )
            return
        
        symbol = context.args[0].upper()
        
        # TRACK USER PROMPT - CRITICAL FOR AI ITERATION
        try:
            from app.signal_tracker_integration import track_user_command
            track_user_command(user_id, username, f"/ai {symbol}", symbol, None)
        except Exception as e:
            print(f"Warning: Failed to track user command: {e}")
        
        # Create cancel button
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_ai_{user_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send processing message with cancel button
        if user_lang == 'id':
            processing_msg = await update.message.reply_text(
                f"🤖 **CryptoMentor AI sedang menganalisis {symbol}...**\n\n"
                "⏳ Mohon tunggu, AI sedang memproses data market...\n\n"
                "💡 Jika terlalu lama, klik tombol Cancel di bawah",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            processing_msg = await update.message.reply_text(
                f"🤖 **CryptoMentor AI is analyzing {symbol}...**\n\n"
                "⏳ Please wait, AI is processing market data...\n\n"
                "💡 If taking too long, click Cancel button below",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        
        # Create cancellation token
        cancel_event = asyncio.Event()
        active_ai_requests[user_id] = {
            'cancel_event': cancel_event,
            'message_id': processing_msg.message_id,
            'symbol': symbol
        }
        
        try:
            # Get market data from crypto API
            from crypto_api import crypto_api
            
            market_data = crypto_api.get_crypto_price(symbol, force_refresh=True)
            
            # Check if cancelled
            if cancel_event.is_set():
                await processing_msg.edit_text(
                    "❌ **Analisis dibatalkan oleh user**",
                    parse_mode='Markdown'
                )
                return
            
            if 'error' in market_data or not market_data.get('success'):
                error_msg = market_data.get('error', 'Unknown error')
                await processing_msg.edit_text(
                    f"❌ **Error**: {error_msg}\n\n"
                    f"💡 Coba symbol lain seperti: BTC, ETH, SOL, XRP",
                    parse_mode='Markdown'
                )
                return
            
            # Get AI analysis with cancellation check
            analysis_task = asyncio.create_task(
                cerebras.analyze_market_simple(
                    symbol=symbol,
                    market_data=market_data,
                    language=user_lang
                )
            )
            
            # Wait for either completion or cancellation
            done, pending = await asyncio.wait(
                [analysis_task, asyncio.create_task(cancel_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Check if cancelled
            if cancel_event.is_set():
                # Cancel the AI task
                analysis_task.cancel()
                await processing_msg.edit_text(
                    "❌ **Analisis dibatalkan oleh user**\n\n"
                    "Silakan coba lagi dengan /ai <symbol>",
                    parse_mode='Markdown'
                )
                return
            
            # Get result
            analysis = await analysis_task
            
            # Send analysis (split if too long)
            if len(analysis) > 4000:
                # Split into chunks
                chunks = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
                await processing_msg.delete()
                for chunk in chunks:
                    await update.message.reply_text(chunk, parse_mode='Markdown')
            else:
                await processing_msg.edit_text(analysis, parse_mode='Markdown')
        
        finally:
            # Clean up
            if user_id in active_ai_requests:
                del active_ai_requests[user_id]
        
    except asyncio.CancelledError:
        print(f"AI analysis cancelled for user {user_id}")
        if user_id in active_ai_requests:
            del active_ai_requests[user_id]
    except Exception as e:
        print(f"Error in handle_ai_analyze: {e}")
        await update.message.reply_text(
            f"❌ **Error**: {str(e)}\n\n"
            "Silakan coba lagi atau hubungi admin.",
            parse_mode='Markdown'
        )


async def handle_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk command /chat <message>
    Chat santai dengan AI tentang market
    
    Usage: /chat gimana market hari ini?
    """
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        db = Database()
        
        # Get user language
        user_lang = db.get_user_language(user_id)
        
        # Check if message provided
        if not context.args:
            if user_lang == 'id':
                await update.message.reply_text(
                    "❌ **Format salah!**\n\n"
                    "Gunakan: `/chat <pesan>`\n\n"
                    "Contoh:\n"
                    "• `/chat gimana market hari ini?`\n"
                    "• `/chat kapan waktu yang tepat beli BTC?`\n"
                    "• `/chat jelaskan tentang support dan resistance`\n"
                    "• `/chat strategi trading yang bagus untuk pemula?`",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ **Wrong format!**\n\n"
                    "Use: `/chat <message>`\n\n"
                    "Examples:\n"
                    "• `/chat how's the market today?`\n"
                    "• `/chat when is the right time to buy BTC?`\n"
                    "• `/chat explain about support and resistance`\n"
                    "• `/chat good trading strategy for beginners?`",
                    parse_mode='Markdown'
                )
            return
        
        user_message = ' '.join(context.args)
        
        # TRACK USER PROMPT - CRITICAL FOR AI ITERATION
        try:
            from app.signal_tracker_integration import track_user_command
            track_user_command(user_id, username, f"/chat {user_message}", None, None)
        except Exception as e:
            print(f"Warning: Failed to track user command: {e}")
        
        # Send typing action
        await update.message.chat.send_action(action="typing")
        
        # Get AI response
        response = await cerebras.chat_about_market(
            user_message=user_message,
            language=user_lang
        )
        
        # Send response (split if too long)
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Error in handle_ai_chat: {e}")
        await update.message.reply_text(
            f"❌ **Error**: {str(e)}\n\n"
            "Silakan coba lagi atau hubungi admin.",
            parse_mode='Markdown'
        )


async def handle_ai_market_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler untuk command /aimarket
    Summary market dengan AI reasoning
    
    Usage: /aimarket
    """
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Unknown"
        db = Database()
        
        # Get user language
        user_lang = db.get_user_language(user_id)
        
        # TRACK USER PROMPT - CRITICAL FOR AI ITERATION
        try:
            from app.signal_tracker_integration import track_user_command
            track_user_command(user_id, username, "/aimarket", None, None)
        except Exception as e:
            print(f"Warning: Failed to track user command: {e}")
        
        # Send processing message
        if user_lang == 'id':
            processing_msg = await update.message.reply_text(
                "🤖 **CryptoMentor AI sedang menganalisis kondisi market global...**\n\n"
                "⏳ Mohon tunggu...",
                parse_mode='Markdown'
            )
        else:
            processing_msg = await update.message.reply_text(
                "🤖 **CryptoMentor AI is analyzing global market conditions...**\n\n"
                "⏳ Please wait...",
                parse_mode='Markdown'
            )
        
        # Get market data for top coins
        from crypto_api import crypto_api
        
        top_coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'MATIC', 'AVAX']
        market_data_list = []
        
        for symbol in top_coins:
            data = crypto_api.get_crypto_price(symbol, force_refresh=True)
            if 'error' not in data:
                market_data_list.append({
                    'symbol': symbol,
                    'price': data.get('price', 0),
                    'change_24h': data.get('change_24h', 0),
                    'volume_24h': data.get('volume_24h', 0)
                })
        
        # Create market summary prompt
        market_summary = cerebras.get_market_summary_prompt(market_data_list)
        
        # Get AI analysis
        if user_lang == 'id':
            prompt = f"{market_summary}\n\nBerikan analisis kondisi market crypto secara keseluruhan dengan reasoning yang jelas. Apa yang terjadi di market? Apa yang harus diperhatikan trader?"
        else:
            prompt = f"{market_summary}\n\nProvide analysis of overall crypto market conditions with clear reasoning. What's happening in the market? What should traders pay attention to?"
        
        response = await cerebras.chat_about_market(
            user_message=prompt,
            language=user_lang
        )
        
        # Send response
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            await processing_msg.delete()
            for chunk in chunks:
                await update.message.reply_text(chunk, parse_mode='Markdown')
        else:
            await processing_msg.edit_text(response, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Error in handle_ai_market_summary: {e}")
        await update.message.reply_text(
            f"❌ **Error**: {str(e)}\n\n"
            "Silakan coba lagi atau hubungi admin.",
            parse_mode='Markdown'
        )
