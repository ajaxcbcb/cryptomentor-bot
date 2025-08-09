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

async def main():
    """Main bot execution with optimized error handling"""
    max_retries = 2 if is_deployment else 1
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"\n🤖 Initializing CryptoMentor AI Bot (Attempt {retry_count + 1}/{max_retries})")

            # Initialize bot
            bot = TelegramBot()
            print("🎯 Bot initialized successfully")

            # Run bot
            await bot.run_bot()
            print("🛑 Bot stopped normally")
            break

        except Exception as e:
            retry_count += 1
            print(f"❌ Bot error (attempt {retry_count}/{max_retries}): {e}")
            logger.error(f"Bot error: {e}")

            if retry_count < max_retries:
                print(f"🔄 Retrying in 10 seconds...")
                await asyncio.sleep(10)
            else:
                print("❌ Max retries reached")
                if is_deployment:
                    sys.exit(1)
                else:
                    break

if __name__ == "__main__":
    try:
        print("🚀 Starting CryptoMentor AI Bot...")

        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            sys.exit(1)

        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

        # Run main async function
        asyncio.run(main())

    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        print("👋 CryptoMentor AI Bot shutdown complete")