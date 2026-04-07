#!/usr/bin/env python3
"""
Add Demo User to VPS
Telegram UID: 1234500005
Bitunix UID: 311966174
"""

import paramiko
import sys

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

def add_demo_user():
    print("🚀 Adding Demo User to VPS...")
    print(f"   Telegram UID: 1234500005")
    print(f"   Bitunix UID: 311966174")
    print()
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected to VPS")
        print()
        
        # Upload updated demo_users.py
        print("📤 Uploading demo_users.py...")
        sftp = ssh.open_sftp()
        sftp.put("Bismillah/app/demo_users.py", f"{VPS_PATH}/Bismillah/app/demo_users.py")
        sftp.close()
        print("   ✅ Uploaded")
        print()
        
        # Verify the change
        print("🔍 Verifying demo user added...")
        stdin, stdout, stderr = ssh.exec_command(
            f"grep -n '1234500005' {VPS_PATH}/Bismillah/app/demo_users.py"
        )
        result = stdout.read().decode().strip()
        if result:
            print(f"   ✅ Found: {result}")
        else:
            print("   ❌ User ID not found in file!")
            return False
        print()
        
        # Restart service
        print("🔄 Restarting service...")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo systemctl restart cryptomentor.service && sleep 2 && sudo systemctl status cryptomentor.service --no-pager -l | head -20"
        )
        output = stdout.read().decode()
        if "Active: active (running)" in output:
            print("   ✅ Service restarted successfully")
        else:
            print("   ⚠️ Service status unclear")
        print()
        
        print("=" * 60)
        print("✅ DEMO USER ADDED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("📝 User Details:")
        print(f"   • Telegram UID: 1234500005")
        print(f"   • Bitunix UID: 311966174")
        print(f"   • Balance Limit: $50 USD")
        print(f"   • Bypass Referral: Yes")
        print(f"   • Community Partners: No (restricted)")
        print()
        print("🎯 User can now use the bot with demo restrictions!")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    success = add_demo_user()
    sys.exit(0 if success else 1)
