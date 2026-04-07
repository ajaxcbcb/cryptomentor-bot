#!/usr/bin/env python3
"""
Check if auto-restore is working
"""
import paramiko

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"

def check():
    print("=" * 80)
    print("CHECKING AUTO-RESTORE LOGS")
    print("=" * 80)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        
        # Check for auto-restore messages
        print("\n1. AUTO-RESTORE MESSAGES:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 500 --no-pager | grep -E '(AutoRestore|auto-restore|Engine restored|restoration)' | tail -30"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No auto-restore messages found")
        
        # Check for health check messages
        print("\n2. HEALTH CHECK MESSAGES:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 500 --no-pager | grep -E '(HealthCheck|health_check)' | tail -20"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No health check messages found yet (runs every 2 minutes)")
        
        # Check for engine start messages
        print("\n3. ENGINE START MESSAGES (Last 20):")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 500 --no-pager | grep -E '(Engine started|SCALPING engine|SWING engine|Scalping.*started)' | tail -20"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No engine start messages found")
        
        # Check scheduler start
        print("\n4. SCHEDULER START:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 200 --no-pager | grep -E '(Scheduler started|ROCKET)' | tail -10"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No scheduler start messages found")
        
        # Check current running engines
        print("\n5. CURRENT SCANNING ACTIVITY:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 100 --no-pager | grep -E 'Scan.*complete|scanning' | tail -15"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No scanning activity")
        
        ssh.close()
        
        print("\n" + "=" * 80)
        print("LOG CHECK COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check()
