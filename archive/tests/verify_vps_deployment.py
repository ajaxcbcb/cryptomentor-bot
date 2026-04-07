#!/usr/bin/env python3
"""
Verify if VPS file is actually updated with the fix
"""
import paramiko

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot/Bismillah"

def verify():
    print("=" * 80)
    print("VERIFYING VPS DEPLOYMENT")
    print("=" * 80)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        
        # Check if the fix is in the file
        print("\n1. Checking if fix is in handlers_autotrade.py...")
        stdin, stdout, stderr = ssh.exec_command(
            f"grep -n 'Priority 2: If task not found but session is active' {VPS_PATH}/app/handlers_autotrade.py | head -5"
        )
        output = stdout.read().decode('utf-8')
        
        if output.strip():
            print("✅ Fix found in file:")
            print(output)
        else:
            print("❌ Fix NOT found in file!")
            print("\nChecking what's actually in the file around line 220...")
            stdin, stdout, stderr = ssh.exec_command(
                f"sed -n '215,230p' {VPS_PATH}/app/handlers_autotrade.py"
            )
            print(stdout.read().decode('utf-8'))
        
        # Check file modification time
        print("\n2. Checking file modification time...")
        stdin, stdout, stderr = ssh.exec_command(
            f"ls -lh {VPS_PATH}/app/handlers_autotrade.py"
        )
        print(stdout.read().decode('utf-8'))
        
        # Check if service restarted recently
        print("\n3. Checking service restart time...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl status cryptomentor --no-pager | grep Active"
        )
        print(stdout.read().decode('utf-8'))
        
        ssh.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
