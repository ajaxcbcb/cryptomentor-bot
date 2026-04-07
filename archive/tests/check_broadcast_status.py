"""
Check if bot is currently broadcasting
Cek status broadcast real-time dari VPS
"""

import paramiko
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"

def check_broadcast_status():
    """Check if bot is currently broadcasting"""
    
    print("="*60)
    print("CEK STATUS BROADCAST BOT")
    print("="*60)
    
    try:
        # Connect to VPS
        print("\n🔌 Connecting to VPS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        print("✅ Connected!")
        
        # Check 1: Recent broadcast logs (last 5 minutes)
        print("\n" + "="*60)
        print("📊 CHECK 1: Recent Broadcast Activity (Last 5 Minutes)")
        print("="*60)
        
        cmd = 'journalctl -u cryptomentor.service --since "5 minutes ago" | grep -i "socialproof\\|broadcast"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        recent_logs = stdout.read().decode()
        
        if recent_logs.strip():
            print("\n🔴 BROADCAST ACTIVITY DETECTED!")
            print(recent_logs)
        else:
            print("\n✅ No broadcast activity in last 5 minutes")
        
        # Check 2: Today's broadcast count
        print("\n" + "="*60)
        print("📊 CHECK 2: Today's Broadcast Count")
        print("="*60)
        
        cmd = 'journalctl -u cryptomentor.service --since today | grep "Queued broadcast" | wc -l'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        count = stdout.read().decode().strip()
        
        print(f"\n📢 Total broadcasts today: {count}")
        
        # Check 3: Last broadcast time
        print("\n" + "="*60)
        print("📊 CHECK 3: Last Broadcast Time")
        print("="*60)
        
        cmd = 'journalctl -u cryptomentor.service | grep "Queued broadcast" | tail -1'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        last_broadcast = stdout.read().decode().strip()
        
        if last_broadcast:
            print(f"\n🕐 Last broadcast:")
            print(last_broadcast)
        else:
            print("\n❌ No broadcasts found in logs")
        
        # Check 4: Recent trade closes (potential triggers)
        print("\n" + "="*60)
        print("📊 CHECK 4: Recent Trade Closes (Last 10 Minutes)")
        print("="*60)
        
        cmd = 'journalctl -u cryptomentor.service --since "10 minutes ago" | grep "Closed trade"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        recent_closes = stdout.read().decode()
        
        if recent_closes.strip():
            print("\n📈 Recent trade closes:")
            print(recent_closes)
        else:
            print("\n✅ No trades closed in last 10 minutes")
        
        # Check 5: Current bot status
        print("\n" + "="*60)
        print("📊 CHECK 5: Bot Service Status")
        print("="*60)
        
        cmd = 'systemctl status cryptomentor.service | head -10'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        status = stdout.read().decode()
        
        if "active (running)" in status:
            print("\n✅ Bot is RUNNING")
        else:
            print("\n❌ Bot is NOT running")
            print(status)
        
        # Check 6: Live monitoring (5 seconds)
        print("\n" + "="*60)
        print("📊 CHECK 6: Live Monitoring (5 seconds)")
        print("="*60)
        print("\n👀 Watching for broadcast activity...")
        
        cmd = 'timeout 5 journalctl -u cryptomentor.service -f | grep -i "socialproof\\|broadcast" || true'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        live_logs = stdout.read().decode()
        
        if live_logs.strip():
            print("\n🔴 LIVE BROADCAST DETECTED!")
            print(live_logs)
        else:
            print("\n✅ No broadcast activity detected in 5 seconds")
        
        ssh.close()
        
        # Summary
        print("\n" + "="*60)
        print("📋 SUMMARY")
        print("="*60)
        
        if recent_logs.strip() or live_logs.strip():
            print("\n🔴 STATUS: BOT SEDANG BROADCAST!")
            print("   Bot sedang mengirim notifikasi ke users")
        else:
            print("\n✅ STATUS: Bot tidak sedang broadcast")
            print("   Bot standby, menunggu trade profit >= $5")
        
        print(f"\n📊 Total broadcasts hari ini: {count}")
        
        if last_broadcast:
            print(f"🕐 Broadcast terakhir: {last_broadcast.split()[0:3]}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_broadcast_status()
