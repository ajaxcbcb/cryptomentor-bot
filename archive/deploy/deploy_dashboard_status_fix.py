#!/usr/bin/env python3
"""
Deploy Dashboard Status Fix to VPS
- Fix "Inactive" status showing when engine is actually running after auto-restore
- Add fallback check to database session status
"""
import paramiko
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot/Bismillah"

def deploy():
    print("=" * 80)
    print("DEPLOYING DASHBOARD STATUS FIX")
    print("=" * 80)
    
    try:
        # Connect to VPS
        print("\n1. Connecting to VPS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        print("✅ Connected")
        
        # Upload handlers_autotrade.py
        print("\n2. Uploading handlers_autotrade.py...")
        sftp = ssh.open_sftp()
        sftp.put("Bismillah/app/handlers_autotrade.py", f"{VPS_PATH}/app/handlers_autotrade.py")
        sftp.close()
        print("✅ Uploaded")
        
        # Restart service
        print("\n3. Restarting cryptomentor service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart cryptomentor")
        time.sleep(2)
        
        # Check status
        print("\n4. Checking service status...")
        stdin, stdout, stderr = ssh.exec_command("systemctl status cryptomentor --no-pager | head -15")
        status = stdout.read().decode('utf-8')
        print(status)
        
        # Check recent logs
        print("\n5. Checking recent logs...")
        stdin, stdout, stderr = ssh.exec_command("journalctl -u cryptomentor -n 20 --no-pager")
        logs = stdout.read().decode('utf-8')
        print(logs)
        
        ssh.close()
        
        print("\n" + "=" * 80)
        print("DEPLOYMENT COMPLETE")
        print("=" * 80)
        print("\n✅ Changes deployed:")
        print("  • Dashboard status now checks DB session as fallback")
        print("  • If session is 'active' but task not found, show as 'Active'")
        print("  • Prevents 'Inactive' showing during auto-restore")
        print("\n📊 Impact:")
        print("  • User sees 'Active' immediately after bot restart")
        print("  • No confusion during auto-restore process")
        print("  • Better UX - status matches reality")
        print("\n💡 How it works:")
        print("  1. Check if engine task is running (primary)")
        print("  2. If not found, check DB session status (fallback)")
        print("  3. If session is 'active', assume engine is starting")
        print("  4. Show 'Active' to avoid user confusion")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
