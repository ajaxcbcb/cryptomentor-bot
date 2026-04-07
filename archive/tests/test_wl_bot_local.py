"""
Test script untuk whitelabel bot dengan license check lokal.
Pastikan license_api.py sudah berjalan di port 8080.
"""
import asyncio
import sys
import os

# Add Whitelabel #1 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Whitelabel #1'))

from dotenv import load_dotenv
load_dotenv('Whitelabel #1/.env')

from app.license_guard import LicenseGuard


async def main():
    print("Testing Whitelabel Bot License Check")
    print("=" * 60)
    print(f"WL_ID: {os.getenv('WL_ID')}")
    print(f"LICENSE_API_URL: {os.getenv('LICENSE_API_URL')}")
    print()
    
    guard = LicenseGuard()
    
    print("Running startup_check()...")
    try:
        result = await guard.startup_check()
        
        print()
        print("=" * 60)
        if result:
            print("✅ Bot boleh jalan (startup_check returned True)")
            print("   License valid atau menggunakan cache fallback")
        else:
            print("❌ Bot harus halt (startup_check returned False)")
            print("   License invalid dan tidak ada cache valid")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
