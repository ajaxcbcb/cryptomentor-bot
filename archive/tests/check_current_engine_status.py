#!/usr/bin/env python3
"""
Check current engine status on VPS
"""
import paramiko
import json

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

def check_status():
    """Check current engine status"""
    print("=" * 80)
    print("CHECKING CURRENT ENGINE STATUS")
    print("=" * 80)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        
        # 1. Check service status
        print("\n1. SERVICE STATUS:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command("systemctl status cryptomentor --no-pager | head -20")
        print(stdout.read().decode('utf-8'))
        
        # 2. Check recent logs (last 50 lines)
        print("\n2. RECENT LOGS (Last 50 lines):")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command("journalctl -u cryptomentor -n 50 --no-pager")
        print(stdout.read().decode('utf-8'))
        
        # 3. Check for active sessions in database
        print("\n3. CHECKING DATABASE FOR ACTIVE SESSIONS:")
        print("-" * 80)
        
        # Create a Python script to check database
        check_db_script = """
import sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
from app.supabase_repo import _client

try:
    s = _client()
    result = s.table("autotrade_sessions").select("telegram_id, status, initial_deposit, leverage, exchange").in_(
        "status", ["active", "uid_verified"]
    ).execute()
    
    if result.data:
        print(f"Found {len(result.data)} active session(s):")
        for session in result.data:
            print(f"  - User {session['telegram_id']}: {session['status']}, ${session.get('initial_deposit', 0)}, {session.get('leverage', 10)}x, {session.get('exchange', 'bitunix')}")
    else:
        print("No active sessions found in database")
except Exception as e:
    print(f"Error checking database: {e}")
"""
        
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPS_PATH} && python3 -c '{check_db_script}'"
        )
        print(stdout.read().decode('utf-8'))
        err = stderr.read().decode('utf-8')
        if err:
            print(f"Errors: {err}")
        
        # 4. Check if engines are actually running
        print("\n4. CHECKING IF ENGINES ARE RUNNING:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 100 --no-pager | grep -E '(Engine started|Scalping.*started|SWING engine|SCALPING engine)' | tail -20"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No engine start messages found in recent logs")
        
        # 5. Check for any stop/cancel messages
        print("\n5. CHECKING FOR STOP/CANCEL MESSAGES:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 200 --no-pager | grep -E '(stopped|cancelled|Stop requested)' | tail -20"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No stop/cancel messages found")
        
        # 6. Check health check scheduler
        print("\n6. HEALTH CHECK SCHEDULER STATUS:")
        print("-" * 80)
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor -n 100 --no-pager | grep -E 'HealthCheck|health_check|restore' | tail -15"
        )
        output = stdout.read().decode('utf-8')
        if output.strip():
            print(output)
        else:
            print("No health check messages found")
        
        ssh.close()
        
        print("\n" + "=" * 80)
        print("STATUS CHECK COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_status()
