#!/usr/bin/env python3
"""
Check if startup notifications were sent to users after bot restart
"""
import paramiko
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"

def check_notifications():
    """Check recent logs for startup notifications"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected\n")
        
        # Check auto-restore logs
        print("="*60)
        print("Checking auto-restore process...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '10 minutes ago' | grep -i 'AutoRestore' | tail -30"
        )
        logs = stdout.read().decode()
        if logs:
            print(logs)
        else:
            print("No auto-restore logs found in last 10 minutes")
        
        # Check for notification sending
        print("\n" + "="*60)
        print("Checking for notification attempts...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '10 minutes ago' | grep -i 'notify\\|notification\\|send_message' | tail -20"
        )
        logs = stdout.read().decode()
        if logs:
            print(logs)
        else:
            print("No notification logs found")
        
        # Check for engine startup
        print("\n" + "="*60)
        print("Checking engine startup logs...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '10 minutes ago' | grep -i 'Engine started\\|Scalping.*Active\\|started.*engine' | tail -20"
        )
        logs = stdout.read().decode()
        if logs:
            print(logs)
        else:
            print("No engine startup logs found")
        
        # Check current running engines
        print("\n" + "="*60)
        print("Checking currently running engines...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '1 minute ago' | grep -i 'Scalping.*Scan cycle' | tail -10"
        )
        logs = stdout.read().decode()
        if logs:
            print("✅ Engines are actively scanning:")
            print(logs)
        else:
            print("⚠️ No recent scan activity found")
        
        ssh.close()
        
        print("\n" + "="*60)
        print("✅ Check complete!")
        print("\n💡 If users didn't receive notifications:")
        print("  1. Check if their Telegram blocked the bot")
        print("  2. Verify their telegram_id is correct in database")
        print("  3. Check bot token is valid")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_notifications()
