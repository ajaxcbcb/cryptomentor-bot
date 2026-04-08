import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
os.chdir('/root/cryptomentor-bot/website-backend')

from app.db.supabase import _client
s = _client()

# active tapi engine=False, atau uid_verified dengan balance
to_start = [8429733088, 1766523174, 6954315669, 1306878013, 7338184122, 1087836223]

for tg_id in to_start:
    s.table("autotrade_sessions").update({
        "status": "active",
        "engine_active": True
    }).eq("telegram_id", tg_id).execute()
    print(f"Started: TG:{tg_id}")

print("Done")
