#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CryptoMentor AI Bot - Main Entry Point
Enhanced with CoinAPI + CoinMarketCap Integration
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

# Setup logging
logging.basicConfig(
    level=logging.WARNING if is_deployment else logging.INFO,
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
    """Main bot execution with error handling and auto-restart"""
    max_retries = 5 if is_deployment else 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            print(f"\n🤖 Initializing CryptoMentor AI Bot (Attempt {retry_count + 1}/{max_retries})")

            # Initialize bot
            bot = TelegramBot()

            print("🎯 Bot initialized successfully")
            print("📡 Starting polling for updates...")

            # Run bot
            await bot.run_bot()

            # If we reach here, bot stopped normally
            print("🛑 Bot stopped by user")
            break

        except Exception as e:
            retry_count += 1
            error_msg = str(e)

            # Enhanced conflict resolution
            if "terminated by other getUpdates request" in error_msg or "Conflict" in error_msg:
                print("❌ CONFLICT: Another bot instance detected!")
                print("🔄 Initiating intelligent cleanup...")

                # Advanced process cleanup
                try:
                    import psutil
                    import signal
                    import time

                    current_pid = os.getpid()
                    killed_processes = 0

                    # Find and terminate conflicting processes
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.pid == current_pid:
                                continue

                            cmdline = ' '.join(proc.info['cmdline'] or [])
                            if any(keyword in cmdline for keyword in ['main.py', 'TelegramBot', 'bot.py']):
                                print(f"🛑 Terminating process {proc.pid}: {proc.info['name']}")
                                proc.terminate()
                                try:
                                    proc.wait(timeout=5)
                                    killed_processes += 1
                                except psutil.TimeoutExpired:
                                    proc.kill()
                                    killed_processes += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    print(f"✅ Terminated {killed_processes} conflicting processes")
                    time.sleep(5)  # Wait for cleanup

                except ImportError:
                    print("⚠️ psutil not available for advanced cleanup")
                except Exception as cleanup_error:
                    print(f"⚠️ Cleanup error: {cleanup_error}")

                if is_deployment:
                    print("🔄 Deployment will auto-restart...")
                    sys.exit(1)
                else:
                    print("💡 Stop all other instances and restart")
                    break

            # Handle NoneType await expression error
            if "object NoneType can't be used in 'await' expression" in error_msg:
                print("❌ Bot initialization error - restarting...")
                if retry_count < max_retries:
                    import time
                    time.sleep(10)
                    continue
                else:
                    sys.exit(1)

            print(f"❌ Bot crashed (attempt {retry_count}/{max_retries}): {e}")
            logger.error(f"Bot crashed: {e}")

            if retry_count < max_retries:
                print(f"🔄 Retrying in 10 seconds... ({retry_count}/{max_retries})")
                import time
                time.sleep(10)  # Shorter delay for faster recovery
            else:
                print("❌ Max retries reached. Bot shutting down.")
                if is_deployment:
                    print("🔄 Deployment will restart automatically...")
                    sys.exit(1)  # Let deployment system handle restart
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