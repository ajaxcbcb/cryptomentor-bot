#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Main Entry Point
Enhanced with async support for python-telegram-bot v22.3
"""

# --- BOOTSTRAP: fix pydantic/supabase sebelum import lain ---
import sys, subprocess
def _pip(spec): 
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", spec])
    except Exception as e:
        print(f"[pip warn] {spec} -> {e}")

for pkg in ("pydantic>=2.6,<3", "pydantic-core>=2.16", "supabase>=2.4", "httpx>=0.24,<0.28"):
    _pip(pkg)

import pydantic as _p
if not hasattr(_p, "with_config"):
    def with_config(*args, **kwargs):
        def _d(obj): return obj
        return _d
    _p.with_config = with_config
# --- END BOOTSTRAP ---

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

# Import Supabase client and related functions
try:
    from app.supabase_conn import health, get_supabase_client
    from app.sb_repo import stats_totals

    ok, reason = health()
    if ok:
        try:
            total_users, premium_users = stats_totals()
            print(f"✅ Supabase connection active - Users: {total_users} | Premium: {premium_users}")
        except Exception as count_error:
            print(f"✅ Supabase connection active - Stats unavailable: {count_error}")
    else:
        print(f"❌ Supabase connection failed: {reason}")

except ImportError as e:
    print(f"⚠️ Supabase integration failed: {e}")
    print("✅ Bot will continue with local database only")
except Exception as e:
    print(f"⚠️ Supabase connection error: {e}")
    print("✅ Bot will continue with local database only")


async def main():
    """Main bot execution with error handling and auto-restart"""
    max_retries = 3 if is_deployment else 2
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"\n🤖 Initializing CryptoMentor AI Bot (Attempt {retry_count + 1}/{max_retries})")

            # Initialize bot
            bot = TelegramBot()

            print("🎯 Bot initialized successfully")
            print("📡 Starting bot run sequence...")

            # Run bot with enhanced logging
            print("🚀 Calling bot.run_bot()...")
            await bot.run_bot()

            # If we reach here, bot stopped normally
            print("🛑 Bot stopped by user")
            break

        except Exception as e:
            retry_count += 1
            error_msg = str(e)

            print(f"❌ Bot crashed (attempt {retry_count}/{max_retries}): {e}")
            logger.error(f"Bot crashed: {e}")

            # Log specific error types for debugging
            if "HTTPXRequest" in error_msg:
                print("🔧 HTTPXRequest initialization error - telegram-bot version issue")
            elif "idle" in error_msg:
                print("🔧 Updater.idle() method missing - using alternative approach")
            elif "max() arg is an empty sequence" in error_msg:
                print("🔧 SnD analysis data validation error - applying fixes")

            if retry_count < max_retries:
                print(f"🔄 Retrying in 15 seconds... ({retry_count}/{max_retries})")
                await asyncio.sleep(15)  # Longer wait for stability
            else:
                print("❌ Max retries reached. Bot shutting down.")
                if is_deployment:
                    print("🔄 Deployment will restart automatically...")
                    sys.exit(1)
                else:
                    print("💡 Manual restart required")
                    sys.exit(1)

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