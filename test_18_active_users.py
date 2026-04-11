"""
Test all 18 active real users:
1. API key valid (can connect to Bitunix)
2. Account balance > 0 (can trade)
3. Report issues
"""
import os
from dotenv import load_dotenv
load_dotenv('/root/cryptomentor-bot/.env')

from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
s = create_client(url, key)

DEMO_USER_IDS = {1234500001, 1234500002, 1234500003, 1234500004, 1234500005}
SKIP = {999999999, 999999998, 999999997, 500000025, 500000026, 8468773924, 899183408}

# Get 18 active real users
sess_res = s.table('autotrade_sessions').select('telegram_id, status, engine_active, leverage, initial_deposit, trading_mode').eq('status', 'active').execute()
active_uids = [
    r for r in (sess_res.data or [])
    if r.get('telegram_id')
    and int(r.get('telegram_id', 0)) not in DEMO_USER_IDS
    and int(r.get('telegram_id', 0)) not in SKIP
]
print(f"Active real users to test: {len(active_uids)}\n")

import sys
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')

from app.lib.crypto import decrypt
from app.bitunix_autotrade_client import BitunixAutoTradeClient

ok_users = []
problem_users = []

for sess in active_uids:
    uid = int(sess['telegram_id'])
    mode = sess.get('trading_mode', 'scalping')
    leverage = sess.get('leverage', 10)
    deposit = sess.get('initial_deposit', 0)

    # Get API keys
    kr = s.table('user_api_keys').select('api_key, api_secret_enc, key_hint, exchange').eq('telegram_id', uid).limit(1).execute()
    if not kr.data:
        print(f"  UID {uid} | ❌ NO API KEYS")
        problem_users.append({'uid': uid, 'issue': 'No API keys'})
        continue

    row = kr.data[0]
    hint = row.get('key_hint', '???')
    exchange = row.get('exchange', 'bitunix')

    try:
        secret = decrypt(row['api_secret_enc'])
    except Exception as e:
        print(f"  UID {uid} | ...{hint} | ❌ DECRYPT FAIL: {e}")
        problem_users.append({'uid': uid, 'issue': f'Decrypt failed: {e}'})
        continue

    # Test connection + get balance
    try:
        client = BitunixAutoTradeClient(api_key=row['api_key'], api_secret=secret)
        conn = client.check_connection()
        if not conn.get('online'):
            err = conn.get('error', 'offline')
            print(f"  UID {uid} | ...{hint} | ❌ CONNECTION FAIL: {err}")
            problem_users.append({'uid': uid, 'issue': f'Connection failed: {err}'})
            continue

        # Get account balance
        acc = client.get_account_info()
        if acc.get('success'):
            available = float(acc.get('available', 0) or 0)
            frozen = float(acc.get('frozen', 0) or 0)
            balance = available + frozen
            can_trade = balance >= 1.0  # minimum $1 to trade
            status = "✅ CAN TRADE" if can_trade else "⚠️ LOW BALANCE"
            print(f"  UID {uid} | ...{hint} | {exchange} | {mode} | {leverage}x | bal=${balance:.2f} | {status}")
            if can_trade:
                ok_users.append({'uid': uid, 'balance': balance, 'mode': mode})
            else:
                problem_users.append({'uid': uid, 'issue': f'Balance too low: ${balance:.2f}'})
        else:
            print(f"  UID {uid} | ...{hint} | ⚠️ Connected but can't fetch balance")
            ok_users.append({'uid': uid, 'balance': 0, 'mode': mode})

    except Exception as e:
        print(f"  UID {uid} | ...{hint} | ❌ ERROR: {str(e)[:60]}")
        problem_users.append({'uid': uid, 'issue': str(e)[:60]})

print(f"\n{'='*50}")
print(f"✅ Can trade: {len(ok_users)}/{len(active_uids)}")
print(f"❌ Problems: {len(problem_users)}/{len(active_uids)}")

if ok_users:
    total_bal = sum(u['balance'] for u in ok_users)
    print(f"💰 Total balance across active users: ${total_bal:,.2f}")

if problem_users:
    print(f"\nUsers with issues:")
    for u in problem_users:
        print(f"  UID {u['uid']} — {u['issue']}")
