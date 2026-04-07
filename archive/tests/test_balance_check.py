"""
Test: cek apakah get_account_info bisa ambil balance dari Bitunix.
Jalankan di VPS: python3 test_balance_check.py
"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Bismillah"))
from dotenv import load_dotenv
load_dotenv("/root/cryptomentor-bot/.env", override=True)

from app.supabase_repo import _client
from app.lib.crypto import decrypt

async def main():
    s = _client()

    # Ambil semua user yang punya API key
    res = s.table("user_api_keys").select("telegram_id, exchange, api_key, api_secret_enc, key_hint").limit(3).execute()
    rows = res.data or []

    if not rows:
        print("❌ Tidak ada API key di database")
        return

    for row in rows:
        uid = row["telegram_id"]
        exchange = row.get("exchange", "bitunix")
        key_hint = row.get("key_hint", "????")
        print(f"\n{'='*50}")
        print(f"User: {uid} | Exchange: {exchange} | Key: ...{key_hint}")

        try:
            api_secret = decrypt(row["api_secret_enc"])
            api_key = row["api_key"]
        except Exception as e:
            print(f"❌ Decrypt error: {e}")
            continue

        # Test get_account_info
        try:
            from app.exchange_registry import get_client
            client = get_client(exchange, api_key, api_secret)

            print("⏳ Calling get_account_info...")
            import time
            t0 = time.time()
            result = await asyncio.wait_for(
                asyncio.to_thread(client.get_account_info),
                timeout=10.0
            )
            elapsed = time.time() - t0
            print(f"⏱ Response time: {elapsed:.2f}s")

            if result.get("success"):
                print(f"✅ Balance OK!")
                print(f"   Available: {result.get('available', 0):.2f} USDT")
                print(f"   Unrealized PnL: {result.get('total_unrealized_pnl', 0):+.2f} USDT")
            else:
                print(f"❌ API Error: {result.get('error', 'unknown')}")

        except asyncio.TimeoutError:
            print(f"❌ TIMEOUT setelah 10 detik — API tidak merespons")
        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\nSelesai.")

if __name__ == "__main__":
    asyncio.run(main())
