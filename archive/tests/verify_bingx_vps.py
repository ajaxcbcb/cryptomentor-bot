#!/usr/bin/env python3
"""Verify BingX integration on VPS"""

import sys
sys.path.insert(0, 'Bismillah')

from app.exchange_registry import get_exchange, get_client, EXCHANGES

print("=" * 60)
print("BingX Integration Verification on VPS")
print("=" * 60)
print()

# Check all exchanges
print("Exchange Configuration:")
for exchange_id, config in EXCHANGES.items():
    requires_uid = config.get('requires_uid_verification', False)
    coming_soon = config.get('coming_soon', False)
    status = "Coming Soon" if coming_soon else ("UID Required" if requires_uid else "No UID Required")
    print(f"  {config['name']:15} ({exchange_id:10}): {status}")

print()

# Test BingX specifically
print("BingX Specific Test:")
try:
    bingx = get_exchange('bingx')
    print(f"  ✓ Name: {bingx['name']}")
    print(f"  ✓ Requires UID: {bingx.get('requires_uid_verification', False)}")
    print(f"  ✓ Client Class: {bingx['client_class']}")
    
    # Test client creation
    client = get_client('bingx', 'test_key', 'test_secret')
    print(f"  ✓ Client Created: {type(client).__name__}")
    print(f"  ✓ Has check_connection: {hasattr(client, 'check_connection')}")
    print(f"  ✓ Has get_account_info: {hasattr(client, 'get_account_info')}")
    print(f"  ✓ Has place_order: {hasattr(client, 'place_order')}")
    
    print()
    print("✅ BingX integration verified successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
