"""Test semua proxy WebShare - cari yang tidak diblokir Bitunix"""
import requests, hashlib, time, uuid

API_KEY = "<REDACTED_API_KEY>"
API_SECRET = "<REDACTED_API_SECRET>"
BASE_URL = "https://fapi.bitunix.com"

# Ganti list ini dengan semua proxy dari WebShare dashboard kamu
# Format: (ip, port, username, password)
PROXIES = [
    ("31.59.20.176", "6754", "<REDACTED_PROXY_USER>", "<REDACTED_PROXY_PASSWORD>"),
    # tambahkan proxy lain dari list WebShare di sini
]

def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def test_proxy(ip, port, user, pwd):
    proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        # Test Bitunix private endpoint
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
        r = requests.get(
            f"{BASE_URL}/api/v1/futures/account",
            params={"marginCoin": "USDT"},
            headers=headers, proxies=proxies, timeout=10
        )
        if r.status_code == 200 and r.json().get("code") == 0:
            return f"✅ BERHASIL - {proxy_url}"
        else:
            return f"❌ GAGAL ({r.status_code}) - {ip}:{port}"
    except Exception as e:
        return f"❌ ERROR - {ip}:{port} - {e}"

print("Testing semua proxy...\n")
for ip, port, user, pwd in PROXIES:
    result = test_proxy(ip, port, user, pwd)
    print(result)
