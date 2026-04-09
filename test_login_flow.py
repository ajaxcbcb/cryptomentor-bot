#!/usr/bin/env python3
"""
Test login flow: cek user di DB, lalu simulate /auth/telegram endpoint
"""
import os, sys, hashlib, hmac, time
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/website-backend/.env')

from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

print("=" * 50)
print("1. CEK USERS DI DATABASE")
print("=" * 50)

c = create_client(url, key)
users = c.table('users').select('telegram_id, username, first_name, last_name, credits, is_premium, premium_until').limit(10).execute()

if not users.data:
    print("ERROR: Tidak ada user di database!")
    sys.exit(1)

print(f"Total users ditemukan: {len(users.data)}")
for u in users.data:
    print(f"  tg_id={u['telegram_id']} | @{u.get('username','?')} | {u.get('first_name','?')} | credits={u.get('credits',0)} | premium={u.get('is_premium',False)}")

print()
print("=" * 50)
print("2. TEST GENERATE JWT TOKEN (simulate login)")
print("=" * 50)

# Test dengan user pertama yang ada
test_user = users.data[0]
tg_id = test_user['telegram_id']

# Generate valid Telegram auth hash untuk test
def make_test_hash(tg_id, first_name, username, auth_date, bot_token):
    data = {
        'id': str(tg_id),
        'first_name': first_name or 'User',
        'auth_date': str(auth_date),
    }
    if username:
        data['username'] = username
    
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return h, data

auth_date = int(time.time())
h, fields = make_test_hash(
    tg_id,
    test_user.get('first_name', 'User'),
    test_user.get('username'),
    auth_date,
    bot_token
)

print(f"Test user: tg_id={tg_id}, username=@{test_user.get('username','?')}")
print(f"Generated hash: {h[:20]}...")

# Verify hash locally
from app.auth.telegram import verify_telegram_auth
payload = {**fields, 'hash': h, 'auth_date': auth_date}
valid = verify_telegram_auth(payload)
print(f"Hash verification: {'VALID' if valid else 'INVALID'}")

if valid:
    from app.auth.jwt import create_token
    token = create_token(tg_id, extra={'username': test_user.get('username'), 'first_name': test_user.get('first_name')})
    print(f"JWT token generated: {token[:40]}...")
    print()
    print("LOGIN FLOW: OK - User bisa login ke website")
else:
    print("ERROR: Hash verification gagal - cek TELEGRAM_BOT_TOKEN di .env")

print()
print("=" * 50)
print("3. CEK DATA KONSISTENSI BOT vs WEBSITE")
print("=" * 50)

# Cek apakah field yang dibutuhkan website ada semua
required_fields = ['telegram_id', 'username', 'first_name', 'credits', 'is_premium']
for u in users.data[:3]:
    missing = [f for f in required_fields if f not in u or u[f] is None]
    status = "OK" if not missing else f"MISSING: {missing}"
    print(f"  @{u.get('username','?')} (id={u['telegram_id']}): {status}")
