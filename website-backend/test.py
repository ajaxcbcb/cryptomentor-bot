from app.db.supabase import _client

res = _client().table('autotrade_sessions').select('*').limit(1).execute()
print(res.data[0].keys() if res.data else 'No data')