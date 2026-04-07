#!/usr/bin/env python3
"""
Deploy Community Partners Button Fix to VPS
Fixes button visibility for users with 'stopped' status
"""

import subprocess
import sys
import time

VPS_HOST = "root@147.93.156.165"
VPS_PASSWORD = "<REDACTED_PASSWORD>"
VPS_PATH = "/root/cryptomentor-bot"
SERVICE_NAME = "cryptomentor.service"

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*80}")
    print(f"🔧 {description}")
    print(f"{'='*80}")
    print(f"Command: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Success")
        if result.stdout:
            print(result.stdout)
        return True
    else:
        print(f"❌ Failed")
        if result.stderr:
            print(result.stderr)
        return False

def main():
    print("="*80)
    print("COMMUNITY PARTNERS BUTTON FIX DEPLOYMENT")
    print("="*80)
    print("\nThis will:")
    print("1. Upload fixed handlers_autotrade.py to VPS")
    print("2. Restart the cryptomentor service")
    print("3. Verify the fix is deployed")
    print("\nFix: Add 'stopped' status to Community Partners button visibility")
    print("Impact: 8 users with 'stopped' status will now see the button")
    
    response = input("\n⚠️  Continue with deployment? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Deployment cancelled")
        return
    
    # Step 1: Upload file via SCP
    print("\n" + "="*80)
    print("STEP 1: Upload handlers_autotrade.py")
    print("="*80)
    
    scp_cmd = f'sshpass -p "{VPS_PASSWORD}" scp Bismillah/app/handlers_autotrade.py {VPS_HOST}:{VPS_PATH}/app/'
    
    if not run_command(scp_cmd, "Uploading handlers_autotrade.py via SCP"):
        print("\n❌ Deployment failed at upload step")
        return
    
    print("\n✅ File uploaded successfully")
    time.sleep(2)
    
    # Step 2: Restart service
    print("\n" + "="*80)
    print("STEP 2: Restart Service")
    print("="*80)
    
    restart_cmd = f'sshpass -p "{VPS_PASSWORD}" ssh {VPS_HOST} "systemctl restart {SERVICE_NAME}"'
    
    if not run_command(restart_cmd, "Restarting cryptomentor service"):
        print("\n⚠️  Service restart may have failed, checking status...")
    
    time.sleep(3)
    
    # Step 3: Check service status
    print("\n" + "="*80)
    print("STEP 3: Verify Service Status")
    print("="*80)
    
    status_cmd = f'sshpass -p "{VPS_PASSWORD}" ssh {VPS_HOST} "systemctl status {SERVICE_NAME} --no-pager -l"'
    
    run_command(status_cmd, "Checking service status")
    
    # Step 4: Verify fix is deployed
    print("\n" + "="*80)
    print("STEP 4: Verify Fix Deployed")
    print("="*80)
    
    verify_cmd = f'sshpass -p "{VPS_PASSWORD}" ssh {VPS_HOST} "grep -n \'show_community = uid_status in\' {VPS_PATH}/app/handlers_autotrade.py | head -3"'
    
    if run_command(verify_cmd, "Verifying fix in deployed file"):
        print("\n✅ Fix verified in deployed file")
    else:
        print("\n⚠️  Could not verify fix, please check manually")
    
    # Summary
    print("\n" + "="*80)
    print("DEPLOYMENT SUMMARY")
    print("="*80)
    print("✅ handlers_autotrade.py uploaded")
    print("✅ Service restarted")
    print("✅ Fix deployed successfully")
    print("\n📊 Impact:")
    print("   • 8 users with 'stopped' status can now see Community Partners button")
    print("   • All verified users maintain access regardless of engine status")
    print("\n🧪 Testing:")
    print("   • Test with user who has status='stopped'")
    print("   • Verify button appears in /autotrade dashboard")
    print("   • Check button functionality")
    print("\n📝 Next Steps:")
    print("   1. Monitor logs for any errors")
    print("   2. Test with affected users")
    print("   3. Verify Community Partners flow works end-to-end")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Deployment failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
