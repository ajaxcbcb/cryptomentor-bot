
#!/usr/bin/env python3
"""Kill conflicting bot instances"""

import os
import time

try:
    import psutil
except ImportError:
    print("❌ psutil not installed. Install with: pip install psutil")
    exit(1)


def kill_bot_instances():
    """Kill all conflicting bot instances"""
    print("🔍 Mencari instance bot yang berjalan...")
    
    current_pid = os.getpid()
    killed_count = 0
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] in ['python3', 'python']:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # Kill if running main.py and not current process
                    if ('main.py' in cmdline or 'bot.py' in cmdline) and proc.pid != current_pid:
                        print(f"🛑 Menghentikan proses: {proc.pid} - {cmdline}")
                        proc.terminate()
                        
                        # Wait for graceful termination
                        try:
                            proc.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            # Force kill if needed
                            proc.kill()
                            
                        killed_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
    except Exception as e:
        print(f"Error saat mencari proses: {e}")
    
    if killed_count > 0:
        print(f"✅ Berhasil menghentikan {killed_count} instance bot")
        print("⏳ Menunggu 3 detik untuk cleanup...")
        time.sleep(3)
    else:
        print("✅ Tidak ada instance bot lain yang berjalan")
    
    print("🚀 Siap untuk menjalankan bot baru!")


if __name__ == "__main__":
    kill_bot_instances()
