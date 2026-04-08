import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from app.db.supabase import _client
s = _client()

print("=" * 60)
print("USERS WITH TRADES vs WITHOUT TRADES")
print("=" * 60)

# Users yang punya trades
trades_res = s.table("autotrade_trades").select("telegram_id").execute()
users_with_trades = set(t["telegram_id"] for t in (trades_res.data or []))
print(f"\nUsers with trades: {len(users_with_trades)}")
print(f"IDs: {list(users_with_trades)[:10]}")

# Semua autotrade sessions
sessions_res = s.table("autotrade_sessions").select(
    "telegram_id, status, engine_active, trading_mode, exchange, exchange_uid, "
    "auto_mode_enabled"
).execute()

print(f"\nTotal sessions: {len(sessions_res.data or [])}")
print("\n--- SESSIONS WITH TRADES ---")
for s_row in (sessions_res.data or []):
    tid = s_row["telegram_id"]
    if tid in users_with_trades:
        print(f"  TG:{tid} | status={s_row.get('status')} | engine={s_row.get('engine_active')} | "
              f"exchange={s_row.get('exchange')} | uid={s_row.get('exchange_uid')} | "
              f"mode={s_row.get('trading_mode')} | auto={s_row.get('auto_mode_enabled')}")

print("\n--- SESSIONS WITHOUT TRADES ---")
for s_row in (sessions_res.data or []):
    tid = s_row["telegram_id"]
    if tid not in users_with_trades:
        print(f"  TG:{tid} | status={s_row.get('status')} | engine={s_row.get('engine_active')} | "
              f"exchange={s_row.get('exchange')} | uid={s_row.get('exchange_uid')} | "
              f"mode={s_row.get('trading_mode')} | auto={s_row.get('auto_mode_enabled')}")

# Cek API keys
print("\n--- API KEYS STATUS ---")
keys_res = s.table("user_api_keys").select("telegram_id, exchange, key_hint").execute()
keys_by_user = {k["telegram_id"]: k for k in (keys_res.data or [])}
print(f"Users with API keys: {list(keys_by_user.keys())}")

# Cek users yang punya session tapi tidak punya trades
no_trade_sessions = [s_row for s_row in (sessions_res.data or []) 
                     if s_row["telegram_id"] not in users_with_trades]
print(f"\nUsers with session but NO trades: {len(no_trade_sessions)}")
for s_row in no_trade_sessions:
    tid = s_row["telegram_id"]
    has_key = tid in keys_by_user
    print(f"  TG:{tid} | has_api_key={has_key} | status={s_row.get('status')} | "
          f"engine={s_row.get('engine_active')} | exchange_uid={s_row.get('exchange_uid')}")
