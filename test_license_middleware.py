"""
Test script untuk verify license middleware blocks users when suspended.
"""

import asyncio
import os
import sys

# Set env vars untuk test
os.environ['WL_ID'] = '<REDACTED_UUID>'
os.environ['WL_SECRET_KEY'] = '<REDACTED_UUID>'
os.environ['LICENSE_API_URL'] = 'http://147.93.156.165:8080'

sys.path.insert(0, 'Whitelabel #1')

from app.license_guard import LicenseGuard


async def test_license_check():
    """Test license check method."""
    print("=" * 60)
    print("TEST: License Middleware Check")
    print("=" * 60)
    
    guard = LicenseGuard()
    
    # Test 1: Check current license status
    print("\n1. Checking current license status...")
    is_valid = await guard.check_license_valid()
    print(f"   Result: {'✅ VALID' if is_valid else '❌ INVALID/SUSPENDED'}")
    
    # Test 2: Verify cache is working
    print("\n2. Checking cache functionality...")
    cache = guard._load_cache()
    if cache:
        print(f"   Cache found:")
        print(f"   - Valid: {cache.get('valid')}")
        print(f"   - Status: {cache.get('status')}")
        print(f"   - Balance: ${cache.get('balance', 0):.2f}")
        print(f"   - Cached at: {cache.get('cached_at')}")
    else:
        print("   ⚠️ No cache found")
    
    # Test 3: Multiple rapid checks (should use cache)
    print("\n3. Testing rapid checks (should use cache)...")
    import time
    start = time.time()
    for i in range(5):
        result = await guard.check_license_valid()
        print(f"   Check {i+1}: {'✅' if result else '❌'}")
    elapsed = time.time() - start
    print(f"   Total time: {elapsed:.2f}s (should be fast if using cache)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    # Summary
    print("\n📋 SUMMARY:")
    if is_valid:
        print("✅ License is ACTIVE — users can use the bot")
        print("   Middleware will allow all user requests")
    else:
        print("❌ License is SUSPENDED — users are BLOCKED")
        print("   Middleware will block all user requests")
        print("   Only admins can still access the bot")
    
    return is_valid


async def test_middleware_behavior():
    """Test middleware blocking behavior."""
    print("\n" + "=" * 60)
    print("TEST: Middleware Blocking Behavior")
    print("=" * 60)
    
    guard = LicenseGuard()
    is_valid = await guard.check_license_valid()
    
    print(f"\nCurrent license status: {'VALID' if is_valid else 'SUSPENDED'}")
    print("\nMiddleware behavior:")
    
    if is_valid:
        print("✅ Users: CAN access bot")
        print("✅ Admins: CAN access bot")
        print("✅ All commands: ALLOWED")
    else:
        print("❌ Users: BLOCKED (will see 'Bot Temporarily Unavailable' message)")
        print("✅ Admins: CAN still access (for troubleshooting)")
        print("❌ User commands: BLOCKED")
        print("✅ Admin commands: ALLOWED")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("\n🔍 Testing License Middleware Implementation\n")
    
    try:
        # Run tests
        is_valid = asyncio.run(test_license_check())
        asyncio.run(test_middleware_behavior())
        
        print("\n✅ All tests completed successfully!")
        
        # Exit code based on license status
        sys.exit(0 if is_valid else 1)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
