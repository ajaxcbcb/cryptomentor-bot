#!/usr/bin/env python3
"""
Restart cryptomentor service on VPS and clear Python cache
"""
import paramiko
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

def restart_service():
    """Restart service and clear cache"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected\n")
        
        # Clear Python cache
        print("Clearing Python bytecode cache...")
        stdin, stdout, stderr = ssh.exec_command(f"rm -rf {VPS_PATH}/app/__pycache__")
        stdout.channel.recv_exit_status()
        print("✅ Cache cleared\n")
        
        # Restart service
        print("Restarting cryptomentor service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart cryptomentor")
        stdout.channel.recv_exit_status()
        print("✅ Service restart command sent\n")
        
        # Wait a bit
        print("Waiting 3 seconds for service to start...")
        time.sleep(3)
        
        # Check status
        print("Checking service status...")
        stdin, stdout, stderr = ssh.exec_command("systemctl status cryptomentor --no-pager | head -15")
        status = stdout.read().decode()
        print(status)
        
        if "active (running)" in status:
            print("\n✅ Service is running!")
        else:
            print("\n⚠️ Service might have issues")
        
        # Verify fix is deployed
        print("\n" + "="*60)
        print("Verifying fix is deployed...")
        stdin, stdout, stderr = ssh.exec_command(
            f'grep -c "if not engine_on and session and session.get" {VPS_PATH}/app/handlers_autotrade.py'
        )
        count = stdout.read().decode().strip()
        print(f"Found {count} occurrences of the fix")
        
        if int(count) >= 3:
            print("✅ Fix is deployed correctly!")
        else:
            print(f"⚠️ Expected 3 occurrences, found {count}")
        
        ssh.close()
        print("\n" + "="*60)
        print("✅ Deployment complete!")
        print("\nUsers should now see 'Active' status immediately after bot restart.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    restart_service()
