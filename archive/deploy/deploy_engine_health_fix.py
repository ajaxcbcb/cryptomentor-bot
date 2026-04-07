#!/usr/bin/env python3
"""
Deploy Engine Health Check Fix to VPS
- Reduced health check interval from 5min to 2min
- Enhanced logging for auto-restore
- Better user notifications
"""
import paramiko
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot/Bismillah"

def deploy():
    print("=" * 80)
    print("DEPLOYING ENGINE HEALTH CHECK FIX")
    print("=" * 80)
    
    try:
        # Connect to VPS
        print("\n1. Connecting to VPS...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        print("✅ Connected")
        
        # Upload scheduler.py
        print("\n2. Uploading scheduler.py...")
        sftp = ssh.open_sftp()
        sftp.put("Bismillah/app/scheduler.py", f"{VPS_PATH}/app/scheduler.py")
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
        stdin, stdout, stderr = ssh.exec_command("journalctl -u cryptomentor -n 30 --no-pager")
        logs = stdout.read().decode('utf-8')
        print(logs)
        
        ssh.close()
        
        print("\n" + "=" * 80)
        print("DEPLOYMENT COMPLETE")
        print("=" * 80)
        print("\n✅ Changes deployed:")
        print("  • Health check interval: 5min → 2min")
        print("  • Enhanced auto-restore logging")
        print("  • Better user notifications")
        print("\n📊 Monitoring:")
        print("  • Health check runs every 2 minutes")
        print("  • Dead engines will be auto-restarted")
        print("  • Users will receive detailed notifications")
        print("\n💡 Next steps:")
        print("  • Monitor logs for auto-restore activity")
        print("  • Check if users still report inactive engines")
        print("  • Collect feedback after 24 hours")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deploy()
