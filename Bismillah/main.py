import asyncio
import nest_asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from bot import TelegramBot

# Apply nest_asyncio to avoid event loop conflicts
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Minimal logging setup
logging.basicConfig(
    level=logging.ERROR,  # Only show errors
    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Main function to run the bot"""
    print("🚀 Starting CryptoMentor AI Bot...")

    # Check if running in deployment
    is_deployment = os.getenv('REPLIT_DEPLOYMENT') == '1' or os.getenv(
        'REPL_DEPLOYMENT') == '1'
    if is_deployment:
        print("📡 Running in Replit Deployment mode (Always On)")
    else:
        print("🔧 Running in development mode")

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            bot = TelegramBot()
            print("🤖 Bot initialized successfully, starting...")
            
            # Use asyncio.run for better event loop management
            asyncio.run(bot.run_bot())
            break  # If successful, exit the retry loop

        except KeyboardInterrupt:
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
                            continue
                    
                    if killed_processes > 0:
                        print(f"✅ Cleaned up {killed_processes} conflicting processes")
                        time.sleep(8)  # Extended wait for proper cleanup
                    else:
                        print("⚠️ No conflicting processes found - using fallback cleanup")
                        import subprocess
                        subprocess.run(["pkill", "-f", "python.*main.py"], check=False)
                        time.sleep(5)
                        
                except ImportError:
                    print("⚠️ Advanced cleanup unavailable, using basic method")
                    import subprocess
                    subprocess.run(["pkill", "-f", "python.*main.py"], check=False)
                    import time
                    time.sleep(5)
                except Exception as cleanup_error:
                    print(f"⚠️ Cleanup error: {cleanup_error}")
                    import time
                    time.sleep(3)
                
                # Force exit to allow deployment system to restart cleanly
                if is_deployment:
                    print("🔄 Exiting for clean restart...")
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
                    raise

    print("🔄 Bot shutdown complete")


if __name__ == "__main__":
    main()
