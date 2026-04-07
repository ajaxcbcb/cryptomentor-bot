"""
Test full flow verifikasi API Key Bitunix:
1. check_connection() via BitunixAutoTradeClient
2. encrypt/decrypt API secret (simulasi save_user_api_keys)
3. Timeout handling (asyncio.wait_for)
"""
import sys
import os
import asyncio

# Load .env dari folder Bismillah
from dotenv import load_dotenv
load_dotenv("Bismillah/.env")

# Tambah path agar bisa import dari Bismillah/app
sys.path.insert(0, "Bismillah")

API_KEY    = os.getenv("BITUNIX_API_KEY")
API_SECRET = os.getenv("BITUNIX_API_SECRET")
ENC_KEY    = os.getenv("ENCRYPTION_KEY")

print(f"ENCRYPTION_KEY set: {'✅' if ENC_KEY else '❌ MISSING'}")
print(f"BITUNIX_API_KEY   : {'✅ ' + API_KEY[-6:] if API_KEY else '❌ MISSING'}")
print(f"BITUNIX_API_SECRET: {'✅ ...'+API_SECRET[-4:] if API_SECRET else '❌ MISSING'}")
print()

# ── Test 1: Encrypt / Decrypt ──────────────────────────────────────
print("=== Test 1: AES-256-GCM Encrypt/Decrypt ===")
try:
    from app.lib.crypto import encrypt, decrypt
    enc = encrypt(API_SECRET)
    dec = decrypt(enc)
    assert dec == API_SECRET, "Decrypt mismatch!"
    print(f"✅ Encrypt OK  → {enc[:30]}...")
    print(f"✅ Decrypt OK  → ...{dec[-4:]}\n")
except Exception as e:
    print(f"❌ GAGAL: {e}\n")
    sys.exit(1)

# ── Test 2: check_connection() sync ───────────────────────────────
print("=== Test 2: BitunixAutoTradeClient.check_connection() ===")
try:
    from app.bitunix_autotrade_client import BitunixAutoTradeClient
    client = BitunixAutoTradeClient(api_key=API_KEY, api_secret=API_SECRET)
    result = client.check_connection()
    if result.get("online"):
        print(f"✅ Koneksi OK: {result.get('message')}\n")
    else:
        print(f"⚠️  Koneksi gagal: {result.get('error')}\n")
except Exception as e:
    print(f"❌ GAGAL: {e}\n")
    sys.exit(1)

# ── Test 3: asyncio.wait_for timeout wrapper (simulasi handler) ────
print("=== Test 3: Async timeout wrapper (simulasi handler) ===")

async def run_verify():
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(client.check_connection),
            timeout=15.0
        )
        return result
    except asyncio.TimeoutError:
        return {"online": False, "error": "Timeout 15 detik"}
    except Exception as e:
        return {"online": False, "error": str(e)}

result = asyncio.run(run_verify())
if result.get("online"):
    print(f"✅ Async verify OK: {result.get('message')}")
else:
    print(f"⚠️  Async verify gagal: {result.get('error')}")

# ── Test 4: Timeout simulation ─────────────────────────────────────
print("\n=== Test 4: Timeout simulation (0.001s) ===")

async def run_timeout_test():
    import time
    def slow_fn():
        time.sleep(2)
        return {"online": True}
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(slow_fn),
            timeout=0.001
        )
        return result
    except asyncio.TimeoutError:
        return {"online": False, "error": "Timeout: server tidak merespons dalam 0.001 detik"}

result = asyncio.run(run_timeout_test())
if not result.get("online") and "Timeout" in result.get("error", ""):
    print(f"✅ Timeout handler bekerja: {result['error']}")
else:
    print(f"❌ Timeout handler tidak bekerja")

print("\n✅ Semua test selesai.")
