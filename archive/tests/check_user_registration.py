"""
Diagnostic: cek kondisi registrasi user di database.
Jalankan di VPS: python3 check_user_registration.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Bismillah"))
from dotenv import load_dotenv
load_dotenv("/root/cryptomentor-bot/.env", override=True)

from app.supabase_repo import _client
from datetime import datetime, timedelta

s = _client()

print("=" * 60)
print("USER REGISTRATION DIAGNOSTIC")
print("=" * 60)

# 1. Total user
total = s.table("users").select("telegram_id", count="exact").execute()
print(f"\n📊 Total users di DB       : {total.count}")

# 2. User baru 7 hari terakhir
week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
new_week = s.table("users").select("telegram_id", count="exact").gte("created_at", week_ago).execute()
print(f"🆕 User baru 7 hari terakhir: {new_week.count}")

# 3. User baru hari ini
today = datetime.utcnow().date().isoformat()
new_today = s.table("users").select("telegram_id", count="exact").gte("created_at", today).execute()
print(f"🆕 User baru hari ini       : {new_today.count}")

# 4. Cek apakah ada user tanpa created_at (data lama)
no_date = s.table("users").select("telegram_id", count="exact").is_("created_at", "null").execute()
print(f"⚠️  User tanpa created_at   : {no_date.count}")

print("\n" + "=" * 60)
print("AUTOTRADE SESSIONS")
print("=" * 60)

# 5. Total autotrade sessions
at_total = s.table("autotrade_sessions").select("telegram_id", count="exact").execute()
print(f"\n📊 Total autotrade sessions : {at_total.count}")

# 6. Breakdown by status
for status in ["active", "uid_verified", "pending_verification", "stopped"]:
    res = s.table("autotrade_sessions").select("telegram_id", count="exact").eq("status", status).execute()
    print(f"   [{status}]: {res.count}")

print("\n" + "=" * 60)
print("REGISTRASI BARU (7 HARI TERAKHIR)")
print("=" * 60)

# 7. User baru yang TIDAK tersimpan di users table
# Cek apakah ada user yang punya autotrade_session tapi tidak ada di users
at_ids_res = s.table("autotrade_sessions").select("telegram_id, status, updated_at").order(
    "updated_at", desc=True
).limit(20).execute()

print(f"\n🔍 Autotrade sessions baru 7 hari: {len(at_ids_res.data or [])}")
for row in (at_ids_res.data or []):
    uid = row["telegram_id"]
    status = row["status"]
    created = row.get("updated_at", "?")[:10]
    # Cek apakah ada di users table
    user_check = s.table("users").select("telegram_id").eq("telegram_id", uid).limit(1).execute()
    in_users = "✅" if user_check.data else "❌ MISSING FROM USERS"
    print(f"   uid={uid} | status={status} | created={created} | users_table={in_users}")

print("\n" + "=" * 60)
print("CEK USER BARU YANG TIDAK MASUK DB")
print("=" * 60)

# 8. Cek bot logs untuk error registrasi - lihat user terbaru
recent_users = s.table("users").select("telegram_id, first_name, created_at").order(
    "created_at", desc=True
).limit(10).execute()

print(f"\n👥 10 user terbaru di DB:")
for u in (recent_users.data or []):
    print(f"   uid={u['telegram_id']} | name={u.get('first_name','?')} | joined={str(u.get('created_at','?'))[:10]}")

print("\n" + "=" * 60)
print("KESIMPULAN")
print("=" * 60)
if new_week.count == 0:
    print("\n🚨 MASALAH: Tidak ada user baru dalam 7 hari!")
    print("   Kemungkinan: /start tidak menyimpan user ke DB")
elif new_today.count == 0:
    print(f"\n⚠️  Tidak ada user baru hari ini (tapi ada {new_week.count} minggu ini)")
else:
    print(f"\n✅ Registrasi berjalan normal: {new_today.count} user baru hari ini")

print("\nSelesai.")
