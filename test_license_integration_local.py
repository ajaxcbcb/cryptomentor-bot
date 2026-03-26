#!/usr/bin/env python3
"""
Test License System Integration - Local
Tests full flow: License API -> Bot License Check
"""
import asyncio
import subprocess
import time
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Whitelabel #1'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'license_server'))

from dotenv import load_dotenv

print("=" * 70)
print("LICENSE SYSTEM INTEGRATION TEST - LOCAL")
print("=" * 70)
print()

# Step 1: Start License API
print("Step 1: Starting License API on port 8080...")
print("-" * 70)

license_api_process = subprocess.Popen(
    [sys.executable, "license_api.py"],
    cwd="license_server",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# Wait for API to start
print("Waiting 3 seconds for License API to start...")
time.sleep(3)

# Check if process is still running
if license_api_process.poll() is not None:
    print("❌ License API failed to start!")
    print("Output:")
    print(license_api_process.stdout.read())
    sys.exit(1)

print("✅ License API started")
print()

# Step 2: Test License API endpoint
print("Step 2: Testing License API endpoint...")
print("-" * 70)

import httpx

async def test_api():
    load_dotenv("Whitelabel #1/.env")
    
    wl_id = os.getenv("WL_ID")
    secret_key = os.getenv("WL_SECRET_KEY")
    api_url = os.getenv("LICENSE_API_URL")
    
    print(f"WL_ID: {wl_id}")
    print(f"SECRET_KEY: {secret_key}")
    print(f"API_URL: {api_url}")
    print()
    
    url = f"{api_url}/api/license/check"
    payload = {"wl_id": wl_id, "secret_key": secret_key}
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            print(f"Status Code: {resp.status_code}")
            print(f"Response: {resp.json()}")
            print()
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    print("✅ License API check PASSED")
                    return True
                else:
                    print(f"❌ License not valid: {data.get('status')}")
                    return False
            else:
                print(f"❌ API returned error: {resp.status_code}")
                return False
    except Exception as exc:
        print(f"❌ API request failed: {exc}")
        return False

api_ok = asyncio.run(test_api())
print()

if not api_ok:
    print("❌ License API test failed - stopping")
    license_api_process.terminate()
    sys.exit(1)

# Step 3: Test Bot License Guard
print("Step 3: Testing Bot License Guard...")
print("-" * 70)

from app.license_guard import LicenseGuard

async def test_bot():
    guard = LicenseGuard()
    
    print("Testing startup_check()...")
    result = await guard.startup_check()
    
    print(f"Result: {result}")
    print()
    
    if result:
        print("✅ Bot license check PASSED - bot can start")
        return True
    else:
        print("❌ Bot license check FAILED - bot will halt")
        return False

bot_ok = asyncio.run(test_bot())
print()

# Cleanup
print("Cleaning up...")
license_api_process.terminate()
license_api_process.wait()

# Final result
print("=" * 70)
if api_ok and bot_ok:
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print()
    print("License system is working correctly!")
    print("You can now deploy to VPS with confidence.")
    sys.exit(0)
else:
    print("❌ TESTS FAILED")
    print("=" * 70)
    sys.exit(1)
