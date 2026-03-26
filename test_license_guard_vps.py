#!/usr/bin/env python3
"""
Test license_guard.py di VPS untuk debug masalah
"""
import asyncio
import sys
import os

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.license_guard import LicenseGuard

async def main():
    print("=" * 60)
    print("Testing LicenseGuard on VPS")
    print("=" * 60)
    print()
    
    # Check env vars
    print("Environment variables:")
    print(f"  WL_ID: {os.getenv('WL_ID')}")
    print(f"  WL_SECRET_KEY: <REDACTED_WL_SECRET_KEY>
    print(f"  LICENSE_API_URL: {os.getenv('LICENSE_API_URL')}")
    print()
    
    # Create license guard
    guard = LicenseGuard()
    
    # Test API call directly
    print("Testing _call_api()...")
    response = await guard._call_api()
    print(f"Response: {response}")
    print(f"Response type: {type(response)}")
    print()
    
    # Test startup_check
    print("Testing startup_check()...")
    result = await guard.startup_check()
    print(f"Result: {result}")
    print()
    
    if result:
        print("✅ License check PASSED - bot can start")
    else:
        print("❌ License check FAILED - bot will halt")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
