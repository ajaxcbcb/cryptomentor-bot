#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/root/cryptomentor-bot/website-backend')
sys.path.insert(0, '/root/cryptomentor-bot/Bismillah')
os.chdir('/root/cryptomentor-bot/website-backend')
from dotenv import load_dotenv
load_dotenv('.env')

from app.auth.jwt import create_token
from app.db.supabase import _client
import subprocess

tg_id = 1234500009
tok = create_token(tg_id)

s = _client()
res = s.table('autotrade_sessions').select('telegram_id,status,engine_active').eq('telegram_id', tg_id).execute()
print('DB before:', res.data)

r = subprocess.run(
    ['curl', '-s', '-X', 'POST', 'http://localhost:8000/dashboard/engine/stop',
     '-H', 'Authorization: Bearer ' + tok],
    capture_output=True, text=True
)
print('STOP response:', r.stdout)

res2 = s.table('autotrade_sessions').select('telegram_id,status,engine_active').eq('telegram_id', tg_id).execute()
print('DB after:', res2.data)
