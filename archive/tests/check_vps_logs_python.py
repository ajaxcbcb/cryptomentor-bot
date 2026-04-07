#!/usr/bin/env python3
"""
Check VPS logs for social proof broadcast activity
Uses subprocess to run SSH commands
"""

import subprocess
import sys

VPS_HOST = "root@147.93.156.165"
SERVICE = "cryptomentor.service"

def run_ssh_command(command):
    """Run SSH command and return output"""
    full_cmd = f'ssh {VPS_HOST} "{command}"'
    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return "⚠️ Command timed out"
    except Exception as e:
        return f"❌ Error: {e}"

def main():
    print("=" * 70)
    print("🔍 CHECKING VPS LOGS FOR SOCIAL PROOF BROADCAST")
    print("=" * 70)
    print()
    
    # 1. Check for SocialProof logs
    print("1️⃣ Searching for 'SocialProof' in logs...")
    print("-" * 70)
    cmd = f"journalctl -u {SERVICE} -n 2000 --no-pager | grep -i socialproof | tail -30"
    output = run_ssh_command(cmd)
    if output.strip():
        print(output)
    else:
        print("❌ No SocialProof logs found")
    print()
    
    # 2. Check for broadcast logs
    print("2️⃣ Searching for 'broadcast' in logs...")
    print("-" * 70)
    cmd = f"journalctl -u {SERVICE} -n 2000 --no-pager | grep -i broadcast | tail -30"
    output = run_ssh_command(cmd)
    if output.strip():
        print(output)
    else:
        print("❌ No broadcast logs found")
    print()
    
    # 3. Check for Position Closed events
    print("3️⃣ Recent 'Position Closed' events...")
    print("-" * 70)
    cmd = f"journalctl -u {SERVICE} -n 1000 --no-pager | grep 'Position Closed' | tail -20"
    output = run_ssh_command(cmd)
    if output.strip():
        print(output)
    else:
        print("❌ No Position Closed events found")
    print()
    
    # 4. Check for broadcast_profit function calls
    print("4️⃣ Searching for 'broadcast_profit' function calls...")
    print("-" * 70)
    cmd = f"journalctl -u {SERVICE} -n 2000 --no-pager | grep broadcast_profit | tail -20"
    output = run_ssh_command(cmd)
    if output.strip():
        print(output)
    else:
        print("❌ No broadcast_profit calls found")
    print()
    
    # 5. Check for errors
    print("5️⃣ Checking for errors related to social proof/broadcast...")
    print("-" * 70)
    cmd = f"journalctl -u {SERVICE} -n 1000 --no-pager | grep -i 'error\\|exception' | grep -i 'social\\|broadcast' | tail -15"
    output = run_ssh_command(cmd)
    if output.strip():
        print(output)
    else:
        print("✅ No errors found")
    print()
    
    # 6. Get recent service status
    print("6️⃣ Service status...")
    print("-" * 70)
    cmd = f"systemctl status {SERVICE} --no-pager | head -20"
    output = run_ssh_command(cmd)
    print(output)
    print()
    
    print("=" * 70)
    print("✅ Log check complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
