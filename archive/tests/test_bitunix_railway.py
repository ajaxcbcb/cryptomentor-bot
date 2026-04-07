"""
Test dari Railway - jalankan ini di Railway console/logs
untuk lihat exact error yang terjadi
"""
import requests, hashlib, time, uuid, os

API_KEY = os.getenv("BITUNIX_API_KEY", "<REDACTED_API_KEY>")
API_SECRET = os.getenv("BITUNIX_API_SECRET", "<REDACTED_API_SECRET>")
BASE_URL = "https://fapi.bitunix.com"

def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# Cek IP server ini
try:
    ip = requests.get("https://api.ipify.org?format=json", timeout=5).json().get("ip")
    print(f"Server IP: {ip}")
except Exception as e:
    print(f"Gagal cek IP: {e}")

# Test public
print("\n=== Public endpoint ===")
r = requests.get(f"{BASE_URL}/api/v1/futures/market/tickers",
                 params={"symbols": "BTCUSDT"}, timeout=10)
print(f"HTTP: {r.status_code} | code: {r.json().get('code')}")

# Test private
print("\n=== Private endpoint ===")
nonce = uuid.uuid4().hex
timestamp = str(int(time.time() * 1000))
qp = "marginCoinUSDT"
digest = sha256_hex(nonce + timestamp + API_KEY + qp)
sign = sha256_hex(digest + API_SECRET)
headers = {
    "api-key": API_KEY, "nonce": nonce,
    "timestamp": timestamp, "sign": sign,
    "Content-Type": "application/json"
}
r = requests.get(f"{BASE_URL}/api/v1/futures/account",
                 params={"marginCoin": "USDT"}, headers=headers, timeout=10)
print(f"HTTP: {r.status_code}")
print(f"Body: {r.text[:400]}")
