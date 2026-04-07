"""
Test script untuk license API lokal.
Jalankan license_api.py terlebih dahulu, lalu jalankan script ini.
"""

import asyncio
import httpx


async def test_license_check():
    """Test POST /api/license/check endpoint."""
    
    # Credentials baru dari registrasi
    wl_id = "<REDACTED_UUID>"
    secret_key = "<REDACTED_UUID>"
    
    url = "http://localhost:8080/api/license/check"
    payload = {
        "wl_id": wl_id,
        "secret_key": secret_key
    }
    
    print(f"Testing license check for WL_ID: {wl_id}")
    print(f"URL: {url}")
    print(f"Payload: {payload}\n")
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}\n")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ License check berhasil!")
                print(f"   Valid: {data.get('valid')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Expires in: {data.get('expires_in_days')} days")
                print(f"   Balance: ${data.get('balance'):.2f} USDT")
                print(f"   Warning: {data.get('warning')}")
            else:
                print(f"❌ License check gagal: {response.json()}")
                
    except httpx.ConnectError:
        print("❌ Tidak bisa connect ke license API!")
        print("   Pastikan license_api.py sudah berjalan di port 8080")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_license_check())
