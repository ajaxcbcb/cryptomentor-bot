#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Main Entry Point
Enhanced with async support for python-telegram-bot v22.3
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Enhanced deployment detection
deployment_indicators = {
    'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
    'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1',
    'REPLIT_ENVIRONMENT': os.getenv('REPLIT_ENVIRONMENT') == 'deployment',
    'deployment_flag': os.path.exists('/tmp/repl_deployment_flag'),
    'replit_slug': bool(os.getenv('REPL_SLUG')),
    'replit_owner': bool(os.getenv('REPL_OWNER'))
}

is_deployment = any(deployment_indicators.values())

# Create deployment flag for consistent detection
if is_deployment:
    try:
        with open('/tmp/repl_deployment_flag', 'w') as f:
            f.write(f"deployment_active_{int(datetime.now().timestamp())}")
    except:
        pass

print("🚀 CryptoMentor AI Bot Starting...")
print("=" * 50)
print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print("🔍 Bot Deployment Detection:")
for check, result in deployment_indicators.items():
    print(f"  {'✅' if result else '❌'} {check}: {result}")
print(f"📊 Bot Deployment Status: {'ENABLED' if is_deployment else 'DISABLED'}")

# Setup logging with debug level to catch all errors
logging.basicConfig(
    level=logging.INFO,  # Use INFO in production
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import bot after environment setup
try:
    from bot import TelegramBot
    print("✅ Bot module imported successfully")
except ImportError as e:
    print(f"❌ Failed to import bot module: {e}")
    sys.exit(1)

# Using local SQLite database only
print("✅ Local SQLite database initialized") will continue with local database only")

# Import handlers and statistics functions
try:
    from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.constants import ParseMode
    from app.lib.guards import admin_guard
    from app.handlers_admin_panel import register_admin_panel_handlers
    from app.handlers_admin_premium import register_admin_premium_handlers
    from app.handlers_admin_debug import register_admin_debug_handlers
    from app.handlers_admin_stats import register_admin_stats
    from app.bot_stats import log_stats_on_startup
except ImportError as e:
    print(f"❌ Failed to import necessary modules: {e}")
    sys.exit(1)

def validate_environment():
    """Validate required environment variables"""
    token = os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found!")
        print("💡 Please set TOKEN in Replit Secrets")
        return False
    return True

TELEGRAM_BOT_TOKEN = os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')

async def main():
    """Main function to start the bot"""
    print("🤖 Starting CryptoMentor AI Bot...")

    # Validate required environment variables
    if not validate_environment():
        return

    # Initialize the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register admin handlers
    register_admin_panel_handlers(application)
    register_admin_premium_handlers(application)
    register_admin_debug_handlers(application)
    register_admin_stats(application)
    
    # Register access tools
    from handlers_access_tools import register_access_tools
    register_access_tools(application)

    print("✅ Bot initialized and handlers registered.")

    # Log bot statistics on startup
    log_stats_on_startup()

    print("🚀 Bot is running...")

    # Run the bot until the user presses Ctrl-C
    application.run_polling()

if __name__ == '__main__':
    # Setup logging untuk console panel
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Import dan panggil console panel
    try:
        from app.db_admin import log_console_panel
        log_console_panel()
    except Exception as e:
        logging.error("❌ Console panel error: %s", e)

    asyncio.run(main())