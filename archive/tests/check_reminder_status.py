"""
Cek status pengiriman reminder autotrade di Supabase.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Bismillah"))

from dotenv import load_dotenv
load_dotenv("/root/cryptomentor-bot/.env", override=True)

from app.supabase_repo import _client
s = _client()

print("=" * 50)
print("REMINDER LOG STATUS")
print("=" * 50)

# Total records
total = s.table("autotrade_reminder_log").select("id", count="exact").execute()
print(f"Total records di reminder_log : {total.count}")

# Dikirim hari ini
today = s.table("autotrade_reminder_log").select("telegram_id", count="exact").eq("sent_date", "2026-03-29").execute()
print(f"Dikirim hari ini (2026-03-29) : {today.count}")

# Total user di DB
users = s.table("users").select("telegram_id", count="exact").execute()
print(f"Total user di DB              : {users.count}")

# User dengan autotrade session
at = s.table("autotrade_sessions").select("telegram_id", count="exact").execute()
print(f"User dengan autotrade session : {at.count}")

print()
print("Sample 5 record reminder_log:")
sample = s.table("autotrade_reminder_log").select("telegram_id, sent_date, count").limit(5).execute()
for r in (sample.data or []):
    print(f"  uid={r['telegram_id']} | date={r['sent_date']} | count={r['count']}")

print()
print("Selesai.")
