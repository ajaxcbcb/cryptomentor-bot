#!/usr/bin/env python3
"""
Check VPS logs using paramiko (SSH library for Python)
"""

import sys

try:
    import paramiko
except ImportError:
    print("Installing paramiko...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
SERVICE = "cryptomentor.service"

def run_ssh_command(ssh, command):
    """Run command via SSH and return output"""
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if error and not output:
            return f"Error: {error}"
        return output
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 80)
    print("🔍 CHECKING VPS LOGS FOR SOCIAL PROOF BROADCAST")
    print("=" * 80)
    print()
    
    # Connect to VPS
    print("🔌 Connecting to VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected successfully!")
        print()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # 1. Check service status
    print("1️⃣ Service Status...")
    print("-" * 80)
    cmd = f"systemctl status {SERVICE} --no-pager | head -15"
    output = run_ssh_command(ssh, cmd)
    print(output)
    print()
    
    # 2. Check for SocialProof logs
    print("2️⃣ Searching for 'SocialProof' in logs...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 2000 --no-pager | grep -i socialproof | tail -30"
    output = run_ssh_command(ssh, cmd)
    if output.strip() and not output.startswith("Error"):
        print(output)
    else:
        print("❌ No SocialProof logs found")
    print()
    
    # 3. Check for broadcast logs
    print("3️⃣ Searching for 'broadcast' in logs...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 2000 --no-pager | grep -i broadcast | tail -30"
    output = run_ssh_command(ssh, cmd)
    if output.strip() and not output.startswith("Error"):
        print(output)
    else:
        print("❌ No broadcast logs found")
    print()
    
    # 4. Check for Position Closed events
    print("4️⃣ Recent 'Position Closed' events...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 1000 --no-pager | grep 'Position Closed' | tail -20"
    output = run_ssh_command(ssh, cmd)
    if output.strip() and not output.startswith("Error"):
        print(output)
    else:
        print("❌ No Position Closed events found")
    print()
    
    # 5. Check for any autotrade engine activity
    print("5️⃣ Autotrade Engine Activity (started/stopped)...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 1000 --no-pager | grep -E 'Engine.*started|Engine.*stopped|AutoTrade.*started' | tail -20"
    output = run_ssh_command(ssh, cmd)
    if output.strip() and not output.startswith("Error"):
        print(output)
    else:
        print("❌ No engine start/stop events found")
    print()
    
    # 6. Check for trade activity
    print("6️⃣ Trade Activity (orders, positions)...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 1000 --no-pager | grep -iE 'order.*success|position.*opened|trade.*opened' | tail -20"
    output = run_ssh_command(ssh, cmd)
    if output.strip() and not output.startswith("Error"):
        print(output)
    else:
        print("❌ No trade activity found")
    print()
    
    # 7. Check recent errors
    print("7️⃣ Recent Errors...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 500 --no-pager | grep -i 'error\\|exception' | tail -20"
    output = run_ssh_command(ssh, cmd)
    if output.strip() and not output.startswith("Error"):
        print(output)
    else:
        print("✅ No recent errors")
    print()
    
    # 8. Check last 100 lines of log
    print("8️⃣ Last 100 Lines of Log...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 100 --no-pager"
    output = run_ssh_command(ssh, cmd)
    print(output)
    print()
    
    # 9. Check if bot process is running
    print("9️⃣ Bot Process Status...")
    print("-" * 80)
    cmd = "ps aux | grep python | grep bot.py | grep -v grep"
    output = run_ssh_command(ssh, cmd)
    if output.strip() and not output.startswith("Error"):
        print("✅ Bot process is running:")
        print(output)
    else:
        print("⚠️ Bot process not found or not running")
    print()
    
    ssh.close()
    
    print("=" * 80)
    print("✅ Log check complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
