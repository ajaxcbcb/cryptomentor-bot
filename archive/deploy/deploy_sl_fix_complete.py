#!/usr/bin/env python3
"""
Deploy SL Price Error Fix to VPS
Fixes error 30029 in StackMentor breakeven SL update
"""

import paramiko
import os
import sys

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

FILES_TO_DEPLOY = [
    ("Bismillah/app/stackmentor.py", f"{VPS_PATH}/Bismillah/app/stackmentor.py"),
    ("Bismillah/app/bitunix_autotrade_client.py", f"{VPS_PATH}/Bismillah/app/bitunix_autotrade_client.py"),
]

def deploy():
    print("🚀 Deploying SL Price Error Fix to VPS...")
    print(f"   Host: {VPS_HOST}")
    print(f"   Path: {VPS_PATH}")
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected!")
        print()
        
        # Upload files
        print("📤 Uploading fixed files...")
        sftp = ssh.open_sftp()
        
        for local_path, remote_path in FILES_TO_DEPLOY:
            if not os.path.exists(local_path):
                print(f"❌ File not found: {local_path}")
                continue
            
            print(f"   • {local_path} → {remote_path}")
            sftp.put(local_path, remote_path)
            print(f"     ✅ Uploaded")
        
        sftp.close()
        print()
        
        # Restart service
        print("🔄 Restarting cryptomentor service...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/cryptomentor-bot && sudo systemctl restart cryptomentor.service && sleep 3 && sudo systemctl status cryptomentor.service --no-pager -l"
        )
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if error and "Active: active (running)" not in output:
            print(f"⚠️ Service restart output:\n{error}")
        
        print(output)
        print()
        
        # Check logs for errors
        print("📊 Checking recent logs...")
        stdin, stdout, stderr = ssh.exec_command(
            "sudo journalctl -u cryptomentor.service -n 20 --no-pager"
        )
        
        logs = stdout.read().decode()
        print(logs[-1000:])  # Last 1000 chars
        print()
        
        print("✅ Deployment complete!")
        print()
        print("📝 What was fixed:")
        print("   1. Added get_ticker() method to BitunixAutoTradeClient")
        print("   2. Added SL validation in StackMentor handle_tp1_hit()")
        print("   3. Prevents error 30029 when moving SL to breakeven")
        print("   4. Graceful handling if market moved too far")
        print()
        print("🔍 Monitor logs:")
        print(f"   ssh {VPS_USER}@{VPS_HOST}")
        print("   sudo journalctl -u cryptomentor.service -f | grep -i 'stackmentor\\|invalid sl'")
        print()
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy()
