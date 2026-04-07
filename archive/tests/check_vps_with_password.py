#!/usr/bin/env python3
"""
Check VPS logs with password authentication using pexpect
"""

import sys

try:
    import pexpect
except ImportError:
    print("Installing pexpect...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pexpect"])
    import pexpect

VPS_HOST = "root@147.93.156.165"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
SERVICE = "cryptomentor.service"

def run_ssh_command(command):
    """Run SSH command with password authentication"""
    ssh_cmd = f'ssh -o StrictHostKeyChecking=no {VPS_HOST} "{command}"'
    
    try:
        child = pexpect.spawn(ssh_cmd, timeout=30, encoding='utf-8')
        
        # Wait for password prompt
        i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
        
        if i == 0:
            # Send password
            child.sendline(VPS_PASSWORD)
            child.expect(pexpect.EOF)
            output = child.before
            child.close()
            return output
        else:
            return "Error: No password prompt"
            
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 80)
    print("🔍 CHECKING VPS LOGS FOR SOCIAL PROOF BROADCAST")
    print("=" * 80)
    print()
    
    # 1. Check service status
    print("1️⃣ Service Status...")
    print("-" * 80)
    cmd = f"systemctl status {SERVICE} --no-pager | head -15"
    output = run_ssh_command(cmd)
    print(output)
    print()
    
    # 2. Check for SocialProof logs
    print("2️⃣ Searching for 'SocialProof' in logs...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 2000 --no-pager | grep -i socialproof | tail -30"
    output = run_ssh_command(cmd)
    if output.strip() and "password:" not in output.lower():
        print(output)
    else:
        print("❌ No SocialProof logs found")
    print()
    
    # 3. Check for broadcast logs
    print("3️⃣ Searching for 'broadcast' in logs...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 2000 --no-pager | grep -i broadcast | tail -30"
    output = run_ssh_command(cmd)
    if output.strip() and "password:" not in output.lower():
        print(output)
    else:
        print("❌ No broadcast logs found")
    print()
    
    # 4. Check for Position Closed events
    print("4️⃣ Recent 'Position Closed' events...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 1000 --no-pager | grep 'Position Closed' | tail -20"
    output = run_ssh_command(cmd)
    if output.strip() and "password:" not in output.lower():
        print(output)
    else:
        print("❌ No Position Closed events found")
    print()
    
    # 5. Check for any autotrade engine activity
    print("5️⃣ Autotrade Engine Activity...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 1000 --no-pager | grep -i 'engine.*user' | tail -20"
    output = run_ssh_command(cmd)
    if output.strip() and "password:" not in output.lower():
        print(output)
    else:
        print("❌ No engine activity found")
    print()
    
    # 6. Check recent errors
    print("6️⃣ Recent Errors...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 500 --no-pager | grep -i 'error\\|exception' | tail -20"
    output = run_ssh_command(cmd)
    if output.strip() and "password:" not in output.lower():
        print(output)
    else:
        print("✅ No recent errors")
    print()
    
    # 7. Check last 50 lines of log
    print("7️⃣ Last 50 Lines of Log...")
    print("-" * 80)
    cmd = f"journalctl -u {SERVICE} -n 50 --no-pager"
    output = run_ssh_command(cmd)
    print(output)
    print()
    
    print("=" * 80)
    print("✅ Log check complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
