"""
Simple Telegram Bot Integration with Automaton
Cara paling mudah untuk integrate ke bot Python kamu
"""

from automaton_simple_client import AutomatonSimpleClient

# Initialize Automaton client
automaton = AutomatonSimpleClient()

# Premium users (ganti dengan user ID kamu)
PREMIUM_USERS = [123456789, 987654321]  # Ganti dengan user ID premium

def is_premium_user(user_id):
    """Check if user is premium"""
    return user_id in PREMIUM_USERS


# ===== CARA 1: Untuk python-telegram-bot library =====

async def ai_signal_handler(update, context):
    """
    Handler untuk command /ai_signal
    Usage: /ai_signal BTC/USDT
    """
    user_id = update.effective_user.id
    
    # Check premium
    if not is_premium_user(user_id):
        await update.message.reply_text(
            "🔒 Fitur Premium!\n"
            "Upgrade ke Premium untuk akses AI signals.\n"
            "Hubungi admin untuk info lebih lanjut."
        )
        return
    
    # Get symbol
    if not context.args:
        await update.message.reply_text(
            "Cara pakai: /ai_signal <symbol>\n"
            "Contoh: /ai_signal BTC/USDT"
        )
        return
    
    symbol = context.args[0].upper()
    
    # Send "analyzing" message
    msg = await update.message.reply_text(
        f"🤖 AI sedang menganalisis {symbol}...\n"
        "Mohon tunggu 30-60 detik."
    )
    
    # Send task to Automaton
    task = f"""
Analyze {symbol} cryptocurrency market. Provide:
1. Market sentiment (bullish/bearish/neutral)
2. Recommendation (BUY/SELL/HOLD)
3. Confidence level (0-100%)
4. Key reasons (max 3 points)
5. Entry price suggestion
6. Stop loss level
7. Take profit targets

Format as clear bullet points for Telegram.
"""
    
    result = automaton.send_task(task, wait_for_response=True, timeout=90)
    
    # Delete analyzing message
    await msg.delete()
    
    # Send result
    if result['success'] and result['response']:
        await update.message.reply_text(
            f"🤖 AI Analysis: {symbol}\n\n"
            f"{result['response']}\n\n"
            f"⚠️ AI-generated. Always DYOR!"
        )
    else:
        await update.message.reply_text(
            "❌ AI sedang sibuk atau timeout.\n"
            "Coba lagi dalam beberapa menit."
        )


# ===== CARA 2: Untuk pyTelegramBotAPI (telebot) =====

def setup_telebot_handlers(bot):
    """
    Setup handlers untuk telebot library
    """
    
    @bot.message_handler(commands=['ai_signal'])
    def ai_signal_telebot(message):
        user_id = message.from_user.id
        
        # Check premium
        if not is_premium_user(user_id):
            bot.reply_to(message, 
                "🔒 Fitur Premium!\n"
                "Upgrade ke Premium untuk akses AI signals."
            )
            return
        
        # Parse command
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message,
                "Cara pakai: /ai_signal <symbol>\n"
                "Contoh: /ai_signal BTC/USDT"
            )
            return
        
        symbol = parts[1].upper()
        
        # Send analyzing message
        msg = bot.reply_to(message, 
            f"🤖 AI sedang menganalisis {symbol}...\n"
            "Mohon tunggu 30-60 detik."
        )
        
        # Send task
        task = f"Analyze {symbol}. Provide trading signal with confidence and reasoning."
        result = automaton.send_task(task, wait_for_response=True, timeout=90)
        
        # Delete analyzing message
        bot.delete_message(message.chat.id, msg.message_id)
        
        # Send result
        if result['success'] and result['response']:
            bot.reply_to(message,
                f"🤖 AI Analysis: {symbol}\n\n"
                f"{result['response']}\n\n"
                f"⚠️ AI-generated. Always DYOR!"
            )
        else:
            bot.reply_to(message,
                "❌ AI timeout. Coba lagi nanti."
            )
    
    @bot.message_handler(commands=['ai_ask'])
    def ai_ask_telebot(message):
        user_id = message.from_user.id
        
        if not is_premium_user(user_id):
            bot.reply_to(message, "🔒 Fitur Premium!")
            return
        
        # Get question
        question = message.text.replace('/ai_ask', '').strip()
        if not question:
            bot.reply_to(message, "Cara pakai: /ai_ask <pertanyaan>")
            return
        
        msg = bot.reply_to(message, "🤖 AI sedang berpikir...")
        
        result = automaton.send_task(
            f"Answer this crypto question concisely: {question}",
            wait_for_response=True,
            timeout=60
        )
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        if result['success'] and result['response']:
            bot.reply_to(message, f"🤖 {result['response']}")
        else:
            bot.reply_to(message, "❌ AI timeout.")


# ===== CARA 3: Function standalone (untuk bot custom) =====

def get_ai_signal(symbol, user_id):
    """
    Standalone function untuk get AI signal
    Bisa dipanggil dari bot manapun
    
    Args:
        symbol: Trading pair (e.g., "BTC/USDT")
        user_id: Telegram user ID
    
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'is_premium': bool
        }
    """
    # Check premium
    if not is_premium_user(user_id):
        return {
            'success': False,
            'message': '🔒 Fitur Premium! Upgrade untuk akses AI.',
            'is_premium': False
        }
    
    # Send task
    task = f"Analyze {symbol}. Provide trading signal with confidence."
    result = automaton.send_task(task, wait_for_response=True, timeout=90)
    
    if result['success'] and result['response']:
        return {
            'success': True,
            'message': f"🤖 AI Analysis: {symbol}\n\n{result['response']}",
            'is_premium': True
        }
    else:
        return {
            'success': False,
            'message': '❌ AI timeout. Coba lagi nanti.',
            'is_premium': True
        }


# ===== EXAMPLE USAGE =====

if __name__ == "__main__":
    print("Contoh penggunaan:")
    print("\n1. Untuk python-telegram-bot:")
    print("   application.add_handler(CommandHandler('ai_signal', ai_signal_handler))")
    
    print("\n2. Untuk telebot:")
    print("   setup_telebot_handlers(bot)")
    
    print("\n3. Standalone:")
    print("   result = get_ai_signal('BTC/USDT', user_id)")
    print("   print(result['message'])")
    
    # Test standalone function
    print("\n" + "="*50)
    print("TEST STANDALONE FUNCTION")
    print("="*50)
    
    result = get_ai_signal("BTC/USDT", 123456789)
    print(f"\nSuccess: {result['success']}")
    print(f"Message: {result['message'][:100]}...")
