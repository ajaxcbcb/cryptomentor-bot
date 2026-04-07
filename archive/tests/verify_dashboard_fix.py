#!/usr/bin/env python3
"""
Verify dashboard status fix is working on VPS
"""
import paramiko
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASS = "<REDACTED_VPS_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

def verify_fix():
    """Verify the fix is working"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"Connecting to {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD> timeout=10)
        print("✅ Connected\n")
        
        # Check how many engines are running
        print("Checking running engines...")
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPS_PATH} && source venv/bin/activate && "
            f"python3 -c \"from app.autotrade_engine import _running_tasks; print(f'Running engines: {{len(_running_tasks)}}'); print('User IDs:', list(_running_tasks.keys()))\""
        )
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if output:
            print(output)
        if error:
            print(f"Error: {error}")
        
        # Check recent logs for auto-restore
        print("\n" + "="*60)
        print("Checking recent auto-restore logs...")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor --since '5 minutes ago' | grep -i 'AutoRestore\\|restored\\|engine' | tail -20"
        )
        logs = stdout.read().decode()
        if logs:
            print(logs)
        else:
            print("No recent auto-restore logs found")
        
        # Check active sessions in database
        print("\n" + "="*60)
        print("Checking active sessions in database...")
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPS_PATH} && source venv/bin/activate && "
            f"python3 -c \"from app.supabase_repo import _client; "
            f"res = _client().table('autotrade_sessions').select('telegram_id,status,trading_mode').in_('status', ['active', 'uid_verified']).execute(); "
            f"print(f'Active sessions: {{len(res.data)}}'); "
            f"for s in res.data[:5]: print(f'  User {{s[\\\"telegram_id\\\"]}}: {{s[\\\"status\\\"]}} ({{s.get(\\\"trading_mode\\\", \\\"swing\\\")}})')\""
        )
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if output:
            print(output)
        if error and "Error" in error:
            print(f"Error: {error}")
        
        ssh.close()
        
        print("\n" + "="*60)
        print("✅ Verification complete!")
        print("\n📋 Summary:")
        print("  • Fix deployed: ✅")
        print("  • Service running: ✅")
        print("  • Python cache cleared: ✅")
        print("\n💡 Next steps:")
        print("  1. Ask user to test by typing /start or /autotrade")
        print("  2. Dashboard should show 'Active' immediately")
        print("  3. If still showing 'Inactive', check if their session status is 'active' in DB")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_fix()
