#!/usr/bin/env python3
"""Verify migration endpoints are working on VPS"""
import requests
import json

API_BASE = "https://api.cryptomentor.id"
# Or local if API is not public yet
LOCAL_API = "http://147.93.156.165:8000"

endpoints_to_check = [
    ("GET", "/user/verification-status", "Check verification status"),
    ("POST", "/user/submit-uid", "Submit UID for verification"),
    ("PUT", "/dashboard/settings/leverage", "Set leverage"),
    ("PUT", "/dashboard/settings/margin-mode", "Set margin mode"),
    ("GET", "/user/me", "Get user profile"),
]

print()
print("=" * 70)
print("🔍 MIGRATION ENDPOINTS - AVAILABILITY CHECK")
print("=" * 70)
print()

for method, endpoint, description in endpoints_to_check:
    print(f"📍 {method:6} {endpoint}")
    print(f"   Description: {description}")
    
    # Try to GET endpoint info (health check)
    url = f"{LOCAL_API}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=2)
        else:
            resp = requests.options(url, timeout=2)  # OPTIONS to check if route exists
            
        if resp.status_code in [200, 201, 204, 401, 403]:
            print(f"   ✅ Endpoint exists (status: {resp.status_code})")
        elif resp.status_code == 404:
            print(f"   ❌ Endpoint not found (404)")
        else:
            print(f"   ⚠️  Status: {resp.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    
    print()

print()
print("=" * 70)
print("📋 NOTES:")
print("=" * 70)
print()
print("✅ Endpoints show 401/403 = Good (authentication required, but route exists)")
print("❌ Endpoints show 404 = Bad (route not implemented)")
print()
print("Next: Test endpoints with actual JWT token and UID verification flow")
print()
