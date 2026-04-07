#!/usr/bin/env python3
"""
Check for notification errors in logs
"""
import paramiko

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"

def check_errors():
    """Check for errors in notification sending"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected\n")
        
        # Check for any errors after auto-restore
        print("="*60)
        print("Checking for errors after auto-restore...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '10 minutes ago' | grep -i 'error\\|exception\\|failed\\|traceback' | grep -v 'PTBUserWarning' | tail -30"
        )
        logs = stdout.read().decode()
        if logs:
            print("⚠️ Found errors:")
            print(logs)
        else:
            print("✅ No errors found")
        
        # Check for Telegram API calls
        print("\n" + "="*60)
        print("Checking for Telegram API activity...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '10 minutes ago' | grep -i 'telegram\\|bot.send' | tail -20"
        )
        logs = stdout.read().decode()
        if logs:
            print(logs)
        else:
            print("No Telegram API activity found")
        
        # Check Python asyncio task creation
        print("\n" + "="*60)
        print("Checking for asyncio task creation...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '10 minutes ago' | grep -i 'create_task\\|asyncio' | tail -15"
        )
        logs = stdout.read().decode()
        if logs:
            print(logs)
        else:
            print("No asyncio task logs found")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_errors()
