#!/usr/bin/env python3
"""
Run database migration on VPS via SSH
"""
import subprocess
import sys

VPS_HOST = "root@147.93.156.165"
VPS_PATH = "/root/cryptomentor-bot"

# Database connection from .env
DB_CONNECTION = "postgresql://neondb_owner:npg_PXo7pTdgJ4ny@ep-divine-wind-aes4g3k8.c-2.us-east-2.aws.neon.tech:5432/neondb?sslmode=require"

print("🚀 Running Scalping Mode Migration on VPS...")
print("=" * 50)

# Step 1: Run migration via SSH
print("\n📊 Step 1: Running database migration...")
migration_cmd = f"""
cd {VPS_PATH} && \
PGPASSWORD=<REDACTED_PASSWORD> psql -h ep-divine-wind-aes4g3k8.c-2.us-east-2.aws.neon.tech -U neondb_owner -d neondb -p 5432 < db/add_trading_mode.sql
"""

try:
    result = subprocess.run(
        ["ssh", VPS_HOST, migration_cmd],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✅ Migration successful!")
        print(result.stdout)
    else:
        print("❌ Migration failed!")
        print(result.stderr)
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("⏱️ Migration timeout - checking if it completed...")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Step 2: Verify migration
print("\n🔍 Step 2: Verifying migration...")
verify_cmd = f"""
PGPASSWORD=<REDACTED_PASSWORD> psql -h ep-divine-wind-aes4g3k8.c-2.us-east-2.aws.neon.tech -U neondb_owner -d neondb -p 5432 -c "SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name='autotrade_sessions' AND column_name='trading_mode';"
"""

try:
    result = subprocess.run(
        ["ssh", VPS_HOST, verify_cmd],
        capture_output=True,
        text=True,
        timeout=15
    )
    
    if "trading_mode" in result.stdout:
        print("✅ Column 'trading_mode' exists!")
        print(result.stdout)
    else:
        print("⚠️ Column verification unclear:")
        print(result.stdout)
        
except Exception as e:
    print(f"⚠️ Verification error: {e}")

# Step 3: Restart service
print("\n🔄 Step 3: Restarting service...")
restart_cmd = "systemctl restart cryptomentor.service && sleep 3 && systemctl status cryptomentor.service --no-pager"

try:
    result = subprocess.run(
        ["ssh", VPS_HOST, restart_cmd],
        capture_output=True,
        text=True,
        timeout=15
    )
    
    if "active (running)" in result.stdout:
        print("✅ Service restarted successfully!")
    else:
        print("⚠️ Service status:")
        print(result.stdout)
        
except Exception as e:
    print(f"⚠️ Restart error: {e}")

# Step 4: Check logs
print("\n📋 Step 4: Checking logs...")
logs_cmd = "journalctl -u cryptomentor.service -n 30 --no-pager"

try:
    result = subprocess.run(
        ["ssh", VPS_HOST, logs_cmd],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print("Last 30 lines of logs:")
    print(result.stdout[-2000:])  # Last 2000 chars
    
    # Check for errors
    if "error" in result.stdout.lower() or "traceback" in result.stdout.lower():
        print("\n⚠️ Possible errors detected in logs!")
    else:
        print("\n✅ No obvious errors in logs")
        
except Exception as e:
    print(f"⚠️ Logs error: {e}")

print("\n" + "=" * 50)
print("✅ Deployment Complete!")
print("\n📊 Next Steps:")
print("1. Test /autotrade command in Telegram")
print("2. Click '⚙️ Trading Mode' button")
print("3. Try switching between modes")
print("4. Monitor logs: ssh root@147.93.156.165 'journalctl -u cryptomentor.service -f'")
