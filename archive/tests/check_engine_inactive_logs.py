#!/usr/bin/env python3
"""
Check VPS logs for engine inactive issues
"""
import paramiko
import re
from datetime import datetime

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

def check_logs():
    """Check VPS logs for engine stop patterns"""
    print("=" * 80)
    print("CHECKING VPS LOGS FOR ENGINE INACTIVE ISSUES")
    print("=" * 80)
    
    try:
        # Connect to VPS
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        
        # Get recent logs with engine stop/error patterns
        commands = [
            # 1. Check for engine stops
            ("Engine Stops", "journalctl -u cryptomentor -n 1000 --no-pager | grep -E '(AutoTrade stopped|AutoTrade cancelled|Engine stopped)' | tail -20"),
            
            # 2. Check for exceptions/crashes
            ("Exceptions/Crashes", "journalctl -u cryptomentor -n 1000 --no-pager | grep -E '(Exception|Error|Traceback|CRASHED)' | tail -30"),
            
            # 3. Check for WebSocket errors
            ("WebSocket Errors", "journalctl -u cryptomentor -n 1000 --no-pager | grep -E '(WS error|WebSocket|websocket)' | tail -20"),
            
            # 4. Check for circuit breaker triggers
            ("Circuit Breaker", "journalctl -u cryptomentor -n 1000 --no-pager | grep -E '(Circuit breaker|Daily loss limit)' | tail -10"),
            
            # 5. Check for API errors
            ("API Errors", "journalctl -u cryptomentor -n 1000 --no-pager | grep -E '(API key|Invalid API|Insufficient balance)' | tail -20"),
            
            # 6. Check current running engines
            ("Current Engines", "journalctl -u cryptomentor -n 200 --no-pager | grep -E 'Engine started|Scalping.*Engine' | tail -15"),
        ]
        
        for title, cmd in commands:
            print(f"\n{'=' * 80}")
            print(f"{title.upper()}")
            print("=" * 80)
            
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode('utf-8')
            
            if output.strip():
                print(output)
            else:
                print(f"No {title.lower()} found")
        
        # Check for specific user complaints
        print(f"\n{'=' * 80}")
        print("CHECKING SPECIFIC USERS WITH ISSUES")
        print("=" * 80)
        
        # Get list of users who had engines stop
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 2000 --no-pager | "
            "grep -E 'AutoTrade (stopped|cancelled)' | "
            "grep -oP 'user \\K[0-9]+' | sort | uniq"
        )
        user_ids = stdout.read().decode('utf-8').strip().split('\n')
        
        if user_ids and user_ids[0]:
            print(f"\nUsers with engine stops: {', '.join(user_ids[:10])}")
            
            # Check last activity for each user
            for user_id in user_ids[:5]:  # Check first 5 users
                print(f"\n--- User {user_id} ---")
                stdin, stdout, stderr = ssh.exec_command(
                    f"journalctl -u cryptomentor -n 2000 --no-pager | "
                    f"grep 'user {user_id}\\|:{user_id}\\]' | tail -10"
                )
                print(stdout.read().decode('utf-8'))
        
        ssh.close()
        
        print("\n" + "=" * 80)
        print("LOG CHECK COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error checking logs: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_logs()
