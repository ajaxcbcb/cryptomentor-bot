"""Test Bitunix Partners API endpoints."""
import os, sys, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Bismillah"))
from dotenv import load_dotenv
load_dotenv("/root/cryptomentor-bot/.env", override=True)

api_key = os.getenv("BITUNIX_PARTNERS_API_KEY", "")
api_secret = os.getenv("BITUNIX_PARTNERS_API_SECRET", "")
base_url = os.getenv("BITUNIX_PARTNERS_BASE_URL", "https://api.bitunix.com")

print(f"Partners API Key: ...{api_key[-8:] if api_key else 'NOT SET'}")
print(f"Partners Base URL: {base_url}")
print()

# Test beberapa endpoint yang mungkin ada untuk cek referral user
endpoints = [
    "/api/v1/partner/referral/users",
    "/api/v1/affiliate/users",
    "/api/v1/partner/users",
    "/api/v1/broker/users",
    "/api/v1/partner/info",
    "/api/v1/affiliate/info",
]

for ep in endpoints:
    try:
        r = requests.get(f"{base_url}{ep}", timeout=5,
                         headers={"api-key": api_key})
        print(f"{ep}: HTTP {r.status_code} | {r.text[:100]}")
    except Exception as e:
        print(f"{ep}: ERROR {e}")
