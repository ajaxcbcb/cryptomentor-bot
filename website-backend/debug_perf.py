import sys
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
import os
os.chdir('/root/cryptomentor-bot/website-backend')

from app.db.supabase import _client
s = _client()

# Cek total closed trades
res = s.table("autotrade_trades").select("telegram_id, pnl_usdt, closed_at").eq("status", "closed").limit(5).execute()
print("Closed trades sample:", res.data)

# Cek untuk user 123456789
res2 = s.table("autotrade_trades").select("pnl_usdt, closed_at").eq("telegram_id", 123456789).eq("status", "closed").limit(5).execute()
print("User 123456789 trades:", res2.data)
