"""Quick test Bitunix API connection - correct signature method"""
import hashlib
import time
import uuid
import requests

API_KEY = "cd73adcaccdd9f1594e2321e9d5ccaee"
API_SECRET = "2aa2d530fbe3096a78d440f93f76f9da"
BASE_URL = "https://fapi.bitunix.com"

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def make_sign(nonce: str, timestamp: str, query_params: str = "", body: str = "") -> str:
    digest = sha256_hex(nonce + timestamp + API_KEY + query_params + body)
    return sha256_hex(digest + API_SECRET)

def get_headers(query_params: str = "", body: str = "") -> dict:
    nonce = uuid.uuid4().hex
    timestamp = str(int(time.time() * 1000))
    sign = make_sign(nonce, timestamp, query_params, body)
    return {
        "api-key": API_KEY,
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": sign,
        "Content-Type": "application/json",
    }

# 1. Public endpoint
print("=== 1. Public: Market Tickers ===")
r = requests.get(f"{BASE_URL}/api/v1/futures/market/tickers?symbols=BTCUSDT", timeout=10)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:300]}\n")

# 2. Private: Get account
print("=== 2. Private: Get Account (USDT) ===")
query_params = "marginCoinUSDT"  # key+value concat, sorted by key
headers = get_headers(query_params=query_params)
r = requests.get(
    f"{BASE_URL}/api/v1/futures/account",
    params={"marginCoin": "USDT"},
    headers=headers,
    timeout=10
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}\n")

# 3. Private: Get open positions
print("=== 3. Private: Get Positions ===")
headers = get_headers(query_params="")
r = requests.get(
    f"{BASE_URL}/api/v1/futures/position/get_pending_positions",
    headers=headers,
    timeout=10
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")
