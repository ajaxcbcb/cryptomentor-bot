
#!/usr/bin/env python3
import os
import signal
import psutil
import time
import requests

def kill_telegram_bot_instances():
    """Kill all running telegram bot instances to resolve conflicts"""
    
    print("🛑 KILLING ALL TELEGRAM BOT INSTANCES")
    print("=" * 40)
    
    killed_processes = []
    
    try:
        # Get all python processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.info
                if not proc_info['cmdline']:
                    continue
                    
                cmdline = ' '.join(proc_info['cmdline'])
                
                # Check if it's our bot process
                if (proc_info['name'] in ['python', 'python3'] and 
                    ('main.py' in cmdline or 'bot.py' in cmdline or 'telegram' in cmdline.lower())):
                    
                    print(f"🎯 Found bot process: PID {proc_info['pid']}")
                    print(f"   Command: {cmdline[:100]}...")
                    
                    # Don't kill our own process
                    if proc_info['pid'] != os.getpid():
                        try:
                            proc.terminate()
                            proc.wait(timeout=5)
                            killed_processes.append(proc_info['pid'])
                            print(f"   ✅ Killed PID {proc_info['pid']}")
                        except psutil.TimeoutExpired:
                            proc.kill()
                            killed_processes.append(proc_info['pid'])
                            print(f"   🔥 Force killed PID {proc_info['pid']}")
                        except psutil.NoSuchProcess:
                            print(f"   ⚠️ Process {proc_info['pid']} already gone")
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
    except Exception as e:
        print(f"❌ Error during process cleanup: {e}")
    
    if killed_processes:
        print(f"\n✅ Killed {len(killed_processes)} bot processes")
        print("⏰ Waiting 10 seconds for cleanup...")
        time.sleep(10)
    else:
        print("\n✅ No conflicting bot processes found")
    
    return len(killed_processes)

def clear_telegram_webhooks():
    """Clear any webhooks that might cause conflicts"""
    print("\n🔧 CLEARING TELEGRAM WEBHOOKS")
    print("=" * 30)
    
    bot_token = os.getenv('TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    
    if not bot_token:
        print("⚠️ No bot token found, skipping webhook cleanup")
        return
    
    try:
        # Delete webhook
        webhook_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
        params = {"drop_pending_updates": True}
        
        response = requests.post(webhook_url, params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ Webhook cleared successfully")
        else:
            print(f"⚠️ Webhook clear returned: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error clearing webhook: {e}")

if __name__ == "__main__":
    print("🚀 TELEGRAM BOT CONFLICT RESOLVER")
    print("=" * 50)
    
    # Kill conflicting processes
    killed_count = kill_telegram_bot_instances()
    
    # Clear webhooks
    clear_telegram_webhooks()
    
    print(f"\n{'🎉 CLEANUP COMPLETE - READY TO RESTART BOT' if killed_count > 0 else '✅ NO CONFLICTS FOUND - SAFE TO START BOT'}")
    print("\n💡 You can now run: python main.py")
