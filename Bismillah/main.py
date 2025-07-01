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

    # Enhanced deployment detection with verification
    deployment_checks = {
        'REPLIT_DEPLOYMENT': os.getenv('REPLIT_DEPLOYMENT') == '1',
        'REPL_DEPLOYMENT': os.getenv('REPL_DEPLOYMENT') == '1',
        'REPLIT_ENVIRONMENT': os.getenv('REPLIT_ENVIRONMENT') == 'deployment',
        'deployment_flag_file': os.path.exists('/tmp/repl_deployment_flag'),
        'cwd_contains_deployment': 'deployment' in os.getcwd().lower(),
        'replit_slug': bool(os.getenv('REPL_SLUG')),
        'replit_owner': bool(os.getenv('REPL_OWNER'))
    }
    
    is_deployment = any(deployment_checks.values())
    
    print(f"🔍 Deployment Detection Results:")
    for check, result in deployment_checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}: {result}")
    
    print(f"📊 Overall Deployment Status: {'✅ DEPLOYMENT MODE' if is_deployment else '❌ DEVELOPMENT MODE'}")
    
    if is_deployment:
        print("📡 Running in Replit Deployment mode (Always On)")
        print("🚀 Real-time API mode: ENABLED (Force refresh for live data)")
        # Force create deployment flag for consistency
        try:
            with open('/tmp/repl_deployment_flag', 'w') as f:
                f.write(f"deployment_verified_{datetime.now().isoformat()}")
            print("✅ Deployment flag verified/created")
        except Exception as e:
            print(f"⚠️ Could not create deployment flag: {e}")
    else:
        print("🔧 Running in development mode")
        print("🔄 API mode: Standard (Cached when appropriate)")

    # Kill any existing bot instances first
    try:
        import psutil
        import signal
        import time
        
        current_pid = os.getpid()
        killed_count = 0
        
        print("🔍 Checking for existing bot instances...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.pid == current_pid:
                    continue
                    
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline.lower() for keyword in ['main.py', 'bot.py', 'telegram']):
                    print(f"🛑 Terminating existing process: {proc.pid}")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                        killed_count += 1
                    except psutil.TimeoutExpired:
                        proc.kill()
                        killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed_count > 0:
            print(f"✅ Cleaned up {killed_count} existing instances")
            time.sleep(5)  # Wait for cleanup
        else:
            print("✅ No conflicting instances found")
            
    except ImportError:
        print("⚠️ psutil not available, using basic cleanup")
        try:
            import subprocess
            subprocess.run(["pkill", "-f", "main.py"], check=False)
            time.sleep(3)
        except:
            pass
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

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
