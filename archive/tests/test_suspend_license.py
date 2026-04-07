#!/usr/bin/env python3
"""
Test script to suspend license and verify middleware blocking
"""
import asyncio
import sys
import os

# Add license_server to path
sys.path.insert(0, 'license_server')

from license_manager import LicenseManager


async def suspend_license():
    """Suspend license by setting balance to 0"""
    print("=" * 60)
    print("SUSPENDING LICENSE")
    print("=" * 60)
    
    manager = LicenseManager()
    client = await manager._get_client()
    
    # Set balance to 0 and status to suspended
    result = await client.table('wl_licenses').update({
        'balance_usdt': 0,
        'status': 'suspended'
    }).eq('wl_id', '<REDACTED_UUID>').execute()
    
    print("✅ License suspended")
    print("   - Balance: $0")
    print("   - Status: suspended")
    print("")
    
    # Verify
    license = await manager.get_license(wl_id='<REDACTED_UUID>')
    print("Verification:")
    print(f"   - Status: {license['status']}")
    print(f"   - Balance: ${license['balance_usdt']}")
    print("")
    print("=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Wait 60 seconds for middleware cache to refresh")
    print("2. Send /start to bot as regular user")
    print("3. Should see: '🚫 Bot Temporarily Unavailable'")
    print("4. Test as admin - should still work")
    print("")


if __name__ == "__main__":
    asyncio.run(suspend_license())
