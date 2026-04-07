"""
Test berbagai cara akses Bitunix dari Railway
"""
import requests
import hashlib, time, uuid

API_KEY = "<REDACTED_API_KEY>"
API_SECRET = "<REDACTED_API_SECRET>"
BASE = "https://fapi.bitunix.com"

def sha256(s): return hashlib.sha256(s.encode()).hexdigest()
def make_sign(nonce, ts, qp=""):
    digest = sha256(nonce + ts + API_KEY + qp)
    return sha256(digest + API_SECRET)

def test_private(label, base_url, extra_headers=None, proxies=None):
    nonce = uuid.uuid4().hex
    ts = str(int(time.time() * 1000))
    qp = "marginCoinUSDT"
    sign = make_sign(nonce, ts, qp)
    headers = {
        "api-key": API_KEY, "nonce": nonce,
        "timestamp": ts, "sign": sign,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    if extra_headers:
        headers.update(extra_headers)
    try:
        kwargs = dict(params={"marginCoin": "USDT"}, headers=headers, timeout=10)
        if proxies:
            kwargs["proxies"] = proxies
        r = requests.get(f"{base_url}/api/v1/futures/account", **kwargs)
        body = r.text[:150]
        print(f"[{label}] HTTP {r.status_code} | {body}")
        return r.status_code == 200
    except Exception as e:
        print(f"[{label}] ERROR: {e}")
        return False

print("=== Test koneksi ke Bitunix ===\n")

# Test 1: Direct
test_private("Direct", BASE)

# Test 2: Via worker (kemungkinan 403)
test_private("Worker", "https://bitunix-proxy.cryptomentor139.workers.dev")

# Test 3: Proxy yang ada
PROXY = "http://<REDACTED_PROXY_USER>:<REDACTED_PROXY_PASSWORD>@31.59.20.176:6754"
test_private("Proxy", BASE, proxies={"http": PROXY, "https": PROXY})

# Test 4: curl_cffi direct
try:
    from curl_cffi import requests as cffi
    nonce = uuid.uuid4().hex
    ts = str(int(time.time() * 1000))
    qp = "marginCoinUSDT"
    sign = make_sign(nonce, ts, qp)
    headers = {"api-key": API_KEY, "nonce": nonce, "timestamp": ts, "sign": sign, "Content-Type": "application/json"}
    r = cffi.get(f"{BASE}/api/v1/futures/account", params={"marginCoin": "USDT"}, headers=headers, impersonate="chrome120", timeout=10)
    print(f"[curl_cffi direct] HTTP {r.status_code} | {r.text[:150]}")
except Exception as e:
    print(f"[curl_cffi direct] ERROR: {e}")

# Test 5: curl_cffi via proxy
try:
    from curl_cffi import requests as cffi
    nonce = uuid.uuid4().hex
    ts = str(int(time.time() * 1000))
    qp = "marginCoinUSDT"
    sign = make_sign(nonce, ts, qp)
    headers = {"api-key": API_KEY, "nonce": nonce, "timestamp": ts, "sign": sign, "Content-Type": "application/json"}
    r = cffi.get(f"{BASE}/api/v1/futures/account", params={"marginCoin": "USDT"}, headers=headers,
                 impersonate="chrome120", timeout=10,
                 proxies={"http": PROXY, "https": PROXY})
    print(f"[curl_cffi+proxy] HTTP {r.status_code} | {r.text[:150]}")
except Exception as e:
    print(f"[curl_cffi+proxy] ERROR: {e}")
