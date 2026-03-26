"""Test proxy WebShare untuk akses Bitunix dari Railway"""
import requests, hashlib, time, uuid

PROXY_URL = "http://<REDACTED_PROXY_USER>:<REDACTED_PROXY_PASSWORD>@31.59.20.176:6754"
API_KEY = "<REDACTED_API_KEY>"
API_SECRET = "<REDACTED_API_SECRET>"
BASE_URL = "https://fapi.bitunix.com"
PROXIES = {"http": PROXY_URL, "https": PROXY_URL}

def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

print("=== Test 1: Cek IP via proxy ===")
try:
    r = requests.get("https://api.ipify.org?format=json", proxies=PROXIES, timeout=10)
    print(f"IP via proxy: {r.json().get('ip')}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== Test 2: Bitunix public endpoint via proxy ===")
try:
    r = requests.get(f"{BASE_URL}/api/v1/futures/market/tickers",
                     params={"symbols": "BTCUSDT"}, proxies=PROXIES, timeout=10)
    print(f"HTTP: {r.status_code} | code: {r.json().get('code')} | msg: {r.json().get('msg')}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n=== Test 3: Bitunix private endpoint via proxy ===")
try:
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
                     params={"marginCoin": "USDT"}, headers=headers,
                     proxies=PROXIES, timeout=10)
    print(f"HTTP: {r.status_code}")
    print(f"Body: {r.text[:300]}")
except Exception as e:
    print(f"ERROR: {e}")
