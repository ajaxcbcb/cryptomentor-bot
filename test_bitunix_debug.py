"""Test API key baru Bitunix"""
import requests, hashlib, time, uuid

API_KEY = "6dfc3a3259add5d059babb1e1203bd1b"
API_SECRET = "13c3e178f5a013281cf4b92dfa20f341"
BASE_URL = "https://fapi.bitunix.com"

def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

nonce = uuid.uuid4().hex
timestamp = str(int(time.time() * 1000))
qp = "marginCoinUSDT"
digest = sha256_hex(nonce + timestamp + API_KEY + qp)
sign = sha256_hex(digest + API_SECRET)

headers = {"api-key": API_KEY, "nonce": nonce, "timestamp": timestamp, "sign": sign, "Content-Type": "application/json"}

print("=== Test Account ===")
r = requests.get(f"{BASE_URL}/api/v1/futures/account", params={"marginCoin": "USDT"}, headers=headers, timeout=10)
print(f"HTTP: {r.status_code}")
print(f"Body: {r.text[:300]}")
