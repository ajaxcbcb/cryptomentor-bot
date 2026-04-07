#!/usr/bin/env python3
"""
Check if dashboard status fix is deployed on VPS
"""
import paramiko
import sys

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

def check_deployment():
    """Check if the fix is deployed on VPS"""
    try:
        # Connect to VPS
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected to VPS\n")
        
        # Check if fix is in the file
        print("Checking if dashboard status fix is deployed...")
        cmd = f'grep -n "if not engine_on and session and session.get" {VPS_PATH}/app/handlers_autotrade.py | head -3'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if output:
            print("✅ Fix found in VPS file:")
            print(output)
            
            # Count occurrences
            count = len(output.strip().split('\n'))
            print(f"\n📊 Found {count} occurrences of the fix")
            
            if count >= 3:
                print("✅ All 3 locations have the fix!")
            else:
                print(f"⚠️ Expected 3 occurrences, found {count}")
        else:
            print("❌ Fix NOT found in VPS file!")
            if error:
                print(f"Error: {error}")
            return False
        
        # Check service status
        print("\n" + "="*60)
        print("Checking service status...")
        stdin, stdout, stderr = ssh.exec_command("systemctl status cryptomentor --no-pager | head -20")
        status_output = stdout.read().decode()
        print(status_output)
        
        # Check if service is active
        if "active (running)" in status_output:
            print("✅ Service is running")
        else:
            print("⚠️ Service might not be running properly")
        
        # Check Python bytecode cache
        print("\n" + "="*60)
        print("Checking Python bytecode cache...")
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {VPS_PATH}/app/__pycache__/handlers_autotrade.*.pyc 2>/dev/null")
        cache_output = stdout.read().decode()
        
        if cache_output:
            print("Found bytecode cache:")
            print(cache_output)
            print("\n💡 Recommendation: Clear Python cache and restart service")
            print("Commands:")
            print(f"  rm -rf {VPS_PATH}/app/__pycache__")
            print("  systemctl restart cryptomentor")
        else:
            print("No bytecode cache found (or already cleared)")
        
        # Get last service restart time
        print("\n" + "="*60)
        print("Checking last service restart...")
        stdin, stdout, stderr = ssh.exec_command("systemctl show cryptomentor -p ActiveEnterTimestamp")
        restart_time = stdout.read().decode().strip()
        print(restart_time)
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_deployment()
    sys.exit(0 if success else 1)
