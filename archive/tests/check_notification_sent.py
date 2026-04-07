#!/usr/bin/env python3
"""
Check if startup notifications were sent after latest restart
"""
import paramiko
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"

def check_sent():
    """Check if notifications were sent"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected\n")
        
        # Check for sendMessage calls
        print("="*60)
        print("Checking for sendMessage API calls...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '5 minutes ago' | grep -i 'sendMessage\\|send_message' | tail -20"
        )
        logs = stdout.read().decode()
        if logs:
            print("✅ Found sendMessage calls:")
            print(logs)
        else:
            print("⚠️ No sendMessage calls found")
        
        # Check for notification success logs
        print("\n" + "="*60)
        print("Checking for notification success logs...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '5 minutes ago' | grep -i 'notification sent\\|Scalping notification\\|Swing notification' | tail -20"
        )
        logs = stdout.read().decode()
        if logs:
            print("✅ Found notification logs:")
            print(logs)
        else:
            print("⚠️ No notification success logs found")
        
        # Check for Telegram POST requests
        print("\n" + "="*60)
        print("Checking for Telegram POST requests...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '5 minutes ago' | grep 'POST.*telegram.*sendMessage' | tail -15"
        )
        logs = stdout.read().decode()
        if logs:
            print("✅ Found Telegram POST requests:")
            print(logs)
        else:
            print("⚠️ No Telegram POST requests found")
        
        # Count how many engines were restored
        print("\n" + "="*60)
        print("Checking restoration summary...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '5 minutes ago' | grep -i 'Restoration Summary\\|Restored:\\|Skipped:\\|Failed:' | tail -10"
        )
        logs = stdout.read().decode()
        if logs:
            print(logs)
        else:
            print("No restoration summary found")
        
        ssh.close()
        
        print("\n" + "="*60)
        print("✅ Check complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Wait a bit for auto-restore to complete
    print("Waiting 10 seconds for auto-restore to complete...")
    time.sleep(10)
    check_sent()
