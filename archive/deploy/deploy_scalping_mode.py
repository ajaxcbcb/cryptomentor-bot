#!/usr/bin/env python3
"""
Deployment script for Scalping Mode feature
Uploads files to VPS and restarts service
"""

import paramiko
import os
from pathlib import Path

# VPS Configuration
VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

# Files to deploy
NEW_FILES = [
    "Bismillah/app/trading_mode.py",
    "Bismillah/app/trading_mode_manager.py",
    "Bismillah/app/scalping_engine.py",
]

UPDATED_FILES = [
    "Bismillah/app/autosignal_fast.py",
    # Add these after manual modifications:
    # "Bismillah/app/handlers_autotrade.py",
    # "Bismillah/app/autotrade_engine.py",
    # "Bismillah/bot.py",
]

DATABASE_MIGRATION = "db/add_trading_mode.sql"


def deploy_files():
    """Deploy files to VPS"""
    print("🚀 Starting deployment to VPS...")
    
    # Create SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect
        print(f"📡 Connecting to {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        sftp = ssh.open_sftp()
        
        # Deploy new files
        print("\n📦 Deploying new files...")
        for file_path in NEW_FILES:
            if not os.path.exists(file_path):
                print(f"  ⚠️  File not found: {file_path}")
                continue
            
            remote_path = f"{VPS_PATH}/{file_path}"
            print(f"  ⬆️  {file_path} -> {remote_path}")
            
            # Create directory if needed
            remote_dir = os.path.dirname(remote_path)
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {remote_dir}")
                stdout.channel.recv_exit_status()
            
            sftp.put(file_path, remote_path)
            print(f"  ✅ Uploaded {file_path}")
        
        # Deploy updated files
        print("\n📝 Deploying updated files...")
        for file_path in UPDATED_FILES:
            if not os.path.exists(file_path):
                print(f"  ⚠️  File not found: {file_path}")
                continue
            
            remote_path = f"{VPS_PATH}/{file_path}"
            print(f"  ⬆️  {file_path} -> {remote_path}")
            sftp.put(file_path, remote_path)
            print(f"  ✅ Updated {file_path}")
        
        # Deploy database migration
        print("\n🗄️  Deploying database migration...")
        if os.path.exists(DATABASE_MIGRATION):
            remote_path = f"{VPS_PATH}/{DATABASE_MIGRATION}"
            sftp.put(DATABASE_MIGRATION, remote_path)
            print(f"  ✅ Uploaded {DATABASE_MIGRATION}")
        else:
            print(f"  ⚠️  Migration file not found: {DATABASE_MIGRATION}")
        
        sftp.close()
        
        # Restart service
        print("\n🔄 Restarting cryptomentor service...")
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPS_PATH} && systemctl restart cryptomentor.service"
        )
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("  ✅ Service restarted successfully")
        else:
            print(f"  ❌ Service restart failed with exit code {exit_status}")
            error_output = stderr.read().decode()
            if error_output:
                print(f"  Error: {error_output}")
        
        # Check service status
        print("\n📊 Checking service status...")
        stdin, stdout, stderr = ssh.exec_command("systemctl status cryptomentor.service")
        status_output = stdout.read().decode()
        
        if "active (running)" in status_output:
            print("  ✅ Service is running")
        else:
            print("  ⚠️  Service status:")
            print(status_output)
        
        # Show recent logs
        print("\n📋 Recent logs:")
        stdin, stdout, stderr = ssh.exec_command(
            "journalctl -u cryptomentor.service -n 20 --no-pager"
        )
        logs = stdout.read().decode()
        print(logs)
        
        print("\n✅ Deployment complete!")
        print("\n📝 Next steps:")
        print("1. Test /autotrade command")
        print("2. Click 'Trading Mode' button")
        print("3. Try switching to Scalping Mode")
        print("4. Monitor logs: journalctl -u cryptomentor.service -f")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        ssh.close()


def run_database_migration():
    """Run database migration on VPS"""
    print("\n🗄️  Running database migration...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(VPS_HOST, username=VPS_USER, password=<REDACTED_PASSWORD>
        
        # Backup database first
        print("  📦 Creating database backup...")
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPS_PATH} && pg_dump cryptomentor > backup_scalping_$(date +%Y%m%d_%H%M%S).sql"
        )
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("  ✅ Database backup created")
        else:
            print("  ⚠️  Backup failed, but continuing...")
        
        # Run migration
        print("  🔄 Running migration script...")
        stdin, stdout, stderr = ssh.exec_command(
            f"cd {VPS_PATH} && psql cryptomentor < {DATABASE_MIGRATION}"
        )
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if exit_status == 0:
            print("  ✅ Migration completed successfully")
            if output:
                print(f"  Output: {output}")
        else:
            print(f"  ❌ Migration failed with exit code {exit_status}")
            if error:
                print(f"  Error: {error}")
        
        # Verify migration
        print("  🔍 Verifying migration...")
        stdin, stdout, stderr = ssh.exec_command(
            "psql cryptomentor -c \"SELECT column_name FROM information_schema.columns WHERE table_name='autotrade_sessions' AND column_name='trading_mode';\""
        )
        verify_output = stdout.read().decode()
        
        if "trading_mode" in verify_output:
            print("  ✅ Column 'trading_mode' exists")
        else:
            print("  ⚠️  Column verification failed")
            print(f"  Output: {verify_output}")
        
    except Exception as e:
        print(f"  ❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        ssh.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  SCALPING MODE DEPLOYMENT")
    print("=" * 60)
    
    # Ask for confirmation
    print("\n⚠️  This will deploy Scalping Mode to production VPS")
    print(f"   Host: {VPS_HOST}")
    print(f"   Path: {VPS_PATH}")
    print("\nFiles to deploy:")
    for f in NEW_FILES + UPDATED_FILES:
        print(f"  - {f}")
    
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() != "yes":
        print("❌ Deployment cancelled")
        exit(0)
    
    # Run migration first
    run_migration = input("\nRun database migration? (yes/no): ")
    if run_migration.lower() == "yes":
        run_database_migration()
    
    # Deploy files
    deploy_files()
