#!/usr/bin/env python3
"""
Deploy License System to VPS - Final
"""
import subprocess
import time

VPS_HOST = "147.93.156.165"
VPS_USER = "root"
ADMIN_ID = "1234500009"

def ssh_exec(command):
    """Execute command on VPS via SSH"""
    full_cmd = f'ssh {VPS_USER}@{VPS_HOST} "{command}"'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr

print("=" * 70)
print("DEPLOYING LICENSE SYSTEM TO VPS")
print("=" * 70)
print()

# Step 1: Register + Activate WL on VPS
print("Step 1: Registering and activating WL on VPS...")
print("-" * 70)

register_script = f"""
cd /root/cryptomentor-bot/license_server
source venv/bin/activate
python << 'PYEOF'
import asyncio
from datetime import datetime, timezone, timedelta
from license_manager import LicenseManager

async def main():
    manager = LicenseManager()
    
    # Register
    result = await manager.register_wl(admin_telegram_id={ADMIN_ID}, monthly_fee=10.0)
    wl_id = result['wl_id']
    secret_key = result['secret_key']
    
    print(f'Registered WL_ID: {{wl_id}}')
    print(f'SECRET_KEY: {{secret_key}}')
    
    # Deposit
    await manager.credit_balance(
        wl_id=wl_id,
        amount=50.0,
        tx_hash='0xVPS_DEPLOY_TEST_123',
        block_number=12345678
    )
    print('Deposit: $50 credited')
    
    # Billing
    client = await manager._get_client()
    license_row = await manager.get_license(wl_id=wl_id)
    balance = float(license_row.get('balance_usdt', 0))
    monthly_fee = float(license_row.get('monthly_fee', 10))
    
    new_balance = balance - monthly_fee
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    await client.table('wl_licenses').update({{
        'balance_usdt': new_balance,
        'status': 'active',
        'expires_at': expires_at.isoformat()
    }}).eq('wl_id', wl_id).execute()
    
    print(f'Billing: Deducted ${{monthly_fee}}, Balance: ${{new_balance}}')
    print(f'Status: active, Expires: {{expires_at}}')
    print()
    print('CREDENTIALS:')
    print(f'{{wl_id}}|{{secret_key}}')

asyncio.run(main())
PYEOF
"""

output = ssh_exec(register_script)
print(output)

# Extract credentials from output
lines = output.strip().split('\\n')
creds_line = [l for l in lines if '|' in l and len(l) == 73]  # UUID|UUID format
if creds_line:
    wl_id, secret_key = creds_line[0].split('|')
    print(f"\\n✅ WL Registered and Activated")
    print(f"   WL_ID: {wl_id}")
    print(f"   SECRET_KEY: {secret_key}")
else:
    print("❌ Failed to extract credentials")
    exit(1)

print()

# Step 2: Update .env
print("Step 2: Updating whitelabel-1 .env...")
print("-" * 70)

update_env = f"""
cd /root/cryptomentor-bot/whitelabel-1
sed -i 's/^WL_ID=.*/WL_ID={wl_id}/' .env
sed -i 's/^WL_SECRET_KEY=<REDACTED_WL_SECRET_KEY> .env
sed -i 's|^LICENSE_API_URL=.*|LICENSE_API_URL=http://147.93.156.165:8080|' .env
echo "✅ .env updated"
cat .env | grep -E '(WL_ID|WL_SECRET_KEY|LICENSE_API_URL)'
"""

output = ssh_exec(update_env)
print(output)
print()

# Step 3: Restart bot
print("Step 3: Restarting whitelabel1 service...")
print("-" * 70)

ssh_exec("sudo systemctl restart whitelabel1")
time.sleep(5)

output = ssh_exec("sudo systemctl status whitelabel1 --no-pager -l | head -15")
print(output)
print()

# Step 4: Check logs
print("Step 4: Checking bot logs for license check...")
print("-" * 70)

output = ssh_exec("sudo journalctl -u whitelabel1 -n 20 --no-pager | grep -E '(License|Started|ERROR|valid)'")
print(output)

print()
print("=" * 70)
print("✅ DEPLOYMENT COMPLETED")
print("=" * 70)
print()
print("Credentials deployed:")
print(f"  WL_ID: {wl_id}")
print(f"  SECRET_KEY: {secret_key}")
print()
print("Next: Test bot in Telegram with /start command")
