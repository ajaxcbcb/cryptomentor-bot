#!/usr/bin/env python3
"""
Automated Deployment Script for Risk Per Trade Phase 1
Run this script to deploy automatically to VPS
"""

import subprocess
import sys
import time

# VPS Configuration
VPS_HOST = "147.93.156.165"
VPS_USER = "root"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"

# Files to deploy
FILES_TO_DEPLOY = [
    "Bismillah/app/supabase_repo.py",
    "Bismillah/app/position_sizing.py",
    "Bismillah/app/handlers_autotrade.py",
]

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(text)
    print("="*60 + "\n")

def run_command(cmd, description):
    """Run shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def check_sshpass():
    """Check if sshpass is installed"""
    result = subprocess.run(
        "sshpass -V",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def main():
    """Main deployment function"""
    print_header("RISK PER TRADE PHASE 1 - AUTOMATED DEPLOYMENT")
    
    print("📋 Configuration:")
    print(f"   VPS: {VPS_USER}@{VPS_HOST}")
    print(f"   Path: {VPS_PATH}")
    print(f"   Files: {len(FILES_TO_DEPLOY)}")
    print()
    
    # Check if sshpass is available
    if not check_sshpass():
        print("⚠️  sshpass not found!")
        print()
        print("Please install sshpass first:")
        print("  - Ubuntu/Debian: sudo apt-get install sshpass")
        print("  - macOS: brew install hudochenkov/sshpass/sshpass")
        print("  - Windows: Use WSL or manual deployment")
        print()
        print("Or run manual deployment commands from DEPLOY_PHASE1_NOW.md")
        sys.exit(1)
    
    # Confirm deployment
    print("⚠️  This will deploy Phase 1 to production VPS!")
    response = input("Continue? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ Deployment cancelled")
        sys.exit(0)
    
    print()
    print_header("STEP 1: CREATE BACKUP")
    
    backup_cmd = f"""sshpass -p '{VPS_PASSWORD}' ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_HOST} '
        mkdir -p {VPS_PATH}/backups/phase1_$(date +%Y%m%d_%H%M%S) &&
        cd {VPS_PATH}/Bismillah/app &&
        cp supabase_repo.py handlers_autotrade.py {VPS_PATH}/backups/phase1_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
    '"""
    
    if not run_command(backup_cmd, "Creating backup"):
        print("⚠️  Backup failed, but continuing...")
    
    print()
    print_header("STEP 2: UPLOAD FILES")
    
    all_success = True
    for i, file_path in enumerate(FILES_TO_DEPLOY, 1):
        print(f"\n[{i}/{len(FILES_TO_DEPLOY)}] Uploading {file_path}...")
        
        scp_cmd = f"sshpass -p '{VPS_PASSWORD}' scp -o StrictHostKeyChecking=no {file_path} {VPS_USER}@{VPS_HOST}:{VPS_PATH}/{file_path}"
        
        if run_command(scp_cmd, f"Upload {file_path}"):
            print(f"   ✅ {file_path} uploaded successfully")
        else:
            print(f"   ❌ {file_path} upload failed!")
            all_success = False
    
    if not all_success:
        print("\n❌ Some files failed to upload!")
        response = input("Continue with restart? (yes/no): ").strip().lower()
        if response != "yes":
            print("❌ Deployment aborted")
            sys.exit(1)
    
    print()
    print_header("STEP 3: RESTART SERVICE")
    
    restart_cmd = f"sshpass -p '{VPS_PASSWORD}' ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_HOST} 'systemctl restart cryptomentor.service'"
    
    if run_command(restart_cmd, "Restarting service"):
        print("✅ Service restarted successfully")
    else:
        print("❌ Service restart failed!")
        print("\nManual restart command:")
        print(f"   ssh {VPS_USER}@{VPS_HOST} 'systemctl restart cryptomentor.service'")
        sys.exit(1)
    
    # Wait for service to start
    print("\n⏳ Waiting for service to start...")
    time.sleep(3)
    
    print()
    print_header("STEP 4: VERIFY DEPLOYMENT")
    
    status_cmd = f"sshpass -p '{VPS_PASSWORD}' ssh -o StrictHostKeyChecking=no {VPS_USER}@{VPS_HOST} 'systemctl status cryptomentor.service --no-pager -l'"
    
    if run_command(status_cmd, "Checking service status"):
        print("✅ Service is running")
    else:
        print("⚠️  Service status check failed")
        print("\nManual check command:")
        print(f"   ssh {VPS_USER}@{VPS_HOST} 'systemctl status cryptomentor.service'")
    
    print()
    print_header("DEPLOYMENT COMPLETE!")
    
    print("✅ Phase 1 deployed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Test in Telegram bot:")
    print("   - Open bot")
    print("   - Send /autotrade")
    print("   - Click Settings")
    print("   - Verify 'Risk Management' button appears")
    print()
    print("2. Check logs if needed:")
    print(f"   ssh {VPS_USER}@{VPS_HOST} 'journalctl -u cryptomentor.service -n 50'")
    print()
    print("3. Monitor for 1-2 hours")
    print()
    print("🎉 Deployment successful!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Deployment failed: {e}")
        sys.exit(1)
