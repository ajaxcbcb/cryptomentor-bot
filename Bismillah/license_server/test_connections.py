"""Test semua koneksi license_server"""
import os, sys, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

import requests

# ── 1. HD Wallet ──────────────────────────────────────────────────
print("=== HD Wallet ===")
try:
    from license_server.wallet_manager import HDWalletManager
    mnemonic = os.environ["MASTER_SEED_MNEMONIC"]
    wm = HDWalletManager(mnemonic)
    addr0 = wm.derive_address(0)
    addr1 = wm.derive_address(1)
    print(f"✅ HD Wallet OK")
    print(f"   Index 0: {addr0}")
    print(f"   Index 1: {addr1}")
except Exception as e:
    print(f"❌ HD Wallet failed: {e}")

print()

# ── 2. Supabase ───────────────────────────────────────────────────
print("=== Supabase (Pusat) ===")
try:
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)
    res = client.table("wl_licenses").select("count", count="exact").execute()
    print(f"✅ Supabase connected! wl_licenses count: {res.count}")
except Exception as e:
    print(f"❌ Supabase failed: {e}")

print()

# ── 3. Moralis API ────────────────────────────────────────────────
print("=== Moralis API (BSC) ===")
try:
    api_key = os.environ.get("MORALIS_API_KEY") or os.environ.get("BSCSCAN_API_KEY", "")
    r = requests.get(
        "https://deep-index.moralis.io/api/v2.2/web3/version",
        headers={"X-API-Key": api_key, "accept": "application/json"},
        timeout=10
    )
    if r.status_code == 200:
        print(f"✅ Moralis API OK — {r.json()}")
    else:
        print(f"❌ Moralis error: {r.status_code} {r.text[:200]}")
except Exception as e:
    print(f"❌ Moralis failed: {e}")

print()

# ── 4. Telegram Bot Token ─────────────────────────────────────────
print("=== Telegram Bot ===")
try:
    bot_token = os.environ["BOT_TOKEN"]
    r = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
    data = r.json()
    if data.get("ok"):
        bot = data["result"]
        print(f"✅ Bot OK — @{bot['username']} ({bot['first_name']})")
    else:
        print(f"❌ Bot error: {data.get('description')}")
except Exception as e:
    print(f"❌ Telegram failed: {e}")
