
#!/usr/bin/env python3
"""Kill conflicting bot instances"""

import os
import sys
import time

try:
    import psutil
except ImportError:
    print("❌ psutil not installed. Installing...")
    os.system("pip install psutil")
    import psutil

def kill_bot_instances():
    """Kill all running bot instances"""
    print("🔍 Searching for running bot instances...")
    
    killed_count = 0
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] == current_pid:
                continue
                
            if proc.info['name'] in ['python', 'python3']:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline for keyword in ['main.py', 'bot.py', 'telegram']):
                    print(f"🛑 Killing process {proc.info['pid']}: {cmdline}")
                    proc.terminate()
                    proc.wait(timeout=3)
                    killed_count += 1
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            print(f"⚠️ Error handling process {proc.info['pid']}: {e}")
    
    print(f"✅ Killed {killed_count} bot instances")
    return killed_count

if __name__ == "__main__":
    killed = kill_bot_instances()
    if killed > 0:
        print("⏳ Waiting 3 seconds before exit...")
        time.sleep(3)
    print("🎯 Clean exit")("🎯 Clean exit")
