import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from app.db.supabase import _client
s = _client()

# active tapi engine=False, atau uid_verified dengan balance
to_start = [1234500019, 1234500018, 6954315669, 1234500016, 1234500017, 1087836223]

for tg_id in to_start:
    s.table("autotrade_sessions").update({
        "status": "active",
        "engine_active": True
    }).eq("telegram_id", tg_id).execute()
    print(f"Started: TG:{tg_id}")

print("Done")
